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
| `GET /reliability?corpus=&variable=&coder_a=regras&coder_b=referencia_ia` | concordância, alfa com intervalo de 95%, matriz de confusão, acerto por categoria e a lista de desacordos |

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

| Variável | Concordância | Kappa | Alfa (intervalo de 95%) | Leitura |
|---|---|---|---|---|
| `origem_do_resumo` | 97,3% | 0,96 | 0,96 (0,92 a 0,99) | confiável |
| `tipo_edicao` | 82,0% | 0,75 | 0,75 (0,67 a 0,83) | provisória |

Com 150 unidades o alfa de `tipo_edicao` pode estar em qualquer ponto entre 0,67 e 0,83: a
amostra não permite dizer se ele está acima ou abaixo do corte de 0,80.

Na amostra de desenvolvimento o `tipo_edicao` v2 chega a 0,85. A diferença para 0,75 é o
tamanho do otimismo de medir nas mesmas unidades que serviram para ajustar as regras.

Onde `tipo_edicao` ainda erra (amostra de validação): reversão e manutenção assistida saem
perfeitas; `forma` só é encontrada em 48% dos casos. As regras não reconhecem "hiperligação"
quando o verbo é genérico ("Adicionando hiperligação" cai em conteúdo) nem resumos sem verbo
("portugues", "wikilink ..."). É a próxima revisão do livro.

Depois da medição houve uma correção de defeitos apontados por uma auditoria independente,
com exemplos inventados por ela e não tirados da amostra: casar texto sem acento, "bot" só
como marcador de autoria, "corrida" não é "correção". Os números acima são os de depois
dessa correção; na amostra de validação ficaram iguais aos de antes.

**Corpora simulados.**

| Variável | Contra a referência por IA | Contra o rótulo do simulador |
|---|---|---|
| `intencao` | 100% (60) | 94,8%, alfa 0,93 (231) |
| `tipo_pagina`, `profundidade`, `autoria` | 100% (40) | 100% (99) |
| `formato_serp` | não se aplica | 100% (231) |

Os 12 desacordos de `intencao` são as consultas "secas" (só o nome do produto): o gerador
as marca como comerciais e as regras, como indefinidas. Concordância tão alta aqui é esperada
e pouco informativa: os textos saem de moldes. `formato_serp` é leitura mecânica de um campo
da plataforma (o formato de maior área); não há o que um segundo codificador interpretar.

## Inferências (codificador por regras)

**Resumos de edição da Wikipedia (1.573, reais)**

| Origem do resumo | Parte | Edições depois revertidas |
|---|---|---|
| Gerado pelo software | 40,1% | 2,1% |
| Escrito pelo editor | 37,6% | 15,7% |
| Em branco | 22,3% | 10,8% |

- **62% dos resumos não foram escritos por ninguém**: 40% vêm de botões, ferramentas e
  robôs, 22% estão em branco. Analisar "o que os editores dizem" é, em boa parte, analisar o
  que a interface escreve por eles.
- **Metade das edições (51%) não informa o que fez** (`sem_informacao`).
- Edições que se declaram de conteúdo são as mais revertidas depois (16,0%); as de manutenção
  assistida, nunca (0%), e 30% delas são de robôs.

**Consultas (simuladas)**: o CTR varia mais com o formato da página de resultados (vitrine de
produtos 5,5%, links tradicionais 10,3%, links do próprio site 14,1%) do que entre as
intenções mais comuns (6,9% a 8,0%) — efeito que o simulador injeta de propósito.

## Limites

- Referência codificada por IA, não por pessoas. Falta uma amostra codificada por humanos.
- `tipo_edicao` é provisória (alfa 0,75, entre 0,67 e 0,83): serve para descrever, não para sustentar conclusão forte.
- As regras ignoram maiúsculas e acentos, mas não erros de digitação nem sinônimos fora da lista.
- O codificador por IA devolve `unanswered`: quantos códigos caíram na categoria residual por falta de resposta válida.
- As regras leem o que o resumo declara, não o que a edição fez (o diff não é analisado).
- Corpora de consultas e páginas são sintéticos; ver [SIMULADOR_PENDENCIAS.md](SIMULADOR_PENDENCIAS.md).
- Os resumos vêm de 12 artigos sobre inteligência artificial em português: não representam a Wikipedia.
