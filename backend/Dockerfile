# ---- Backend: FastAPI + WeasyPrint (multi-stage, offline friendly) ----
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# مكتبات النظام اللازمة لـ WeasyPrint + Pillow + asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libharfbuzz-subset0 \
    libjpeg-dev libopenjp2-7-dev libffi-dev \
    libcairo2 libgdk-pixbuf2.0-0 libxml2 libxslt1.1 \
    fonts-dejavu curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# مجلد الرفوعات (يُربط مع volume خارجي)
RUN mkdir -p /uploads && chmod 700 /uploads

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
