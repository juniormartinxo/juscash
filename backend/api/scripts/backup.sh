#!/bin/bash

# Database backup script
set - e

BACKUP_DIR = "/backups"
DATE = $(date +% Y % m % d_ % H % M % S)
DB_NAME = "${DB_NAME:-dje_db}"
DB_USER = "${DB_USER:-dje_user}"
DB_HOST = "${DB_HOST:-localhost}"
DB_PORT = "${DB_PORT:-5432}"
RETENTION_DAYS = "${RETENTION_DAYS:-7}"

mkdir - p "$BACKUP_DIR"

echo "🗄️  Starting database backup..."

# Create backup
BACKUP_FILE = "$BACKUP_DIR/dje_backup_$DATE.sql"
PGPASSWORD = "$POSTGRES_PASSWORD" pg_dump \
-h "$DB_HOST" \
-p "$DB_PORT" \
-U "$DB_USER" \
-d "$DB_NAME" \
--no - owner \
--no - privileges \
    > "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"
echo "✅ Backup created: ${BACKUP_FILE}.gz"

# Clean old backups
find "$BACKUP_DIR" - name "dje_backup_*.sql.gz" - mtime + $RETENTION_DAYS - delete
  echo "🧹 Cleaned backups older than $RETENTION_DAYS days"

# Optional: Upload to cloud storage
if [-n "$AWS_S3_BUCKET"]; then
    aws s3 cp "${BACKUP_FILE}.gz" "s3://$AWS_S3_BUCKET/backups/"
    echo "☁️  Backup uploaded to S3"
fi

echo "✅ Backup process completed"

---

# Makefile
  .PHONY: help install dev build start test lint clean docker - build docker - run docker - down setup

# Default target
help: ## Show this help message
@echo "Available commands:"
@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pnpm install

dev: ## Start development server
	pnpm dev

build: ## Build the application
	pnpm build

start: ## Start production server
	pnpm start

test: ## Run tests
	pnpm test

test - watch: ## Run tests in watch mode
	pnpm test--watch

test - coverage: ## Run tests with coverage
	pnpm test--coverage

lint: ## Lint and format code
	pnpm lint

type - check: ## Check TypeScript types
	pnpm type - check

clean: ## Clean build artifacts
rm - rf dist /
  rm - rf coverage /
    rm - rf node_modules/.cache /

      setup: ## Setup development environment
        ./scripts/dev-setup.sh

docker - build: ## Build Docker image
	docker build - t dje - api.

  docker - run: ## Run Docker container
	docker run - p 3001: 3001 --env - file.env dje - api

docker - up: ## Start all services with Docker Compose
docker - compose up - d

docker - down: ## Stop all services
docker - compose down

docker - logs: ## View API logs
docker - compose logs - f api

prisma - generate: ## Generate Prisma client
	pnpm prisma: generate

prisma - migrate: ## Run database migrations
	pnpm prisma: migrate

prisma - studio: ## Open Prisma Studio
	pnpm prisma: studio

prisma - reset: ## Reset database
	pnpm prisma: reset

db - seed: ## Seed database with sample data
	pnpm db: seed

monitor: ## Run system monitoring
  ./scripts/monitor.sh

backup: ## Create database backup
  ./scripts/backup.sh

load - test: ## Run load tests(requires k6)
	k6 run scripts/load-test.js

security - audit: ## Run security audit
	pnpm audit--audit - level moderate