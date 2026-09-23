"""نقطة الدخول: FastAPI + تسجيل الراوترات + تهيئة DB/Search."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routers import dossier, documents, persons, relations, search_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    try:
        from .search import ensure_index
        ensure_index()
    except Exception:
        pass
    yield


app = FastAPI(title="منظومة الاستقصاء — API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # خلف Nginx داخلي فقط — لا كشف خارجي
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(persons.router)
app.include_router(relations.router)
app.include_router(documents.router)
app.include_router(dossier.router)
app.include_router(search_router.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
