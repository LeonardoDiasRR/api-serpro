# Guia de Consulta CPF — API SERPRO (consulta-cpf-df-v2)

Referência: [apicenter.estaleiro.serpro.gov.br](https://apicenter.estaleiro.serpro.gov.br/documentacao/consulta-cpf/pt/chamadas/consulta-cpf-df-v2/)

---

## Visão Geral

A API Consulta CPF do SERPRO disponibiliza dados cadastrais de Pessoas Físicas via HTTP REST. O cliente envia o Número de Inscrição no CPF (NI) e recebe as informações cadastrais do contribuinte.

- **Base URL (Produção):** `https://gateway.apiserpro.serpro.gov.br/consulta-cpf-df/v2`
- **Base URL (Trial/Demo):** `https://gateway.apiserpro.serpro.gov.br/consulta-cpf-df-trial/v1`
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
  "scope": "am_application_scope default",
  "token_type": "Bearer",
  "expires_in": 3295,
  "access_token": "c66a7def1c96f7008a0c397dc588b6d7"
}
```

- O token expira em **1 hora**.
- Renove quando a API retornar `HTTP 401`.

---

## Endpoints

### GET /cpf/{ni} — Consultar CPF

Retorna os dados cadastrais de um CPF.

```
GET https://gateway.apiserpro.serpro.gov.br/consulta-cpf-df/v2/cpf/{ni}
```

**Parâmetros:**

| Parâmetro | Tipo   | Local | Descrição                                      |
|-----------|--------|-------|------------------------------------------------|
| `ni`      | string | path  | Número de Inscrição no CPF (11 dígitos, sem máscara) |

**Headers obrigatórios:**

| Header          | Valor              |
|-----------------|--------------------|
| `Authorization` | `Bearer {token}`   |
| `Accept`        | `application/json` |

**Exemplo de requisição:**

```bash
curl -X GET \
  "https://gateway.apiserpro.serpro.gov.br/consulta-cpf-df/v2/cpf/40442820135" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer c66a7def1c96f7008a0c397dc588b6d7"
```

**Exemplos de resposta (200 OK):**

```json
{
  "ni": "62396927272",
  "nome": "LEONARDO DE ALMEIDA DIAS",
  "situacao": {
    "codigo": "0",
    "descricao": "REGULAR"
  },
  "nascimento": "24011980",
  "dataInscricao": "24081996"
}

