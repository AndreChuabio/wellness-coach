"""
startup.py - Materialize Google credentials from env vars on Railway.

Railway doesn't have a writable repo for credentials.json / token.pickle,
so we accept them as env vars and write them to /tmp at boot:

  GOOGLE_CREDENTIALS_JSON         -> /tmp/credentials.json
  GOOGLE_TOKEN_PICKLE_B64_<USER>  -> /tmp/token_<user>.pickle

After this runs, calendar_fetch.py finds the files via its standard lookup.
Locally, env vars are usually unset and we no-op.
"""

import base64
import logging
import os
from pathlib import Path

from users import USERS

logger = logging.getLogger(__name__)

TMP_DIR = Path("/tmp")
TMP_CREDENTIALS = TMP_DIR / "credentials.json"


def _tmp_token_path(user: str) -> Path:
    return TMP_DIR / f"token_{user}.pickle"


def materialize_railway_creds() -> None:
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        TMP_CREDENTIALS.write_text(creds_json)
        # Expose via the standard env var so calendar_fetch picks it up
        os.environ.setdefault("GOOGLE_CREDENTIALS_PATH", str(TMP_CREDENTIALS))
        logger.info("Materialized GOOGLE_CREDENTIALS_JSON -> %s", TMP_CREDENTIALS)

    for user in USERS:
        env_key = f"GOOGLE_TOKEN_PICKLE_B64_{user.upper()}"
        b64 = os.getenv(env_key)
        if not b64:
            continue
        try:
            raw = base64.b64decode(b64)
        except Exception as e:
            logger.error("Could not base64-decode %s: %s", env_key, e)
            continue
        path = _tmp_token_path(user)
        path.write_bytes(raw)
        # Per-user override env var, picked up by calendar_fetch
        os.environ.setdefault(f"GOOGLE_TOKEN_PATH_{user.upper()}", str(path))
        logger.info("Materialized %s -> %s (%d bytes)", env_key, path, len(raw))
