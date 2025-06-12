-- CreateEnum
CREATE TYPE "publication_log_action" AS ENUM ('CRIADA', 'ATUALIZADA', 'VISUALIZADA', 'STATUS_CHANGED', 'MOVED_TO_COLUMN', 'EXPORTED');

-- CreateEnum
CREATE TYPE "publication_status" AS ENUM ('NOVA', 'LIDA', 'ENVIADA_PARA_ADV', 'CONCLUIDA');

-- CreateEnum
CREATE TYPE "scraping_execution_type" AS ENUM ('SCHEDULED', 'MANUAL', 'TEST', 'RETRY');

-- CreateEnum
CREATE TYPE "scraping_execution_status" AS ENUM ('RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT');

-- CreateEnum
CREATE TYPE "scraping_log_level" AS ENUM ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL');

-- CreateEnum
CREATE TYPE "auth_log_action" AS ENUM ('LOGIN', 'LOGOUT', 'PASSWORD_RESET_REQUEST', 'PASSWORD_RESET_CONFIRM', 'PASSWORD_CHANGE', 'REFRESH_TOKEN', 'ACCOUNT_LOCK', 'FAILED_ATTEMPT');

-- CreateEnum
CREATE TYPE "auth_log_status" AS ENUM ('SUCCESS', 'FAILURE', 'SUSPICIOUS', 'BLOCKED');

-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "password_hash" TEXT NOT NULL,
    "last_password_change" TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,
    "is_password_temporary" BOOLEAN DEFAULT true,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "deactivated_at" TIMESTAMP(3),

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "user_refresh_tokens" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "token" TEXT NOT NULL,
    "expires_at" TIMESTAMP(3) NOT NULL,
    "device" TEXT,
    "ip" TEXT,
    "revoked" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "user_refresh_tokens_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "user_sessions" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "refresh_token" TEXT NOT NULL,
    "token_expires_at" TIMESTAMP(3) NOT NULL,
    "device_type" TEXT NOT NULL,
    "device_name" TEXT,
    "device_identifier" TEXT,
    "ip_address" TEXT,
    "user_agent" TEXT,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "last_activity" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "revoked_at" TIMESTAMP(3),
    "revoked_by_user" BOOLEAN DEFAULT false,

    CONSTRAINT "user_sessions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "auth_logs" (
    "id" TEXT NOT NULL,
    "ip_address" TEXT,
    "user_agent" TEXT,
    "email" TEXT NOT NULL,
    "user_id" TEXT,
    "action" "auth_log_action" NOT NULL,
    "status" "auth_log_status" NOT NULL,
    "failure_reason" TEXT,
    "device_info" JSONB,
    "location_info" JSONB,
    "session_id" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "auth_logs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "publications" (
    "id" TEXT NOT NULL,
    "process_number" TEXT NOT NULL,
    "publication_date" DATE,
    "availability_date" DATE NOT NULL,
    "authors" TEXT[],
    "defendant" TEXT NOT NULL DEFAULT 'Instituto Nacional do Seguro Social - INSS',
    "lawyers" JSONB,
    "gross_value" INTEGER,
    "net_value" INTEGER,
    "interest_value" INTEGER,
    "attorney_fees" INTEGER,
    "content" TEXT NOT NULL,
    "status" "publication_status" NOT NULL DEFAULT 'NOVA',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "scraping_source" TEXT NOT NULL DEFAULT 'DJE-SP',
    "caderno" TEXT NOT NULL DEFAULT '3',
    "instancia" TEXT NOT NULL DEFAULT '1',
    "local" TEXT NOT NULL DEFAULT 'Capital',
    "parte" TEXT NOT NULL DEFAULT '1',
    "extraction_metadata" JSONB,
    "scraping_execution_id" TEXT,

    CONSTRAINT "publications_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "publication_logs" (
    "id" TEXT NOT NULL,
    "publication_id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "action" "publication_log_action" NOT NULL,
    "old_data" JSONB,
    "new_data" JSONB,
    "notes" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "publication_logs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "scraping_executions" (
    "id" TEXT NOT NULL,
    "execution_type" "scraping_execution_type" NOT NULL,
    "status" "scraping_execution_status" NOT NULL DEFAULT 'RUNNING',
    "started_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "finished_at" TIMESTAMP(3),
    "execution_time_seconds" INTEGER,
    "publications_found" INTEGER NOT NULL DEFAULT 0,
    "publications_new" INTEGER NOT NULL DEFAULT 0,
    "publications_duplicated" INTEGER NOT NULL DEFAULT 0,
    "publications_failed" INTEGER NOT NULL DEFAULT 0,
    "publications_saved" INTEGER NOT NULL DEFAULT 0,
    "criteria_used" JSONB,
    "max_publications_limit" INTEGER,
    "scraper_version" TEXT,
    "browser_user_agent" TEXT,
    "error_details" JSONB,

    CONSTRAINT "scraping_executions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "scraping_logs" (
    "id" TEXT NOT NULL,
    "scraping_execution_id" TEXT,
    "level" "scraping_log_level" NOT NULL DEFAULT 'INFO',
    "message" TEXT NOT NULL,
    "context" JSONB,
    "error_stack" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "scraping_logs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "scraping_configurations" (
    "id" TEXT NOT NULL,
    "key" TEXT NOT NULL,
    "value" TEXT NOT NULL,
    "description" TEXT,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "scraping_configurations_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE INDEX "users_email_idx" ON "users"("email");

