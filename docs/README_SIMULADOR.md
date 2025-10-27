# 🔮 Simulador de Dados GA4 e Google Search Console

**Versão:** 1.0  
**Data:** 26 de outubro de 2025

## 📋 Visão Geral

Este simulador gera dados sintéticos **realistas** que emulam perfeitamente os retornos das APIs do Google Analytics 4 (GA4) e Google Search Console (GSC), permitindo desenvolvimento e testes sem depender de conexões com APIs reais.

## ✨ Características

### Realismo Estatístico
- **Distribuições apropriadas**: Poisson para contagens, Normal para durações, Beta para taxas
- **Correlações reais**: Posição → CTR, Sessões → Conversões, Engagement → Duration
- **Long-tail distribution**: Keywords seguem distribuição realista (poucas com muito volume, muitas com pouco)
- **Sazonalidade**: Fins de semana têm menos tráfego B2B
- **Tendências**: Crescimento orgânico ao longo do tempo

### Dados Gerados

#### Google Analytics 4 (GA4)
1. **Traffic** (Tráfego)
   - 8 fontes de tráfego realistas (organic, cpc, social, direct, etc.)
   - Métricas: sessions, active_users, new_users, page_views, avg_duration
   - Proporções realistas: 35% orgânico, 20% direto, 15% Google Ads, etc.

2. **Conversions** (Conversões)
   - 5 eventos de conversão (purchase, sign_up, add_to_cart, etc.)
   - Métricas: key_events, event_count, revenue, transactions
   - Taxas de conversão realistas por tipo de evento

3. **Engagement** (Engajamento)
   - 9 landing pages principais
   - 3 tipos de dispositivo (60% mobile, 35% desktop, 5% tablet)
   - Métricas: engagement_rate, engaged_sessions, duration, event_count

#### Google Search Console (GSC)
1. **Query Performance** (Palavras-chave)
   - 16 queries com distribuição long-tail
   - Métricas: clicks, impressions, CTR, position
   - CTR calculado realisticamente baseado na posição

2. **Page Performance** (URLs)
   - Performance por página do site
   - URLs correlacionadas com queries

3. **Country Performance** (Países)
   - 7 países (70% Brasil, 10% EUA, 5% Portugal, etc.)
   - Métricas por localização geográfica

4. **Device Performance** (Dispositivos)
   - Mobile, Desktop, Tablet
   - Proporções realistas mobile-first

5. **Date Performance** (Série Temporal)
   - Dados diários com sazonalidade semanal
   - Tendência de crescimento orgânico

## 🚀 Uso

### Uso Básico

```bash
# Gera 30 dias de dados (padrão)
python tests/simulador_dados.py

# Gera 90 dias de dados
python tests/simulador_dados.py --days 90

# Modo verboso (mais informações)
python tests/simulador_dados.py --verbose

# Limpa dados existentes antes
python tests/simulador_dados.py --clear
```

### Combinações Úteis

```bash
# Recomeçar do zero com 60 dias de dados
python tests/simulador_dados.py --days 60 --clear --verbose

# Adicionar mais 30 dias aos dados existentes
python tests/simulador_dados.py --days 30
```

## 📊 Exemplo de Saída

```
======================================================================
🔮 SIMULADOR DE DADOS - GA4 & GOOGLE SEARCH CONSOLE
======================================================================

✅ Conectado ao banco de dados DuckDB

📅 Período de simulação:
   De: 2025-09-27
   Até: 2025-10-26
   Total: 30 dias

📊 GOOGLE ANALYTICS 4
----------------------------------------------------------------------
🚦 Gerando dados de tráfego...
   ✅ 240 registros de tráfego inseridos
🎯 Gerando dados de conversões...
   ✅ 750 registros de conversões inseridos
💎 Gerando dados de engajamento...
   ✅ 810 registros de engajamento inseridos

🔍 GOOGLE SEARCH CONSOLE
----------------------------------------------------------------------
🔑 Gerando dados de queries (palavras-chave)...
   ✅ 16 registros de queries inseridos
📄 Gerando dados de páginas...
   ✅ 9 registros de páginas inseridos
🌍 Gerando dados por país...
   ✅ 7 registros por país inseridos
📱 Gerando dados por dispositivo...
   ✅ 3 registros por dispositivo inseridos
📈 Gerando série temporal diária...
   ✅ 30 registros de série temporal inseridos

======================================================================
✨ SIMULAÇÃO CONCLUÍDA COM SUCESSO!
======================================================================

📊 Resumo dos dados inseridos:
   GA4 Traffic:              240 registros
   GA4 Conversions:          750 registros
   GA4 Engagement:           810 registros
   GSC Query Performance:     16 registros
   GSC Page Performance:       9 registros
   GSC Country Performance:    7 registros
   GSC Device Performance:     3 registros
   GSC Date Performance:      30 registros
   ----------------------------------------
   TOTAL:                   1865 registros

🚀 Próximos passos:
   1. Inicie a API: uvicorn app.main:app --reload
   2. Acesse: http://localhost:8000/docs
   3. Teste os endpoints com os dados simulados!
```

## 🔬 Detalhes Técnicos

### Algoritmo de CTR Realista

O simulador usa um algoritmo baseado em estudos reais de CTR por posição no Google:

| Posição | CTR Médio |
|---------|-----------|
| 1       | 28%       |
| 2       | 15%       |
| 3       | 11%       |
| 4-5     | 8%        |
| 6-10    | 3-5%      |

Com variação natural de ±20% para cada resultado.

### Correlações Implementadas

