#!/bin/bash

# ============================================
# SaaS Automation - Coolify One-Click Deploy
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     SaaS Automation Platform - Coolify Deployment           ║${NC}"
echo -e "${BLUE}║     Create unlimited SaaS projects with one click!          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running on server with Coolify
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Check if Coolify is accessible
echo -e "${YELLOW}🔍 Checking Coolify installation...${NC}"
if curl -s http://localhost:8000/api/health &> /dev/null; then
    echo -e "${GREEN}✅ Coolify is running${NC}"
else
    echo -e "${YELLOW}⚠️  Coolify not detected on port 8000${NC}"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Gather configuration
echo ""
echo -e "${BLUE}📝 Configuration Setup${NC}"
echo -e "${YELLOW}Please provide the following information:${NC}"
echo ""

read -p "Your domain (e.g., saasplatform.com): " DOMAIN
read -p "GitHub organization name: " GITHUB_ORG
read -p "GitHub personal access token: " GITHUB_TOKEN
read -p "Coolify API token (from Coolify settings): " COOLIFY_TOKEN
read -p "Admin email: " ADMIN_EMAIL

# Generate passwords
echo -e "${YELLOW}🔐 Generating secure passwords...${NC}"
DB_ROOT_PASSWORD=$(openssl rand -base64 32)
DB_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
N8N_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 32)
MINIO_PASSWORD=$(openssl rand -base64 32)

# Create project directory
PROJECT_DIR="/opt/saas-automation"
echo -e "${YELLOW}📁 Creating project directory...${NC}"
sudo mkdir -p $PROJECT_DIR/{services,templates,scripts,workflows}
sudo chown -R $USER:$USER $PROJECT_DIR
cd $PROJECT_DIR

# Create environment file
echo -e "${YELLOW}📄 Creating environment configuration...${NC}"
cat > .env << EOF
# Domain Configuration
DOMAIN=$DOMAIN
N8N_HOST=n8n.$DOMAIN
API_HOST=api.$DOMAIN
DASHBOARD_HOST=dashboard.$DOMAIN
MINIO_HOST=storage.$DOMAIN

# Generated Passwords
DB_ROOT_PASSWORD=$DB_ROOT_PASSWORD
DB_PASSWORD=$DB_PASSWORD
DB_N8N_PASSWORD=$DB_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
N8N_USER=admin
N8N_PASSWORD=$N8N_PASSWORD
N8N_ENCRYPTION_KEY=$(openssl rand -hex 16)
JWT_SECRET=$JWT_SECRET
NEXTAUTH_SECRET=$JWT_SECRET
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=$MINIO_PASSWORD

# GitHub Configuration
GITHUB_TOKEN=$GITHUB_TOKEN
GITHUB_ORG=$GITHUB_ORG

# Coolify Integration
COOLIFY_API_TOKEN=$COOLIFY_TOKEN
COOLIFY_INSTANCE_URL=http://host.docker.internal:3000

# Admin
ADMIN_EMAIL=$ADMIN_EMAIL

# Environment
NODE_ENV=production
TZ=America/New_York
EOF

# Copy Docker Compose file
echo -e "${YELLOW}📄 Creating Docker Compose configuration...${NC}"
cp /home/claude/docker-compose.coolify.yml $PROJECT_DIR/docker-compose.yml

# Create database initialization script
echo -e "${YELLOW}🗄️ Creating database setup scripts...${NC}"
cat > scripts/create-databases.sh << 'EOF'
#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER saas WITH PASSWORD '$DB_PASSWORD';
    CREATE DATABASE saasdb OWNER saas;
    GRANT ALL PRIVILEGES ON DATABASE saasdb TO saas;
    
    CREATE USER n8n WITH PASSWORD '$DB_N8N_PASSWORD';
    CREATE DATABASE n8n OWNER n8n;
    GRANT ALL PRIVILEGES ON DATABASE n8n TO n8n;
EOSQL
EOF
chmod +x scripts/create-databases.sh

# Create API service files
echo -e "${YELLOW}🚀 Creating API Gateway service...${NC}"
mkdir -p services/api
cat > services/api/package.json << 'EOF'
{
  "name": "saas-api-gateway",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "helmet": "^7.1.0",
    "pg": "^8.11.3",
    "redis": "^4.6.10",
    "jsonwebtoken": "^9.0.2",
    "express-rate-limit": "^7.1.5"
  }
}
EOF

cat > services/api/index.js << 'EOF'
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');

const app = express();
app.use(helmet());
app.use(cors());
app.use(express.json());

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'api-gateway' });
});

app.post('/api/projects', async (req, res) => {
  const { projectName, description } = req.body;
  
  // TODO: Implement project creation logic
  res.json({
    success: true,
    message: 'Project creation initiated',
    project: { name: projectName, description }
  });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`API Gateway running on port ${PORT}`);
});
EOF

cat > services/api/Dockerfile << 'EOF'
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3001
CMD ["npm", "start"]
EOF

