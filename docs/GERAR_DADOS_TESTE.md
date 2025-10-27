# 🎯 Guia: Popular sua Propriedade GA4 com Dados

## ✅ Opção 1: Gerar Dados Simulados (Recomendado para Testes)

### Passo 1: Criar API Secret no GA4

1. **Acesse:** https://analytics.google.com/
2. Clique em **Admin** (⚙️ canto inferior esquerdo)
3. Na coluna **Property**, clique em **Data Streams**
4. Clique no seu stream web (G-MDVLRDYZFE)
5. Role até encontrar **"Measurement Protocol API secrets"**
6. Clique em **"Create"**
7. Nome: `test-data-generator`
8. Clique em **"Create"**
9. **Copie o "Secret value"** (começa com algo como `abc123xyz...`)

### Passo 2: Configurar o Script

Abra o arquivo `scripts/gerar_dados_teste.py` e substitua:

```python
API_SECRET = "YOUR_API_SECRET"  # ← Cole o secret que você copiou
```

Por:

```python
API_SECRET = "abc123xyz..."  # ← O secret que você copiou
```

### Passo 3: Gerar Dados

```bash
source .venv/Scripts/activate
python scripts/gerar_dados_teste.py
```

Isso vai:
- ✅ Simular 50 sessões de usuários
- ✅ Gerar page views, navegação, conversões
- ✅ Diferentes cidades, fontes de tráfego, páginas
- ✅ Dados aparecem em tempo real em alguns minutos
- ✅ Dados históricos em 24-48 horas

---

## ✅ Opção 2: Ativar Dados Demo no GA4

O Google Analytics 4 não tem uma opção nativa de "dados demo" como havia no Universal Analytics.

**Alternativas:**

### A) Adicionar a conta demo do Google à sua conta

1. **Acesse:** https://analytics.google.com/analytics/web/demoAccount
2. Clique em **"Access Demo Account"**
3. A conta demo (54516992) aparecerá na sua lista
4. **Mas:** Você não pode adicionar Service Account nela

### B) Usar dados da conta demo via OAuth

Requer configuração OAuth 2.0 (mais complexo, não recomendado para automação)

---

## ✅ Opção 3: Adicionar Código ao Site Real

Se você tem um site/blog:

1. **Copie este código:**

```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-MDVLRDYZFE"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-MDVLRDYZFE');
</script>
```

2. **Cole no `<head>`** do seu HTML
3. Faça deploy
4. Visite o site algumas vezes
5. Aguarde 24-48h para dados aparecerem

---

## 📊 Verificar Dados em Tempo Real

Depois de gerar dados (qualquer opção):

1. **Acesse:** https://analytics.google.com/
2. Vá em **Reports** → **Realtime**
3. Você verá usuários ativos agora (se usou Measurement Protocol)

---

## 🔄 Testar Coleta Novamente

Depois de ter dados:

```bash
source .venv/Scripts/activate
python scripts/test_sua_propriedade.py
```

Ou coleta completa:

```bash
python scripts/exemplo_coleta_ga4.py
```

---

## 💡 Recomendação

Para **aprendizado e testes rápidos**:

1. ✅ **Use Opção 1** (Dados Simulados via Measurement Protocol)
2. ✅ Leva apenas 5 minutos para configurar
3. ✅ Dados aparecem em tempo real
4. ✅ Controle total sobre os dados gerados
5. ✅ Perfeito para testar toda a pipeline de coleta

---

## 📚 Documentação Útil

- **Measurement Protocol:** https://developers.google.com/analytics/devguides/collection/protocol/ga4
- **Data API:** https://developers.google.com/analytics/devguides/reporting/data/v1
- **Demo Account:** https://support.google.com/analytics/answer/6367342
