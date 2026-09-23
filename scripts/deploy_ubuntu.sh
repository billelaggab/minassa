#!/usr/bin/env bash
# نشر الإنتاج على Ubuntu Server جديد — يعمل دون إنترنت بعد البناء الأول
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[1/6] تحديث النظام وتثبيت Docker..."
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "[2/6] تجهيز ملف البيئة..."
[ -f .env ] || cp .env.example .env
echo ">>> حرّر القيم السرية الآن: nano .env (POSTGRES_PASSWORD / MEILI_MASTER_KEY / API_TOKEN)"

echo "[3/6] جلب خط تجوال محليا (يتطلب إنترنت لمرة واحدة فقط)..."
bash scripts/fetch_fonts.sh || true

echo "[4/6] بناء وتشغيل الحاويات..."
sudo docker compose up -d --build

echo "[5/6] انتظار الجاهزية..."
sleep 15
sudo docker compose ps
curl -sf http://localhost:8080/ -o /dev/null && echo "الواجهة تعمل على http://localhost:8080"
curl -sf -H "X-API-Token: $(grep API_TOKEN .env | cut -d= -f2)" http://localhost:8080/api/health || echo "(افحص التوكن في .env)"

echo "[6/6] تم. النسخ الاحتياطي: bash scripts/backup.sh"
