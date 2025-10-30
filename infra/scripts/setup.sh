#!/bin/bash
set -e

echo "🚀 Agentic Company Platform - Setup Script"
echo "==========================================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f docker/.env ]; then
    echo "📝 Creating .env file from template..."
    cp docker/.env.example docker/.env
    echo "⚠️  Please edit docker/.env and fill in your configuration values!"
    echo "   Required:"
    echo "   - TELEGRAM_BOT_TOKEN (get from @BotFather on Telegram)"
    echo "   - LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY (will be generated on first run)"
    echo ""
    read -p "Press enter when you've updated docker/.env, or Ctrl+C to exit..."
else
    echo "✅ .env file exists"
fi

# Create required directories
echo ""
echo "📁 Creating required directories..."
mkdir -p docker/documents
mkdir -p docker/agent-output
mkdir -p docker/open-webui-data
mkdir -p services/n8n
echo "✅ Directories created"

# Pull and start services
echo ""
echo "🐳 Starting Docker services..."
cd docker
docker-compose up -d postgres qdrant temporal

echo ""
echo "⏳ Waiting for databases to be ready (30 seconds)..."
sleep 30

# Pull Ollama models
echo ""
echo "🤖 Pulling Ollama models (this may take a while)..."
docker-compose up -d ollama

echo "⏳ Waiting for Ollama to start (10 seconds)..."
sleep 10

echo "📥 Pulling models..."
docker exec -it agentic-ollama ollama pull mistral:7b-instruct
docker exec -it agentic-ollama ollama pull qwen2.5-coder:7b
docker exec -it agentic-ollama ollama pull nomic-embed-text

echo "✅ Models downloaded"

# Start all services
echo ""
echo "🚀 Starting all services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for all services to be healthy (60 seconds)..."
sleep 60

# Check health
echo ""
echo "🔍 Checking service health..."

AGENTS_HEALTH=$(curl -s http://localhost:9000/health | grep -o '"status":"healthy"' || echo "unhealthy")
APPROVAL_UI_HEALTH=$(curl -s http://localhost:9001/health | grep -o '"status":"healthy"' || echo "unhealthy")
TEMPORAL_HEALTH=$(docker exec agentic-temporal tctl workflow list > /dev/null 2>&1 && echo "healthy" || echo "unhealthy")

echo ""
echo "Service Status:"
echo "  Agents:      $([[ "$AGENTS_HEALTH" == *"healthy"* ]] && echo "✅" || echo "⚠️ ")"
echo "  Approval UI: $([[ "$APPROVAL_UI_HEALTH" == *"healthy"* ]] && echo "✅" || echo "⚠️ ")"
echo "  Temporal:    $([[ "$TEMPORAL_HEALTH" == "healthy" ]] && echo "✅" || echo "⚠️ ")"
echo ""

# Get Langfuse keys
echo "🔑 Langfuse API Keys:"
echo "   Visit http://localhost:3000 to create your account and get API keys"
echo "   Then update docker/.env with:"
echo "   LANGFUSE_PUBLIC_KEY=pk-lf-..."
echo "   LANGFUSE_SECRET_KEY=sk-lf-..."
echo ""

# Setup complete
echo "✅ Setup complete!"
echo ""
echo "🌐 Access the services:"
echo "   Temporal UI:   http://localhost:8080"
echo "   Langfuse:      http://localhost:3000"
echo "   Approval UI:   http://localhost:9001"
echo "   n8n:           http://localhost:5678 (admin/admin)"
echo "   Open WebUI:    http://localhost:8081"
echo "   Agents API:    http://localhost:9000/health"
echo "   Qdrant:        http://localhost:6333/dashboard"
echo ""
echo "📚 Next steps:"
echo "   1. Configure Telegram bot (optional):"
echo "      - Get token from @BotFather"
echo "      - Add to docker/.env as TELEGRAM_BOT_TOKEN"
echo "      - Import n8n workflow from services/n8n/telegram-approval-workflow.json"
echo ""
echo "   2. Add documents to docker/documents/ for RAG ingestion"
echo ""
echo "   3. Run tests:"
echo "      pytest tests/ -v"
echo ""
echo "   4. Start your first workflow:"
echo "      See README.md for examples"
echo ""
