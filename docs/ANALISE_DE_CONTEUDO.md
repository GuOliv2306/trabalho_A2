# Análise de conteúdo (Bardin), automatizada e validada

## As etapas e onde estão

| Etapa de Bardin | Aqui |
|---|---|
| Pré-análise: corpus, unidade de registro, leitura flutuante | três corpora; unidade declarada em cada livro de códigos |
| Exploração: codificação por categorias | `POST /code` aplica o livro (regras ou IA) |
| Tratamento e inferência | `GET /results`: frequências e desempenho por categoria |
| Validação | `GET /reliability`: concordância entre dois codificadores |

O livro de códigos é dado puro (`src/content_analysis/codebooks.py`): definição, exemplos,
regras de decisão para casos duvidosos e regras automáticas. Categorias mutuamente
exclusivas (um código por unidade) e exaustivas (há sempre uma categoria residual).

## Corpora e variáveis

| Corpus | Unidade | Variáveis | Dado |
|---|---|---|---|
| `seo_consultas` | a consulta | `intencao`, `formato_serp` | simulado (231) |
| `seo_paginas` | a página | `tipo_pagina`, `profundidade`, `autoria` | simulado (99) |
| `wikipedia_resumos` | o resumo de edição | `tipo_edicao`, `origem_do_resumo` | real (1.573) |

- `intencao`: navegacional, transacional, informacional, comercial, indefinida.
- `formato_serp`: o formato de maior área na página de resultados (registro da plataforma, não interpretação).
- `tipo_pagina` (lido no endereço), `profundidade` (contagem de palavras), `autoria` (sem autoria, autor identificado, autor com credenciais).
- `tipo_edicao`: reversão, administrativa, manutenção assistida, fontes, forma, conteúdo, sem informação.
- `origem_do_resumo`: em branco, gerado pelo software, escrito pelo editor.

## Rotas (`/api/v1/content-analysis`)

| Rota | Faz |
|---|---|
| `GET /codebooks?corpus=` | publica o livro de códigos (sem `corpus`, lista os corpora) |
| `GET /sample?corpus=&n=&seed=` | amostra reproduzível, para um segundo codificador classificar às cegas |
| `POST /code` `{"corpus", "coder": "regras"\|"llm", "admin_key"}` | codifica o corpus inteiro e grava (recodificar substitui) |
| `GET /results?corpus=&variable=&coder=regras` | por categoria: `n`, `share` e desempenho (cliques, CTR, posição; ou reversão, robôs, anônimos) |
| `GET /reliability?corpus=&variable=&coder_a=regras&coder_b=referencia_ia` | concordância, matriz de confusão, acerto por categoria e a lista de desacordos |

Codificadores gravados: `regras`, `llm` (opcional), `verdade_simulador` (rótulo do gerador),
`referencia_ia` (amostra de validação) e `referencia_ia_desenvolvimento` (amostra usada para revisar o livro).

O codificador por IA (`coder: "llm"`) recebe o livro como instrução e precisa de
`OPENAI_API_KEY`. Está testado com um dublê; **não foi executado contra a API real**.

## Como ler a validação

Dois codificadores classificam as mesmas unidades sem se ver; a API compara.

- **Concordância percentual**: em quantas unidades deram o mesmo código.
- **Kappa de Cohen e alfa de Krippendorff**: a mesma coisa, descontando o que coincidiria por acaso. De 0 a 1.
- Faixas (Krippendorff): **≥ 0,80 confiável**; **0,667 a 0,80 provisória**; abaixo disso, revisar o livro.

## O que foi feito e o que deu

A referência foi classificada **por IA** (agentes de contexto limpo, às cegas: receberam só
definições e exemplos, nunca as regras nem os códigos automáticos). **Não é validação humana**:
mede se dois procedimentos independentes chegam ao mesmo código, não se o código está certo.

**Rodada 1 (livro v1).** Nos corpora simulados, concordância total. Nos resumos reais da
Wikipedia (150 unidades), `tipo_edicao` deu alfa 0,66 — insuficiente.

**Revisão (livro v2).** Os desacordos e as dúvidas do segundo codificador viraram regras de
decisão: resumo com várias ações vale a primeira declarada; remoção feita à mão é conteúdo,
não reversão; imagem é conteúdo; marcador de ferramenta é manutenção assistida.

**Rodada 2 (livro v2, amostra nova de 150 unidades que não participou da revisão).**

| Variável | Concordância | Kappa | Alfa | Leitura |
|---|---|---|---|---|
| `origem_do_resumo` | 97,3% | 0,96 | 0,96 | confiável |
| `tipo_edicao` | 82,0% | 0,75 | 0,75 | provisória |

Na amostra de desenvolvimento o `tipo_edicao` v2 chega a 0,84. A diferença para 0,75 é o
tamanho do otimismo de medir nas mesmas unidades que serviram para ajustar as regras.

Onde `tipo_edicao` ainda erra (amostra de validação): reversão e manutenção assistida saem
perfeitas; `forma` só é encontrada em 48% dos casos. As regras não reconhecem "hiperligação"
quando o verbo é genérico ("Adicionando hiperligação" cai em conteúdo) nem resumos sem verbo
("portugues", "wikilink ..."). As regras não foram mais ajustadas depois desta medição, para
a amostra continuar valendo como validação. É a próxima revisão do livro.

**Corpora simulados.**

| Variável | Contra a referência por IA | Contra o rótulo do simulador |
|---|---|---|
| `intencao` | 100% (60) | 94,8%, alfa 0,93 (231) |
| `formato_serp`, `tipo_pagina`, `profundidade`, `autoria` | 100% | 100% |

Os 12 desacordos de `intencao` são as consultas "secas" (só o nome do produto): o gerador
as marca como comerciais e as regras, como indefinidas. Concordância tão alta aqui é esperada
e pouco informativa: os textos saem de moldes.

## Inferências (codificador por regras)

**Resumos de edição da Wikipedia (1.573, reais)**

| Origem do resumo | Parte | Edições depois revertidas |
|---|---|---|
| Gerado pelo software | 40,2% | 2,1% |
| Escrito pelo editor | 37,5% | 15,8% |
| Em branco | 22,3% | 10,8% |

- **Quase dois terços dos resumos não foram escritos por ninguém**: 40% vêm de botões,
  ferramentas e robôs, 22% estão em branco. Analisar "o que os editores dizem" é, em boa
  parte, analisar o que a interface escreve por eles.
- **Metade das edições (51%) não informa o que fez** (`sem_informacao`).
- Edições que se declaram de conteúdo são as mais revertidas depois (16,5%); as de manutenção
  assistida, nunca (0%), e 30% delas são de robôs.

**Consultas (simuladas)**: o CTR varia mais com o formato da página de resultados (vitrine de
produtos 4,8%, links tradicionais 10,3%, links do próprio site 23,8%) do que com a intenção —
efeito que o simulador injeta de propósito.

## Limites

- Referência codificada por IA, não por pessoas. Falta uma amostra codificada por humanos.
- `tipo_edicao` é provisória (alfa 0,75): serve para descrever, não para sustentar conclusão forte.
- As regras leem o que o resumo declara, não o que a edição fez (o diff não é analisado).
- Corpora de consultas e páginas são sintéticos; ver [SIMULADOR_PENDENCIAS.md](SIMULADOR_PENDENCIAS.md).
- Os resumos vêm de 12 artigos sobre inteligência artificial em português: não representam a Wikipedia.
