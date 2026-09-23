# دليل التثبيت والتشغيل — منظومة الاستقصاء (عربي كامل)

> المنصة عربية بالكامل (RTL)، بخط **تجوَّل (Tajawal)** محلي، ووضع ليلي افتراضي، وتعمل **دون إنترنت** بعد الإعداد الأول.

مصدر الخط الرسمي: https://fonts.google.com/specimen/Tajawal

---

## 1) المتطلبات

- خادم **Ubuntu 22.04+** (أو أي جهاز للتجربة المحلية)
- **Docker + Docker Compose v2**
- منفذ واحد فقط: `8080` (قابل للتغيير عبر `FRONT_PORT` في `.env`)
- لا حاجة لأي اتصال خارجي بعد البناء

## 2) البنية (Blueprint)

```
.
├── docker-compose.yml          # db + meilisearch + backend + frontend
├── .env.example                # انسخه إلى .env وعدّل الأسرار
├── backend/
│   ├── Dockerfile              # FastAPI + WeasyPrint
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # نقطة الدخول
│       ├── config.py           # إعدادات البيئة
│       ├── database.py         # async engine + init_db
│       ├── models.py           # persons/phones/emails/socials/notes/relationships/documents
│       ├── schemas.py          # Pydantic الصارمة
│       ├── arabic_normalize.py # أ=إ=آ→ا، ة→ه، ى→ي، إزالة التشكيل
│       ├── search.py           # Meilisearch + احتياطي Postgres
│       ├── security.py         # توكن + تعقيم ملفات + bleach ضد XSS
│       ├── routers/            # persons / relations / documents / dossier / search
│       └── templates/dossier.html  # قالب الطباعة + PDF (@media print)
├── frontend/
│   ├── Dockerfile              # build ثم Nginx
│   ├── nginx.conf              # بروكسي /api و /files + سياسات أمان
│   └── src/                    # React+Vite+Tailwind — RTL عربي
├── scripts/
│   ├── deploy_ubuntu.sh        # نشر كامل بأمر واحد
│   ├── fetch_fonts.sh          # جلب خط تجوال محليا
│   └── backup.sh               # نسخ احتياطي
└── INSTALL_AR.md               # هذا الملف
```

### شبكة Docker

- `internal` (داخلية معزولة): `db` + `meilisearch` + `backend`
- `edge`: `backend` + `frontend` فقط
- المكشوف للخارج: **`frontend:8080`** فقط — الباكند والقاعدة والبحث غير منشورة

## 3) التثبيت على خادم جديد (3 أوامر)

```bash
git clone <repo> intel && cd intel
cp .env.example .env && nano .env   # غيّر POSTGRES_PASSWORD و MEILI_MASTER_KEY و API_TOKEN
sudo bash scripts/deploy_ubuntu.sh
```

ثم افتح: **http://SERVER_IP:8080** وأدخل `API_TOKEN` في حقل رمز الدخول أعلى اللوحة.

## 4) التشغيل اليدوي (بدون السكربت)

```bash
cp .env.example .env && nano .env
bash scripts/fetch_fonts.sh        # مرة واحدة بإنترنت لجلب Tajawal محليا
sudo docker compose up -d --build
sudo docker compose ps
curl http://localhost:8080/
```

## 5) الاختبار السريع

```bash
export T=$(grep API_TOKEN .env | cut -d= -f2)
# الصحة
curl -H "X-API-Token: $T" http://localhost:8080/api/health
# إنشاء شخص
curl -H "X-API-Token: $T" -H "Content-Type: application/json" \
  -d '{"full_name":"أحمد الصحفي","aliases":"أبو تحقيق","nationality":"يمني","occupation":"مصدر"}' \
  http://localhost:8080/api/persons
# بحث عربي (جرّب: احمد بدون همزة — يجد أحمد)
curl -H "X-API-Token: $T" "http://localhost:8080/api/search?q=احمد"
# دوسية PDF
curl -H "X-API-Token: $T" "http://localhost:8080/api/dossier/<ID>/pdf" -o dossier.pdf
```

## 6) التطبيع العربي في البحث

`backend/app/arabic_normalize.py`:

- `أ/إ/آ/ٱ → ا` — `ة → ه` — `ى → ي` — حذف التطويل `ـ` والتشكيل — توحيد المسافات
- يُخزَّن حقل `search_blob` مطبَّعا في Meilisearch، والاستعلام يُجرَّب بصيغتين (الأصلية + المطبَّعة)
- عند تعطل Meilisearch يسقط تلقائيا إلى `ILIKE` في Postgres

## 7) الدوسية والطباعة

- من صفحة الشخص: خيارات **استبعاد السرّي / استبعاد المرفقات** ثم **تنزيل PDF** أو **طباعة مباشرة**
- علامة مائية ديناميكية حسب الحساسية (عام / سرّي / سرّي للغاية)
- `page-break-inside: avoid` يمنع كسر الجداول والملاحظات بين الصفحات
- الملاحظات السرّية مخفية افتراضيا وتتطلب تفعيلا واعيا

## 8) سياسات الأمان المطبقة

| التهديد | المعالجة |
|---|---|
| Path Traversal | `sanitize_filename()` + فحص `is_safe_path()` — أسماء UUID على القرص |
| SQL Injection | ORM بالكامل (SQLAlchemy) بدون SQL خام |
| XSS | `bleach` + Markdown معقّم + Jinja autoescape |
| sniffing المسارات | التنزيل عبر `/files/{uuid}` بالتوكن فقط — لا مسارات حقيقية |
| سلسلة الحيازة | `SHA-256` لكل ملف + فهرس أدلة في الدوسية |
| تسريب خارجي | CSP صارمة + لا CDN + خطوط محلية + `MEILI_NO_ANALYTICS=true` |

## 9) النسخ الاحتياطي والاستعادة

```bash
bash scripts/backup.sh   # ينتج backups/db_*.sql + uploads_*.tar.gz
# استعادة القاعدة:
cat backups/db_XXX.sql | sudo docker compose exec -T db psql -U intel inteldb
```

## 10) استكشاف الأخطاء

- `sudo docker compose logs -f backend` — سجل الباكند
- `sudo docker compose logs -f meilisearch` — سجل البحث
- خطأ 401: التوكن في الواجهة لا يطابق `API_TOKEN` في `.env`
- صفحة بيضاء: تأكد من نسخ `frontend/public/fonts/Tajawal-*.ttf` قبل `docker compose build`
- PDF فارغ الخط: انسخ الخط أيضا إلى `backend/app/static/fonts/`

## 11) الإيقاف والتنظيف

```bash
sudo docker compose down        # إيقاف مع بقاء البيانات (volumes)
sudo docker compose down -v     # حذف البيانات نهائيا — بحذر!
```
