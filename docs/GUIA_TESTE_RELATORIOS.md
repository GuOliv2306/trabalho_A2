# 🚀 Guia Rápido: Testando o Endpoint de Relatórios

## ⚙️ Configuração Inicial

### 1. Instalar Dependências
```bash
pip install agno openai
# ou
pip install -r requirements.txt
```

### 2. Configurar API Key da OpenAI

**Opção A: Arquivo .env (recomendado para desenvolvimento)**
```bash
# Criar arquivo .env na raiz do projeto
echo "OPENAI_API_KEY=sk-proj-sua-chave-aqui" > .env
```

**Opção B: Variável de Ambiente (temporária)**
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sk-proj-sua-chave-aqui"

# Windows CMD
set OPENAI_API_KEY=sk-proj-sua-chave-aqui

# Linux/Mac
export OPENAI_API_KEY=sk-proj-sua-chave-aqui
```

**Opção C: Variáveis do Sistema (permanente)**
- Windows: Painel de Controle → Sistema → Variáveis de Ambiente
- Linux/Mac: Adicionar ao `~/.bashrc` ou `~/.zshrc`

### 3. Obter API Key da OpenAI
1. Acesse: https://platform.openai.com/api-keys
2. Faça login ou crie conta
3. Click "Create new secret key"
4. Copie a chave (começa com `sk-proj-...`)

**⚠️ IMPORTANTE:** Nunca commite a chave no Git! O arquivo `.env` já está no `.gitignore`.

---

## 🧪 Testando o Endpoint

### Iniciar a API
```bash
cd trabalho_A2
python -m app.main
# ou
uvicorn app.main:app --reload
```

A API estará disponível em: `http://localhost:8000`

### Requisição Básica (cURL)
```bash
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "period_days": 30,
    "detail_level": "executive",
    "language": "pt-br"
  }'
```

### Requisição com Python
```python
import requests
import json

url = "http://localhost:8000/api/v1/reports/generate"

payload = {
    "period_days": 30,
    "focus_areas": ["traffic", "conversions"],
    "detail_level": "executive",
    "language": "pt-br"
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    report = response.json()
    print("✅ Relatório gerado com sucesso!")
    print(f"Report ID: {report['report_id']}")
    print(f"Confidence Score: {report['metadata']['confidence_score']}")
    print(f"\n{report['executive_summary']}")
else:
    print(f"❌ Erro: {response.status_code}")
    print(response.text)
```

### Requisição via Swagger UI
1. Abra no navegador: `http://localhost:8000/docs`
2. Encontre `POST /api/v1/reports/generate`
3. Click "Try it out"
4. Preencha os parâmetros:
```json
{
  "period_days": 30,
  "focus_areas": ["traffic", "conversions"],
  "detail_level": "executive",
  "language": "pt-br"
}
```
5. Click "Execute"

---

## 📊 Parâmetros Disponíveis

### `period_days` (obrigatório)
- **Tipo**: integer (1-365)
- **Padrão**: 30
- **Descrição**: Período de análise em dias
- **Exemplos**: 7, 30, 90

### `focus_areas` (opcional)
- **Tipo**: array de strings
- **Padrão**: null (analisa tudo)
- **Opções**: "traffic", "conversions", "engagement", "keywords"
- **Exemplo**: `["traffic", "conversions"]`

### `detail_level` (opcional)
- **Tipo**: string
- **Padrão**: "executive"
- **Opções**:
  - `"executive"`: Resumido, foco em insights
  - `"detailed"`: Completo, análise profunda
  - `"technical"`: Técnico, com detalhes ML
- **Exemplo**: `"executive"`

### `language` (opcional)
- **Tipo**: string
- **Padrão**: "pt-br"
- **Opções**: "pt-br", "en", "es"
- **Exemplo**: `"pt-br"`

---

## 📋 Estrutura da Resposta

