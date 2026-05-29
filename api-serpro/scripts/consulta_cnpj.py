import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))

import requests
from obter_token import obter_token

PROD_BASE = "https://gateway.apiserpro.serpro.gov.br/consulta-cnpj-df/v2"
TRIAL_BASE = "https://gateway.apiserpro.serpro.gov.br/consulta-cnpj-df-trial/v2"

_ERROR_MESSAGES: Dict[int, str] = {
    400: "CNPJ inválido (formato incorreto).",
    401: "Não autorizado. Token inválido ou expirado.",
    403: "Acesso proibido. Verifique o caminho da requisição.",
    404: "CNPJ não encontrado na base de dados.",
    500: "Erro interno no servidor SERPRO.",
    502: "Erro de integração no gateway SERPRO.",
    504: "Timeout no gateway SERPRO.",
}


def limpar_cnpj(cnpj: str) -> str:
    """Remove '.', '/', '-' formatting characters from a CNPJ string."""
    return re.sub(r"[./\-]", "", cnpj)


def validar_cnpj(cnpj: str) -> None:
    """Raise ValueError if CNPJ does not contain exactly 14 numeric digits."""
    if not re.fullmatch(r"\d{14}", cnpj):
        raise ValueError(
            f"CNPJ inválido: '{cnpj}'. Deve conter exatamente 14 dígitos numéricos."
        )


def _make_request(url: str, headers: Dict[str, str]) -> requests.Response:
    """Execute GET request, converting network errors to descriptive exceptions."""
    try:
        return requests.get(url, headers=headers, timeout=30)
    except requests.exceptions.ConnectionError as exc:
        raise ConnectionError(f"Falha de conexão à API SERPRO CNPJ: {exc}") from exc
    except requests.exceptions.Timeout:
        raise TimeoutError("Timeout na consulta CNPJ (30s)")


def _check_response(response: requests.Response) -> None:
    """Raise RuntimeError with descriptive message for non-2xx responses."""
    if response.status_code in (200, 206):
        return
    msg = _ERROR_MESSAGES.get(
        response.status_code, f"Erro desconhecido: HTTP {response.status_code}"
    )
    raise RuntimeError(f"Erro na consulta CNPJ: {msg}")


def consultar_cnpj(
    cnpj: str,
    endpoint: str = "basica",
    trial: bool = False,
    carimbo: bool = False,
    tag: Optional[str] = None,
) -> dict:
    """Query the SERPRO CNPJ API and return the parsed JSON response.

    Args:
        cnpj: CNPJ with or without formatting characters.
        endpoint: One of 'basica', 'qsa', 'empresa'.
        trial: Use the trial (test) environment when True.
        carimbo: Request a timestamp signature via x-signature header.
        tag: Optional billing tag (truncated to 32 chars).

    Returns:
        Parsed JSON dict from the SERPRO response.
    """
    cnpj = limpar_cnpj(cnpj)
    validar_cnpj(cnpj)

    base_url = TRIAL_BASE if trial else PROD_BASE
    url = f"{base_url}/{endpoint}/{cnpj}"

    token = obter_token()
    headers: Dict[str, str] = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    if carimbo:
        headers["x-signature"] = "1"
    if tag:
        headers["X-Request-Tag"] = tag[:32]

    response = _make_request(url, headers)

    if response.status_code == 401:
        token = obter_token(force_refresh=True)
        headers["Authorization"] = f"Bearer {token}"
        response = _make_request(url, headers)

    _check_response(response)
    return response.json()


def main() -> None:
    """CLI entry point for CNPJ consultation."""
    parser = argparse.ArgumentParser(description="Consulta CNPJ na API do SERPRO")
    parser.add_argument("cnpj", help="CNPJ a consultar (com ou sem formatação)")
    parser.add_argument(
        "--endpoint",
        choices=["basica", "qsa", "empresa"],
        default="basica",
        help="Endpoint da API (padrão: basica)",
    )
    parser.add_argument("--trial", action="store_true", help="Usar ambiente trial")
    parser.add_argument("--pretty", action="store_true", help="Imprimir JSON formatado")
    parser.add_argument(
        "--carimbo", action="store_true", help="Solicitar Carimbo de Tempo"
    )
    parser.add_argument("--tag", help="Tag de agrupamento no faturamento (máx 32 chars)")
    args = parser.parse_args()

    try:
        resultado = consultar_cnpj(
            cnpj=args.cnpj,
            endpoint=args.endpoint,
            trial=args.trial,
            carimbo=args.carimbo,
            tag=args.tag,
        )
        print(json.dumps(resultado, ensure_ascii=False, indent=2 if args.pretty else None))
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
