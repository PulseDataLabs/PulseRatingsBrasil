<p align="center">
  <a href="https://github.com/PulseDataLabs/PulseRatingsBrasil">
    <img src="assets/full-logo.png" alt="Pulse Ratings Logo" width="220">
  </a>
</p>

<h1 align="center">Pulse Ratings Brasil</h1>

<p align="center">
  <strong>Pipeline Serverless e Automatizado de Captura de Ratings de Crédito Brasileiros</strong>
</p>

<p align="center">
  <a href="https://github.com/PulseDataLabs/PulseRatingsBrasil/actions/workflows/main.yml">
    <img src="https://github.com/PulseDataLabs/PulseRatingsBrasil/actions/workflows/main.yml/badge.svg" alt="Build Status">
  </a>
  <img src="https://img.shields.io/badge/python-3.13-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/github/last-commit/PulseDataLabs/PulseRatingsBrasil" alt="Last Commit">
  <img src="https://img.shields.io/github/stars/PulseDataLabs/PulseRatingsBrasil" alt="Stars">
</p>

<hr>

O **Pulse Ratings Brasil** é um pipeline de ETL (Extração, Transformação e Carga) serverless projetado para coletar, tratar e disponibilizar dados de ratings de crédito (corporativos e soberanos) das principais agências de classificação de risco em atuação no Brasil: **S&P**, **Moody's**, **Fitch**, **Austin Rating** e **Liberum Ratings**.

Ele funciona 100% de forma automatizada via **GitHub Actions**, salvando o histórico consolidado diretamente no repositório em formato CSV plano. Os dados tratados alimentam um dashboard interativo servido via **GitHub Pages**.

---

## 🚀 Recursos e Diferenciais

*   **Arquitetura Baseada em OOP**: Scrapers estruturados sob uma classe base infraestrutural (`BaseScraper`) que gerencia nativamente o ciclo de vida, sanitização de tipos e geração de logs.
*   **Deduplicação Inteligente**: A persistência em CSV mescla dados novos com antigos no mesmo dia, substituindo re-execuções sem duplicar linhas e mantendo o histórico intacto.
*   **Detecção de Schema Drift**: Alertas automáticos caso as colunas das tabelas originais fornecidas pelas agências mudem de layout.
*   **Catálogo Dinâmico**: Geração automatizada do catálogo de dados (`datasets.json`) e mapeamento de tipos de campos (`schemas.json`) a cada execução do pipeline.
*   **Dashboard Vanilla CSS/JS**: Uma interface web rápida e responsiva para buscar, filtrar por agência e baixar os arquivos CSV sem sobrecarga de frameworks pesados.

---

## 📐 Arquitetura do Pipeline

```mermaid
graph TD
    A[GitHub Actions Cron / Trigger] --> B[run_all.py Orchestrator]
    B -->|Dynamic Discovery| C["scrapers/ folder"]
    B -->|Executes Phase 1| D["Independent Scrapers: Entities (Moody's, S&P, Fitch, Austin, Liberum)"]
    B -->|Executes Phase 2| E["Dependent Scrapers: Ratings (Moody's, S&P, Fitch, Austin, Liberum)"]
    D --> F["data/*.csv files"]
    E --> F
    F --> G["scripts/consolidar_emissores.py"]
    G --> H["data/emissores_consolidado.csv"]
    F & H --> I["data/datasets.json (generate_catalog.py)"]
    I --> J[git push origin main]
    J --> K[GitHub Pages / index.html]
```

---

## 📂 Estrutura do Projeto

```
PulseRatingsBrasil/
├── .github/
│   └── workflows/
│       └── main.yml                 # Agendamento do pipeline no GitHub Actions
├── data/                            # Datasets, schemas e metadados de controle
│   ├── datasets.json                # Catálogo estruturado de metadados dos datasets
│   ├── schemas.json                 # Definição e mapeamento de campos e tipos
│   ├── pipeline_status.json / .js   # Logs de saúde e duração da última execução
│   ├── last_updates.json / .js      # Período de cobertura temporal de cada CSV
│   ├── emissores_consolidado.csv    # Emissores consolidados (1 linha por emissor + CNPJ)
│   └── *.csv                        # Séries temporais de ratings de crédito
├── tests/                           # Testes automatizados
│   ├── __init__.py
│   └── test_consolidar_emissores.py # Testes do script de consolidação
├── scrapers/                        # Módulos de captura
│   ├── utils/
│   │   ├── __init__.py
│   │   └── base.py                  # Classe base BaseScraper
│   └── *.py                         # Scripts de coleta (duplas emissores/ratings por fonte)
├── utils/                           # Utilitários compartilhados auxiliares
│   ├── __init__.py
│   ├── base.py                      # Salvamento de CSVs e helpers HTTP
│   └── parsers.py                   # Parsers auxiliares para formatos especiais
├── scripts/                         # Scripts de ciclo de vida
│   ├── consolidar_emissores.py      # Consolida emissores das agências em 1 CSV
│   ├── generate_catalog.py          # Gerador automatizado do catálogo de datasets
│   ├── preencher_cnpj_cvm.py        # Preenche CNPJ via dados offline da CVM
│   ├── preencher_cnpj_api.py        # Preenche CNPJ via CNPJ Aberto API (1.000 req/dia)
│   ├── preencher_cnpj_rfb.py        # Preenche CNPJ via base local da Receita Federal
│   └── utils/
│       ├── __init__.py
│       └── ux.py                    # Utilitários de UX (cores, ícones, progresso)
├── run_all.py                       # Orquestrador CLI central do projeto
├── requirements.txt                 # Dependências do Python
├── .env.example                     # Template de variáveis de ambiente
├── index.html                       # Dashboard estático do projeto
└── README.md
```

