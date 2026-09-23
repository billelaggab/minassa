#!/usr/bin/env bash
# جلب خط تجوال (Tajawal) من Google Fonts مرة واحدة ثم التوزيع محليا — بعده يعمل النظام Air-Gapped
# المصدر: https://fonts.google.com/specimen/Tajawal
set -euo pipefail
ROOT="$(dirname "$0")/.."
mkdir -p "$ROOT/frontend/public/fonts" "$ROOT/backend/app/static/fonts"
cd /tmp
echo "تنزيل Tajawal..."
curl -sL -o tajawal.zip "https://fonts.google.com/download?family=Tajawal" || true
if [ -f tajawal.zip ]; then
  unzip -o -j tajawal.zip "*.ttf" -d tajawal_out 2>/dev/null || true
  cp -f tajawal_out/Tajawal-Regular.ttf "$ROOT/frontend/public/fonts/" 2>/dev/null || true
  cp -f tajawal_out/Tajawal-Bold.ttf "$ROOT/frontend/public/fonts/" 2>/dev/null || true
  cp -f tajawal_out/Tajawal-Regular.ttf "$ROOT/backend/app/static/fonts/" 2>/dev/null || true
  cp -f tajawal_out/Tajawal-Bold.ttf "$ROOT/backend/app/static/fonts/" 2>/dev/null || true
fi
# بديل عبر gstatic عند فشل الحزمة
for w in Regular Bold; do
  [ -f "$ROOT/frontend/public/fonts/Tajawal-$w.ttf" ] || \
    curl -sL -o "$ROOT/frontend/public/fonts/Tajawal-$w.ttf" "https://github.com/google/fonts/raw/main/ofl/tajawal/Tajawal%5BsC%2Cwght%5D.ttf" || true
done
cp -f "$ROOT/frontend/public/fonts/"*.ttf "$ROOT/backend/app/static/fonts/" 2>/dev/null || true
ls -la "$ROOT/frontend/public/fonts" "$ROOT/backend/app/static/fonts" || true
echo "انتهى. تحقق من وجود Tajawal-Regular.ttf و Tajawal-Bold.ttf"
