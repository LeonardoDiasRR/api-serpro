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

_SITUACAO_CNPJ: Dict[str, str] = {
    "1": "Nula", "2": "Ativa", "3": "Suspensa",
    "4": "Inapta", "5": "Ativa Não Regular", "8": "Baixada",
}

_TIPO_LOGRADOURO: Dict[str, str] = {
    "AVENIDA": "Av.", "RUA": "Rua", "RODOVIA": "Rod.", "ALAMEDA": "Al.",
    "TRAVESSA": "Tv.", "LARGO": "Lg.", "PRAÇA": "Pça.", "SETOR": "St.",
    "QUADRA": "Qd.", "ESTRADA": "Est.",
}

_TIPO_SOCIO: Dict[str, str] = {
    "1": "Pessoa Jurídica", "2": "Pessoa Física", "3": "Sócio Estrangeiro",
}

_QUALIFICACAO_SOCIO: Dict[str, str] = {
    "05": "Administrador", "08": "Conselheiro de Administração", "10": "Diretor",
    "16": "Presidente", "17": "Procurador", "18": "Secretário",
    "20": "Sociedade Consorciada", "21": "Sociedade Filiada", "22": "Sócio",
    "23": "Sócio Capitalista", "24": "Sócio Comanditado", "25": "Sócio Comanditário",
    "26": "Sócio de Indústria", "28": "Sócio-Gerente",
    "29": "Sócio Incapaz ou Relat.Incapaz (exceto menor)",
    "30": "Sócio Menor (Assistido/Representado)", "31": "Sócio Ostensivo",
    "33": "Tesoureiro", "37": "Sócio Pessoa Jurídica Domiciliado no Exterior",
    "38": "Sócio Pessoa Física Residente ou Domiciliado no Exterior",
    "47": "Sócio Pessoa Física Residente no Brasil",
    "48": "Sócio Pessoa Jurídica Domiciliado no Brasil",
    "49": "Sócio-Administrador", "52": "Sócio com Capital", "53": "Sócio sem Capital",
    "54": "Fundador", "55": "Sócio Comanditado Residente no Exterior",
    "56": "Sócio Comanditário Pessoa Física Residente no Exterior",
    "57": "Sócio Comanditário Pessoa Jurídica Domiciliado no Exterior",
    "58": "Sócio Comanditário Incapaz", "59": "Produtor Rural",
    "63": "Cotas em Tesouraria",
    "65": "Titular Pessoa Física Residente ou Domiciliado no Brasil",
    "66": "Titular Pessoa Física Residente ou Domiciliado no Exterior",
    "67": "Titular Pessoa Física Incapaz ou Relativamente Incapaz (exceto menor)",
    "68": "Titular Pessoa Física Menor (Assistido/Representado)",
    "70": "Administrador Residente ou Domiciliado no Exterior",
    "71": "Conselheiro de Administração Residente ou Domiciliado no Exterior",
    "72": "Diretor Residente ou Domiciliado no Exterior",
    "73": "Presidente Residente ou Domiciliado no Exterior",
    "74": "Sócio-Administrador Residente ou Domiciliado no Exterior",
    "75": "Fundador Residente ou Domiciliado no Exterior",
    "76": "Protetor", "77": "Vice-Presidente",
    "78": "Titular Pessoa Jurídica Domiciliada no Brasil",
    "79": "Titular Pessoa Jurídica Domiciliada no Exterior",
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


def _enrich_response(data: dict) -> dict:
    """Add descriptive labels for coded fields in the API response.

    Enriches the response in-place with human-readable descriptions for:
      - socios[].qualificacao       → codigo_qualificacao + descricao_qualificacao
      - socios[].tipoSocio           → descricao_tipo_socio
      - socios[].representanteLegal.qualificacao → descricao_qualificacao
      - situacaoCadastral.codigo     → descricao_situacao
      - naturezaJuridica.codigo      → (already returns descricao)
      - tipoEstabelecimento          → descricao_tipo_estabelecimento
      - porte                         → descricao_porte
    """
    # --- Tipo de Estabelecimento ---
    _TIPO_ESTABELECIMENTO = {"1": "Matriz", "2": "Filial"}
    te = data.get("tipoEstabelecimento", "")
    if te in _TIPO_ESTABELECIMENTO:
        data["descricao_tipo_estabelecimento"] = _TIPO_ESTABELECIMENTO[te]

    # --- Porte ---
    _PORTE = {"01": "Microempresa (ME)", "03": "Empresa de Pequeno Porte (EPP)", "05": "Demais empresas"}
    po = data.get("porte", "")
    if po in _PORTE:
        data["descricao_porte"] = _PORTE[po]

    # --- Situação Cadastral ---
    sc = data.get("situacaoCadastral", {})
    if sc and sc.get("codigo") in _SITUACAO_CNPJ:
        sc["descricao"] = _SITUACAO_CNPJ[sc["codigo"]]

    # --- Sócios ---
    socios = data.get("socios", [])
    for s in socios:
        q = s.get("qualificacao", "")
        if q in _QUALIFICACAO_SOCIO:
            s["codigo_qualificacao"] = q
            s["descricao_qualificacao"] = _QUALIFICACAO_SOCIO[q]

        ts = s.get("tipoSocio", "")
        if ts in _TIPO_SOCIO:
            s["descricao_tipo_socio"] = _TIPO_SOCIO[ts]

        rl = s.get("representanteLegal", {})
        if rl:
            rq = rl.get("qualificacao", "")
            if rq in _QUALIFICACAO_SOCIO:
                rl["descricao_qualificacao"] = _QUALIFICACAO_SOCIO[rq]

    return data


def _fmt_date(d: str) -> str:
    """Convert YYYY-MM-DD to DD/MM/YYYY."""
    if not d:
        return ""
    parts = d.split("-")
    if len(parts) == 3:
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return d


def _fmt_capital(valor: int) -> str:
    """Format capital social in Brazilian currency (API value ÷ 100)."""
    reais = valor / 100
    return "R$ " + f"{reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_telefone(ddd: str, numero: str) -> str:
    """Format phone as (DDD) XXXX-XXXX or (DDD) XXXXX-XXXX."""
    n = numero.strip()
    if len(n) == 9:
        return f"({ddd}) {n[:5]}-{n[5:]}"
    if len(n) == 8:
        return f"({ddd}) {n[:4]}-{n[4:]}"
    return f"({ddd}) {n}"


def _fmt_endereco(endereco: dict, include_cep: bool = False) -> str:
    """Format address as a single readable line."""
    tipo_raw = endereco.get("tipoLogradouro", "")
    tipo = _TIPO_LOGRADOURO.get(tipo_raw.upper(), tipo_raw.title())
    logradouro = endereco.get("logradouro", "").title()
    numero = endereco.get("numero", "")
    complemento = endereco.get("complemento", "").title()
    bairro = endereco.get("bairro", "").title()
    municipio = endereco.get("municipio", {}).get("descricao", "").title()
    uf = endereco.get("uf", "")

    addr = f"{tipo} {logradouro}, {numero}"
    if complemento:
        addr += f" - {complemento}"
    addr += f", {bairro}, {municipio}/{uf}"

    if include_cep:
        cep = re.sub(r"[^0-9]", "", endereco.get("cep", ""))
        if len(cep) == 8:
            addr += f" - CEP {cep[:5]}-{cep[5:]}"

    return addr


def _fmt_situacao(situacao: dict, include_date: bool = False) -> str:
    """Format situação cadastral with optional date."""
    codigo = situacao.get("codigo", "")
    descricao = _SITUACAO_CNPJ.get(codigo, codigo)
    result = f"{descricao} (código {codigo})"
    if include_date and situacao.get("data"):
        result += f" desde {_fmt_date(situacao['data'])}"
    return result


def _fmt_cnpj(cnpj: str) -> str:
    """Format 14 digits as XX.XXX.XXX/XXXX-XX."""
    n = re.sub(r"[^0-9]", "", cnpj)
    if len(n) != 14:
        return cnpj
    return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"


def _print_formatted(data: dict, endpoint: str, cnpj: str = "") -> None:
    """Print human-readable output for basica, qsa, or empresa endpoints."""
    end = data.get("endereco", {})
    is_basica = endpoint == "basica"

    # Cabeçalho
    print(f"CNPJ: {_fmt_cnpj(cnpj)}")
    print(f"Razão social: {data.get('nomeEmpresarial', '')}")
    print(f"Nome Fantasia: {data.get('nomeFantasia', '')}")

    # Situação
    sc = data.get("situacaoCadastral", {})
    situacao_desc = _SITUACAO_CNPJ.get(sc.get("codigo", ""), "").upper()
    situacao_data = _fmt_date(sc.get("data", "")) if sc.get("data") else ""
    if situacao_desc and situacao_data:
        print(f"Situação: {situacao_desc} (desde {situacao_data})")
    else:
        print(f"Situação: {situacao_desc}")

    # Endereço (com travessão)
    addr = _fmt_endereco(end, include_cep=True)
    if " — " not in addr:
        addr = addr.replace(" - ", " — ")
    print(f"Endereço: {addr}")
    print(f"Capital Social: {_fmt_capital(data.get('capitalSocial', 0))}")

    # Quadro de Sócios
    if endpoint in ("qsa", "empresa"):
        socios = data.get("socios", [])
        if socios:
            print()
            print("---")
            print()
            print("Quadro de Sócios:")
            print()
            for s in socios:
                qual = _QUALIFICACAO_SOCIO.get(
                    s.get("qualificacao", ""), s.get("qualificacao", "")
                )
                print(f"**{s.get('nome', '')}**")
                print(f"• Qualificação: {qual}")
                print()


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
    parser.add_argument("--json", dest="output_json", action="store_true", help="Imprimir JSON compacto")
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
        if args.pretty:
            print(json.dumps(resultado, ensure_ascii=False, indent=2))
        elif args.output_json:
            print(json.dumps(resultado, ensure_ascii=False))
        else:
            _print_formatted(resultado, args.endpoint, cnpj=args.cnpj)
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