---

## ☁️ Deploy no Databricks (Opcional)

O pipeline pode ser executado em um cluster Databricks para armazenar os CSVs no DBFS e alimentar dashboards via Databricks SQL.

### Setup

1. Crie um cluster Databricks (runtime 15.4 LTS ou superior).
2. Configure o **init script** do cluster para instalar o `curl-cffi`:
   - Cluster → Advanced → Init Scripts → adicione o caminho para `databricks/init.sh` no DBFS ou Workspace.
3. Instale as demais dependências:
   ```bash
   pip install -r databricks/requirements.txt
   ```
4. Defina a variável de ambiente `DATABRICKS_DATA_PATH` no cluster ou job:
   ```
   DATABRICKS_DATA_PATH=/dbfs/FileStore/pulse_ratings/data
   ```
   Se não definida, o pipeline salva os dados em `data/` (comportamento padrão local).

### Execução

```bash
# Pipeline completo
python databricks/run_pipeline.py

# Apenas um scraper
python databricks/run_pipeline.py --scraper fitch_emissores

# Dry-run (apenas log, não salva)
python databricks/run_pipeline.py --dry-run
```

O script respeita o mesmo sistema de descoberta de scrapers e fases do `run_all.py`.

### Como funciona

- `databricks/run_pipeline.py` orquestra os scrapers, escrevendo os CSVs no diretório definido por `DATABRICKS_DATA_PATH`.
- O diretório de saída é resolvido por `utils/paths.get_data_dir()`, que prioriza a variável de ambiente com fallback para `data/`.
- O `BaseScraper` em `scrapers/utils/base.py` usa `get_data_dir()` para determinar onde salvar, sem alterar o comportamento local.

> **Nota:** O deploy no Databricks é adicional e não interfere no pipeline GitHub Actions. Ambos compartilham o mesmo código de scrapers.

---

## 💻 Guia do Desenvolvedor

