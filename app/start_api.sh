#!/bin/bash

# Script para iniciar a API FastAPI
# Uso: ./app/start_api.sh

echo "=========================================="
echo "🚀 Iniciando API de Analytics Dashboard"
echo "=========================================="

# Verifica se está no diretório correto
if [ ! -f "app/main.py" ]; then
    echo "❌ Erro: Execute este script do diretório raiz do projeto"
    exit 1
fi

# Ativa ambiente virtual (se existir)
if [ -d ".venv" ]; then
    echo "✓ Ativando ambiente virtual..."
    source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null
else
    echo "⚠️  Aviso: Ambiente virtual não encontrado"
fi

# Verifica dependências
echo "✓ Verificando dependências..."
python -c "import fastapi, duckdb, pandas" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dependências faltando. Instalando..."
    pip install -q fastapi uvicorn duckdb pandas
fi

# Verifica se banco existe
if [ -f "data/processed/ga4_data.duckdb" ]; then
    echo "✓ Banco de dados encontrado"
else
    echo "⚠️  Aviso: Banco de dados não encontrado em data/processed/ga4_data.duckdb"
    echo "   Execute 'python scripts/exemplo_coleta_ga4.py' para popular o banco"
fi

echo ""
echo "=========================================="
echo "✅ Servidor iniciando..."
echo "=========================================="
echo ""
echo "📖 Documentação interativa:"
echo "   - Swagger UI: http://127.0.0.1:8000/docs"
echo "   - ReDoc: http://127.0.0.1:8000/redoc"
echo ""
echo "🔗 Endpoints principais:"
echo "   - GET  /health"
echo "   - GET  /api/v1/overview/kpis"
echo "   - GET  /api/v1/analysis/correlation_matrix"
echo "   - GET  /api/v1/analysis/page_clusters"
echo "   - GET  /api/v1/page_analysis?path=/pagina/exemplo"
echo "   - POST /api/v1/predict/simulator"
echo ""
echo "Para parar o servidor: Ctrl+C"
echo "=========================================="
echo ""

# Inicia servidor com auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
