import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from consulta_cpf import (
    _check_response,
    consultar_cpf,
    limpar_cpf,
    validar_cpf,
)


def test_limpar_cpf_removes_formatting():
    assert limpar_cpf("404.428.201-35") == "40442820135"


def test_limpar_cpf_leaves_digits_unchanged():
    assert limpar_cpf("40442820135") == "40442820135"


def test_validar_cpf_accepts_11_digits():
    validar_cpf("40442820135")  # must not raise


def test_validar_cpf_rejects_short():
    with pytest.raises(ValueError, match="11 dígitos"):
        validar_cpf("1234567890")


def test_validar_cpf_rejects_non_numeric():
    with pytest.raises(ValueError, match="11 dígitos"):
        validar_cpf("4044282013X")


def _mock_response(status_code: int, json_data: dict = None) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    return mock


def test_consultar_cpf_success():
    expected = {
        "ni": "40442820135",
        "nome": "Pessoa Teste",
        "situacao": {"codigo": "0", "descricao": "Regular"},
    }
    with patch("consulta_cpf.obter_token", return_value="tok"):
        with patch("consulta_cpf.requests.get", return_value=_mock_response(200, expected)):
            result = consultar_cpf("40442820135")
    assert result == expected


def test_consultar_cpf_cleans_input():
    with patch("consulta_cpf.obter_token", return_value="tok"):
        with patch("consulta_cpf.requests.get", return_value=_mock_response(200)) as mock_get:
            consultar_cpf("404.428.201-35")
    called_url = mock_get.call_args[0][0]
    assert "40442820135" in called_url


def test_consultar_cpf_prod_url_by_default():
    with patch("consulta_cpf.obter_token", return_value="tok"):
        with patch("consulta_cpf.requests.get", return_value=_mock_response(200)) as mock_get:
            consultar_cpf("40442820135")
    called_url = mock_get.call_args[0][0]
    assert "trial" not in called_url
    assert "consulta-cpf-df/v2" in called_url


def test_consultar_cpf_trial_uses_trial_url():
    with patch("consulta_cpf.obter_token", return_value="tok"):
        with patch("consulta_cpf.requests.get", return_value=_mock_response(200)) as mock_get:
            consultar_cpf("40442820135", trial=True)
    called_url = mock_get.call_args[0][0]
    assert "trial" in called_url


def test_consultar_cpf_retries_on_401():
    resp_401 = _mock_response(401)
    resp_200 = _mock_response(200, {"ni": "40442820135"})
    with patch("consulta_cpf.obter_token", side_effect=["token1", "token2"]):
        with patch("consulta_cpf.requests.get", side_effect=[resp_401, resp_200]):
            result = consultar_cpf("40442820135")
    assert result == {"ni": "40442820135"}


def test_consultar_cpf_raises_on_422_lgpd():
    with patch("consulta_cpf.obter_token", return_value="tok"):
        with patch("consulta_cpf.requests.get", return_value=_mock_response(422)):
            with pytest.raises(RuntimeError, match="menor de 18"):
                consultar_cpf("30272095079")


def test_consultar_cpf_raises_on_451_lgpd():
    with patch("consulta_cpf.obter_token", return_value="tok"):
        with patch("consulta_cpf.requests.get", return_value=_mock_response(451)):
            with pytest.raises(RuntimeError, match="menor de 16"):
                consultar_cpf("20803407009")


def test_consultar_cpf_raises_on_404():
    with patch("consulta_cpf.obter_token", return_value="tok"):
        with patch("consulta_cpf.requests.get", return_value=_mock_response(404)):
            with pytest.raises(RuntimeError, match="não encontrado"):
                consultar_cpf("40442820135")


def test_consultar_cpf_raises_on_400():
    with patch("consulta_cpf.obter_token", return_value="tok"):
        with patch("consulta_cpf.requests.get", return_value=_mock_response(400)):
            with pytest.raises(RuntimeError, match="inválido"):
                consultar_cpf("40442820135")


def test_consultar_cpf_raises_on_406_invalid_accept():
    with patch("consulta_cpf.obter_token", return_value="tok"):
        with patch("consulta_cpf.requests.get", return_value=_mock_response(406)):
            with pytest.raises(RuntimeError, match="Accept"):
                consultar_cpf("40442820135")


def test_check_response_allows_206():
    _check_response(_mock_response(206))  # must not raise


def test_consultar_cpf_raises_on_invalid_format():
    with pytest.raises(ValueError, match="11 dígitos"):
        consultar_cpf("123")
