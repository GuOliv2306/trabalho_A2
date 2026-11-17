# Quase-experimentos

## A pergunta

"A mudança X causou a subida ou a queda?" O Search Console sozinho não responde: update do
algoritmo, sazonalidade e mudanças do site acontecem juntos. Cada método abaixo constrói um
**contrafactual** — o que teria acontecido sem a mudança — de um jeito diferente.

| Método | Compara com | Rota | Quando usar |
|---|---|---|---|
| Série temporal interrompida | a própria tendência anterior | `GET /its` | não há páginas de controle |
| Contrafactual por controles | previsão feita a partir das páginas de controle | `GET /control-counterfactual` | há controles e interessa a série dia a dia |
| Diferença-em-diferenças | páginas parecidas que não mudaram | `GET /did` | mudança em parte das páginas, escolhidas a dedo |
| Teste A/B de SEO | grupo sorteado do mesmo template | `GET /ab-test`, `GET /ab-split` | dá para sortear antes de mudar |

O contrafactual por controles segue a lógica do CausalImpact, mas com regressão simples e
reamostragem em blocos no lugar do modelo bayesiano de séries estruturais. Não é o pacote do Google.

## Rotas (`/api/v1/quasi-experiments`)

Todas as de estimativa recebem `intervention_id`, `metric` (`clicks` ou `impressions`) e
`end_date` opcional (corta a janela). Devolvem:

- `relative_effect` (0.10 = +10%), `ci95`, `p_value`;
- `true_effect`: o efeito que o simulador injetou, para conferir o método;
- `pressupostos` do método e `leitura_do_meio`.

| Rota | Extras na resposta |
|---|---|
| `GET /interventions` | registro de mudanças e eventos externos, `n_treated`, `n_control`, `randomized` |
| `GET /its` | `level_change`, `slope_change_per_day`, `series` (real e contrafactual por dia) |
| `GET /control-counterfactual` | `pre_fit_r2`, `series` |
| `GET /did` | `naive_before_after`, `control_change`, `balance`, `placebo_pre`, `event_study` semanal |
| `GET /ab-test` | o mesmo do DiD + `permutation_p_value`. `400` se a intervenção não foi sorteada |
| `GET /ab-split?template=&seed=&days=28` | planeja um teste: sorteio estratificado pelo tráfego recente, com `balance` |

Como ler o DiD: `placebo_pre` repete a conta dentro do período anterior, onde o efeito tem de
ser zero; se o intervalo não contém zero, as tendências não eram paralelas e o resultado não vale.

## O painel simulado

`ExperimentSimulator` (em `tests/simulador_dados.py`) gera 99 páginas × 120 dias com
sazonalidade semanal, tendência leve e quatro eventos de efeito conhecido:

| Intervenção | Data | Páginas | Sorteada | Efeito verdadeiro |
|---|---|---|---|---|
| `titulos_blog` | 13/09/2025 | 30 posts (controle: 12 categorias) | não | +15% |
| `schema_categorias` | 23/09/2025 | 12 categorias de maior tráfego (controle: outras 12) | não | +20% |
| `descricao_produtos_ab` | 28/09/2025 | 20 produtos (controle: outros 20) | sim | +10% |
| `update_algoritmo` | 18/10/2025 | site inteiro (evento externo) | — | −12% |

`POST /api/v1/admin/populate-database` regenera o painel terminando na data de hoje.

## O que os métodos acharam (cliques, banco versionado)

| Intervenção | Verdade | ITS, janela inteira | ITS até 16/10 | Controles | DiD |
|---|---|---|---|---|---|
| `titulos_blog` | +15,0% | +9,2% [3,5; 14,5] | +14,8% [12,5; 17,4] | +13,9% [11,9; 15,6] | +13,5% [11,7; 15,2] |
| `schema_categorias` | +20,0% | +12,7% [7,4; 18,1] | +20,0% [16,9; 23,1] | +19,1% [17,1; 21,1] | +18,6% [17,0; 20,2] |
| `descricao_produtos_ab` | +10,0% | +1,3% [−3,2; 5,4] | +10,4% [8,3; 12,5] | +11,8% [9,9; 13,7] | +9,8% [6,8; 12,9] |

- **Sem grupo de comparação, o update do algoritmo vira "efeito".** A série interrompida na
  janela inteira erra as três; no teste A/B conclui que não houve efeito (p = 0,52) quando houve +10%.
- **Cortar a janela antes do update conserta**, mas só porque sabemos a data dele. Na
  plataforma real nem todo update é anunciado.
- **DiD e A/B absorvem o choque comum** sem precisar saber quando ele ocorreu. No teste A/B
  o p-valor por permutação é 0,0005.
- Em 20 simulações com sementes diferentes, a média do DiD bateu o efeito verdadeiro nas três
  intervenções e o intervalo de 95% o cobriu em 59 de 60 casos.

## Limites

- O painel é **sintético**: prova que os estimadores funcionam, não diz nada sobre SEO real.
- Tendências paralelas valem por construção no simulador. Em dado real, é o pressuposto a testar.
- Erros agrupados por página; intervalo da série interrompida por reamostragem em blocos de 7 dias.
- O que o gerador ainda não cobre está em [SIMULADOR_PENDENCIAS.md](SIMULADOR_PENDENCIAS.md).
