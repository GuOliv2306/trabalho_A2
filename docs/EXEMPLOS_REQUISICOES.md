# 📡 Exemplos de Requisições para a API

Este arquivo contém exemplos práticos de como testar cada endpoint da API usando `curl`, `httpie` ou diretamente no navegador.

## 🔧 Ferramentas

- **curl**: Pré-instalado no Linux/Mac/Windows 10+
- **httpie**: Mais legível (`pip install httpx`)
- **Navegador**: Para endpoints GET

---

## 🏥 Health Check

### cURL
```bash
curl http://localhost:8000/health
```

### httpie
```bash
http GET http://localhost:8000/health
```

### Navegador
```
http://localhost:8000/health
```

**Resposta esperada:**
```json
{"status": "ok"}
```

---

## 📊 Dashboard Overview - KPIs

### cURL
```bash
curl http://localhost:8000/api/v1/overview/kpis
```

### httpie
```bash
http GET http://localhost:8000/api/v1/overview/kpis
```

### Navegador
```
http://localhost:8000/api/v1/overview/kpis
```

### JavaScript (Fetch)
```javascript
fetch('http://localhost:8000/api/v1/overview/kpis')
  .then(res => res.json())
  .then(data => console.log(data));
```

**Resposta esperada:**
```json
{
  "totalPaginas": 150,
  "sessoesTotais": 45230,
  "conversoesTotais": 1205,
  "mediaBounceRate": 0.58,
  "mediaSessionDuration": 215.4
}
```

---

## 🔬 Análise - Matriz de Correlação

### cURL
```bash
curl http://localhost:8000/api/v1/analysis/correlation_matrix
```

### httpie
```bash
http GET http://localhost:8000/api/v1/analysis/correlation_matrix
```

### JavaScript (Axios)
```javascript
import axios from 'axios';

axios.get('http://localhost:8000/api/v1/analysis/correlation_matrix')
  .then(response => console.log(response.data));
```

**Resposta esperada:**
```json
{
  "conversions": {
    "sessions": 0.55,
    "pageViews": 0.42,
    "avgSessionDuration": 0.30
  },
  "engagementRate": {
    "sessions": 0.38,
    "pageViews": 0.45,
    "avgSessionDuration": 0.75
  }
}
```

---

## 🗂️ Análise - Clusters de Páginas

### cURL
```bash
curl http://localhost:8000/api/v1/analysis/page_clusters
```

### httpie
```bash
http GET http://localhost:8000/api/v1/analysis/page_clusters
```

### Python (requests)
```python
import requests

response = requests.get('http://localhost:8000/api/v1/analysis/page_clusters')
print(response.json())
```

**Resposta esperada:**
```json
{
  "clusters": [
    {
      "clusterId": 0,
      "clusterName": "Páginas de Alto Engajamento",
      "avgEngagementRate": 0.75,
      "avgSessionDuration": 420.5,
      "avgConversions": 210,
      "totalPaginas": 45
    }
  ]
}
```

---

## 🔍 Análise de Página Específica

### cURL
```bash
# Exemplo: análise da página /produtos/item-1
curl "http://localhost:8000/api/v1/page_analysis?path=/produtos/item-1"

# URL encoding para caminhos complexos
curl "http://localhost:8000/api/v1/page_analysis?path=%2Fprodutos%2Fitem-1"
```

### httpie
```bash
http GET "http://localhost:8000/api/v1/page_analysis?path=/produtos/item-1"
```

### JavaScript (Fetch)
```javascript
const pagePath = '/produtos/item-1';
const encodedPath = encodeURIComponent(pagePath);

fetch(`http://localhost:8000/api/v1/page_analysis?path=${encodedPath}`)
  .then(res => res.json())
  .then(data => console.log(data));
```

### Python
```python
import requests

params = {'path': '/produtos/item-1'}
response = requests.get('http://localhost:8000/api/v1/page_analysis', params=params)
print(response.json())
```

**Resposta esperada:**
```json
{
  "pagePath": "/produtos/item-1",
  "dadosReais": {
    "sessions": 885,
    "pageViews": 1024,
    "averageSessionDuration": 390.10,
    "engagementRate": 0.68,
    "conversions": 42
  },
  "analisePreditiva": {
    "clusterName": "Produto de Sucesso",
    "riscoDeRejeicao": "Baixo"
  }
}
```

---

## 🤖 Simulador Preditivo (POST)

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/predict/simulator \
  -H "Content-Type: application/json" \
  -d '{
    "contagemDePalavras": 1200,
    "numeroDeImagens": 5,
    "precoDoProduto": 79.90
  }'
```

### httpie
```bash
http POST http://localhost:8000/api/v1/predict/simulator \
  contagemDePalavras:=1200 \
  numeroDeImagens:=5 \
  precoDoProduto:=79.90
```

### JavaScript (Fetch)
```javascript
const payload = {
  contagemDePalavras: 1200,
  numeroDeImagens: 5,
  precoDoProduto: 79.90
};

fetch('http://localhost:8000/api/v1/predict/simulator', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
})
  .then(res => res.json())
  .then(data => console.log(data));
```

### Python (requests)
```python
import requests

payload = {
    "contagemDePalavras": 1200,
    "numeroDeImagens": 5,
    "precoDoProduto": 79.90
}

response = requests.post(
    'http://localhost:8000/api/v1/predict/simulator',
    json=payload
)
print(response.json())
```

