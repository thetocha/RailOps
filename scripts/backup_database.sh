#!/bin/sh
# Dump the production PostgreSQL database from the running db container.
# Credentials stay in Compose/container environment; they are not passed on argv.
set -eu

COMPOSE_FILE="${COMPOSE_FILE:-compose.production.yaml}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_USER="${DB_USER:-railops}"
DB_NAME="${DB_NAME:-railops}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="${BACKUP_DIR}/railops-${STAMP}.dump"

mkdir -p "${BACKUP_DIR}"
docker compose -f "${COMPOSE_FILE}" exec -T db \
  pg_dump -U "${DB_USER}" -d "${DB_NAME}" -Fc --no-password > "${DEST}"
chmod 600 "${DEST}"
echo "${DEST}"
