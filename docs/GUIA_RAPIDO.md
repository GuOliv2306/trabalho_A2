# 🚀 Guia Rápido - Coleta de Dados GA4

## ⚡ Comandos Essenciais

### Sempre começar ativando o ambiente:
```bash
cd "c:\Users\guguo\OneDrive\Área de Trabalho\trabalho_A2"
source .venv/Scripts/activate
```

---

## 📊 1. Gerar Dados Simulados

```bash
python scripts/gerar_dados_teste.py
```
- Simula 50 sessões de usuários
- Pode executar múltiplas vezes para mais dados
- Dados aparecem em ~24-48h (histórico) ou ~30min (realtime)

---

## 🧪 2. Testar Conexão

```bash
python scripts/test_sua_propriedade.py
```
- Verifica se tudo está funcionando
- Mostra quantos dados existem

---

## 📥 3. Coletar Dados do GA4

```bash
python scripts/exemplo_coleta_ga4.py
```
- Coleta traffic, conversions, engagement
- Salva em: `data/raw/` (JSON) e `data/processed/` (DuckDB)

---

## 🔄 4. Dados em Tempo Real

```bash
python scripts/test_realtime.py
```
- Vê usuários ativos agora
- Útil para verificar se dados simulados chegaram

---

## 📁 Onde ficam os dados?

- **JSONs:** `data/raw/ga4_*.json`
- **Banco:** `data/processed/ga4_data.duckdb`

---

## 📚 Documentação Completa

Para uma IA continuar me ajudando:
- **Ver:** `INSTRUCOES_PARA_PROXIMA_IA.md` (explicação completa)
- **Ver:** `docs/CONFIGURACAO_COMPLETA.md` (detalhes técnicos)

---

## ⚙️ Informações Importantes

- **Property ID:** 509656370
- **Measurement ID:** G-MDVLRDYZFE
- **Credenciais:** `config/credentials.json` (já configurado)

---

## ✅ Próximos Passos

1. **Agora:** Executar `gerar_dados_teste.py` quantas vezes quiser
2. **Amanhã (24-48h):** Executar `exemplo_coleta_ga4.py` para coletar dados reais
3. **Depois:** Implementar limpeza (`scripts/exemplo_limpeza_dados.py`)
4. **Futuro:** Machine Learning usando dados limpos

---

## 🆘 Problema?

**Erro ao executar scripts?**
→ Verifique se ativou o ambiente: `source .venv/Scripts/activate`

**Sem dados (0 rows)?**
→ Normal! Execute `gerar_dados_teste.py` e aguarde 24-48h

**Erro 403 Permission?**
→ Verifique se Service Account está no GA4: https://analytics.google.com/

---

## 🤖 Para Continuar com IA

Abra o arquivo `INSTRUCOES_PARA_PROXIMA_IA.md` e mostre para o modelo de IA.
Ele terá todas as informações para me ajudar a continuar!

---

**Status:** ✅ Tudo configurado e funcionando!
