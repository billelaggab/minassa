#!/usr/bin/env bash
# نسخ احتياطي: قاعدة البيانات + الرفوعات + إعداد Meilisearch
set -euo pipefail
cd "$(dirname "$0")/.."
STAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
sudo docker compose exec -T db pg_dump -U "${POSTGRES_USER:-intel}" "${POSTGRES_DB:-inteldb}" > "backups/db_${STAMP}.sql"
sudo docker run --rm -v intel_uploads:/src -v "$PWD/backups:/dst" alpine tar czf "/dst/uploads_${STAMP}.tar.gz" -C /src .
echo "تم النسخ: backups/db_${STAMP}.sql + uploads_${STAMP}.tar.gz"
