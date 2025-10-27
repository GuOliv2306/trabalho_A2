# ⚠️ Scripts - ATENÇÃO

**Data da alteração:** 26 de outubro de 2025

---

## ❌ Scripts DESABILITADOS (NÃO USE!)

Os seguintes scripts foram desabilitados porque dependem de APIs do Google que foram removidas:

### Coleta de Dados:
- ❌ `exemplo_coleta_ga4.py` - Requer GA4 Data API
- ❌ `exemplo_coleta_gsc.py` - Requer GSC API
- ❌ `coleta_ga4_configuravel.py` - Requer GA4 Data API

### Measurement Protocol:
- ❌ `gerar_dados_teste.py` - Requer Measurement Protocol
- ❌ `validar_eventos.py` - Requer Measurement Protocol  

### Testes de Conexão:
- ❌ `test_demo_account.py` - Requer GA4 API
- ❌ `test_realtime.py` - Requer GA4 API
- ❌ `test_sua_propriedade.py` - Requer GA4 API
- ❌ `teste_data_api.py` - Requer GA4 API

### Utilitários Google:
- ❌ `get_property_id.py` - Requer GA4 Admin API
- ❌ `listar_data_streams.py` - Requer GA4 Admin API
- ❌ `verificar_service_account.py` - Requer GA4 Admin API

**⚠️ NÃO EXECUTE ESSES SCRIPTS!** Eles causarão erros de importação.

---

## ✅ Alternativa: Use o Simulador

Ao invés de coletar dados reais, use:

### Criar Simulador (você mesmo):
```bash
# Crie este arquivo:
tests/simulador_dados.py
```

### Popular Banco com Dados de Teste:
```bash
# Este script FUNCIONA (não usa APIs do Google):
python tests/create_test_data.py
```

---

## 📁 Estrutura Recomendada

```
scripts/
├── [DESABILITADOS] exemplo_coleta_*.py
├── [DESABILITADOS] gerar_dados_teste.py
├── [DESABILITADOS] test_*.py
└── README_SCRIPTS_DESABILITADOS.md  ← você está aqui

tests/
├── create_test_data.py  ✅ USE ESTE
├── cleanup_test_data.py  ✅ USE ESTE
├── test_api.py  ✅ USE ESTE
└── [CRIAR] simulador_dados.py  🔮 IMPLEMENTE ESTE
```

---

## 🔮 Próximo Passo

Implemente o simulador seguindo o guia em:
- `GUIA_RAPIDO_SEM_APIS.md`
- `ESTADO_ATUAL_PROJETO.md`

---

## 💡 Se Precisar Reativar

Para reativar as conexões com Google (NÃO recomendado agora):
1. Descomente imports nos arquivos em `src/ga/` e `src/gsc/`
2. Reinstale: `pip install google-analytics-data google-api-python-client`
3. Configure credenciais novamente

**Mas foque no simulador primeiro!** É mais produtivo.
