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

O **Pulse Ratings Brasil** é um pipeline de ETL (Extração, Transformação e Carga) serverless projetado para coletar, tratar e disponibilizar dados de ratings de crédito (corporativos e soberanos) das principais agências de classificação de risco em atuação no Brasil: **S&P**, **Moody's** e **Fitch**.

Ele funciona 100% de forma automatizada via **GitHub Actions**, salvando o histórico consolidado diretamente no repositório em formato CSV plano, sem custos com banco de dados ou servidores. Os dados tratados alimentam um dashboard interativo servido via **GitHub Pages**.

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
    B -->|Executes Phase 1| D["Independent Scrapers: Entities (Moody's, S&P, Fitch)"]
    B -->|Executes Phase 2| E["Dependent Scrapers: Ratings (Moody's, S&P, Fitch)"]
    D --> F["data/*.csv files"]
    E --> F
    B -->|Calls generate_catalog.py| G["data/datasets.json"]
    F & G --> H[git push origin main]
    H --> I[GitHub Pages / index.html]
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
│   └── *.csv                        # Séries temporais de ratings de crédito
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
│   └── generate_catalog.py          # Gerador automatizado do catálogo de datasets
├── run_all.py                       # Orquestrador CLI central do projeto
├── requirements.txt                 # Dependências do Python
├── .env.example                     # Template de variáveis de ambiente
├── index.html                       # Dashboard estático do projeto
└── README.md
```

---

## 💻 Guia do Desenvolvedor

### Instalação Local

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/PulseDataLabs/PulseRatingsBrasil.git
    cd PulseRatingsBrasil
    ```

2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure o arquivo de variáveis de ambiente:**
    ```bash
    cp .env.example .env
    ```
    *(Edite o `.env` caso precise definir chaves de API, como `SP_GLOBAL_API_KEY`, caso queira evitar o fallback dinâmico).*

### Executando os Scrapers

*   **Executar todos os scrapers ativos:**
    ```bash
    python run_all.py
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

---

## 🧩 Grupos de Scrapers

O orquestrador `run_all.py` organiza os scrapers em grupos. Este repositório contém scrapers de múltiplos domínios:

| Grupo | Descrição | Scrapers |
|-------|-----------|----------|
| `ratings` | Ratings de crédito (S&P, Moody's, Fitch) | `standard_and_poors_ratings`, `standard_and_poors_entidades`, `moodys_ratings`, `moodys_entidades`, `fitch_ratings`, `fitch_entidades` |
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

---

## 📊 Schema dos Dados

Cada arquivo CSV segue o padrão: **UTF-8**, separador **vírgula**, decimal **ponto**, datas **YYYY-MM-DD**.

Os campos comuns a todos os datasets:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `dt_captura` | date | Data da captura pelo pipeline |
| `no_entidade` | str | Nome do emissor |

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
- Suporte a 6 datasets de ratings (3 agências × ratings + emissores)
- Detecção automática de schema drift

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
  <sub>Dados públicos de rating — S&P, Moody's e Fitch · Open-source</sub>
</p>