# Create Dashboard service files
echo -e "${YELLOW}📊 Creating Dashboard service...${NC}"
mkdir -p services/dashboard
cat > services/dashboard/package.json << 'EOF'
{
  "name": "saas-dashboard",
  "version": "1.0.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }
}
EOF

cat > services/dashboard/Dockerfile << 'EOF'
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package*.json ./
EXPOSE 3000
CMD ["npm", "start"]
EOF

# Create Builder service
echo -e "${YELLOW}🔨 Creating Builder service...${NC}"
mkdir -p services/builder
cat > services/builder/Dockerfile << 'EOF'
FROM node:20-alpine
WORKDIR /app
RUN apk add --no-cache git openssh
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3002
CMD ["npm", "start"]
EOF

# Create n8n workflows directory
echo -e "${YELLOW}📋 Creating n8n workflow templates...${NC}"
cat > workflows/create-saas-project.json << 'EOF'
{
  "name": "Create SaaS Project",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "create-project",
        "responseMode": "responseNode"
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "typeVersion": 1
    }
  ],
  "connections": {}
}
EOF

# Create deployment script
echo -e "${YELLOW}🚀 Creating deployment script...${NC}"
cat > deploy.sh << 'EOF'
#!/bin/bash

echo "🚀 Deploying SaaS Automation Platform to Coolify..."

# Check if docker compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Create network if it doesn't exist
docker network create saas-network 2>/dev/null || true

# Pull latest images
echo "📦 Pulling Docker images..."
docker compose pull

# Start services
echo "🚀 Starting services..."
docker compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
services=("n8n" "api" "postgres" "redis")
for service in "${services[@]}"; do
    if docker compose ps | grep $service | grep -q "healthy\|running"; then
        echo "✅ $service is running"
    else
        echo "❌ $service failed to start"
    fi
done

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Access your services:"
echo "   n8n Automation: https://n8n.$DOMAIN"
echo "   API Gateway: https://api.$DOMAIN"
echo "   Dashboard: https://dashboard.$DOMAIN"
echo "   Object Storage: https://storage.$DOMAIN"
echo ""
echo "📝 Credentials saved in .env file"
echo "   n8n Username: admin"
echo "   n8n Password: Check .env file"
echo ""
echo "📚 Next steps:"
echo "   1. Configure DNS records for your domain"
echo "   2. Set up SSL certificates in Coolify"
echo "   3. Configure Stripe and Resend API keys"
echo "   4. Import n8n workflows"
echo "   5. Test project creation"
EOF
chmod +x deploy.sh

# Create Coolify API integration script
echo -e "${YELLOW}🔗 Creating Coolify API integration...${NC}"
cat > scripts/coolify-integration.js << 'EOF'
const axios = require('axios');

class CoolifyIntegration {
  constructor(apiToken, instanceUrl) {
    this.apiToken = apiToken;
    this.instanceUrl = instanceUrl || 'http://localhost:3000';
  }

  async createApplication(projectData) {
    try {
      const response = await axios.post(
        `${this.instanceUrl}/api/v1/applications`,
        {
          name: projectData.name,
          gitRepository: projectData.gitUrl,
          gitBranch: 'main',
          buildPack: 'nixpacks',
          port: 3000
        },
        {
          headers: {
            'Authorization': `Bearer ${this.apiToken}`,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to create application:', error.message);
      throw error;
    }
  }

  async deployApplication(applicationId) {
    try {
      const response = await axios.post(
        `${this.instanceUrl}/api/v1/applications/${applicationId}/deploy`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${this.apiToken}`
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to deploy application:', error.message);
      throw error;
    }
  }
}

module.exports = CoolifyIntegration;
EOF

# Final message
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ SaaS Automation Platform prepared for Coolify deployment!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📁 Project location: $PROJECT_DIR${NC}"
echo ""
echo -e "${YELLOW}🚀 To deploy, run:${NC}"
echo "   cd $PROJECT_DIR"
echo "   ./deploy.sh"
echo ""
echo -e "${YELLOW}📝 Configuration saved in:${NC}"
echo "   $PROJECT_DIR/.env"
echo ""
echo -e "${YELLOW}🔐 Credentials:${NC}"
echo "   Admin Email: $ADMIN_EMAIL"
echo "   n8n User: admin"
echo "   n8n Password: (check .env file)"
echo ""
echo -e "${YELLOW}🌐 After deployment, access:${NC}"
echo "   n8n: https://n8n.$DOMAIN"
echo "   API: https://api.$DOMAIN"
echo "   Dashboard: https://dashboard.$DOMAIN"
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo "   1. Run ./deploy.sh to start all services"
echo "   2. Configure DNS A records for all subdomains"
echo "   3. Access Coolify and verify services"
echo "   4. Import n8n workflows"
echo "   5. Add Stripe and Resend API keys"
echo ""
echo -e "${GREEN}Ready to generate unlimited SaaS projects! 🚀${NC}"