**Resposta esperada:**
```json
{
  "inputFeatures": {
    "contagemDePalavras": 1200,
    "numeroDeImagens": 5,
    "precoDoProduto": 79.90
  },
  "predictedPerformance": {
    "estimativaEngagementRate": 0.72,
    "estimativaBounceRate": 0.28,
    "estimativaSessionDuration": 310.5,
    "estimativaConversoesPorMilSessoes": 45.2
  },
  "recommendations": [
    "✅ Excelente contagem de palavras para engajamento.",
    "✅ Número adequado de imagens.",
    "💰 Produto de valor médio. Destaque benefícios e diferenciais."
  ]
}
```

---

## 🧪 Casos de Teste do Simulador

### Caso 1: Artigo Longo (Blog Post)
```bash
curl -X POST http://localhost:8000/api/v1/predict/simulator \
  -H "Content-Type: application/json" \
  -d '{
    "contagemDePalavras": 2500,
    "numeroDeImagens": 8,
    "precoDoProduto": 0
  }'
```

### Caso 2: Produto Caro
```bash
curl -X POST http://localhost:8000/api/v1/predict/simulator \
  -H "Content-Type: application/json" \
  -d '{
    "contagemDePalavras": 800,
    "numeroDeImagens": 12,
    "precoDoProduto": 2499.00
  }'
```

### Caso 3: Página Minimalista
```bash
curl -X POST http://localhost:8000/api/v1/predict/simulator \
  -H "Content-Type: application/json" \
  -d '{
    "contagemDePalavras": 150,
    "numeroDeImagens": 1,
    "precoDoProduto": 0
  }'
```

### Caso 4: Landing Page de Conversão
```bash
curl -X POST http://localhost:8000/api/v1/predict/simulator \
  -H "Content-Type: application/json" \
  -d '{
    "contagemDePalavras": 650,
    "numeroDeImagens": 4,
    "precoDoProduto": 49.90
  }'
```

---

## 🔄 Testando Múltiplos Cenários (Bash Script)

Crie um arquivo `test_scenarios.sh`:

```bash
#!/bin/bash

echo "Testando múltiplos cenários..."

scenarios=(
  '{"contagemDePalavras": 500, "numeroDeImagens": 2, "precoDoProduto": 0}'
  '{"contagemDePalavras": 1500, "numeroDeImagens": 6, "precoDoProduto": 99.90}'
  '{"contagemDePalavras": 3000, "numeroDeImagens": 10, "precoDoProduto": 0}'
  '{"contagemDePalavras": 200, "numeroDeImagens": 1, "precoDoProduto": 1999.00}'
)

for i in "${!scenarios[@]}"; do
  echo ""
  echo "Cenário $((i+1)):"
  curl -s -X POST http://localhost:8000/api/v1/predict/simulator \
    -H "Content-Type: application/json" \
    -d "${scenarios[$i]}" | jq
done
```

Execute:
```bash
chmod +x test_scenarios.sh
./test_scenarios.sh
```

---

## 📊 Testando Performance (Batch)

### Python Script para 100 simulações
```python
import requests
import time

def test_performance():
    url = 'http://localhost:8000/api/v1/predict/simulator'
    
    start = time.time()
    
    for i in range(100):
        payload = {
            "contagemDePalavras": 1000 + (i * 10),
            "numeroDeImagens": (i % 10) + 1,
            "precoDoProduto": (i % 5) * 100
        }
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            print(f"Erro na requisição {i+1}: {response.status_code}")
    
    elapsed = time.time() - start
    print(f"\n✓ 100 requisições completadas em {elapsed:.2f}s")
    print(f"  Média: {(elapsed/100)*1000:.1f}ms por request")

if __name__ == '__main__':
    test_performance()
```

---

## 🌐 Testando CORS

### JavaScript (Console do Navegador)
```javascript
// Teste de CORS - Execute no console de https://example.com
fetch('http://localhost:8000/api/v1/overview/kpis')
  .then(res => res.json())
  .then(data => console.log('✓ CORS OK:', data))
  .catch(err => console.error('✗ CORS Error:', err));
```

---

## 📖 Documentação Interativa

### Swagger UI
```
http://localhost:8000/docs
```

### ReDoc
```
http://localhost:8000/redoc
```

### OpenAPI Schema (JSON)
```
http://localhost:8000/openapi.json
```

---

## 🐛 Troubleshooting

### Erro: Connection refused
**Causa:** API não está rodando.

**Solução:**
```bash
uvicorn app.main:app --reload
```

### Erro: 404 Not Found
**Causa:** Endpoint incorreto.

**Solução:** Verifique a URL no `/docs`.

### Erro: 422 Unprocessable Entity
**Causa:** Dados inválidos enviados ao POST.

**Solução:** Validar estrutura JSON:
```bash
# Válido
curl -X POST http://localhost:8000/api/v1/predict/simulator \
  -d '{"contagemDePalavras": 1000, "numeroDeImagens": 5, "precoDoProduto": 50}'

# Inválido (campo negativo)
curl -X POST http://localhost:8000/api/v1/predict/simulator \
  -d '{"contagemDePalavras": -100, "numeroDeImagens": 5, "precoDoProduto": 50}'
```

---

## 📚 Recursos Adicionais

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [cURL Docs](https://curl.se/docs/)
- [HTTPie Docs](https://httpie.io/docs)
- [Postman](https://www.postman.com/)
