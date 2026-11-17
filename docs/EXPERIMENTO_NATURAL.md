# Experimento natural: o fim da edição anônima na Wikipédia em português

## A ideia

Um quase-experimento precisa de uma mudança com data conhecida. Na Wikipedia, a própria
plataforma fornece uma: em **4 de outubro de 2020**, por decisão da comunidade, a edição em
português passou a aceitar só contas registradas. As edições em espanhol e francês não mudaram.

Pergunta: **o que essa regra causou nas reversões e no volume de edições?**

É o argumento da disciplina em forma de número: a plataforma muda uma regra e o
"comportamento" medido muda junto. E é dado real — não existe `true_effect` para conferir.

## Desenho

| | |
|---|---|
| Tratado | artigos na pt.wikipedia |
| Controle | os **mesmos artigos** na es.wikipedia (ou fr.wikipedia) |
| Janela | out/2018 a set/2022, contagens mensais |
| Artigos | sorteio reprodutível entre os links de "Inteligência artificial" que existem nos três idiomas |
| Quem entra | artigo criado antes da janela e com edição anônima nos 6 primeiros meses, nos dois idiomas |
| Estimativa | de abr/2019 em diante: 18 meses antes, 24 depois |

Três decisões que mudam o resultado, e por quê:

- **Sorteio, não "os mais vistos".** Artigos muito populares (Brasil, Google, Isaac Newton) já
  estavam protegidos contra anônimos antes de 2020: neles a regra nova não mudou nada.
- **Só artigos abertos a anônimos.** São os que de fato sofreram a intervenção.
- **O período que decide quem entra fica fora da conta.** Escolher artigos por terem anônimos
  e medir no mesmo período inflaria o "antes" e exageraria a queda.

**Reversão** é medida por conteúdo idêntico: a edição devolve o artigo a uma das 15 versões
anteriores. Não usa as tags do MediaWiki, que só passaram a marcar edições revertidas em 2020
— justamente a data do experimento.

## Rotas (`/api/v1/quasi-experiments/natural`)

| Rota | Faz |
|---|---|
| `GET /experiments` | experimentos, pares coletados e elegíveis, referência externa |
| `POST /collect` `{"experiment", "seed", "max_candidates", "admin_key"}` | coleta o histórico real (vários minutos, centenas de requisições) |
| `GET /estimate?experiment=&outcome=&method=&control_lang=` | efeito, intervalo, placebo, série mensal dos dois grupos |

- `outcome`: `reverts`, `human_edits`, `registered_edits`, `anon_edits` (checagem do tratamento).
- `method`: `ratio_did` (padrão, para contagens pequenas), `did` (em log, por artigo), `control_counterfactual` (extrapola a tendência anterior).

`ratio_did` compara razões de somas: (pt depois ÷ pt antes) dividido por (controle depois ÷
controle antes). Não usa log(1 + y), então funciona com artigos de poucas edições por mês. Em
simulação com contagens de 0 a 3 por mês e efeito verdadeiro de −40%, a média das estimativas
ficou a menos de 3 pontos do valor verdadeiro e o intervalo o cobriu em pelo menos 34 de 40
casos, enquanto o DiD em log subestimou.

## O que foi coletado

40 artigos × 3 idiomas, 5.760 linhas mensais. Elegíveis: **13 pares** com o espanhol, **9** com o francês.

## O que deu

**A intervenção aconteceu.** Nos artigos elegíveis, as edições anônimas em português vão de
100 para 0. O último mês com edição anônima em pt é setembro de 2020, o que bate com a data oficial.

**Reversões** (método padrão, razões):

| Controle | pt antes → depois | Controle antes → depois | Efeito estimado | Intervalo de 95% |
|---|---|---|---|---|
| Espanhol (13 pares) | 67 → 16 | 383 → 353 | −74% | −87% a −53% |
| Francês (9 pares) | 50 → 9 | 73 → 72 | −82% | −92% a −64% |

**Edições de pessoas**: −56% (−74% a −29%) contra o espanhol; −73% (−85% a −36%) contra o francês.

**Edições de contas registradas**: −39% e −52%, com intervalos que incluem zero. Inconclusivo.

## Por que não dá para afirmar o tamanho do efeito

1. **Os artigos em português já vinham caindo.** O placebo — a mesma conta feita só no período
   anterior, onde o efeito tem de ser zero — dá −41% para reversões contra o espanhol. O
   intervalo é largo (−79% a +16%) e inclui zero, então não reprova o método; mas também não o
   aprova. Parte dos −74% pode ser queda que já estava em curso.
2. **Outro método discorda.** O contrafactual por controles, que extrapola a tendência
   anterior, não vê efeito nas reversões: +23% (−54% a +112%) contra o espanhol. A conclusão
   depende de qual pressuposto se aceita: "pt teria variado como o controle" (efeito grande) ou
   "pt teria seguido a própria tendência" (efeito indistinguível de zero).
3. **A amostra é pequena.** São 67 reversões antes e 16 depois em português. Os intervalos são largos.
4. **O DiD em log não serve aqui.** Com poucas edições por artigo e mês, ele puxa tudo para
   zero e a rota devolve o aviso de contagens pequenas.

**O que se pode dizer:** a regra eliminou a edição anônima nesses artigos, e as reversões
caíram muito mais em português do que nos mesmos artigos em espanhol e francês. A direção
concorda com o estudo da Wikimedia. O tamanho do efeito causal **não fica estabelecido** por
esta amostra.

## Referência externa

O estudo da Wikimedia Foundation sobre a mesma mudança encontrou, na wiki inteira, queda de
cerca de 44% a 47% nas reversões em relação ao mesmo trimestre do ano anterior, e crescimento
de 26% em contas novas.
[IP Editing Restriction Study / Portuguese Wikipedia](https://meta.wikimedia.org/wiki/IP_Editing:_Privacy_Enhancement_and_Abuse_Mitigation/IP_Editing_Restriction_Study/Portuguese_Wikipedia)

Não é a mesma medida: o estudo compara pt com ela mesma um ano antes, na wiki inteira, contando
edições revertidas em 48 horas. Aqui são poucos artigos, todos abertos a anônimos (onde o
vandalismo anônimo se concentrava), comparados com outro idioma. Mesma direção; números não comparáveis.

## Limites

- 13 e 9 pares de artigos, vizinhos de uma única página-semente. Vale para esse recorte.
- A pandemia de 2020 e a onda de interesse por IA depois de 2022 atingem os três idiomas, mas talvez não por igual.
- Robôs que combatem vandalismo também revertem; a queda nas reversões inclui o trabalho que eles deixaram de ter.
- Quem editava sem conta e passou a editar com conta aparece como "edição registrada": não dá para separar conversão de abandono.
- Não foi feito: o segundo experimento que propus (efeito de proteger um artigo). Proteção é aplicada
  justamente quando o vandalismo dispara, então um antes/depois mostraria queda mesmo sem efeito
  nenhum. Precisa de um desenho com artigos pareados pelo pico, que não cabe neste recorte.
