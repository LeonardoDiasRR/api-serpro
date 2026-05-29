import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

import requests

CACHE_FILE = Path(__file__).parent.parent / ".token_cache.json"
TOKEN_URL = "https://gateway.apiserpro.serpro.gov.br/token"
TOKEN_EXPIRY_BUFFER = 300  # 5 minutes


def _get_credentials() -> Tuple[str, str]:
    """Get consumer key and secret from environment variables."""
    key = os.environ.get("SERPRO_CONSUMER_KEY")
    secret = os.environ.get("SERPRO_CONSUMER_SECRET")
    if not key or not secret:
        raise ValueError(
            "SERPRO_CONSUMER_KEY and SERPRO_CONSUMER_SECRET must be set "
            "in environment variables or in a .env file"
        )
    return key, secret


def _load_cached_token() -> Optional[str]:
    """Load token from cache file if still valid (more than 5 min remaining)."""
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
        expires_at = cache.get("expires_at", 0)
        if time.time() < expires_at - TOKEN_EXPIRY_BUFFER:
            return cache.get("access_token")
    except (json.JSONDecodeError, KeyError, OSError):
        pass
    return None


def _save_token_to_cache(token: str, expires_in: int) -> None:
    """Persist token and expiry timestamp to cache file."""
    cache = {
        "access_token": token,
        "expires_at": time.time() + expires_in,
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def _fetch_new_token() -> str:
    """Request a new access token from SERPRO OAuth2 endpoint."""
    key, secret = _get_credentials()
    credentials = base64.b64encode(f"{key}:{secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    try:
        response = requests.post(
            TOKEN_URL,
            headers=headers,
            data="grant_type=client_credentials",
            timeout=30,
        )
    except requests.exceptions.ConnectionError as exc:
        raise ConnectionError(
            f"Falha de conexão ao servidor de autenticação SERPRO: {exc}"
        ) from exc
    except requests.exceptions.Timeout:
        raise TimeoutError("Timeout ao tentar obter token do SERPRO (30s)")

    if response.status_code == 401:
        raise PermissionError(
            "Credenciais inválidas. Verifique SERPRO_CONSUMER_KEY e SERPRO_CONSUMER_SECRET."
        )
    if not response.ok:
        raise RuntimeError(
            f"Erro ao obter token: HTTP {response.status_code} — {response.text}"
        )

    payload = response.json()
    token = payload["access_token"]
    expires_in = int(payload.get("expires_in", 3600))
    _save_token_to_cache(token, expires_in)
    return token


def obter_token(force_refresh: bool = False) -> str:
    """Return a valid SERPRO Bearer token, using the file cache when possible.

    Args:
        force_refresh: Skip cache and always fetch a new token.

    Returns:
        Access token string ready to use as 'Bearer <token>'.
    """
    if not force_refresh:
        cached = _load_cached_token()
        if cached:
            return cached
    return _fetch_new_token()


if __name__ == "__main__":
    try:
        print(obter_token())
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)