### Instalação Local

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/PulseDataLabs/PulseRatingsBrasil.git
    cd PulseRatingsBrasil
    ```

2.  **Configure o ambiente virtual e instale as dependências:**

    ##### Opção A: Recomendada (Usando `uv`)
    O `uv` é um gerenciador de pacotes extremamente rápido escrito em Rust.
    ```bash
    # Cria o ambiente virtual (.venv)
    uv venv

    # Ativa o ambiente virtual
    source .venv/bin/activate

    # Instala as dependências
    uv pip install -r requirements.txt
    ```

    ##### Opção B: Tradicional (venv + pip)
    Caso prefira a abordagem clássica do Python:
    ```bash
    # Cria o ambiente virtual (venv)
    python -m venv venv

    # Ativa o ambiente virtual
    source venv/bin/activate

    # Instala as dependências
    pip install -r requirements.txt
    ```

3.  **Configure o arquivo de variáveis de ambiente:**
    ```bash
    cp .env.example .env
    ```
    *(Edite o `.env` caso queira evitar o fallback dinâmico de APIs ou configurar a persistência de dados no Oracle Cloud Autonomous Database).*

#### 🗄️ Persistência no Oracle Cloud Autonomous Database

Para habilitar a gravação automatizada dos dados no Oracle Cloud Autonomous Database, configure as seguintes variáveis no arquivo `.env`:
*   `ORACLE_DB_USER`: Usuário do banco de dados.
*   `ORACLE_DB_PASSWORD`: Senha do usuário.
*   `ORACLE_DB_DSN`: O DSN de conexão (Service Name do seu banco de dados).
*   `ORACLE_DB_WALLET_DIR`: O caminho local absoluto para o diretório descompactado contendo os arquivos da Wallet (ex: contendo `cwallet.sso`, `tnsnames.ora`). Se omitido ou vazio, o driver tentará conectar via **One-Way TLS**. Caso preenchido, usará **Mutual TLS (mTLS)**.
*   `ORACLE_DB_WALLET_PASSWORD`: A senha da Wallet (opcional).

Se as credenciais não forem fornecidas ou a variável de ambiente `SKIP_ORACLE_DB` estiver configurada como `1`, a persistência no banco de dados será ignorada silenciosamente e sem crashar a gravação local dos arquivos CSV.

### Executando os Scrapers

*   **Executar todos os scrapers ativos:**
    ```bash
    python run_all.py
    ```

*   **Executar ignorando a persistência no banco de dados Oracle:**
    ```bash
    python run_all.py --skip-db
    ```

*   **Executar sequencialmente (ideal para depuração):**
    ```bash
    python run_all.py --sequential
    ```

*   **Executar apenas um scraper específico:**
    ```bash
    python run_all.py --scraper moodys_ratings
    ```

*   **Regenerar apenas o catálogo `datasets.json`:**
    ```bash
    python run_all.py --generate-catalog
    ```

### Preenchimento de CNPJ

O campo `cnpj_emissor` do consolidado é preenchido por 3 scripts, executados em ordem:

| Script | Fonte | Onde roda | Limitação |
|--------|-------|-----------|-----------|
| `preencher_cnpj_cvm.py` | CVM (cias abertas + fundos) | GitHub Actions (automático) | ~400-500 matches |
| `preencher_cnpj_api.py` | [CNPJ Aberto API](https://cnpjaberto.com) | GitHub Actions (automático) | 1.000 req/dia free |
| `preencher_cnpj_api_proxy.py` | Idem + proxy automático | Local (quando API bate rate limit) | Depende dos proxies públicos |
| `preencher_cnpj_rfb.py` | Receita Federal (base completa) | **Local apenas** | ~1.4GB download |

**RFB (local — download automático via WebDAV):**
```bash
# Executar (baixa Empresas*.zip do mês mais recente automaticamente):
python scripts/preencher_cnpj_rfb.py

