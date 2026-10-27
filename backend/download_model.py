"""Fetch the trained model artifact at startup if it is not already present.

The ~36 MB ``birdvision_model.keras`` is kept out of Git, so deployment hosts
download it on boot from a direct URL given in the ``MODEL_URL`` environment
variable (for example a GitHub Release asset). The small class map / config /
metrics JSON files ship in the repository and need no download.

Used by the container CMD and the Render start command:
    python download_model.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import os
import sys

from app.config import get_settings


def main() -> int:
    settings = get_settings()
    dest = settings.model_path
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"[model] already present: {dest} "
              f"({dest.stat().st_size / 1e6:.1f} MB)")
        return 0

    url = os.environ.get("MODEL_URL", "").strip()
    if not url:
        print("[model] ERROR: model file is missing and MODEL_URL is not set.\n"
              "        Set MODEL_URL to a direct download link for "
              "birdvision_model.keras (e.g. a GitHub Release asset).",
              file=sys.stderr)
        return 1

    import httpx

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"[model] downloading from {url}\n        -> {dest}")
    try:
        with httpx.stream("GET", url, follow_redirects=True, timeout=180) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_bytes(1 << 20):
                    f.write(chunk)
    except Exception as exc:  # noqa: BLE001
        print(f"[model] download failed: {exc}", file=sys.stderr)
        if dest.exists():
            dest.unlink(missing_ok=True)
        return 1

    size = dest.stat().st_size
    if size < 1_000_000:
        print(f"[model] downloaded file is too small ({size} bytes); "
              "check MODEL_URL.", file=sys.stderr)
        dest.unlink(missing_ok=True)
        return 1
    print(f"[model] done ({size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