{
  "ni": "59558369268",
  "nome": "NIEDIMA MATOS DE MACEDO",
  "situacao": {
    "codigo": "3",
    "descricao": "TITULAR FALECIDO"
  },
  "nascimento": "04121976",
  "obito": "2025",
  "dataInscricao": "14041995"
}
```

---

### GET /status — Status da API

Verifica se a API está operacional.

```
GET https://gateway.apiserpro.serpro.gov.br/consulta-cpf-df/v2/status
```

---

## Campos Retornados

| Campo              | Descrição                                          | Formato      | Obrigatório |
|--------------------|----------------------------------------------------|--------------|-------------|
| `ni`               | Número de Inscrição no CPF                         | 11 dígitos   | Sim         |
| `nome`             | Nome da Pessoa Física                              | string       | Sim         |
| `situacao.codigo`  | Código da situação cadastral                       | string       | Sim         |
| `situacao.descricao` | Descrição da situação cadastral                  | string       | Sim         |
| `nascimento`       | Data de nascimento                                 | DDMMAAAA     | Sim         |
| `obito`            | Ano de óbito (quando aplicável)                    | AAAA         | Não         |
| `dataInscricao`    | Data de inscrição no CPF                           | DDMMAAAA     | Opcional*   |
| `nomeSocial`       | Nome social da Pessoa Física                       | string       | Não         |

> \* Apesar de tecnicamente opcional, a ausência de `dataInscricao` aciona retorno `206 Conteúdo Parcial`.

---

## Situações Cadastrais

| Código | Descrição                   | Significado                                                           |
|--------|-----------------------------|-----------------------------------------------------------------------|
| `0`    | Regular                     | CPF válido, sem pendências                                            |
| `2`    | Suspensa                    | Dados incorretos ou incompletos no cadastro                           |
| `3`    | Titular Falecido            | CPF de pessoa falecida                                                |
| `4`    | Pendente de Regularização   | DIRPF obrigatória não entregue nos últimos 5 anos                    |
| `5`    | Cancelada por Multiplicidade| CPF duplicado ou vinculado a múltiplas pessoas                        |
| `8`    | Nula                        | Cancelado por fraude confirmada ou erro grave de emissão              |
| `9`    | Cancelada de Ofício         | Cancelado por decisão administrativa ou judicial                      |

---

## Códigos HTTP de Retorno

| Código | Nome                          | Descrição                                                               | Bilhetado |
|--------|-------------------------------|-------------------------------------------------------------------------|-----------|
| `200`  | OK                            | Consulta realizada com sucesso                                          | Sim       |
| `206`  | Conteúdo Parcial              | Dados retornados parcialmente (ex.: `dataInscricao` ausente)           | Sim       |
| `400`  | Requisição Inválida           | Número de CPF inválido                                                  | Não       |
| `401`  | Não Autorizado                | Token inválido ou expirado                                              | Não       |
| `403`  | Proibido                      | Caminho incorreto na requisição ou sem permissão                        | Não       |
| `404`  | Não Encontrado                | CPF não existe na base                                                  | Sim       |
| `406`  | Not Acceptable                | Header `Accept` inválido — use `application/json` ou `*/*`             | Sim       |
| `422`  | LGPD: Menor de Idade          | Dados bloqueados — titular tem menos de 18 anos (LGPD)                 | Sim       |
| `451`  | LGPD: Menor de 16 anos        | Dados bloqueados — titular tem menos de 16 anos (Lei Felca/nº 15.211)  | Sim       |
| `500`  | Erro no Servidor              | Erro interno no servidor SERPRO                                         | Não       |
| `504`  | Tempo Esgotado do Gateway     | Gateway não respondeu a tempo — requisição não chegou à API             | Não       |

---

## CPFs de Teste (Ambiente Trial)

Utilize os CPFs fictícios abaixo no ambiente `consulta-cpf-df-trial/v1`:

| CPF           | Situação Cadastral                     |
|---------------|----------------------------------------|
| `40442820135` | Regular                                |
| `63017285995` | Regular                                |
| `91708635203` | Regular                                |
| `58136053391` | Regular                                |
| `40532176871` | Suspensa                               |
| `47123586964` | Suspensa                               |
| `07691852312` | Pendente de Regularização              |
| `10975384600` | Pendente de Regularização              |
| `01648527949` | Cancelada por Multiplicidade           |
| `47893062592` | Cancelada por Multiplicidade           |
| `98302514705` | Nula                                   |
| `18025346790` | Nula                                   |
| `64913872591` | Cancelada de Ofício                    |
| `52389071686` | Cancelada de Ofício                    |
| `05137518743` | Titular Falecido                       |
| `08849979878` | Titular Falecido                       |
| `30272095079` | Menor de 18 anos → retorna `422`       |
| `14898746071` | Menor de 18 anos → retorna `422`       |
| `20803407009` | Menor de 16 anos → retorna `451`       |
| `78411139000` | Menor de 16 anos → retorna `451`       |
| `88373571094` | Conteúdo Parcial → retorna `206`       |
| `47460609080` | Conteúdo Parcial → retorna `206`       |

---

## Exemplo Completo (Python)

```python
import requests
import base64

# Credenciais (obtidas na Área do Cliente SERPRO)
CONSUMER_KEY = "djaR21PGoYp1iyK2n2ACOH9REdUb"
CONSUMER_SECRET = "ObRsAJWOL4fv2Tp27D1vd8fB3Ote"

TOKEN_URL = "https://gateway.apiserpro.serpro.gov.br/token"
API_BASE  = "https://gateway.apiserpro.serpro.gov.br/consulta-cpf-df/v2"


def obter_token():
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


def consultar_cpf(ni: str, token: str) -> dict:
    resp = requests.get(
        f"{API_BASE}/cpf/{ni}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )
    resp.raise_for_status()
    return resp.json()


token = obter_token()
dados = consultar_cpf("40442820135", token)
print(dados)
```

---

## Observações Importantes

- **Case-sensitive:** o gateway diferencia maiúsculas de minúsculas nos endpoints. Use exatamente `/cpf/{ni}`.
- **Formato do NI:** envie o CPF com **11 dígitos, sem pontos ou traços** (ex.: `40442820135`).
- **Renovação de token:** gere um novo token a cada 1 hora ou quando receber `401`.
- **Contratação:** para uso em produção, é necessário contrato com o SERPRO via [cliente.serpro.gov.br](https://cliente.serpro.gov.br).
