import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import obter_token as ot


@pytest.fixture(autouse=True)
def patch_cache_file(tmp_path):
    cache_path = tmp_path / ".token_cache.json"
    with patch.object(ot, "CACHE_FILE", cache_path):
        yield cache_path


@pytest.fixture(autouse=True)
def set_env_vars():
    with patch.dict(os.environ, {"SERPRO_CONSUMER_KEY": "test_key", "SERPRO_CONSUMER_SECRET": "test_secret"}):
        yield


def test_get_credentials_returns_key_and_secret():
    key, secret = ot._get_credentials()
    assert key == "test_key"
    assert secret == "test_secret"


def test_get_credentials_raises_when_missing():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="SERPRO_CONSUMER_KEY"):
            ot._get_credentials()


def test_load_cached_token_returns_none_when_no_cache(patch_cache_file):
    assert ot._load_cached_token() is None


def test_load_cached_token_returns_token_when_valid(patch_cache_file):
    cache = {"access_token": "valid_token", "expires_at": time.time() + 3600}
    patch_cache_file.write_text(json.dumps(cache))
    assert ot._load_cached_token() == "valid_token"


def test_load_cached_token_returns_none_when_expired(patch_cache_file):
    cache = {"access_token": "expired_token", "expires_at": time.time() - 1}
    patch_cache_file.write_text(json.dumps(cache))
    assert ot._load_cached_token() is None


def test_load_cached_token_returns_none_when_expiring_soon(patch_cache_file):
    # Token expiring in less than TOKEN_EXPIRY_BUFFER (300s) should not be returned
    cache = {"access_token": "expiring_token", "expires_at": time.time() + 100}
    patch_cache_file.write_text(json.dumps(cache))
    assert ot._load_cached_token() is None


def test_save_token_to_cache_writes_file(patch_cache_file):
    ot._save_token_to_cache("my_token", 3600)
    data = json.loads(patch_cache_file.read_text())
    assert data["access_token"] == "my_token"
    assert data["expires_at"] > time.time()


def test_fetch_new_token_success():
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "new_token", "expires_in": 3600}

    with patch("obter_token.requests.post", return_value=mock_response):
        with patch("obter_token._save_token_to_cache") as mock_save:
            token = ot._fetch_new_token()

    assert token == "new_token"
    mock_save.assert_called_once_with("new_token", 3600)


def test_fetch_new_token_raises_on_401():
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.ok = False

    with patch("obter_token.requests.post", return_value=mock_response):
        with pytest.raises(PermissionError, match="Credenciais inválidas"):
            ot._fetch_new_token()


def test_fetch_new_token_raises_on_non_ok():
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.ok = False
    mock_response.text = "Service Unavailable"

    with patch("obter_token.requests.post", return_value=mock_response):
        with pytest.raises(RuntimeError, match="503"):
            ot._fetch_new_token()


def test_obter_token_uses_cache_when_valid(patch_cache_file):
    cache = {"access_token": "cached_token", "expires_at": time.time() + 3600}
    patch_cache_file.write_text(json.dumps(cache))

    with patch("obter_token._fetch_new_token") as mock_fetch:
        token = ot.obter_token()

    assert token == "cached_token"
    mock_fetch.assert_not_called()


def test_obter_token_fetches_when_no_cache():
    with patch("obter_token._load_cached_token", return_value=None):
        with patch("obter_token._fetch_new_token", return_value="fresh_token") as mock_fetch:
            token = ot.obter_token()

    assert token == "fresh_token"
    mock_fetch.assert_called_once()


def test_obter_token_force_refresh_ignores_cache(patch_cache_file):
    cache = {"access_token": "cached_token", "expires_at": time.time() + 3600}
    patch_cache_file.write_text(json.dumps(cache))

    with patch("obter_token._fetch_new_token", return_value="fresh_token"):
        token = ot.obter_token(force_refresh=True)

    assert token == "fresh_token"
