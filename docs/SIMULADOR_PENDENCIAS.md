# Simulador: o que gera e o que falta

Verificação feita em 16/11/2026 para sustentar os quase-experimentos e a análise de conteúdo.

## Antes

O simulador original (`GA4Simulator`, `GSCSimulator`) **não era suficiente**:

| Necessidade | O que havia |
|---|---|
| Série por página e por dia | só o total diário do site, 30 dias |
| Páginas em grupos por template | 9 páginas |
| Registro de mudanças com data | nenhum |
| Efeito conhecido para conferir o método | nenhum |
| Texto, tamanho e autoria das páginas | só caminho e nome |
| Consultas variadas com intenção | 15 consultas fixas |
| Formato da página de resultados | nenhum |

## Agora

`ExperimentSimulator` (mesmo arquivo, `tests/simulador_dados.py`) acrescenta, de forma
determinística por `seed`:

- 99 páginas (40 produtos, 24 categorias, 30 posts, 5 institucionais) com título, contagem de palavras e assinatura;
- painel página×dia de 120 dias (cliques, impressões, posição), com sazonalidade semanal e tendência;
- 3 mudanças do site e 1 update do algoritmo, com data, grupos tratado/controle e efeito verdadeiro;
- 231 consultas com formato dominante da página de resultados;
- o código verdadeiro de cada variável do livro de códigos (`verdade_simulador`).

## O que ainda falta evoluir

**Para os quase-experimentos**

1. **Efeito gradual.** Hoje o efeito aparece inteiro no dia da mudança. O real cresce conforme o buscador rastreia e reindexa.
2. **Cadeia posição → CTR → clique.** O efeito entra direto nos cliques; a posição muda à parte. Falta o efeito passar pela posição.
3. **Contaminação entre grupos.** Tratadas e controles não disputam as mesmas consultas. Falta canibalização e transbordo por links internos.
4. **Tendências não paralelas.** Valem por construção. Falta um cenário em que as tratadas já vinham crescendo, para o placebo ter o que acusar.
5. **Efeitos heterogêneos.** O efeito é igual para todas as páginas tratadas; o update atinge todos os templates por igual.
6. **Painel consulta×página×dia.** As consultas só têm totais. Não dá para medir efeito por intenção de busca nem ligar consulta à página de destino.
7. **Defeitos do dado real.** Sem dias faltando, sem consultas omitidas por privacidade, sem falhas de coleta, sem valores extremos.
8. **Controle do tamanho do teste.** Número de páginas, duração e efeito são fixos. Falta parametrizar para estudar o menor efeito detectável.
9. **Mudança de formato da página de resultados no tempo.** O formato é fixo por consulta; não há o evento "o buscador passou a mostrar vitrine".

**Para a análise de conteúdo**

10. **Texto das páginas.** Há título, contagem de palavras e assinatura, mas não o corpo. Profundidade é só extensão; sinais de experiência no texto não existem.
11. **Linguagem variada.** Consultas e assinaturas saem de moldes. Faltam erros de digitação, paráfrases, intenções mistas e outros idiomas — por isso a concordância com `verdade_simulador` é otimista.
12. **Mais sinais de autoria.** Falta página de autor, data de atualização, fontes citadas, dados estruturados.
13. **Formato de resultado por consulta e por dia**, e não um formato fixo.

**Estrutura**

14. **Dois sites.** O simulador antigo usa 9 páginas e 15 consultas; o novo, 99 e 231. As tabelas não conversam (`engagement`/`gsc_query_performance` contra `seo_*`). Falta unificar.
15. **Linha de comando.** `python tests/simulador_dados.py` não gera o painel novo; só a rota `populate-database` gera.