# Para recriar o banco SQLite do zero (útil para atualizar a base):
python scripts/preencher_cnpj_rfb.py --rebuild-db
```

O script descobre o mês mais recente via WebDAV no repositório oficial da
Receita Federal, baixa os 10 arquivos `Empresas0.zip`..`Empresas9.zip`
(~1.4GB total), extrai as empresas para um banco SQLite local com índice
de nomes normalizados, e busca cada emissor pendente por nome exato ou
fallback por palavras significativas.

**Proxy automático (quando a API bater rate limit):**
```bash
python scripts/preencher_cnpj_api_proxy.py
```

Raspa proxies gratuitos de 4 fontes públicas, valida o primeiro
funcionando contra `httpbin.org`, e delega o preenchimento à API
com o proxy setado automaticamente via `CNPJABERTO_PROXY`.

---

## 🧩 Grupos de Scrapers

O orquestrador `run_all.py` organiza os scrapers em grupos. Este repositório contém scrapers de múltiplos domínios:

| Grupo | Descrição | Scrapers |
|-------|-----------|----------|
| `ratings` | Ratings de crédito (S&P, Moody's, Fitch, Austin, Liberum) | `standard_and_poors_ratings`, `standard_and_poors_emissores`, `moodys_ratings`, `moodys_emissores`, `fitch_ratings`, `fitch_emissores`, `austin_ratings`, `austin_emissores`, `liberum_ratings`, `liberum_emissores` |
| `consolidated` | Emissores consolidados (1 linha por emissor) | `emissores_consolidado` |
| `anbima` | Dados ANBIMA | *(implementação externa)* |
| `b3` | Dados B3 | *(implementação externa)* |
| `bcb` | Dados Banco Central | *(implementação externa)* |
| `cvm` | Dados CVM | *(implementação externa)* |
| `ibge` | Dados IBGE | *(implementação externa)* |
| `misc` | Outras fontes | *(implementação externa)* |

Apenas o grupo `ratings` está ativo por padrão neste repositório público.

---

## 📡 Fontes de Dados

### S&P
- **Tipo:** Scraper web com extração dinâmica de chave pública
- **Autenticação:** Opcional (`SP_GLOBAL_API_KEY`). Sem a chave, o scraper extrai a chave pública dinamicamente.
- **Dados coletados:** Ratings de emissor e lista de emissores
- **Frequência:** Cada execução do pipeline

### Moody's
- **Tipo:** Planilhas Excel (.xlsx) e dados estruturados
- **Autenticação:** Pública (sem chave)
- **Dados coletados:** Ratings de emissor e lista de emissores
- **Frequência:** Cada execução do pipeline

### Fitch
- **Tipo:** API GraphQL pública
- **Autenticação:** Pública (sem chave)
- **Dados coletados:** Ratings de emissor e lista de emissores
- **Frequência:** Cada execução do pipeline

### Austin Rating
- **Tipo:** Web scraper concorrente baseado em requisições HTTP e tabelas HTML
- **Autenticação:** Pública (sem chave)
- **Dados coletados:** Ratings de emissor e lista de emissores
- **Frequência:** Cada execução do pipeline

### Liberum Ratings
- **Tipo:** Consumo direto da API pública de listagem do painel em React
- **Autenticação:** Pública (sem chave para listagem de ratings ativos / arrays internos)
- **Dados coletados:** Ratings por classe/escala e lista de emissores
- **Frequência:** Cada execução do pipeline

---

## 📊 Schema dos Dados

Cada arquivo CSV segue o padrão: **UTF-8**, separador **vírgula**, decimal **ponto**, datas **YYYY-MM-DD**.

Os campos comuns a todos os datasets:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `dt_captura` | date | Data da captura pelo pipeline |
| `no_emissor` | str | Nome do emissor |

O dataset `emissores_consolidado.csv` possui estrutura própria:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `no_emissor_padronizado` | str | Nome normalizado (uppercase, sem acentos, sem sufixos) |
| `no_emissor_fitch` | str | Nome original na fonte Fitch |
| `no_emissor_moodys` | str | Nome original na fonte Moody's |
| `no_emissor_standard_and_poors` | str | Nome original na fonte S&P |
| `no_emissor_austin` | str | Nome original na fonte Austin Rating |
| `no_emissor_liberum` | str | Nome original na fonte Liberum Ratings |
| `cnpj_emissor` | str | CNPJ do emissor (preenchido via CVM + CNPJ Aberto API + base RFB) |

As definições completas de campos e tipos são geradas automaticamente em [`data/schemas.json`](data/schemas.json) a cada execução e exibidas no [dashboard](https://pulsedatalabs.github.io/PulseRatingsBrasil/).

---

## 🤝 Como Contribuir

1. Faça um **fork** do repositório
2. Crie uma **branch** para sua feature: `git checkout -b minha-feature`
3. Faça o **commit** das alterações: `git commit -m "feat: descrição concisa"`
4. Envie para o **remote**: `git push origin minha-feature`
5. Abra um **Pull Request**

### Convenções
- Commits seguem [Conventional Commits](https://www.conventionalcommits.org/)
- Código Python segue [PEP 8](https://peps.python.org/pep-0008/)
- Docstrings no formato Google style

---

## ❓ Troubleshooting

| Problema | Causa | Solução |
|----------|-------|---------|
| S&P retorna dados vazios | Chave pública expirada ou bloqueada | Executar novamente — o scraper tenta extrair nova chave automaticamente |
| Schema drift alerta | Agência modificou colunas do layout | Revisar o drift em `pipeline_status.json` e atualizar se necessário |
| Pipeline timeout no GH Actions | Execução excede 6h | Verificar scraper específico com `--sequential` localmente |
| Erro `xlrd.biffh.XLRDError` | Arquivo Excel no formato `.xlsx` | O fallback para `openpyxl` é automático |

---

## 📋 Changelog

### 2026-06
- Padronização do campo de captura para `dt_captura`
- Dashboard com busca, filtros e schema dinâmico
- Suporte a 10 datasets de ratings (5 agências × ratings + emissores)
- Integração da **Austin Rating** e da **Liberum Ratings** (incluindo tratamento de timeouts e retries na API)
- Detecção automática de schema drift
- Consolidação de emissores: script + testes + dataset `emissores_consolidado.csv` com suporte a 5 agências
- Sistema de UX unificado (cores, progresso, logging) nos scrapers e orquestrador

### 2026-05
- Pipeline inicial com scrapers S&P, Moody's e Fitch
- Schema drift detection
- Catálogo dinâmico de datasets

---

## 🔒 Segurança

Para reportar vulnerabilidades, abra uma [issue](https://github.com/PulseDataLabs/PulseRatingsBrasil/issues) com o label `security` ou entre em contato pelo GitHub.

---

## 📄 Licença

Este projeto está sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para obter mais detalhes.

Desenvolvido com 💙 por **[PulseDataLabs](https://github.com/PulseDataLabs)**.

---

<p align="center">
  <sub>Dados públicos de rating — S&P, Moody's, Fitch, Austin e Liberum</sub>
</p>
