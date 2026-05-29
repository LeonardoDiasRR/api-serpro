import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from consulta_cnpj import (
    _check_response,
    consultar_cnpj,
    limpar_cnpj,
    validar_cnpj,
)


def test_limpar_cnpj_removes_formatting():
    assert limpar_cnpj("34.238.864/0001-68") == "34238864000168"


def test_limpar_cnpj_leaves_digits_unchanged():
    assert limpar_cnpj("34238864000168") == "34238864000168"


def test_validar_cnpj_accepts_14_digits():
    validar_cnpj("34238864000168")  # must not raise


def test_validar_cnpj_rejects_short():
    with pytest.raises(ValueError, match="14 dígitos"):
        validar_cnpj("1234567890123")


def test_validar_cnpj_rejects_non_numeric():
    with pytest.raises(ValueError, match="14 dígitos"):
        validar_cnpj("3423886400016X")


def _mock_response(status_code: int, json_data: dict = None) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    return mock


def test_consultar_cnpj_success():
    expected = {"ni": "34238864000168", "nomeEmpresarial": "Empresa Teste"}
    with patch("consulta_cnpj.obter_token", return_value="tok"):
        with patch("consulta_cnpj.requests.get", return_value=_mock_response(200, expected)):
            result = consultar_cnpj("34238864000168")
    assert result == expected


def test_consultar_cnpj_cleans_input():
    with patch("consulta_cnpj.obter_token", return_value="tok"):
        with patch("consulta_cnpj.requests.get", return_value=_mock_response(200)) as mock_get:
            consultar_cnpj("34.238.864/0001-68")
    called_url = mock_get.call_args[0][0]
    assert "34238864000168" in called_url


def test_consultar_cnpj_prod_url_by_default():
    with patch("consulta_cnpj.obter_token", return_value="tok"):
        with patch("consulta_cnpj.requests.get", return_value=_mock_response(200)) as mock_get:
            consultar_cnpj("34238864000168")
    called_url = mock_get.call_args[0][0]
    assert "trial" not in called_url
    assert "consulta-cnpj-df/v2" in called_url


def test_consultar_cnpj_trial_uses_trial_url():
    with patch("consulta_cnpj.obter_token", return_value="tok"):
        with patch("consulta_cnpj.requests.get", return_value=_mock_response(200)) as mock_get:
            consultar_cnpj("34238864000168", trial=True)
    called_url = mock_get.call_args[0][0]
    assert "trial" in called_url


def test_consultar_cnpj_endpoint_empresa():
    with patch("consulta_cnpj.obter_token", return_value="tok"):
        with patch("consulta_cnpj.requests.get", return_value=_mock_response(200)) as mock_get:
            consultar_cnpj("34238864000168", endpoint="empresa")
    called_url = mock_get.call_args[0][0]
    assert "/empresa/" in called_url


def test_consultar_cnpj_carimbo_adds_header():
    with patch("consulta_cnpj.obter_token", return_value="tok"):
        with patch("consulta_cnpj.requests.get", return_value=_mock_response(200)) as mock_get:
            consultar_cnpj("34238864000168", carimbo=True)
    headers = mock_get.call_args[1]["headers"]
    assert headers.get("x-signature") == "1"


def test_consultar_cnpj_tag_truncated_to_32():
    long_tag = "A" * 50
    with patch("consulta_cnpj.obter_token", return_value="tok"):
        with patch("consulta_cnpj.requests.get", return_value=_mock_response(200)) as mock_get:
            consultar_cnpj("34238864000168", tag=long_tag)
    headers = mock_get.call_args[1]["headers"]
    assert len(headers.get("X-Request-Tag", "")) == 32


def test_consultar_cnpj_retries_on_401():
    resp_401 = _mock_response(401)
    resp_200 = _mock_response(200, {"ni": "34238864000168"})
    with patch("consulta_cnpj.obter_token", side_effect=["token1", "token2"]):
        with patch("consulta_cnpj.requests.get", side_effect=[resp_401, resp_200]):
            result = consultar_cnpj("34238864000168")
    assert result == {"ni": "34238864000168"}


def test_consultar_cnpj_raises_on_404():
    with patch("consulta_cnpj.obter_token", return_value="tok"):
        with patch("consulta_cnpj.requests.get", return_value=_mock_response(404)):
            with pytest.raises(RuntimeError, match="não encontrado"):
                consultar_cnpj("34238864000168")


def test_consultar_cnpj_raises_on_400():
    with patch("consulta_cnpj.obter_token", return_value="tok"):
        with patch("consulta_cnpj.requests.get", return_value=_mock_response(400)):
            with pytest.raises(RuntimeError, match="inválido"):
                consultar_cnpj("34238864000168")


def test_check_response_allows_206():
    _check_response(_mock_response(206))  # must not raise


def test_consultar_cnpj_raises_on_invalid_format():
    with pytest.raises(ValueError, match="14 dígitos"):
        consultar_cnpj("123")
