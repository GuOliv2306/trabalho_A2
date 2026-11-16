# Analytics API — Métodos Digitais

API FastAPI sobre DuckDB para a disciplina de Métodos Digitais. Combina um painel de
marketing (KPIs, correlações, clusters, relatório por IA) com **métodos nativamente digitais**:
coleta real da Wikipedia e análises que tratam o dado como produto da plataforma.

- Conceito e rotas de métodos digitais: [`docs/METODOS_DIGITAIS.md`](docs/METODOS_DIGITAIS.md)
- Arquitetura: [`docs/CODEBASE_MAP.md`](docs/CODEBASE_MAP.md)

## Rodar

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Documentação interativa em http://localhost:8000/docs.

`.env` (opcional, veja `.env.example`):

| Variável | Para quê |
|---|---|
| `OPENAI_API_KEY` | relatório por IA (sem ela, sai um relatório simples de fallback) |
| `ADMIN_KEY` | protege `populate-database` e `wikipedia/collect` |
| `WIKIPEDIA_USER_AGENT` | identificação enviada à Wikipedia (padrão: URL do repositório) |

## Dados

- **Wikipedia (real)**: `POST /api/v1/digital-methods/wikipedia/collect`. O banco versionado já
  traz uma coleta de 12 artigos em torno de "Inteligência artificial".
- **GA4 / Search Console (sintético)**: `POST /api/v1/admin/populate-database`
  com `{"days": 50, "overwrite": true, "admin_key": "..."}`. A coleta real do Google está desativada.

## Rotas

| Grupo | Rota |
|---|---|
| Saúde | `GET /health` |
| Painel | `GET /api/v1/overview/kpis` |
| Análise | `GET /api/v1/analysis/correlation_matrix` |
| Clusters | `GET /api/v1/ml/channel_clusters`, `GET /api/v1/ml/keyword_clusters` |
| Métodos digitais | `POST /api/v1/digital-methods/wikipedia/collect` |
| | `GET /api/v1/digital-methods/wikipedia/edit-history` |
| | `GET /api/v1/digital-methods/wikipedia/controversy` |
| | `GET /api/v1/digital-methods/wikipedia/link-network` |
| | `GET /api/v1/digital-methods/wikipedia/editions` |
| | `GET /api/v1/digital-methods/search/rank-effect` |
| | `GET /api/v1/digital-methods/search/query-network` |
| Dados brutos | `GET /api/v1/data/all`, `GET /api/v1/data/summary` |
| Relatório IA | `POST /api/v1/reports/generate` |
| Admin | `POST /api/v1/admin/populate-database`, `GET /api/v1/admin/database-stats` |

Removidas (o frontend deve parar de chamar): `/api/v1/ml/page_clusters`,
`/api/v1/page_analysis`, `/api/v1/predict/simulator`.

## Testes

```bash
python -m pytest tests/test_api.py tests/test_digital_methods.py -v
RUN_NETWORK=1 python -m pytest tests/test_digital_methods.py -k live   # bate na Wikipedia real
```

## Deploy

Render (`https://siteup.onrender.com`): build `pip install -r requirements.txt`, start
`python app/main.py`. O frontend Next.js fica em outro repositório, na Vercel.
