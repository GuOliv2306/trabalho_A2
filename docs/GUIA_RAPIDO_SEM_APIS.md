# 🚀 GUIA RÁPIDO - Projeto Sem Conexões GA4/GSC

**Data:** 26 de outubro de 2025

---

## ✅ O QUE FUNCIONA AGORA

### 1. API FastAPI
```bash
uvicorn app.main:app --reload
# Acesse: http://localhost:8000/docs
```

### 2. Popular Banco com Dados de Teste
```bash
python tests/create_test_data.py
```

### 3. Testar API
```bash
pytest tests/test_api.py -v
```

### 4. Limpar Dados de Teste
```bash
python tests/cleanup_test_data.py
```

---

## ❌ O QUE NÃO FUNCIONA MAIS

- ❌ `scripts/exemplo_coleta_ga4.py` - Requer GA4 API
- ❌ `scripts/exemplo_coleta_gsc.py` - Requer GSC API
- ❌ `scripts/gerar_dados_teste.py` - Requer Measurement Protocol
- ❌ Qualquer script em `scripts/` que tente conectar com Google

**NÃO EXECUTE** esses scripts - eles darão erro!

---

## 🔮 PRÓXIMO PASSO: Criar Simulador

### Onde implementar:
Crie um novo arquivo: `tests/simulador_dados.py`

### O que ele deve fazer:
```python
from src.collectors.db_storage import GA4DatabaseStorage
import random
from datetime import datetime, timedelta

def gerar_dados_simulados():
    """Popula o banco com dados GA4/GSC simulados."""
    db = GA4DatabaseStorage()
    
    # 1. Gerar dados de TRÁFEGO
    traffic_data = []
    for i in range(100):
        traffic_data.append({
            "property_id": "simulado_123",
            "date": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
            "source": random.choice(["google", "direct", "facebook", "instagram"]),
            "medium": random.choice(["organic", "cpc", "referral", "none"]),
            "campaign": random.choice(["summer_sale", "black_friday", "(not set)"]),
            "sessions": random.randint(10, 1000),
            "active_users": random.randint(5, 800),
            "new_users": random.randint(2, 400),
            "page_views": random.randint(20, 2000),
            "average_session_duration": random.uniform(30, 600),
            "bounce_rate": random.uniform(0.2, 0.8),
        })
    
    db.insert_traffic_data(traffic_data)
    print(f"✅ {len(traffic_data)} registros de tráfego inseridos")
    
    # 2. Gerar dados de CONVERSÕES
    conversions_data = []
    # ... similar ao traffic
    
    # 3. Gerar dados de ENGAJAMENTO
    engagement_data = []
    # ... similar ao traffic
    
    # 4. Gerar dados GSC
    gsc_query_data = []
    # ... queries do Search Console

if __name__ == "__main__":
    gerar_dados_simulados()
```

### Depois de criar:
```bash
python tests/simulador_dados.py
uvicorn app.main:app --reload
# API funcionará com dados simulados!
```

---

## 📊 Estrutura das Tabelas

### GA4 Traffic (campos obrigatórios):
```python
{
    "property_id": str,
    "date": str,  # YYYY-MM-DD
    "source": str,
    "medium": str,
    "campaign": str,
    "sessions": int,
    "active_users": int,
    "new_users": int,
    "page_views": int,
    "average_session_duration": float,
    "bounce_rate": float,
}
```

### GA4 Conversions:
```python
{
    "property_id": str,
    "date": str,
    "event_name": str,
    "source": str,
    "medium": str,
    "key_events": int,
    "event_count": int,
    "total_revenue": float,
    "transactions": int,
    "purchase_revenue": float,
}
```

### GA4 Engagement:
```python
{
    "property_id": str,
    "date": str,
    "page_path": str,
    "screen_name": str,
    "device": str,
    "engagement_rate": float,
    "engaged_sessions": int,
    "average_session_duration": float,
    "event_count": int,
    "user_engagement_duration": float,
}
```

### GSC Query Performance:
```python
{
    "site_url": str,
    "query": str,  # palavra-chave
    "start_date": str,
    "end_date": str,
    "clicks": int,
    "impressions": int,
    "ctr": float,  # 0.0 a 1.0
    "position": float,  # posição média
}
```

---

## 🎯 Checklist de Validação

Depois de criar o simulador, teste:

- [ ] Popular banco: `python tests/simulador_dados.py`
- [ ] Iniciar API: `uvicorn app.main:app --reload`
- [ ] Testar health: `curl http://localhost:8000/health`
- [ ] Testar KPIs: `curl http://localhost:8000/api/v1/overview/kpis`
- [ ] Ver docs: http://localhost:8000/docs
- [ ] Executar testes: `pytest tests/test_api.py -v`

Se todos passarem: ✅ **Sistema funcionando com dados simulados!**

---

## 📚 Documentação Completa

Leia o arquivo completo: `ESTADO_ATUAL_PROJETO.md`

---

## 🆘 Problemas?

### Erro de import:
Se aparecer erro `ModuleNotFoundError: No module named 'google'`:
- ✅ **Isso é esperado!** Removemos as conexões do Google
- ❌ **NÃO** reinstale as bibliotecas
- ✅ Use o simulador de dados ao invés

### Banco vazio:
```bash
python tests/create_test_data.py
```

### API não inicia:
Verifique se o ambiente está ativo:
```bash
source .venv/Scripts/activate
```
