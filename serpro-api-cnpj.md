# Guia de Consulta CNPJ — API SERPRO (consulta-cnpj-df-v2)

Referência: [apicenter.estaleiro.serpro.gov.br](https://apicenter.estaleiro.serpro.gov.br/documentacao/consulta-cnpj/pt/consulta-cnpj-df-v2/)

---

## Visão Geral

A API Consulta CNPJ do SERPRO disponibiliza dados cadastrais de Pessoas Jurídicas via HTTP REST. O cliente envia o Número de Inscrição no CNPJ (NI) e recebe dados cadastrais, societários e de atividade econômica.

- **Base URL (Produção):** `https://gateway.apiserpro.serpro.gov.br/consulta-cnpj-df/v2`
- **Base URL (Trial/Demo):** `https://gateway.apiserpro.serpro.gov.br/consulta-cnpj-df-trial/v2`
- **Autenticação:** OAuth2 — Bearer Token
- **Endpoint de Token:** `https://gateway.apiserpro.serpro.gov.br/token`

---

## Autenticação

### Passo 1 — Obtenha as credenciais

Acesse a [Área do Cliente SERPRO](https://cliente.serpro.gov.br) e recupere:

- **Consumer Key** (ex.: `djaR21PGoYp1iyK2n2ACOH9REdUb`)
- **Consumer Secret** (ex.: `ObRsAJWOL4fv2Tp27D1vd8fB3Ote`)

> Mantenha essas credenciais protegidas — elas identificam seu contrato com o SERPRO.

### Passo 2 — Gere o Bearer Token

Codifique `Consumer Key:Consumer Secret` em Base64:

```bash
echo -n "djaR21PGoYp1iyK2n2ACOH9REdUb:ObRsAJWOL4fv2Tp27D1vd8fB3Ote" | base64
# Resultado: ZGphUjIxUEdvWXAxaXlLMm4yQUNPSDlSRWRVYjpPYlJzQUpXT0w0ZnYyVHAyN0QxdmQ4ZkIzT3RlCg
```

Solicite o token via POST:

```bash
curl -k \
  -d "grant_type=client_credentials" \
  -H "Authorization: Basic ZGphUjIxUEdvWXAxaXlLMm4yQUNPSDlSRWRVYjpPYlJzQUpXT0w0ZnYyVHAyN0QxdmQ4ZkIzT3RlCg" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  https://gateway.apiserpro.serpro.gov.br/token
```

### Passo 3 — Receba o Token

```json
{
  "scope": "default",
  "token_type": "Bearer",
  "expires_in": 3295,
  "access_token": "c66a7def1c96f7008a0c397dc588b6d7"
}
```

- O token expira em **1 hora**.
- Renove quando a API retornar `HTTP 401`.

---

## Endpoints

A v2 oferece três endpoints com diferentes níveis de detalhe. Todos usam `GET` e recebem o CNPJ (14 dígitos, sem máscara) no path.

### GET /basica/{ni} — Dados Básicos

Retorna dados cadastrais e de endereço. **Não inclui** sócios nem informações de Simples/MEI.

```
GET https://gateway.apiserpro.serpro.gov.br/consulta-cnpj-df/v2/basica/{ni}
```

**Exemplo:**

```bash
curl -X GET \
  "https://gateway.apiserpro.serpro.gov.br/consulta-cnpj-df/v2/basica/34238864000168" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer c66a7def1c96f7008a0c397dc588b6d7"
```

**Resposta (200 OK):**

```jsonc
{
  "ni": "34238864000168",
  "tipoEstabelecimento": "1",           // Matriz
  "nomeEmpresarial": "SERVICO DE E-COMERCE LTDA",
  "nomeFantasia": "E-COMERCE",
  "situacaoCadastral": {
    "codigo": "2",                      // Ativa
    "data": "2004-05-22",
    "motivo": ""
  },
  "naturezaJuridica": {
    "codigo": "2011",
    "descricao": "Empresa Pública"
  },
  "dataAbertura": "1967-06-30",
  "cnaePrincipal": {
    "codigo": "6204000",
    "descricao": "Consultoria em e-comerce"
  },
  "cnaeSecundarias": [],
  "endereco": {
    "tipoLogradouro": "ST",
    "logradouro": "DE GRANDE AREA NORTE",
    "numero": "Q.601",
    "complemento": "LOTE V",
    "cep": "70836900",
    "bairro": "ASA NORTE",
    "municipio": { "codigo": "9701", "descricao": "BRASILIA" },
    "uf": "DF",
    "pais": { "codigo": "105", "descricao": "BRASIL" }
  },
  "municipioJurisdicao": { "codigo": "9701", "descricao": "BRASILIA" },
  "telefones": [{ "ddd": "061", "numero": "4338456" }],
  "correioEletronico": "",
  "capitalSocial": 0,
  "porte": "05",                        // Demais empresas
  "situacaoEspecial": "",
  "dataSituacaoEspecial": ""
}
```

> Os campos `tipoEstabelecimento`, `situacaoCadastral.codigo` e `porte` retornam apenas o **código numérico**. Consulte as [Tabelas de Referência](#tabelas-de-referência) para o texto correspondente.

---

### GET /qsa/{ni} — Dados Básicos + Quadro Societário

Inclui tudo do `/basica` mais `socios` e `informacoesAdicionais` (Simples/MEI), **sem** CPF dos sócios.

```
GET https://gateway.apiserpro.serpro.gov.br/consulta-cnpj-df/v2/qsa/{ni}
```

**Exemplo:**

```bash
curl -X GET \
  "https://gateway.apiserpro.serpro.gov.br/consulta-cnpj-df/v2/qsa/34238864000168" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer c66a7def1c96f7008a0c397dc588b6d7"
```

**Campos adicionais na resposta:**

```json
{
  "informacoesAdicionais": {
    "optanteSimples": false,
    "optanteMei": false,
    "listaPeriodosSimples": []
  },
  "socios": [
    {
      "tipoSocio": "2",
      "nome": "FULANO DE TAL",
      "qualificacao": "49",
      "pais": { "codigo": "105", "descricao": "BRASIL" },
      "representanteLegal": {
        "nome": "",
        "qualificacao": ""
      }
    }
  ]
}
```

---

### GET /empresa/{ni} — Dados Completos

Inclui tudo do `/qsa` **mais** CPF dos sócios e CPF do representante legal. Requer contrato com permissão para dados sensíveis.

```
GET https://gateway.apiserpro.serpro.gov.br/consulta-cnpj-df/v2/empresa/{ni}
```

**Campos exclusivos do `/empresa`:**

```json
{
  "socios": [
    {
      "cpf": "12345678901",
      "dataInclusao": "2010-03-15",
      "representanteLegal": {
        "cpf": "98765432100",
        "nome": "REPRESENTANTE LTDA",
        "qualificacao": "10"
      }
    }
  ]
}
```

---

## Parâmetros e Headers

| Parâmetro | Tipo   | Local  | Descrição                                          |
|-----------|--------|--------|----------------------------------------------------|
| `ni`      | string | path   | CNPJ com 14 dígitos, sem pontuação (ex.: `34238864000168`) |

| Header          | Valor              | Obrigatório |
|-----------------|--------------------|-------------|
| `Authorization` | `Bearer {token}`   | Sim         |
| `Accept`        | `application/json` | Recomendado |

> O gateway é **case-sensitive** — use os paths exatamente como documentados.

---

## Campos Retornados por Endpoint

| Campo                              | Descrição                                              | /basica | /qsa | /empresa |
|------------------------------------|--------------------------------------------------------|:-------:|:----:|:--------:|
| `ni`                               | CNPJ (14 dígitos)                                      | x       | x    | x        |
| `tipoEstabelecimento`              | Tipo de estabelecimento (Matriz/Filial)                | x       | x    | x        |
| `nomeEmpresarial`                  | Razão social                                           | x       | x    | x        |
| `nomeFantasia`                     | Nome fantasia                                          | x       | x    | x        |
| `situacaoCadastral.codigo`         | Código da situação cadastral                           | x       | x    | x        |
| `situacaoCadastral.data`           | Data da situação cadastral                             | x       | x    | x        |
| `situacaoCadastral.motivo`         | Motivo da situação cadastral                           | x       | x    | x        |
| `naturezaJuridica.codigo`          | Código da natureza jurídica                            | x       | x    | x        |
| `naturezaJuridica.descricao`       | Descrição da natureza jurídica                         | x       | x    | x        |
| `dataAbertura`                     | Data de abertura (AAAA-MM-DD)                          | x       | x    | x        |
| `cnaePrincipal.codigo`             | Código CNAE principal                                  | x       | x    | x        |
| `cnaePrincipal.descricao`          | Descrição CNAE principal                               | x       | x    | x        |
| `cnaeSecundarias`                  | Lista de CNAEs secundários                             | x       | x    | x        |
| `endereco.*`                       | Endereço completo (logradouro, CEP, município, UF)     | x       | x    | x        |
| `telefones`                        | Lista de telefones (ddd + número)                      | x       | x    | x        |
| `correioEletronico`                | E-mail da empresa                                      | x       | x    | x        |
| `capitalSocial`                    | Capital social ÷ 100 = valor real em R$                | x       | x    | x        |
| `porte`                            | Código do porte da empresa                             | x       | x    | x        |
| `situacaoEspecial`                 | Situação especial (falência, liquidação etc.)          | x       | x    | x        |
| `dataSituacaoEspecial`             | Data da situação especial                              | x       | x    | x        |
| `informacoesAdicionais.optanteSimples` | Indicador de optante pelo Simples Nacional         |         | x    | x        |
| `informacoesAdicionais.optanteMei` | Indicador de MEI                                       |         | x    | x        |
| `informacoesAdicionais.listaPeriodosSimples` | Histórico de períodos no Simples              |         | x    | x        |
| `socios.tipoSocio`                 | Tipo de sócio                                          |         | x    | x        |
| `socios.nome`                      | Nome do sócio                                          |         | x    | x        |
| `socios.qualificacao`              | Qualificação do sócio                                  |         | x    | x        |
| `socios.pais`                      | País de residência do sócio                            |         | x    | x        |
| `socios.representanteLegal.nome`   | Nome do representante legal                            |         | x    | x        |
| `socios.representanteLegal.qualificacao` | Qualificação do representante legal              |         | x    | x        |
| `socios.cpf`                       | CPF do sócio                                           |         |      | x        |
| `socios.dataInclusao`              | Data de entrada na sociedade                           |         |      | x        |
| `socios.representanteLegal.cpf`    | CPF do representante legal                             |         |      | x        |

> **Atenção:** Quando `naturezaJuridica.codigo` = `213-5` (Empresário Individual), os campos de sócios **não são retornados**.

> **Capital Social:** o valor retornado inclui centavos sem separador. Divida por 100 para obter o valor em R$ (ex.: `100000` → R$ 1.000,00).

---

## Tabelas de Referência

### Situação Cadastral

| Código | Descrição          | Significado                                                                  |
|--------|--------------------|------------------------------------------------------------------------------|
| `1`    | Nula               | CNPJ com fraude comprovada ou inconsistência grave; não pode ser reativado   |
| `2`    | Ativa              | Empresa em operação, sem pendências ou irregularidades                       |
| `3`    | Suspensa           | Falhou em obrigações legais (impostos, declarações); pode ser regularizada   |
| `4`    | Inapta             | Omissões obrigatórias por dois anos consecutivos; sujeita a restrições       |
| `5`    | Ativa Não Regular  | Em operação, mas com pendências ou irregularidades                           |
| `8`    | Baixada            | Encerrada voluntariamente ou pela Receita Federal; irreversível               |

### Tipo de Estabelecimento

| Código | Descrição |
|--------|-----------|
| `1`    | Matriz    |
| `2`    | Filial    |

### Porte da Empresa

| Código | Descrição                    |
|--------|------------------------------|
| `01`   | Microempresa (ME)            |
| `03`   | Empresa de Pequeno Porte (EPP) |
| `05`   | Demais empresas              |

### Tipo de Sócio

| Código | Descrição         |
|--------|-------------------|
| `1`    | Pessoa Jurídica   |
| `2`    | Pessoa Física     |
| `3`    | Sócio Estrangeiro |

### Qualificação de Sócio

| Código | Descrição |
|--------|-----------|
| `05` | Administrador |
| `08` | Conselheiro de Administração |
| `10` | Diretor |
| `16` | Presidente |
| `17` | Procurador |
| `18` | Secretário |
| `20` | Sociedade Consorciada |
| `21` | Sociedade Filiada |
| `22` | Sócio |
| `23` | Sócio Capitalista |
| `24` | Sócio Comanditado |
| `25` | Sócio Comanditário |
| `26` | Sócio de Indústria |
| `28` | Sócio-Gerente |
| `29` | Sócio Incapaz ou Relat.Incapaz (exceto menor) |
| `30` | Sócio Menor (Assistido/Representado) |
| `31` | Sócio Ostensivo |
| `33` | Tesoureiro |
| `37` | Sócio Pessoa Jurídica Domiciliado no Exterior |
| `38` | Sócio Pessoa Física Residente ou Domiciliado no Exterior |
| `47` | Sócio Pessoa Física Residente no Brasil |
| `48` | Sócio Pessoa Jurídica Domiciliado no Brasil |
| `49` | Sócio-Administrador |
| `52` | Sócio com Capital |
| `53` | Sócio sem Capital |
| `54` | Fundador |
| `55` | Sócio Comanditado Residente no Exterior |
| `56` | Sócio Comanditário Pessoa Física Residente no Exterior |
| `57` | Sócio Comanditário Pessoa Jurídica Domiciliado no Exterior |
| `58` | Sócio Comanditário Incapaz |
| `59` | Produtor Rural |
| `63` | Cotas em Tesouraria |
| `65` | Titular Pessoa Física Residente ou Domiciliado no Brasil |
| `66` | Titular Pessoa Física Residente ou Domiciliado no Exterior |
| `67` | Titular Pessoa Física Incapaz ou Relativamente Incapaz (exceto menor) |
| `68` | Titular Pessoa Física Menor (Assistido/Representado) |
| `70` | Administrador Residente ou Domiciliado no Exterior |
| `71` | Conselheiro de Administração Residente ou Domiciliado no Exterior |
| `72` | Diretor Residente ou Domiciliado no Exterior |
| `73` | Presidente Residente ou Domiciliado no Exterior |
| `74` | Sócio-Administrador Residente ou Domiciliado no Exterior |
| `75` | Fundador Residente ou Domiciliado no Exterior |
| `76` | Protetor |
| `77` | Vice-Presidente |
| `78` | Titular Pessoa Jurídica Domiciliada no Brasil |
| `79` | Titular Pessoa Jurídica Domiciliada no Exterior |

---

### Situação Especial (valores possíveis)

| Descrição                    |
|------------------------------|
| Início de Concordata         |
| Término de Concordata        |
| Em Liquidação                |
| Em Liquidação Extra-Judicial |
| Falido                       |
| Intervenção                  |
| Financeiro e de Capitais     |
| Liquidação Judicial          |
| Liquidação Extra-Judicial    |
| Recuperação Judicial         |

---

## Códigos HTTP de Retorno

| Código | Nome                    | Descrição                                                              | Bilhetado |
|--------|-------------------------|------------------------------------------------------------------------|-----------|
| `200`  | OK                      | Consulta realizada com sucesso                                         | Sim       |
| `206`  | Conteúdo Parcial        | Dados retornados de forma incompleta                                   | Sim       |
| `400`  | Requisição Inválida     | Número de CNPJ inválido                                                | Não       |
| `401`  | Não Autorizado          | Token inválido ou expirado                                             | Não       |
| `403`  | Proibido                | Caminho errado na URL ou sem permissão de contrato                     | Não       |
| `404`  | Não Encontrado          | CNPJ não existe na base                                                | Sim       |
| `500`  | Erro no Servidor        | Erro interno no servidor SERPRO                                        | Não       |
| `502`  | Erro de Integração      | Falha de integração interna que impediu retornar os dados              | Não       |
| `504`  | Tempo Esgotado          | Gateway não respondeu a tempo; requisição não chegou à API             | Não       |

---

## CNPJs de Teste (Ambiente Trial)

Use a base URL `https://gateway.apiserpro.serpro.gov.br/consulta-cnpj-df-trial/v2`:

| CNPJ             | Situação (`codigo`) | /basica | /qsa | /empresa |
|------------------|---------------------|:-------:|:----:|:--------:|
| `34238864000168` | `2` — Ativa         | ✅      | ✅   | ✅       |
| `54447820000155` | `3` — Suspensa      | ✅      | ✅   | ✅       |
| `46768703000165` | `4` — Inapta        | ✅      | ✅   | ✅       |
| `31151791000184` | `8` — Baixada       | ✅      | ✅   | ✅       |
| `34428654000132` | `1` — Nula          | ✅      | ✅   | ✅       |

---

## Exemplo Completo (Python)

```python
import requests
import base64

CONSUMER_KEY    = "SEU_CONSUMER_KEY"
CONSUMER_SECRET = "SEU_CONSUMER_SECRET"

TOKEN_URL = "https://gateway.apiserpro.serpro.gov.br/token"
API_BASE  = "https://gateway.apiserpro.serpro.gov.br/consulta-cnpj-df/v2"


def obter_token() -> str:
    credenciais = base64.b64encode(f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode()).decode()
    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        headers={
            "Authorization": f"Basic {credenciais}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def consultar_cnpj(ni: str, token: str, nivel: str = "basica") -> dict:
    """
    nivel: "basica" | "qsa" | "empresa"
    """
    resp = requests.get(
        f"{API_BASE}/{nivel}/{ni}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )
    resp.raise_for_status()
    return resp.json()


token = obter_token()

# Dados básicos
basica = consultar_cnpj("34238864000168", token, nivel="basica")
print(basica["nomeEmpresarial"])

# Quadro societário
qsa = consultar_cnpj("34238864000168", token, nivel="qsa")
for socio in qsa.get("socios", []):
    print(socio["nome"], socio["qualificacao"])

# Dados completos (inclui CPF dos sócios)
empresa = consultar_cnpj("34238864000168", token, nivel="empresa")
```

---

## Observações Importantes

- **Case-sensitive:** o gateway diferencia maiúsculas de minúsculas. Use os paths exatamente como documentados (`/basica`, `/qsa`, `/empresa`).
- **Formato do NI:** envie o CNPJ com **14 dígitos, sem pontos, barras ou traços** (ex.: `34238864000168`).
- **Capital Social:** divida o valor retornado por `100` para obter o valor real em R$.
- **Empresário Individual:** quando `naturezaJuridica.codigo` = `213-5`, o grupo `socios` não é retornado.
- **Renovação de token:** gere um novo token a cada 1 hora ou quando receber `401`.
- **Contratação:** para uso em produção, é necessário contrato com o SERPRO via [cliente.serpro.gov.br](https://cliente.serpro.gov.br).
- **Qualificações de sócio:** a tabela completa está disponível no [Anexo V da Receita Federal](https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/cnpj/tabelas-utilizadas-pelo-programa-cnpj/Anexo_V3.pdf).
