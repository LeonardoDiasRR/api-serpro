# API SERPRO — Consulta CPF e CNPJ

Scripts Python para consultar as APIs de CPF e CNPJ do SERPRO com autenticação OAuth2.

## Pré-requisitos

- Python 3.8+
- Biblioteca `requests`
- Opcional: `python-dotenv` (para usar arquivo `.env`)

## Instalação

```bash
pip install requests python-dotenv
```

## Configuração

Crie um arquivo `.env` na raiz do projeto (`api-serpro/.env`):

```env
SERPRO_CONSUMER_KEY=sua_consumer_key_aqui
SERPRO_CONSUMER_SECRET=seu_consumer_secret_aqui
```

> **Como obter as credenciais:** Acesse a Área do Cliente SERPRO, faça login, vá em "Meus Aplicativos" e copie a Consumer Key e Consumer Secret do aplicativo configurado para as APIs de CPF e/ou CNPJ.

## Uso

### Obter Token

```bash
python scripts/obter_token.py
```

### Consultar CNPJ

```bash
# Dados básicos (produção)
python scripts/consulta_cnpj.py 34.238.864/0001-68 --pretty

# Quadro de sócios
python scripts/consulta_cnpj.py 34238864000168 --endpoint qsa --pretty

# Dados completos (empresa)
python scripts/consulta_cnpj.py 34238864000168 --endpoint empresa --pretty

# Ambiente trial (testes)
python scripts/consulta_cnpj.py 34238864000168 --trial --pretty

# Com Carimbo de Tempo e tag de faturamento
python scripts/consulta_cnpj.py 34238864000168 --carimbo --tag "meu-sistema" --pretty
```

### Consultar CPF

```bash
# Produção
python scripts/consulta_cpf.py 404.428.201-35 --pretty

# Ambiente trial (testes)
python scripts/consulta_cpf.py 40442820135 --trial --pretty
```

## Ambientes

### Produção
Requer credenciais válidas com contrato ativo no SERPRO.

### Trial (Testes)
Use a flag `--trial`. Não requer contrato ativo. CNPJs e CPFs fictícios disponíveis:

#### CNPJs de Teste

| CNPJ | Situação |
|---|---|
| 34238864000168 | ATIVO |
| 54447820000155 | SUSPENSO |
| 46768703000165 | INAPTO |
| 31151791000184 | BAIXADO |
| 34428654000132 | NULO |

#### CPFs de Teste

| CPF | Situação |
|---|---|
| 40442820135 | Regular |
| 63017285995 | Regular |
| 40532176871 | Suspensa |
| 07691852312 | Pendente de Regularização |
| 01648527949 | Cancelada por Multiplicidade |
| 98302514705 | Nula |
| 64913872591 | Cancelada de Ofício |
| 05137518743 | Titular Falecido |
| 30272095079 | Menor de 18 anos (HTTP 422) |
| 20803407009 | Menor de 16 anos (HTTP 451) |
| 88373571094 | Conteúdo Parcial (HTTP 206) |

## Estrutura do Projeto

```
api-serpro/
├── .env                    # Credenciais (não versionar)
├── .gitignore
├── .token_cache.json       # Cache do token (gerado automaticamente)
├── README.md
├── SKILL.md
├── scripts/
│   ├── obter_token.py      # Gerenciamento do token OAuth2
│   ├── consulta_cnpj.py    # Consulta CNPJ
│   └── consulta_cpf.py     # Consulta CPF
└── tests/
    ├── test_obter_token.py
    ├── test_consulta_cnpj.py
    └── test_consulta_cpf.py
```

## Códigos de Retorno

### CNPJ

| HTTP | Significado | Bilhetado |
|---|---|---|
| 200 | OK | Sim |
| 206 | Conteúdo parcial | Sim |
| 400 | CNPJ inválido | Não |
| 401 | Não autorizado | Não |
| 403 | Caminho inválido | Não |
| 404 | Não encontrado | Sim |
| 500 | Erro interno | Não |
| 502 | Erro de integração | Não |
| 504 | Timeout gateway | Não |

### CPF

| HTTP | Significado | Bilhetado |
|---|---|---|
| 200 | OK | Sim |
| 206 | Conteúdo parcial | Sim |
| 400 | CPF inválido | Não |
| 401 | Não autorizado | Não |
| 403 | Caminho inválido | Não |
| 404 | Não encontrado | Sim |
| 422 | Menor de 18 anos (LGPD) | Sim |
| 451 | Menor de 16 anos (LGPD) | Sim |
| 500 | Erro interno | Não |
| 504 | Timeout gateway | Não |

## Segurança

- **Nunca versione o arquivo `.env`** — ele já está no `.gitignore`
- **Nunca versione `.token_cache.json`** — contém token de acesso ativo
- Rotacione suas credenciais periodicamente na Área do Cliente SERPRO
