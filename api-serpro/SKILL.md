# Skill: Consulta SERPRO — CPF e CNPJ

## Descrição

Skill para consultar as APIs de CPF e CNPJ do SERPRO (Serviço Federal de Processamento de Dados) via OAuth2. Oferece scripts Python executáveis via CLI e importáveis como módulos, com cache automático de token e tratamento completo de erros.

## Arquitetura

```
Credenciais (.env)
       │
       ▼
obter_token.py ──── .token_cache.json
  OAuth2 CC grant       (cache 1h)
       │
       ├──────────────────────┐
       ▼                      ▼
consulta_cnpj.py        consulta_cpf.py
  GET /basica/{cnpj}      GET /cpf/{ni}
  GET /qsa/{cnpj}
  GET /empresa/{cnpj}
       │                      │
       ▼                      ▼
   JSON Response          JSON Response
```

## APIs Utilizadas

| API | Versão | Base URL Produção | Base URL Trial | Autenticação |
|---|---|---|---|---|
| Consulta CNPJ | v2 | `https://gateway.apiserpro.serpro.gov.br/consulta-cnpj-df/v2` | `https://gateway.apiserpro.serpro.gov.br/consulta-cnpj-df-trial/v2` | Bearer Token |
| Consulta CPF | v2 (prod) / v1 (trial) | `https://gateway.apiserpro.serpro.gov.br/consulta-cpf-df/v2` | `https://gateway.apiserpro.serpro.gov.br/consulta-cpf-df-trial/v1` | Bearer Token |
| Auth Token | — | `https://gateway.apiserpro.serpro.gov.br/token` | (mesmo endpoint) | Basic Auth (Base64) |

## Módulos

### `obter_token.py`

**Responsabilidade:** Gerenciar o ciclo de vida do token OAuth2.

**Entradas:**
- Variáveis de ambiente: `SERPRO_CONSUMER_KEY`, `SERPRO_CONSUMER_SECRET`
- Opcional: arquivo `.env` na raiz do projeto

**Saídas:**
- `obter_token(force_refresh=False) -> str` — retorna token Bearer válido

**Cache:**
- Arquivo `.token_cache.json` na raiz do projeto
- Reutiliza token se restar mais de 5 minutos de validade
- Renova automaticamente quando expirado ou quando `force_refresh=True`

---

### `consulta_cnpj.py`

**Responsabilidade:** Consultar dados cadastrais de pessoa jurídica via CNPJ.

**Endpoints disponíveis:**

| Endpoint | Dados retornados |
|---|---|
| `basica` | Cadastro, endereço, CNAE, situação |
| `qsa` | Quadro de Sócios e Administradores |
| `empresa` | Completo: básico + QSA + SIMPLES/MEI |

**Parâmetros CLI:**

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `cnpj` | posicional | — | CNPJ (com ou sem formatação) |
| `--endpoint` | opção | `basica` | Endpoint: basica, qsa, empresa |
| `--trial` | flag | False | Usar ambiente trial |
| `--pretty` | flag | False | JSON formatado |
| `--carimbo` | flag | False | Solicitar Carimbo de Tempo |
| `--tag` | string | None | Tag de faturamento (máx 32 chars) |

**Tratamento de erros:** Todos os códigos HTTP documentados. Em caso de HTTP 401, renova o token automaticamente e repete a requisição uma vez.

**Atenção:** O campo `capitalSocial` é retornado em centavos — divida por 100 para obter o valor em reais. Campos marcados com `*` na documentação (`cpf`, `dataInclusao` dos sócios) estão disponíveis apenas no endpoint `/empresa`.

---

### `consulta_cpf.py`

**Responsabilidade:** Consultar dados cadastrais de pessoa física via CPF.

**Endpoint:** `GET /cpf/{ni}`

**Parâmetros CLI:**

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `cpf` | posicional | — | CPF (com ou sem formatação) |
| `--trial` | flag | False | Usar ambiente trial |
| `--pretty` | flag | False | JSON formatado |

**Tratamento de erros:** Inclui HTTP 422 (menor de 18 anos, LGPD) e 451 (menor de 16 anos, Lei Felca). Em caso de HTTP 401, renova o token e repete.

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `SERPRO_CONSUMER_KEY` | Sim | Consumer Key do aplicativo SERPRO |
| `SERPRO_CONSUMER_SECRET` | Sim | Consumer Secret do aplicativo SERPRO |

## Exemplos de Uso Programático

```python
import sys
sys.path.insert(0, "api-serpro/scripts")

# Consultar CNPJ básico
from consulta_cnpj import consultar_cnpj
dados = consultar_cnpj("34238864000168")
print(dados["nomeEmpresarial"])
capital_reais = dados["capitalSocial"] / 100

# Consultar CNPJ completo (trial)
dados_empresa = consultar_cnpj("34238864000168", endpoint="empresa", trial=True)
socios = dados_empresa.get("socios", [])

# Consultar CPF
from consulta_cpf import consultar_cpf
cpf_dados = consultar_cpf("40442820135", trial=True)
print(cpf_dados["nome"], cpf_dados["situacao"]["descricao"])

# Obter token diretamente
from obter_token import obter_token
token = obter_token()
```

## Limitações e Observações

- **Token expira em 1 hora.** O cache evita requisições desnecessárias ao endpoint de autenticação.
- **CPFs de menores retornam 422 ou 451** por exigência da LGPD e Lei Felca — não é erro de implementação.
- **`capitalSocial` do CNPJ** é retornado em centavos. Divida por 100 para obter reais.
- **O gateway é case-sensitive** nos caminhos de endpoint (`basica`, não `Basica`).
- **Campos `cpf` e `dataInclusao` dos sócios** só estão disponíveis no endpoint `/empresa`, não em `/qsa`.
- **HTTP 206** (conteúdo parcial) é uma resposta válida — ocorre quando campos opcionais como `dataInscricao` (CPF) não estão disponíveis.
- **Ambiente trial da API CPF usa v1**, não v2 — URLs são diferentes entre produção e trial.
