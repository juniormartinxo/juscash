#!/bin/bash
set -e

echo "🚀 Setting up production environment..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
  echo "❌ Don't run this script as root"
  exit 1
fi

# Check required environment variables
REQUIRED_VARS=("DATABASE_URL" "JWT_ACCESS_SECRET" "JWT_REFRESH_SECRET")
for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var}" ]; then
    echo "❌ Required environment variable $var is not set"
    exit 1
  fi
done

# Install dependencies
echo "📦 Installing production dependencies..."
pnpm install --prod --frozen-lockfile

# Generate Prisma client
echo "🔧 Generating Prisma client..."
pnpm prisma:generate

# Run database migrations
echo "🗄️ Running database migrations..."
pnpm prisma:migrate:deploy

# Build application
echo "🏗️ Building application..."
pnpm build

# Create necessary directories
mkdir -p logs
mkdir -p backups

# Set proper permissions
chmod +x scripts/*.sh
chmod 600 .env

# Verify production build
echo "✅ Verifying production build..."
if [ ! -f "dist/app.js" ]; then
  echo "❌ Production build failed - dist/app.js not found"
  exit 1
fi

# Test database connection
echo "🔍 Testing database connection..."
node -e "
  import { PrismaClient } from './dist/generated/prisma/index.js';
  const prisma = new PrismaClient();
  prisma.\$queryRaw\`SELECT 1\`.then(() => {
    console.log('✅ Database connection successful');
    process.exit(0);
  }).catch((error) => {
    console.error('❌ Database connection failed:', error.message);
    process.exit(1);
  });
"

echo "🎉 Production setup completed successfully!"
echo ""
echo "To start the application:"
echo "  pnpm start"
echo ""
echo "To run with PM2:"
echo "  pm2 start dist/app.js --name dje-api"
echo ""
echo "To check health:"
echo "  curl http://localhost:3001/health"