"""LLM enrichment service — powered by Groq.

This is strictly an *enrichment* layer: it explains and summarizes a species that
the CNN already identified. It never classifies images, and the CNN remains fully
functional when the LLM is unavailable.

Uses Groq's OpenAI-compatible Chat Completions API over httpx. The API key is read
from the server environment and never exposed to the client. Models default to
``openai/gpt-oss-120b`` with ``openai/gpt-oss-20b`` as a transient-failure
fallback (both verified available on Groq).
"""

from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass

import httpx

from app.config import get_settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

_SYSTEM = (
    "You are a concise ornithology assistant for the BirdVision AI app. "
    "You are given a bird species that a separate CNN image classifier has "
    "identified. Explain and summarize factual information about that species. "
    "Prefer widely established facts; if you are unsure, say so rather than "
    "inventing specifics. Never claim to have seen the user's photo."
)

MAX_RETRIES = 2  # up to 2 retries (3 attempts) for transient errors only


class LLMError(RuntimeError):
    """LLM failure with a classified ``kind`` for clean frontend messaging.

    kind ∈ {unavailable, rate_limited, timeout, auth, quota, config, empty}.
    Only 'unavailable', 'rate_limited' and 'timeout' are transient/retryable.
    """

    def __init__(self, message: str, kind: str = "unavailable"):
        super().__init__(message)
        self.kind = kind


_STATUS_KIND = {
    400: ("config", False),
    401: ("auth", False),
    403: ("auth", False),
    404: ("config", False),
    413: ("config", False),
    422: ("config", False),
    429: ("rate_limited", True),
    500: ("unavailable", True),
    502: ("unavailable", True),
    503: ("unavailable", True),
    504: ("timeout", True),
}


def _kind_for_status(code: int) -> tuple[str, bool]:
    return _STATUS_KIND.get(code, ("unavailable", code >= 500))


def _classify_transport(exc: Exception) -> tuple[str, bool]:
    text = str(exc).lower()
    if "timed out" in text or "timeout" in text:
        return ("timeout", True)
    return ("unavailable", True)  # connection errors are transient


@dataclass
class _CacheEntry:
    expires: float
    value: dict


_cache: dict[str, _CacheEntry] = {}
_CACHE_TTL_S = 3600.0


def is_configured() -> bool:
    return bool(get_settings().groq_api_key)


def _call_model(model: str, prompt: str, as_json: bool) -> str:
    """One Groq chat-completion attempt; raises a classified LLMError."""
    settings = get_settings()
    if not settings.groq_api_key:
        raise LLMError("Groq API key not configured", kind="auth")
    payload: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_completion_tokens": 900,
    }
    if as_json:
        payload["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
    try:
        with httpx.Client(timeout=settings.groq_timeout_s) as client:
            resp = client.post(GROQ_URL, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        kind, retryable = _classify_transport(exc)
        err = LLMError(f"Groq request failed: {exc}", kind=kind)
        err.retryable = retryable  # type: ignore[attr-defined]
        raise err

    if resp.status_code >= 400:
        kind, retryable = _kind_for_status(resp.status_code)
        detail = _safe_error_detail(resp)
        err = LLMError(f"Groq error {resp.status_code}: {detail}", kind=kind)
        err.retryable = retryable  # type: ignore[attr-defined]
        raise err

    try:
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError) as exc:
        raise LLMError(f"Malformed Groq response: {exc}", kind="empty")
    if not text or not text.strip():
        raise LLMError("Groq returned an empty response", kind="empty")
    return text


def _safe_error_detail(resp: httpx.Response) -> str:
    """Extract a short, non-secret error message from an error response."""
    try:
        body = resp.json()
        return str(body.get("error", {}).get("message", ""))[:160]
    except ValueError:
        return resp.text[:160]


def _generate_on(model: str, prompt: str, as_json: bool) -> str:
    """One model with up to MAX_RETRIES retries on transient errors (exp
    backoff + jitter)."""
    last: LLMError | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return _call_model(model, prompt, as_json)
        except LLMError as exc:
            last = exc
            retryable = getattr(exc, "retryable", exc.kind in
                                ("unavailable", "rate_limited", "timeout"))
            if not retryable or attempt == MAX_RETRIES:
                raise
            delay = min(0.6 * (2 ** attempt), 3.0) + random.uniform(0, 0.3)
            time.sleep(delay)
    assert last is not None
    raise last


def _generate(prompt: str, as_json: bool = False) -> str:
    settings = get_settings()
    try:
        return _generate_on(settings.groq_model, prompt, as_json)
    except LLMError as primary:
        fallback = settings.groq_fallback_model
        # Fall back only for transient failures (never auth/quota/config), and
        # never for timeouts (the service is slow, not the model).
        if (
            fallback
            and fallback != settings.groq_model
            and primary.kind in ("unavailable", "rate_limited")
        ):
            try:
                return _generate_on(fallback, prompt, as_json)
            except LLMError:
                raise primary
        raise


# --------------------------------------------------------------------------- #
# Public enrichment API (unchanged signatures from the previous provider)
# --------------------------------------------------------------------------- #
def species_intelligence(common_name: str, scientific_name: str | None) -> dict:
    cache_key = f"intel::{common_name}::{scientific_name}"
    now = time.time()
    hit = _cache.get(cache_key)
    if hit and hit.expires > now:
        return hit.value

    sci = f" (scientific name: {scientific_name})" if scientific_name else ""
    prompt = (
        f"The species is '{common_name}'{sci}. Return a JSON object with keys: "
        "overview (string, 2 sentences), physical_features (array of strings), "
        "habitat (string), diet (string), behavior (string), "
        "interesting_facts (array of strings), conservation (string), "
        "follow_up_questions (array of 3 short strings). "
        "If the scientific name was not provided, do not invent one. "
        "Respond with only the JSON object."
    )
    data = _parse_json(_generate(prompt, as_json=True))
    required = {
        "overview", "physical_features", "habitat", "diet", "behavior",
        "interesting_facts", "conservation", "follow_up_questions",
    }
    if not required.issubset(data.keys()):
        raise LLMError("LLM response missing required fields", kind="empty")
    data["_disclaimer"] = (
        "Generated by Groq (openai/gpt-oss) as an explanation of a "
        "CNN-identified species. Treat as AI-generated enrichment, not "
        "independently verified data."
    )
    _cache[cache_key] = _CacheEntry(expires=now + _CACHE_TTL_S, value=data)
    return data


def ask_expert(common_name: str, scientific_name: str | None, question: str) -> dict:
    sci = f" (scientific name: {scientific_name})" if scientific_name else ""
    prompt = (
        f"The species in question is '{common_name}'{sci}. "
        f"Answer this birdwatching question clearly in 2-4 sentences: {question}"
    )
    answer = _generate(prompt, as_json=False)
    return {
        "answer": answer.strip(),
        "_disclaimer": "AI-generated answer (Groq) about a CNN-identified species.",
    }


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError("LLM returned invalid JSON", kind="empty") from exc
    if not isinstance(data, dict):
        raise LLMError("LLM JSON was not an object", kind="empty")
    return data


def _classify(exc: Exception) -> tuple[str, bool]:
    """Compatibility helper for tests: classify a raw exception."""
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if isinstance(code, int):
        return _kind_for_status(code)
    m = re.search(r"\b(400|401|403|404|429|500|502|503|504)\b", str(exc))
    if m:
        return _kind_for_status(int(m.group(1)))
    return _classify_transport(exc)