1. **Posição ↔ CTR**: Quanto melhor a posição, maior o CTR (inverso)
2. **Sessões ↔ Conversões**: Mais tráfego = mais conversões (não linear)
3. **Engagement Rate ↔ Duration**: Maior engajamento = maior tempo no site
4. **Dispositivo ↔ Métricas**: Mobile tem menor duração e engajamento
5. **Fonte de Tráfego ↔ Qualidade**: Orgânico tem melhor engajamento que social

### Sazonalidade

- **Semanal**: Fins de semana têm 30% menos tráfego (B2B)
- **Crescimento**: 0.5-1% de crescimento diário ao longo do período

## 📐 Arquitetura

```
simulador_dados.py
├── DataSimulatorConfig
│   └── Configurações globais (fontes, páginas, eventos, etc.)
├── GA4Simulator
│   ├── generate_traffic_data()
│   ├── generate_conversions_data()
│   └── generate_engagement_data()
├── GSCSimulator
│   ├── generate_query_performance()
│   ├── generate_page_performance()
│   ├── generate_country_performance()
│   ├── generate_device_performance()
│   └── generate_date_performance()
└── main()
    └── Orquestra toda a simulação
```

## 🎛️ Customização

### Ajustar Proporções de Tráfego

Edite `DataSimulatorConfig.TRAFFIC_SOURCES`:

```python
TRAFFIC_SOURCES = [
    ("google", "organic", "(not set)", 0.35),  # 35% orgânico
    ("(direct)", "(none)", "(not set)", 0.20),  # 20% direto
    # ... adicione ou modifique conforme necessário
]
```

### Adicionar Novas Páginas

Edite `DataSimulatorConfig.LANDING_PAGES`:

```python
LANDING_PAGES = [
    ("/", "Home", 0.25),
    ("/sua-nova-pagina", "Nova Página", 0.10),
    # ...
]
```

### Modificar Keywords

Edite `DataSimulatorConfig.SEARCH_QUERIES`:

```python
SEARCH_QUERIES = [
    ("sua keyword", proporção, impressões_base, posição_média),
    # ...
]
```

## ✅ Validação

O simulador garante que:

1. **CTR é consistente**: `clicks = impressions * ctr`
2. **Proporções somam 1.0**: Todas as distribuições de proporção somam 100%
3. **Valores mínimos**: Nunca gera valores negativos ou zerados
4. **Ranges válidos**: CTR entre 0-1, posição entre 1-20, etc.
5. **Correlações mantidas**: Métricas relacionadas seguem padrões esperados

## 🧪 Testando o Simulador

### 1. Execute o Simulador
```bash
python tests/simulador_dados.py --days 30 --verbose
```

### 2. Inicie a API
```bash
uvicorn app.main:app --reload
```

### 3. Teste os Endpoints

```bash
# Health check
curl http://localhost:8000/health

# KPIs do dashboard
curl http://localhost:8000/api/v1/overview/kpis

# Matriz de correlação
curl http://localhost:8000/api/v1/analysis/correlation_matrix
```

### 4. Visualize no Navegador
Acesse: http://localhost:8000/docs

## 📊 Comparação: Simulador vs APIs Reais

| Aspecto | APIs Reais | Simulador |
|---------|-----------|-----------|
| Setup | Credenciais, OAuth | Nenhum |
| Latência | 1-5 segundos | Instantâneo |
| Limites | Quotas diárias | Ilimitado |
| Custo | Pode ter custo | Grátis |
| Controle | Dados reais | Total controle |
| Reprodutibilidade | Difícil | Fácil (seed) |
| Testes | Ambiente real | Cenários controlados |

## 🔄 Integração com Testes

### Pytest

```python
import pytest
from tests.simulador_dados import GA4Simulator, GSCSimulator

def test_traffic_generation():
    sim = GA4Simulator()
    data = sim.generate_traffic_data(datetime.now(), days=7)
    
    assert len(data) == 7 * 8  # 7 dias * 8 fontes
    assert all(d['sessions'] > 0 for d in data)
    assert all(0 <= d['average_session_duration'] <= 600 for d in data)
```

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'src'"

**Solução**: Execute a partir da raiz do projeto:
```bash
cd trabalho_A2
python tests/simulador_dados.py
```

### Erro: "DuckDB não instalado"

**Solução**: Instale as dependências:
```bash
pip install -r requirements.txt
```

### Banco vazio após execução

**Solução**: Verifique se não há erros silenciosos:
```bash
python tests/simulador_dados.py --verbose
```

## 📚 Referências

- [GA4 Data API Documentation](https://developers.google.com/analytics/devguides/reporting/data/v1)
- [Search Console API Documentation](https://developers.google.com/webmaster-tools/v1/searchanalytics)
- [CTR by Position Study](https://www.advancedwebranking.com/ctrstudy/)
- [Mobile vs Desktop Traffic Trends](https://www.statista.com/topics/779/mobile-internet/)

## 🤝 Contribuindo

Para adicionar novas funcionalidades ao simulador:

1. Adicione configurações em `DataSimulatorConfig`
2. Implemente método gerador na classe apropriada
3. Adicione chamada em `main()`
4. Documente o uso neste README

## 📝 Changelog

### v1.0 (2025-10-26)
- ✨ Versão inicial
- ✅ Simulação completa GA4 (traffic, conversions, engagement)
- ✅ Simulação completa GSC (queries, pages, countries, devices, dates)
- ✅ Distribuições estatísticas realistas
- ✅ Correlações entre métricas
- ✅ CLI com argumentos
- ✅ Documentação completa

---

**Desenvolvido por:** Assistente IA Especializado  
**Para:** Projeto de Analytics Dashboard  
**Licença:** MIT
