# 🎯 Guia Rápido: Popular Dados no Render

## Resumo Executivo

Você tem **3 opções** para popular dados no Render:

| Opção | Quando Usar | Prós | Contras |
|-------|-------------|------|---------|
| **1. Endpoint Admin** | Testes + Frontend | ✅ Simples<br>✅ Via API | ❌ Dados perdidos no redeploy |
| **2. PostgreSQL** | Produção Real | ✅ Persistente<br>✅ Backup | ❌ Mais complexo<br>❌ Pago |
| **3. Startup Script** | MVP rápido | ✅ Automático | ❌ Aumenta tempo de startup |

---

## 🚀 Opção Recomendada: Endpoint Admin

### Passo 1: Configure no Render

**Variáveis de Ambiente:**
```
OPENAI_API_KEY=sk-proj-Af-uoVa4yu8_8M9pTP5drE7DsTeq1z4UyH27_-0TCqo6LtPwvUYdALb4plpzJOk2fFJ-5JoeItT3BlbkFJ2wmz4TKKgfu6pDbn9dSBGTXWPXXGIk7vbso
ADMIN_KEY=gere_uma_chave_secreta_forte_aqui_123456
```

### Passo 2: Deploy no Render

```bash
# Build Command
pip install -r requirements.txt

# Start Command
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Passo 3: Popular Dados (Após Deploy)

```bash
# Substitua pela URL do seu app no Render
curl -X POST "https://seu-app.onrender.com/api/v1/admin/populate-database" \
  -H "Content-Type: application/json" \
  -d '{
    "days": 30,
    "overwrite": false,
    "admin_key": "sua_chave_do_passo_1"
  }'
```

**Resposta esperada:**
```json
{
  "status": "success",
  "message": "Banco de dados populado com 30 dias de dados",
  "statistics": {
    "traffic_records": 1864,
    "engagement_records": 1864,
    "conversion_records": 1864,
    "gsc_records": 1864
  }
}
```

### Passo 4: Verificar Dados

```bash
curl https://seu-app.onrender.com/api/v1/admin/database-stats
```

### Passo 5: Testar Relatório

```bash
curl -X POST "https://seu-app.onrender.com/api/v1/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{"period_days": 7, "detail_level": "executive"}'
```

---

## 🎨 Integração com Frontend

### Criar Página de Admin (React/Next.js)

```jsx
// pages/admin.jsx
import { useState } from 'react';

