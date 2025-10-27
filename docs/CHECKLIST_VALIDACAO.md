# ✅ CHECKLIST - Testar Sistema Após Remoção das APIs

**Execute estes comandos para validar que tudo está funcionando:**

---

## 1️⃣ Ativar Ambiente Virtual

```bash
cd "c:\Users\guguo\OneDrive\Área de Trabalho\trabalho_A2"
source .venv/Scripts/activate
```

**Resultado esperado:** Prompt com `(.venv)` no início

---

## 2️⃣ Popular Banco com Dados de Teste

```bash
python tests/create_test_data.py
```

**Resultado esperado:**
```
🔄 Gerando dados de teste...
  → Inserindo dados de tráfego...
  ✅ 63 registros de tráfego inseridos
  → Inserindo dados de engajamento...
  ✅ 210 registros de engajamento inseridos
  → Inserindo dados de conversões...
  ✅ 112 registros de conversões inseridos
  ...
```

---

## 3️⃣ Iniciar API

```bash
uvicorn app.main:app --reload
```

**Resultado esperado:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**⚠️ Deixe este terminal aberto!**

---

## 4️⃣ Testar Endpoints (Novo Terminal)

Abra um **novo terminal** e execute:

### Health Check
```bash
curl http://localhost:8000/health
```
**Esperado:** `{"status":"ok"}`

### KPIs
```bash
curl http://localhost:8000/api/v1/overview/kpis
```
**Esperado:** JSON com totalPaginas, sessoesTotais, etc.

### Documentação Interativa
Abra no navegador:
```
http://localhost:8000/docs
```
**Esperado:** Interface Swagger com todos os endpoints

---

## 5️⃣ Executar Testes Automatizados

No terminal (com API rodando):

```bash
pytest tests/test_api.py -v
```

**Resultado esperado:**
```
tests/test_api.py::test_health_check PASSED
tests/test_api.py::test_get_kpis PASSED
tests/test_api.py::test_get_correlation_matrix PASSED
...
====== 10 passed in X.XXs ======
```

---

## 6️⃣ Testar Simulador Preditivo

```bash
curl -X POST http://localhost:8000/api/v1/predict/simulator \
  -H "Content-Type: application/json" \
  -d '{"contagemDePalavras": 1200, "numeroDeImagens": 5, "precoDoProduto": 79.90}'
```

**Esperado:** JSON com predições de performance

---

## 7️⃣ Limpar Dados de Teste (Opcional)

```bash
python tests/cleanup_test_data.py
```

**Resultado esperado:**
```
🧹 Limpando dados de teste...
  ✅ Traffic limpo
  ✅ Engagement limpo
  ...
```

---

## ✅ VALIDAÇÃO COMPLETA

Se todos os testes acima passaram:

- ✅ Ambiente configurado corretamente
- ✅ Banco de dados funcionando
- ✅ API REST operacional
- ✅ Todos os endpoints respondendo
- ✅ Testes automatizados passando
- ✅ Sistema pronto para receber simulador

---

## ❌ Se Algo Falhou

### Erro de Import (ex: "No module named 'google'")
**Causa:** Script antigo tentando usar APIs removidas  
**Solução:** Não execute scripts em `scripts/`, use apenas os em `tests/`

### Banco vazio (0 registros)
**Causa:** Banco não foi populado  
**Solução:** Execute `python tests/create_test_data.py`

### API não inicia
**Causa:** Ambiente não ativado  
**Solução:** `source .venv/Scripts/activate`

### Porta 8000 em uso
**Causa:** API já rodando  
**Solução:** `uvicorn app.main:app --reload --port 8001`

---

## 📚 Próximo Passo

Depois de validar tudo, implemente o simulador:

```bash
# Criar arquivo
tests/simulador_dados.py

# Seguir template em:
GUIA_RAPIDO_SEM_APIS.md
```

---

**✨ Sistema Validado e Pronto! ✨**
