#!/bin/bash
# ============================================
# TempoNest Local Development Setup Script
# ============================================
#
# Value Proposition: One-Command Setup
# - Installs all dependencies
# - Sets up environment variables
# - Initializes database
# - Starts development environment
#
# Usage: ./scripts/setup.sh
# ============================================

set -e

echo "🚀 TempoNest Setup Script"
echo "========================="
echo ""

# Check if pnpm is installed
if ! command -v pnpm &> /dev/null; then
    echo "❌ pnpm is not installed. Please install pnpm first:"
    echo "   npm install -g pnpm"
    exit 1
fi

echo "✅ pnpm is installed"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pnpm install
echo "✅ Dependencies installed"
echo ""

# Copy environment variables
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please update .env with your actual values"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Start Docker services
echo "🐳 Starting Docker services..."
pnpm docker:dev:build
echo "✅ Docker services started"
echo ""

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Generate Prisma client
echo "🔨 Generating Prisma client..."
pnpm db:generate
echo "✅ Prisma client generated"
echo ""

# Push database schema
echo "📊 Pushing database schema..."
pnpm db:push
echo "✅ Database schema pushed"
echo ""

# Seed database
echo "🌱 Seeding database..."
pnpm db:seed
echo "✅ Database seeded"
echo ""

echo "✨ Setup complete!"
echo ""
echo "📋 Available services:"
echo "   - PostgreSQL:        localhost:5432"
echo "   - Redis:             localhost:6379"
echo "   - Plausible:         http://localhost:8000"
echo "   - MailHog:           http://localhost:8025"
echo "   - MinIO Console:     http://localhost:9001"
echo ""
echo "🎯 Next steps:"
echo "   1. Update .env with your actual values"
echo "   2. Run 'pnpm dev' to start development servers"
echo "   3. Open http://localhost:3000 in your browser"
echo ""
echo "📚 Useful commands:"
echo "   pnpm dev              - Start all apps"
echo "   pnpm dev:web          - Start web app only"
echo "   pnpm dev:admin        - Start admin app only"
echo "   pnpm db:studio        - Open Prisma Studio"
echo "   pnpm docker:dev:down  - Stop Docker services"
echo ""