export default function AdminPage() {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [message, setMessage] = useState('');

  const populateDB = async () => {
    setLoading(true);
    setMessage('');
    
    try {
      const response = await fetch('/api/v1/admin/populate-database', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          days: 30,
          overwrite: false,
          admin_key: process.env.NEXT_PUBLIC_ADMIN_KEY // .env.local
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setMessage('✅ Dados populados com sucesso!');
        fetchStats(); // Atualizar estatísticas
      } else {
        setMessage('❌ Erro: ' + data.detail);
      }
    } catch (error) {
      setMessage('❌ Erro: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/admin/database-stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Erro ao buscar stats:', error);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>🔧 Painel Administrativo</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={populateDB} 
          disabled={loading}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            backgroundColor: loading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? '⏳ Populando...' : '🚀 Popular Banco de Dados (30 dias)'}
        </button>
      </div>

      {message && (
        <div style={{
          padding: '10px',
          marginBottom: '20px',
          backgroundColor: message.includes('✅') ? '#d4edda' : '#f8d7da',
          border: `1px solid ${message.includes('✅') ? '#c3e6cb' : '#f5c6cb'}`,
          borderRadius: '5px'
        }}>
          {message}
        </div>
      )}

      <button 
        onClick={fetchStats}
        style={{
          padding: '8px 16px',
          marginBottom: '20px',
          backgroundColor: '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer'
        }}
      >
        📊 Atualizar Estatísticas
      </button>

      {stats && (
        <div style={{
          backgroundColor: '#f8f9fa',
          padding: '20px',
          borderRadius: '5px',
          border: '1px solid #dee2e6'
        }}>
          <h2>📊 Estatísticas do Banco</h2>
          <p><strong>Total de registros:</strong> {stats.record_counts.total.toLocaleString()}</p>
          <p><strong>Tráfego:</strong> {stats.record_counts.ga4_traffic.toLocaleString()}</p>
          <p><strong>Engagement:</strong> {stats.record_counts.ga4_engagement.toLocaleString()}</p>
          <p><strong>Conversões:</strong> {stats.record_counts.ga4_conversions.toLocaleString()}</p>
          <p><strong>GSC:</strong> {stats.record_counts.gsc_performance.toLocaleString()}</p>
          <p><strong>Período:</strong> {stats.date_range.start} a {stats.date_range.end}</p>
        </div>
      )}
    </div>
  );
}
```

**Configure `.env.local` no frontend:**
```bash
# Frontend .env.local
NEXT_PUBLIC_ADMIN_KEY=sua_chave_secreta
NEXT_PUBLIC_API_URL=https://seu-app.onrender.com
```

---

## 📋 Checklist de Deploy

### Antes do Deploy

- [ ] Commit dos novos endpoints (`/api/v1/admin/populate-database` e `/database-stats`)
- [ ] `.env.example` atualizado
- [ ] Documentação criada (`POPULAR_DADOS_PRODUCAO.md`)

### No Render Dashboard

- [ ] Criar novo Web Service
- [ ] Conectar repositório GitHub
- [ ] Adicionar variáveis:
  - [ ] `OPENAI_API_KEY`
  - [ ] `ADMIN_KEY`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Após Deploy

- [ ] Aguardar deploy finalizar (~5-10 min)
- [ ] Testar health: `GET /api/v1/health`
- [ ] Popular dados: `POST /api/v1/admin/populate-database`
- [ ] Verificar stats: `GET /api/v1/admin/database-stats`
- [ ] Testar KPIs: `GET /api/v1/kpis`
- [ ] Gerar relatório: `POST /api/v1/reports/generate`

---

## 🔐 Segurança

### Gerar ADMIN_KEY Forte

```bash
# Opção 1: OpenSSL
openssl rand -hex 32

# Opção 2: Python
python -c "import secrets; print(secrets.token_hex(32))"

# Exemplo de output:
# a7f3e9d2c8b1a4f0e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5
```

### Proteger Frontend

```jsx
// Adicionar autenticação simples
const ADMIN_PASSWORD = 'sua_senha_aqui';

const [authenticated, setAuthenticated] = useState(false);
const [password, setPassword] = useState('');

const handleLogin = () => {
  if (password === ADMIN_PASSWORD) {
    setAuthenticated(true);
    localStorage.setItem('admin_auth', 'true');
  } else {
    alert('Senha incorreta!');
  }
};

if (!authenticated) {
  return (
    <div>
      <input 
        type="password" 
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Senha de administrador"
      />
      <button onClick={handleLogin}>Entrar</button>
    </div>
  );
}
```

---

## ❓ FAQ Rápido

**P: Preciso popular toda vez que fizer deploy?**  
R: Sim (com DuckDB). Use PostgreSQL para persistência.

**P: Quantos dias de dados gerar?**  
R: 30 dias é ideal. Mais que 90 pode deixar lento.

**P: Os dados parecem reais?**  
R: Sim! Distribuições estatísticas e correlações realistas.

**P: Como migrar para dados reais depois?**  
R: Implementar coleta GA4/GSC real e desabilitar simulador.

**P: Posso popular do frontend?**  
R: Sim! Use `fetch()` como no exemplo React acima.

---

## 🎯 TL;DR

1. **Configure Render**: `OPENAI_API_KEY` + `ADMIN_KEY`
2. **Deploy**: Push para GitHub → Render faz deploy
3. **Popular**: `curl POST /api/v1/admin/populate-database`
4. **Verificar**: `curl GET /api/v1/admin/database-stats`
5. **Integrar**: Frontend chama APIs normalmente
6. **Repetir**: Popular após cada redeploy (ou migrar para PostgreSQL)

**Pronto! 🚀**
