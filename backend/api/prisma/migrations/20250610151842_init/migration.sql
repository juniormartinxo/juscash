-- CreateEnum
CREATE TYPE "publication_log_action" AS ENUM ('CRIADA', 'ATUALIZADA', 'DELETADA', 'VISUALIZADA', 'DOWNLOADED');

-- CreateEnum
CREATE TYPE "publication_status" AS ENUM ('NOVA', 'LIDA', 'PROCESSADA');

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
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "publication_logs_pkey" PRIMARY KEY ("id")
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

-- AddForeignKey
ALTER TABLE "user_refresh_tokens" ADD CONSTRAINT "user_refresh_tokens_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "user_sessions" ADD CONSTRAINT "user_sessions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "auth_logs" ADD CONSTRAINT "auth_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "publication_logs" ADD CONSTRAINT "publication_logs_publication_id_fkey" FOREIGN KEY ("publication_id") REFERENCES "publications"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "publication_logs" ADD CONSTRAINT "publication_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