```json
{
  "report_id": "uuid-do-relatorio",
  "generated_at": "2025-11-11T15:30:00Z",
  "period": {
    "start_date": "2025-10-12",
    "end_date": "2025-11-11",
    "days": 30
  },
  "executive_summary": "Texto narrativo com resumo executivo...",
  "sections": [
    {
      "title": "🎯 Visão Geral de Performance",
      "content": "Narrativa sobre KPIs...",
      "key_insights": [
        "Insight 1",
        "Insight 2"
      ],
      "data_references": {
        "total_sessions": 1500,
        "conversion_rate": 2.5
      }
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "category": "traffic",
      "action": "Aumentar investimento em google/organic",
      "rationale": "Este canal apresentou 45% de conversões..."
    }
  ],
  "metadata": {
    "data_sources": ["kpis", "channel_clusters", "keyword_clusters", "page_clusters", "correlations"],
    "ml_models_used": ["channel_profiling", "keyword_clustering", "page_segmentation"],
    "agent_model": "gpt-4o-mini",
    "confidence_score": 0.87,
    "generation_timestamp": "2025-11-11T15:30:05Z"
  }
}
```

---

## ⏱️ Performance Esperada

- **Tempo de resposta**: 7-15 segundos
- **Custo por relatório**: ~$0.001 - $0.003 (menos de 1 centavo)
- **Tokens usados**: ~2000-4000 tokens

---

## 🔍 Verificando se Está Funcionando

### 1. Health Check
```bash
curl http://localhost:8000/health
# Deve retornar: {"status": "ok"}
```

### 2. Verificar Dados Simulados
```bash
curl http://localhost:8000/api/v1/data/all | jq '.traffic | length'
# Deve retornar número > 0
```

### 3. Testar Endpoint de Relatório
```bash
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{"period_days": 7, "detail_level": "executive"}' | jq '.report_id'
# Deve retornar um UUID
```

---

## ❌ Troubleshooting

### Erro: "OPENAI_API_KEY não encontrada"
**Solução:** Configure a variável de ambiente conforme seção "Configuração Inicial"

### Erro: "No module named 'agno'"
**Solução:** 
```bash
pip install agno openai
```

### Erro: "Insufficient quota" (OpenAI)
**Solução:** 
- Adicione créditos na conta OpenAI
- Ou use modelo mais barato (já está usando gpt-4o-mini)

### Erro: "Timeout" ou demora muito
**Causas possíveis:**
- Banco de dados vazio (rode o simulador primeiro)
- API OpenAI lenta
- Muitos dados para processar

**Solução:**
```bash
# Gerar dados simulados
cd tests
python simulador_dados.py

# Ou reduzir period_days
# {"period_days": 7} em vez de 30
```

### Relatório vazio ou com "fallback mode"
**Causa:** Agente Agno falhou, usou modo simplificado

**Solução:**
- Verificar logs no terminal
- Verificar se API key está válida
- Verificar se há dados nos endpoints base

---

## 📝 Logs e Debug

### Ver logs da API
```bash
# A API já mostra logs no terminal onde foi iniciada
# Procure por:
# INFO: Iniciando geração de relatório...
# INFO: Coletando dados dos endpoints...
# INFO: Relatório gerado com sucesso
```

### Ativar modo debug do Agno
Editar `app/report_agent.py`:
```python
agent = create_report_agent(debug_mode=True)  # Mude para True
```

---

## 🎯 Casos de Uso

### Relatório Executivo Rápido (7 dias)
```json
{
  "period_days": 7,
  "detail_level": "executive"
}
```

### Análise Mensal Completa
```json
{
  "period_days": 30,
  "detail_level": "detailed"
}
```

### Foco em Tráfego e Conversões
```json
{
  "period_days": 30,
  "focus_areas": ["traffic", "conversions"],
  "detail_level": "executive"
}
```

### Análise Técnica para Time de Marketing
```json
{
  "period_days": 90,
  "detail_level": "technical"
}
```

---

## 🚀 Deploy (Render)

### 1. Commit do código (SEM .env)
```bash
git add .
git commit -m "feat: adiciona endpoint de relatórios com Agno"
git push
```

### 2. Configurar no Render
- Dashboard → Seu Serviço → Environment
- Adicionar variável:
  ```
  Key: OPENAI_API_KEY
  Value: sk-proj-sua-chave-real
  ```

### 3. Testar no Render
```bash
curl -X POST "https://seu-app.onrender.com/api/v1/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{"period_days": 30}'
```

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique logs no terminal
2. Teste endpoints individuais primeiro (`/api/v1/overview/kpis`)
3. Confirme que dados simulados existem
4. Verifique API key da OpenAI

**Tempo esperado de setup:** 5-10 minutos