-- CreateIndex
CREATE INDEX "users_created_at_idx" ON "users"("created_at");

-- CreateIndex
CREATE UNIQUE INDEX "user_refresh_tokens_token_key" ON "user_refresh_tokens"("token");

-- CreateIndex
CREATE UNIQUE INDEX "user_sessions_refresh_token_key" ON "user_sessions"("refresh_token");

-- CreateIndex
CREATE INDEX "user_sessions_user_id_is_active_idx" ON "user_sessions"("user_id", "is_active");

-- CreateIndex
CREATE INDEX "auth_logs_user_id_created_at_idx" ON "auth_logs"("user_id", "created_at");

-- CreateIndex
CREATE INDEX "auth_logs_email_created_at_idx" ON "auth_logs"("email", "created_at");

-- CreateIndex
CREATE UNIQUE INDEX "publications_process_number_key" ON "publications"("process_number");

-- CreateIndex
CREATE INDEX "publications_process_number_idx" ON "publications"("process_number");

-- CreateIndex
CREATE INDEX "publications_status_idx" ON "publications"("status");

-- CreateIndex
CREATE INDEX "publications_availability_date_idx" ON "publications"("availability_date");

-- CreateIndex
CREATE INDEX "publications_created_at_idx" ON "publications"("created_at");

-- CreateIndex
CREATE INDEX "publications_status_availability_date_idx" ON "publications"("status", "availability_date");

-- CreateIndex
CREATE INDEX "publications_availability_date_created_at_idx" ON "publications"("availability_date", "created_at");

-- CreateIndex
CREATE INDEX "publications_scraping_source_caderno_idx" ON "publications"("scraping_source", "caderno");

-- CreateIndex
CREATE INDEX "publications_defendant_idx" ON "publications"("defendant");

-- CreateIndex
CREATE INDEX "publication_logs_publication_id_created_at_idx" ON "publication_logs"("publication_id", "created_at");

-- CreateIndex
CREATE INDEX "publication_logs_user_id_created_at_idx" ON "publication_logs"("user_id", "created_at");

-- CreateIndex
CREATE INDEX "publication_logs_action_created_at_idx" ON "publication_logs"("action", "created_at");

-- CreateIndex
CREATE INDEX "scraping_executions_execution_type_started_at_idx" ON "scraping_executions"("execution_type", "started_at");

-- CreateIndex
CREATE INDEX "scraping_executions_status_started_at_idx" ON "scraping_executions"("status", "started_at");

-- CreateIndex
CREATE INDEX "scraping_executions_started_at_idx" ON "scraping_executions"("started_at");

-- CreateIndex
CREATE INDEX "scraping_logs_scraping_execution_id_created_at_idx" ON "scraping_logs"("scraping_execution_id", "created_at");

-- CreateIndex
CREATE INDEX "scraping_logs_level_created_at_idx" ON "scraping_logs"("level", "created_at");

-- CreateIndex
CREATE INDEX "scraping_logs_created_at_idx" ON "scraping_logs"("created_at");

-- CreateIndex
CREATE UNIQUE INDEX "scraping_configurations_key_key" ON "scraping_configurations"("key");

-- CreateIndex
CREATE INDEX "scraping_configurations_key_is_active_idx" ON "scraping_configurations"("key", "is_active");

-- AddForeignKey
ALTER TABLE "user_refresh_tokens" ADD CONSTRAINT "user_refresh_tokens_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "user_sessions" ADD CONSTRAINT "user_sessions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "auth_logs" ADD CONSTRAINT "auth_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "publications" ADD CONSTRAINT "publications_scraping_execution_id_fkey" FOREIGN KEY ("scraping_execution_id") REFERENCES "scraping_executions"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "publication_logs" ADD CONSTRAINT "publication_logs_publication_id_fkey" FOREIGN KEY ("publication_id") REFERENCES "publications"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "publication_logs" ADD CONSTRAINT "publication_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
