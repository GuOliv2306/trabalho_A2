# 🚀 Como Popular Dados em Produção (Render)

Este guia explica **3 formas** de popular dados no ambiente de produção (Render) para alimentar a API de analytics.

---

## 📊 Contexto

**Localmente:**
- Simulador gera dados fictícios
- DuckDB armazena em `data/processed/ga4_data.duckdb`
- API lê do DuckDB

**No Render:**
- DuckDB é arquivo local (não persiste entre deploys)
- Precisa popular dados a cada deploy ou usar banco persistente

---

## 🎯 Opção 1: Endpoint Administrativo (RECOMENDADO para testes)

### Como Funciona
API possui endpoint `/api/v1/admin/populate-database` que gera dados sob demanda.

### Configuração no Render

1. **Adicione variável de ambiente** no Render Dashboard:
   ```
   ADMIN_KEY=sua_chave_secreta_forte_123456
   ```

2. **Faça deploy** normalmente.

3. **Popular dados após deploy**:
   ```bash
   curl -X POST "https://seu-app.onrender.com/api/v1/admin/populate-database" \
     -H "Content-Type: application/json" \
     -d '{
       "days": 30,
       "overwrite": false,
       "admin_key": "sua_chave_secreta_forte_123456"
     }'
   ```

### Vantagens
✅ Simples de implementar  
✅ Não precisa acessar servidor  
✅ Pode ser chamado do frontend ou Postman  
✅ Protegido por ADMIN_KEY

### Desvantagens
❌ Dados são perdidos a cada redeploy  
❌ Precisa popular manualmente após cada deploy

### Uso no Frontend
```javascript
// Função para popular dados (página de admin)
async function populateDatabase() {
  const response = await fetch('https://seu-app.onrender.com/api/v1/admin/populate-database', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      days: 30,
      overwrite: false,
      admin_key: 'sua_chave_secreta'
    })
  });
  
  const data = await response.json();
  console.log('Dados populados:', data);
}
```

---

## 🗄️ Opção 2: PostgreSQL Persistente (RECOMENDADO para produção)

### Como Funciona
Substitui DuckDB por PostgreSQL (banco gerenciado pelo Render).

### Configuração

1. **Crie PostgreSQL no Render Dashboard**:
   - New → PostgreSQL
   - Nome: `analytics-db`
   - Copia URL de conexão

2. **Adicione variável de ambiente**:
   ```
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   ```

3. **Modifique `db_storage.py`**:
   ```python
   import os
   import duckdb
   import psycopg2  # pip install psycopg2-binary
   
   class GA4DatabaseStorage:
       def __init__(self):
           db_url = os.getenv("DATABASE_URL")
           
           if db_url and db_url.startswith("postgresql"):
               # Usar PostgreSQL
               self.conn = psycopg2.connect(db_url)
               self.db_type = "postgres"
           else:
               # Usar DuckDB (desenvolvimento)
               self.conn = duckdb.connect("data/processed/ga4_data.duckdb")
               self.db_type = "duckdb"
   ```

4. **Popular dados iniciais**:
   - Use Opção 1 (endpoint) OU
   - Execute script localmente conectado ao Postgres do Render

### Vantagens
✅ Dados persistem entre deploys  
✅ Backup automático (Render)  
✅ Escalável  
✅ Pronto para produção

### Desvantagens
❌ Requer migração de código  
❌ PostgreSQL pago após free tier  
❌ Mais complexo de configurar

---

## 🔄 Opção 3: Popular Durante Build (startup script)

### Como Funciona
Script executa automaticamente ao iniciar aplicação no Render.

### Configuração

1. **Crie `startup.sh`** na raiz do projeto:
   ```bash
   #!/bin/bash
   
   # Verifica se banco está vazio
   python -c "
   from src.collectors.db_storage import GA4DatabaseStorage
   db = GA4DatabaseStorage()
   count = db.conn.execute('SELECT COUNT(*) FROM ga4_traffic').fetchone()[0]
   print(f'Records: {count}')
   exit(0 if count > 0 else 1)
   " || {
     # Banco vazio, popular
     echo "Populando banco de dados..."
     python tests/simulador_dados.py --days 30
   }
   
   # Inicia API
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

2. **Configure Render** para usar script:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `bash startup.sh`

### Vantagens
✅ Automático após deploy  
✅ Não precisa chamar endpoint manualmente

### Desvantagens
❌ Aumenta tempo de startup  
❌ Dados perdidos a cada redeploy  
❌ Startup pode falhar se demorar >60s

---

## 🎯 Recomendação por Caso de Uso

### Para Testes e Desenvolvimento Frontend
**→ Use Opção 1 (Endpoint Administrativo)**
- Rápido de implementar
- Fácil de testar
- Integra bem com frontend

### Para MVP ou Demonstração
**→ Use Opção 1 + Opção 3 (Endpoint + Startup)**
- Popular automaticamente no primeiro deploy
- Permitir repopular via API quando necessário

### Para Produção Real com Clientes
**→ Use Opção 2 (PostgreSQL)**
- Dados persistentes
- Backup automático
- Escalável

---

## 📝 Checklist para Render

### Configuração Inicial

- [ ] Criar conta no Render
- [ ] Criar novo Web Service
- [ ] Conectar repositório GitHub
- [ ] Configurar variáveis de ambiente:
  - [ ] `OPENAI_API_KEY=sk-proj-...`
  - [ ] `ADMIN_KEY=sua_chave_secreta` (para Opção 1)
  - [ ] `DATABASE_URL=postgresql://...` (para Opção 2)

