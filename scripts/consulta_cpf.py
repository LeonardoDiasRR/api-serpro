import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent))

import requests
from obter_token import obter_token

PROD_BASE = "https://gateway.apiserpro.serpro.gov.br/consulta-cpf-df/v2"
TRIAL_BASE = "https://gateway.apiserpro.serpro.gov.br/consulta-cpf-df-trial/v1"

_ERROR_MESSAGES: Dict[int, str] = {
    400: "CPF inválido (formato incorreto).",
    401: "Não autorizado. Token inválido ou expirado.",
    403: "Acesso proibido. Verifique o caminho da requisição.",
    404: "CPF não encontrado na base de dados.",
    406: "Header Accept inválido. Use 'application/json'.",
    422: "Dados de menor de 18 anos bloqueados por LGPD.",
    451: "Dados de menor de 16 anos bloqueados (Lei Felca / LGPD).",
    500: "Erro interno no servidor SERPRO.",
    504: "Timeout no gateway SERPRO.",
}


def limpar_cpf(cpf: str) -> str:
    """Remove '.' and '-' formatting characters from a CPF string."""
    return re.sub(r"[.\-]", "", cpf)


def validar_cpf(cpf: str) -> None:
    """Raise ValueError if CPF does not contain exactly 11 numeric digits."""
    if not re.fullmatch(r"\d{11}", cpf):
        raise ValueError(
            f"CPF inválido: '{cpf}'. Deve conter exatamente 11 dígitos numéricos."
        )


def _make_request(url: str, headers: Dict[str, str]) -> requests.Response:
    """Execute GET request, converting network errors to descriptive exceptions."""
    try:
        return requests.get(url, headers=headers, timeout=30)
    except requests.exceptions.ConnectionError as exc:
        raise ConnectionError(f"Falha de conexão à API SERPRO CPF: {exc}") from exc
    except requests.exceptions.Timeout:
        raise TimeoutError("Timeout na consulta CPF (30s)")


def _check_response(response: requests.Response) -> None:
    """Raise RuntimeError with descriptive message for non-2xx responses."""
    if response.status_code in (200, 206):
        return
    msg = _ERROR_MESSAGES.get(
        response.status_code, f"Erro desconhecido: HTTP {response.status_code}"
    )
    raise RuntimeError(f"Erro na consulta CPF: {msg}")


def consultar_cpf(cpf: str, trial: bool = False) -> dict:
    """Query the SERPRO CPF API and return the parsed JSON response.

    Args:
        cpf: CPF with or without formatting characters.
        trial: Use the trial (test) environment when True.

    Returns:
        Parsed JSON dict from the SERPRO response.
    """
    cpf = limpar_cpf(cpf)
    validar_cpf(cpf)

    base_url = TRIAL_BASE if trial else PROD_BASE
    url = f"{base_url}/cpf/{cpf}"

    token = obter_token()
    headers: Dict[str, str] = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }

    response = _make_request(url, headers)

    if response.status_code == 401:
        token = obter_token(force_refresh=True)
        headers["Authorization"] = f"Bearer {token}"
        response = _make_request(url, headers)

    _check_response(response)
    return response.json()


def main() -> None:
    """CLI entry point for CPF consultation."""
    parser = argparse.ArgumentParser(description="Consulta CPF na API do SERPRO")
    parser.add_argument("cpf", help="CPF a consultar (com ou sem formatação)")
    parser.add_argument("--trial", action="store_true", help="Usar ambiente trial")
    parser.add_argument("--pretty", action="store_true", help="Imprimir JSON formatado")
    args = parser.parse_args()

    try:
        resultado = consultar_cpf(cpf=args.cpf, trial=args.trial)
        print(json.dumps(resultado, ensure_ascii=False, indent=2 if args.pretty else None))
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
