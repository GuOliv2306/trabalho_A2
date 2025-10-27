# Scripts do Projeto

## 📊 Measurement Protocol (Envio de Eventos)

### `validar_eventos.py`
Valida a estrutura dos eventos antes de enviar para produção.

```bash
python scripts/validar_eventos.py
```

**O que faz:**
- Testa se API Secret e Measurement ID estão corretos
- Valida a estrutura dos eventos
- Usa endpoint de validação com `validation_behavior=ENFORCE_RECOMMENDATIONS`

---

### `gerar_dados_teste.py`
Gera eventos simulados para popular o GA4 com dados de teste.

```bash
python scripts/gerar_dados_teste.py
```

**O que faz:**
- Envia 50 sessões de usuários simuladas
- Inclui page_views, navegação e conversões (10%)
- Eventos aparecem nos relatórios em **24-48 horas**

**Configuração:**
- Measurement ID: `G-MDVLRDYZFE`
- API Secret: `E_AABYDGRHSYMNNnWyz`

---

## 📥 Coleta de Dados (Data API)

### `exemplo_coleta_ga4.py`
Coleta dados do GA4 via Data API usando Service Account.

```bash
python scripts/exemplo_coleta_ga4.py
```

**O que faz:**
- Coleta tráfego, conversões e engagement dos últimos 7 dias
- Salva JSONs em `data/raw/`
- Armazena em DuckDB: `data/processed/ga4_data.duckdb`

**Requisitos:**
- Service Account configurado em `config/credentials.json`
- Permissão "Viewer" na propriedade GA4

---

## 🧪 Scripts de Teste

### `teste_data_api.py`
Testa acesso do Service Account à propriedade GA4.

### `test_realtime.py`
Testa coleta de dados em tempo real.

### `test_sua_propriedade.py`
Testa conexão com a propriedade configurada.

---

## ⚙️ Configuração

### Variáveis principais:
- **Property ID:** `509656370`
- **Measurement ID:** `G-MDVLRDYZFE`
- **API Secret:** `E_AABYDGRHSYMNNnWyz`
- **Service Account:** `ga4-account-test@projeto-analiseseo.iam.gserviceaccount.com`

### Arquivos necessários:
- `config/credentials.json` - Service Account JSON
- `.venv/` - Ambiente virtual Python

---

## 🔄 Fluxo de Trabalho

1. **Validar configuração:**
   ```bash
   python scripts/validar_eventos.py
   ```

2. **Gerar dados de teste:**
   ```bash
   python scripts/gerar_dados_teste.py
   ```

3. **Aguardar 24-48h** (processamento do GA4)

4. **Coletar dados:**
   ```bash
   python scripts/exemplo_coleta_ga4.py
   ```

---

## ⚠️ Importante

### Measurement Protocol:
- Dados levam **24-48h** para aparecer nos relatórios
- Status 204 = evento aceito
- Não requer Service Account (usa API Secret)

### Data API:
- Requer Service Account com permissão "Viewer"
- Coleta dados históricos
- Retorna dados já processados pelo GA4

### Certificados SSL (Windows):
Scripts incluem `verify=False` como workaround para problemas de certificado SSL no Windows.
