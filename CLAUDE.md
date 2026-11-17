# CLAUDE.md

# O PROJETO É SEU

**Você é dono deste backend.** Pode sofisticar, sempre pensando em melhoria e no melhor resultado.
Termine o que começar, do início ao fim:

- Comece pelas partes difíceis.
- Não pare enquanto faltar algo que foi pedido.
- Só diga que funciona se viu funcionando (teste rodado, servidor no ar, dado real).
- TDD: teste antes do código. De tempos em tempos, peça a um agente de contexto limpo para auditar.
- Mantenha a essência e a estrutura do projeto; adicione antes de modernizar o que já funciona.
- Corte o que atrapalha (código morto, ML de enchimento, docs velhos).

## O que é

API FastAPI (projeto em português) sobre um DuckDB local, para a disciplina de **Métodos Digitais**.
Quatro frentes: painel de marketing com dados sintéticos (GA4 / Search Console simulados);
**métodos nativamente digitais** com dados reais da Wikipedia; **quase-experimentos**
(série interrompida, contrafactual por controles, diff-in-diff, teste A/B) sobre um painel
simulado de efeito conhecido, e um **experimento natural** com dado real (o fim da edição
anônima na pt.wikipedia); e **análise de conteúdo** (Bardin) com livro de códigos,
codificador por regras ou IA e validação por concordância. A tese que guia as features:
o dado é produzido pela plataforma, então toda análise devolve `leitura_do_meio` — o que o
número diz sobre o meio e o limite do que diz sobre o tema.

**Stack**: Python, FastAPI, DuckDB, pandas, scikit-learn, requests, Agno + OpenAI, pytest.

**Estrutura**: `app/main.py` (todas as rotas), `app/report_*` (relatório por IA),
`src/digital_methods/` (coletor da Wikipedia + análises puras), `src/quasi_experiments/`
(estimadores causais), `src/content_analysis/` (livros de códigos, codificador, concordância),
`src/collectors/db_storage.py`
(DuckDB), `src/ml/` (clusters), `src/cleaning/`, `tests/`.

## Comandos (da raiz do repositório)

```bash
python -m uvicorn app.main:app --reload --port 8000
python -m pytest tests/test_api.py tests/test_digital_methods.py tests/test_quasi_experiments.py tests/test_natural_experiments.py tests/test_content_analysis.py -v
RUN_NETWORK=1 python -m pytest tests/test_digital_methods.py -k live   # Wikipedia real
```

## Regras da casa

- Entrada do usuário em SQL sempre por parâmetro, nunca f-string.
- Chamadas à Wikipedia só por `_query`/`_get` em `src/digital_methods/wikipedia.py` (limite de requisições).
- Mudou formato de resposta de rota? O frontend na Vercel (outro repositório) depende disso — avise.
- Estimador causal novo só entra com teste que recupera um efeito conhecido.
- Em dado real não há gabarito: mostre o placebo e o método que discorda antes de afirmar um efeito.
- Nunca use o mesmo período para escolher as unidades e para medir o "antes".
- Categoria nova no livro de códigos: definição, exemplo e teste; depois recodifique e veja a concordância.
- Nunca apresente codificação feita por IA como validação humana.
- Commits locais por etapa testada; sem push sem pedir.

Detalhes: [docs/CODEBASE_MAP.md](docs/CODEBASE_MAP.md) · [docs/METODOS_DIGITAIS.md](docs/METODOS_DIGITAIS.md) ·
[docs/QUASE_EXPERIMENTOS.md](docs/QUASE_EXPERIMENTOS.md) · [docs/EXPERIMENTO_NATURAL.md](docs/EXPERIMENTO_NATURAL.md) · [docs/ANALISE_DE_CONTEUDO.md](docs/ANALISE_DE_CONTEUDO.md) ·
[docs/SIMULADOR_PENDENCIAS.md](docs/SIMULADOR_PENDENCIAS.md)