### Build Settings

- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: 
  - Opção 1/2: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Opção 3: `bash startup.sh`

### Após Deploy

- [ ] Testar health: `GET https://seu-app.onrender.com/api/v1/health`
- [ ] Popular dados: `POST /api/v1/admin/populate-database`
- [ ] Verificar estatísticas: `GET /api/v1/admin/database-stats`
- [ ] Testar relatório: `POST /api/v1/reports/generate`

---

## 🔐 Segurança

### Proteja o Endpoint Administrativo

**NÃO exponha publicamente sem proteção!**

```bash
# ✅ CORRETO - Com ADMIN_KEY
curl -X POST "https://seu-app.onrender.com/api/v1/admin/populate-database" \
  -H "Content-Type: application/json" \
  -d '{"days": 30, "admin_key": "chave_secreta"}'

# ❌ ERRADO - Sem proteção (só funciona se ADMIN_KEY não estiver configurada)
curl -X POST "https://seu-app.onrender.com/api/v1/admin/populate-database" \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'
```

### Gere ADMIN_KEY Forte

```bash
# Linux/Mac
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"

# Exemplo:
# ADMIN_KEY=8f7e6d5c4b3a2910abcdef1234567890fedcba0987654321
```

---

## 🧪 Testando Localmente

### 1. Popular dados
```bash
curl -X POST "http://localhost:8000/api/v1/admin/populate-database" \
  -H "Content-Type: application/json" \
  -d '{"days": 30, "overwrite": false}'
```

### 2. Ver estatísticas
```bash
curl http://localhost:8000/api/v1/admin/database-stats
```

### 3. Testar relatório
```bash
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{"period_days": 7, "detail_level": "executive"}'
```

---

## 🚀 Integração com Frontend

### Exemplo React

```jsx
import { useState } from 'react';

function AdminPanel() {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  const populateDatabase = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/admin/populate-database', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          days: 30,
          overwrite: false,
          admin_key: process.env.REACT_APP_ADMIN_KEY
        })
      });
      
      const data = await response.json();
      console.log('✅ Dados populados:', data);
      
      // Atualizar estatísticas
      await fetchStats();
    } catch (error) {
      console.error('❌ Erro:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    const response = await fetch('/api/v1/admin/database-stats');
    const data = await response.json();
    setStats(data);
  };

  return (
    <div>
      <h2>Painel Administrativo</h2>
      
      <button onClick={populateDatabase} disabled={loading}>
        {loading ? 'Populando...' : 'Popular Banco de Dados'}
      </button>
      
      {stats && (
        <div>
          <h3>Estatísticas</h3>
          <p>Total de registros: {stats.record_counts.total}</p>
          <p>Período: {stats.date_range.start} a {stats.date_range.end}</p>
        </div>
      )}
    </div>
  );
}
```

---

## ❓ FAQ

### Preciso popular dados toda vez que fizer deploy?
- **Com Opção 1 (DuckDB)**: Sim
- **Com Opção 2 (PostgreSQL)**: Não
- **Com Opção 3 (Startup)**: Sim, mas é automático

### Os dados simulados são realistas?
Sim! O simulador gera:
- Distribuições estatísticas realistas (Poisson, Normal)
- Correlações entre métricas (posição → CTR)
- Séries temporais com tendências
- Long-tail distribution para keywords
- Proporções realistas por fonte/dispositivo

### Posso misturar dados reais e simulados?
Não recomendado. Escolha uma fonte:
- **Desenvolvimento**: 100% simulador
- **Produção**: 100% dados reais (integrar GA4/GSC APIs reais)

### Como migrar de simulador para dados reais?
1. Implemente coletores reais (`src/collectors/ga_orchestrator.py`)
2. Configure credenciais GA4/GSC
3. Execute coleta periódica (cron job ou scheduler)
4. Remova/desabilite endpoint de população simulada

---

## 📚 Próximos Passos

1. **Testar localmente**: Popular dados e verificar endpoints
2. **Escolher opção**: Decidir entre Opção 1, 2 ou 3
3. **Configurar Render**: Deploy com variáveis de ambiente
4. **Popular dados**: Usar endpoint ou startup script
5. **Integrar frontend**: Consumir API do frontend React/Next

---

## 🆘 Suporte

**Problemas comuns:**

### "ModuleNotFoundError: No module named 'tests.simulador_dados'"
→ Certifique-se de que `tests/simulador_dados.py` está no repositório

### "ADMIN_KEY inválida"
→ Configure `ADMIN_KEY` no Render (variáveis de ambiente)

### "Timeout ao popular dados"
→ Reduza `days` (ex: 7 em vez de 30) ou use PostgreSQL

### "Dados perdidos após redeploy"
→ Use PostgreSQL (Opção 2) para persistência

---

**📌 Recomendação Final:**

Para seu caso (integrar com frontend), use **Opção 1** inicialmente:
1. Deploy no Render com `ADMIN_KEY`
2. Popular via endpoint após deploy
3. Frontend consome APIs normalmente
4. Migrar para PostgreSQL quando for produção real
