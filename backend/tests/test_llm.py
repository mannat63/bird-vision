"""Groq LLM enrichment tests with mocked HTTP/generation (no live API calls)."""

from __future__ import annotations

import json

import httpx
import pytest

from app.services import llm


@pytest.fixture(autouse=True)
def _clear_cache():
    llm._cache.clear()
    yield
    llm._cache.clear()


# --- schema validation / public API --------------------------------------- #
def test_species_intelligence_validates_schema(monkeypatch):
    payload = {
        "overview": "A seabird.", "physical_features": ["dark plumage"],
        "habitat": "open ocean", "diet": "fish", "behavior": "soaring",
        "interesting_facts": ["long-lived"], "conservation": "near threatened",
        "follow_up_questions": ["a", "b", "c"],
    }
    monkeypatch.setattr(llm, "_generate", lambda prompt, as_json=False: json.dumps(payload))
    out = llm.species_intelligence("Black footed Albatross", "Phoebastria nigripes")
    assert out["habitat"] == "open ocean"
    assert "Groq" in out["_disclaimer"]


def test_species_intelligence_rejects_incomplete(monkeypatch):
    monkeypatch.setattr(llm, "_generate", lambda prompt, as_json=False: json.dumps({"overview": "x"}))
    with pytest.raises(llm.LLMError):
        llm.species_intelligence("X", None)


def test_ask_expert(monkeypatch):
    monkeypatch.setattr(llm, "_generate", lambda prompt, as_json=False: "They eat fish.")
    out = llm.ask_expert("Albatross", None, "What does it eat?")
    assert "fish" in out["answer"]


def test_parse_json_strips_code_fence():
    assert llm._parse_json('```json\n{"a": 1}\n```') == {"a": 1}


# --- error classification -------------------------------------------------- #
class _Exc(Exception):
    def __init__(self, msg, code=None):
        super().__init__(msg)
        if code is not None:
            self.code = code


def test_classify_status_codes():
    assert llm._kind_for_status(503) == ("unavailable", True)
    assert llm._kind_for_status(429) == ("rate_limited", True)
    assert llm._kind_for_status(401) == ("auth", False)
    assert llm._kind_for_status(400) == ("config", False)


def test_classify_transport_timeout():
    assert llm._classify_transport(httpx.ReadTimeout("timed out")) == ("timeout", True)
    assert llm._classify_transport(httpx.ConnectError("refused")) == ("unavailable", True)


# --- HTTP call + retry/fallback via mocked httpx --------------------------- #
class _Resp:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class _Client:
    def __init__(self, resp):
        self._resp = resp

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def post(self, url, json=None, headers=None):
        assert headers and headers["Authorization"].startswith("Bearer ")
        if isinstance(self._resp, Exception):
            raise self._resp
        return self._resp


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    yield
    get_settings.cache_clear()


def _ok_payload(text="hello"):
    return {"choices": [{"message": {"content": text}}]}


def test_call_model_success(monkeypatch):
    monkeypatch.setattr(httpx, "Client", lambda *a, **k: _Client(_Resp(200, _ok_payload("hi"))))
    assert llm._call_model("openai/gpt-oss-120b", "p", False) == "hi"


def test_call_model_503_is_retryable(monkeypatch):
    monkeypatch.setattr(httpx, "Client", lambda *a, **k: _Client(_Resp(503, {"error": {"message": "busy"}})))
    with pytest.raises(llm.LLMError) as e:
        llm._call_model("m", "p", False)
    assert e.value.kind == "unavailable"
    assert getattr(e.value, "retryable") is True


def test_call_model_401_not_retryable(monkeypatch):
    monkeypatch.setattr(httpx, "Client", lambda *a, **k: _Client(_Resp(401, {"error": {"message": "bad key"}})))
    with pytest.raises(llm.LLMError) as e:
        llm._call_model("m", "p", False)
    assert e.value.kind == "auth"
    assert getattr(e.value, "retryable") is False


def test_generate_on_retries_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def flaky(model, prompt, as_json):
        calls["n"] += 1
        if calls["n"] < 3:
            e = llm.LLMError("503", kind="unavailable"); e.retryable = True
            raise e
        return "ok"

    monkeypatch.setattr(llm, "_call_model", flaky)
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    assert llm._generate_on("m", "p", False) == "ok"
    assert calls["n"] == 3


def test_generate_on_stops_after_max_retries(monkeypatch):
    calls = {"n": 0}

    def always(model, prompt, as_json):
        calls["n"] += 1
        e = llm.LLMError("503", kind="unavailable"); e.retryable = True
        raise e

    monkeypatch.setattr(llm, "_call_model", always)
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    with pytest.raises(llm.LLMError):
        llm._generate_on("m", "p", False)
    assert calls["n"] == llm.MAX_RETRIES + 1


def test_generate_falls_back_to_secondary_model(monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setenv("GROQ_FALLBACK_MODEL", "openai/gpt-oss-20b")
    seen = []

    def per_model(model, prompt, as_json):
        seen.append(model)
        if model == "openai/gpt-oss-120b":
            e = llm.LLMError("503", kind="unavailable"); e.retryable = True
            raise e
        return "from-fallback"

    monkeypatch.setattr(llm, "_generate_on",
                        lambda model, prompt, aj: per_model(model, prompt, aj))
    out = llm._generate("p", as_json=False)
    assert out == "from-fallback"
    assert seen == ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
    get_settings.cache_clear()


def test_generate_does_not_fall_back_on_auth(monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    seen = []

    def per_model(model, prompt, aj):
        seen.append(model)
        raise llm.LLMError("bad key", kind="auth")

    monkeypatch.setattr(llm, "_generate_on", per_model)
    with pytest.raises(llm.LLMError):
        llm._generate("p")
    assert seen == ["openai/gpt-oss-120b"]  # no fallback on auth error
    get_settings.cache_clear()
