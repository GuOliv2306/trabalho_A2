# 🚀 GUIA RÁPIDO - Testar Endpoints ML

## ⚡ Quick Start (3 minutos)

### 1️⃣ **Iniciar a API**
```bash
cd "c:\Users\guguo\OneDrive\Área de Trabalho\trabalho_A2"
source .venv/Scripts/activate
uvicorn app.main:app --reload
```

### 2️⃣ **Testar no navegador**
Abra: **http://localhost:8000/docs**

Procure pela tag **"Machine Learning"** e teste:
- ✅ `/api/v1/ml/channel_clusters`
- ✅ `/api/v1/ml/keyword_clusters`
- ✅ `/api/v1/ml/page_clusters`

### 3️⃣ **Testar via terminal**
```bash
# Em outro terminal
cd "c:\Users\guguo\OneDrive\Área de Trabalho\trabalho_A2"
source .venv/Scripts/activate
python tests/test_ml_endpoints.py
```

---

## 📝 Testes Manuais (curl)

### **Channel Clusters (Canais)**
```bash
curl http://localhost:8000/api/v1/ml/channel_clusters
```

### **Keyword Clusters (Keywords)**
```bash
curl http://localhost:8000/api/v1/ml/keyword_clusters
```

### **Page Clusters (Páginas)**
```bash
curl http://localhost:8000/api/v1/ml/page_clusters
```

### **Personalizar número de clusters**
```bash
# 5 clusters ao invés de 3
curl "http://localhost:8000/api/v1/ml/channel_clusters?n_clusters=5"
```

---

## ✅ Resultado Esperado

Cada endpoint deve retornar:

```json
{
  "algoritmo": "K-Means Clustering",
  "n_clusters": 3,
  "total_canais": 8,
  "canais": [...],           // Dados com cluster_id
  "cluster_centers": [...],  // Centros dos clusters
  "segment_summary": [...]   // Estatísticas por cluster
}
```

---

## ⚠️ Se der erro "Dados insuficientes"

Execute o simulador:
```bash
python tests/simulador_dados.py --clear --days 30
```

Isso vai popular o banco com dados suficientes para clustering.

---

## 🎯 Verificar se funcionou

No Swagger UI (`/docs`):
1. Procure a tag **"Machine Learning"**
2. Deve ter **3 endpoints** verdes
3. Clique em "Try it out" e execute
4. Se retornar JSON com clusters → ✅ **FUNCIONOU!**

---

## 📊 Comparar com endpoint antigo

O endpoint antigo `/api/v1/analysis/page_clusters` foi **removido**.

Agora use: `/api/v1/ml/page_clusters` (com ML real!)

---

## 🎉 Pronto!

Se os 3 endpoints retornarem dados, **a integração ML está completa!** 🚀
