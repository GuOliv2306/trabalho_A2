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

O contrafactual por controles segue a lógica do CausalImpact, mas com regressão simples
(controle + tendência) e reamostragem em blocos no lugar do modelo bayesiano de séries estruturais. Não é o pacote do Google.

## Rotas (`/api/v1/quasi-experiments`)

Todas as de estimativa recebem `intervention_id`, `metric` (`clicks` ou `impressions`) e
`end_date` opcional (corta a janela). Devolvem:

- `relative_effect` (0.10 = +10%), `ci95`, `p_value`. O efeito é a razão média (geométrica) entre o real e o contrafactual;
- `true_effect`: o efeito que o simulador injetou nos cliques, para conferir o método (`null` para impressões);
- `avisos`: por exemplo, contagens pequenas demais;
- `pressupostos` do método e `leitura_do_meio`.

| Rota | Extras na resposta |
|---|---|
| `GET /interventions` | registro de mudanças e eventos externos, `n_treated`, `n_control`, `randomized` |
| `GET /its` | `level_change`, `slope_change_per_day`, `series` (real e contrafactual por dia) |
| `GET /control-counterfactual` | `pre_fit_r2`, `series` |
| `GET /did` | `naive_before_after`, `control_change`, `balance`, `placebo_pre`, `event_study` semanal, `units_dropped` |
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
| `titulos_blog` | +15,0% | +10,7% [4,1; 16,6] | +16,5% [14,1; 19,4] | +16,6% [13,0; 20,6] | +15,2% [13,0; 17,4] |
| `schema_categorias` | +20,0% | +11,3% [5,3; 17,8] | +18,8% [16,9; 20,6] | +20,2% [16,8; 23,2] | +20,7% [18,4; 23,0] |
| `descricao_produtos_ab` | +10,0% | +2,8% [−1,6; 6,8] | +10,7% [8,3; 12,9] | +9,6% [6,1; 13,3] | +8,5% [5,9; 11,1] |

- **Sem grupo de comparação, o update do algoritmo vira "efeito".** A série interrompida na
  janela inteira subestima as três; no teste A/B conclui que não houve efeito (p = 0,19) quando houve +10%.
- **Cortar a janela antes do update conserta**, mas só porque sabemos a data dele. Na
  plataforma real nem todo update é anunciado.
- **Controles, DiD e A/B absorvem o choque comum** sem precisar saber quando ele ocorreu. No
  teste A/B o p-valor por permutação é 0,0005.
- **O placebo também erra.** No teste A/B deste banco o placebo do período anterior acusa
  diferença (intervalo de −5,4% a −0,5%), embora o sorteio garanta que não há. É o falso alarme
  esperado: em 100 simulações o placebo acusou em 11 de 300 casos.

O exemplo com `end_date=2025-10-16` vale para o banco versionado. Depois de um
`populate-database` as datas acompanham o dia de hoje (o update fica 24 dias antes do fim).

## Quanto confiar nos intervalos

Medido por simulação, com efeito verdadeiro conhecido. O intervalo de 95% deveria cobrir o
valor verdadeiro em 95% das vezes.

| Método | Viés | Cobertura medida |
|---|---|---|
| DiD (100 painéis do simulador, 3 intervenções) | nenhum (média igual ao efeito verdadeiro) | 91% (274 de 300) |
| Série interrompida (200 séries) | nenhum | 90% com dias independentes; 82% com dias correlacionados |
| Contrafactual por controles (200 séries) | −0,3 ponto | 92% com dias independentes; 88% com dias correlacionados |
| Teste A/B, p-valor por permutação (auditoria independente, 300 painéis sem efeito) | — | 3% de falsos positivos (esperado: 5%) |

Os intervalos da série interrompida e do contrafactual são **otimistas**: leia-os como um
pouco mais largos do que aparecem.

## Limites

- O painel é **sintético**: prova que os estimadores funcionam, não diz nada sobre SEO real.
- `true_effect` vale para cliques. Para `metric=impressions` a rota devolve `null`: o simulador não injeta um efeito conhecido nas impressões.
- **Contagens pequenas.** Os métodos usam log(1 + y). Com páginas de 0 a 3 cliques por dia o efeito
  sai puxado para zero (um +50% verdadeiro aparece como cerca de +23%). A resposta traz `avisos` quando isso ocorre.
- Tendências paralelas valem por construção no simulador. Em dado real, é o pressuposto a testar.
- Se as páginas de controle forem ruidosas, o contrafactual absorve só parte de um choque comum.
- Unidades sem dados antes ou depois da data saem da conta (`units_dropped`).
- O que o gerador ainda não cobre está em [SIMULADOR_PENDENCIAS.md](SIMULADOR_PENDENCIAS.md).
