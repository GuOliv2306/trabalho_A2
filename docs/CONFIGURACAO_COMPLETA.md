# 📊 Configuração Completa - Coleta de Dados GA4

## ✅ Status Atual

### Configurado e Funcionando:
- ✅ **Property ID:** 509656370
- ✅ **Measurement ID:** G-MDVLRDYZFE
- ✅ **Service Account:** ga4-account-test@projeto-analiseseo.iam.gserviceaccount.com
- ✅ **Credenciais:** config/credentials.json
- ✅ **Ambiente Virtual:** .venv configurado
- ✅ **Dependências:** Instaladas
- ✅ **APIs Ativadas:**
  - Google Analytics Data API ✅
  - Google Analytics Admin API ✅
- ✅ **Conexão:** Testada e funcionando
- ✅ **Estrutura:** Completa (coleta, limpeza, armazenamento)

---

## 📁 Arquivos Principais

### Scripts Prontos:
- `scripts/exemplo_coleta_ga4.py` - Coleta completa de dados
- `scripts/test_sua_propriedade.py` - Teste rápido de conexão
- `scripts/gerar_dados_teste.py` - Gera dados simulados
- `scripts/get_property_id.py` - Descobre Property ID

### Estrutura de Código:
- `src/ga/ga_client.py` - Cliente base GA4
- `src/ga/collectors.py` - Coletores especializados
- `src/collectors/ga_orchestrator.py` - Orquestrador de coleta
- `src/collectors/db_storage.py` - Armazenamento em DuckDB
- `src/cleaning/` - Limpeza de dados

---

## 🚀 Comandos Principais

### Ativar ambiente virtual:
```bash
source .venv/Scripts/activate
```

### Testar conexão:
```bash
python scripts/test_sua_propriedade.py
```

### Coletar dados:
```bash
python scripts/exemplo_coleta_ga4.py
```

### Gerar dados de teste (após configurar API_SECRET):
```bash
python scripts/gerar_dados_teste.py
```

---

## 📋 Próximos Passos

### 1️⃣ Popular com Dados (Escolha uma opção):

**Opção A: Dados Simulados (Rápido - 5 min)**
1. Criar API Secret no GA4
2. Configurar em `gerar_dados_teste.py`
3. Executar script
4. Ver: `docs/GERAR_DADOS_TESTE.md`

**Opção B: Site Real**
1. Adicionar código gtag.js ao site
2. Aguardar visitas
3. Dados em 24-48h

### 2️⃣ Testar Coleta com Dados
```bash
python scripts/test_sua_propriedade.py
python scripts/exemplo_coleta_ga4.py
```

### 3️⃣ Explorar Dados Coletados
- JSONs em: `data/raw/`
- Banco: `data/processed/ga4_data.duckdb`

### 4️⃣ Implementar Limpeza
- Usar: `src/cleaning/data_cleaner.py`
- Ver: `scripts/exemplo_limpeza_dados.py`

---

## 🔐 Credenciais e Permissões

### Service Account Email:
```
ga4-account-test@projeto-analiseseo.iam.gserviceaccount.com
```

### Permissões Necessárias:
- ✅ Google Analytics Data API (leitura)
- ✅ Google Analytics Admin API (listagem)
- ✅ Property Access: Viewer (na propriedade 509656370)

### APIs Ativadas no Google Cloud:
- ✅ analyticsdata.googleapis.com
- ✅ analyticsadmin.googleapis.com

---

## 📊 Estrutura de Dados

### Reports Coletados:
1. **Traffic** (Tráfego)
   - Sessões, usuários, pageviews
   - Fontes, meios, campanhas
   
2. **Conversions** (Conversões)
   - Eventos-chave, transações
   - Receita, conversões
   
3. **Engagement** (Engajamento)
   - Duração, bounce rate
   - Páginas mais vistas

### Armazenamento:
- **Raw:** JSON em `data/raw/`
- **Processed:** DuckDB em `data/processed/`
- **Tabelas:** ga4_traffic, ga4_conversions, ga4_engagement

---

## 🛠️ Troubleshooting

### Erro 403 (Permission Denied):
- Verificar se Service Account foi adicionada no GA4
- Admin → Property Access Management
- Aguardar 2-3 minutos após adicionar

### Sem dados retornados:
- Normal se propriedade é nova
- Gerar dados de teste ou aguardar dados reais

### API não habilitada:
- Acessar link fornecido no erro
- Clicar em "Enable"
- Aguardar 1-2 minutos

---

## 📚 Documentação

- **GA4 Data API:** https://developers.google.com/analytics/devguides/reporting/data/v1
- **Measurement Protocol:** https://developers.google.com/analytics/devguides/collection/protocol/ga4
- **DuckDB:** https://duckdb.org/docs/

---

## ✨ Sucesso!

Você tem agora uma pipeline completa de coleta de dados do GA4:
1. ✅ Autenticação configurada
2. ✅ Coleta automatizada
3. ✅ Armazenamento em JSON + DB
4. ✅ Estrutura para limpeza e ML
5. ✅ Scripts prontos para uso

**Próximo:** Popular com dados e testar coleta completa! 🚀
