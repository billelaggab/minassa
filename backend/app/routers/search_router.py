"""البحث الموحد: Meilisearch أولا، ثم احتياطي Postgres مع التطبيع العربي."""
from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..arabic_normalize import normalize_arabic
from ..database import get_db
from ..models import Email, IntelNote, Person, Phone, SocialAccount
from ..search import global_search
from ..security import require_token

router = APIRouter(prefix="/api/search", tags=["بحث"], dependencies=[Depends(require_token)])


@router.get("")
async def search(q: str, limit: int = 20, db: AsyncSession = Depends(get_db)):
    q = (q or "").strip()
    if not q:
        return {"query": q, "hits": [], "engine": "none"}
    hits = global_search(q, limit=limit)
    if hits:
        return {"query": q, "hits": hits, "engine": "meilisearch"}
    # احتياطي: LIKE على الاسم + المستعارات + الهواتف + الإيميلات + نص الملاحظات
    nq = f"%{q}%"
    persons = (await db.execute(
        select(Person).where(or_(Person.full_name.ilike(nq), Person.aliases.ilike(nq)))
        .options(selectinload(Person.phones)).limit(limit))).scalars().all()
    ph = (await db.execute(select(Phone).where(Phone.number.ilike(nq)).limit(limit))).scalars().all()
    em = (await db.execute(select(Email).where(Email.email.ilike(nq)).limit(limit))).scalars().all()
    no = (await db.execute(select(IntelNote).where(
        or_(IntelNote.title.ilike(nq), IntelNote.content.ilike(nq))).limit(limit))).scalars().all()
    norm = normalize_arabic(q)
    return {"query": q, "normalized": norm, "engine": "postgres-fallback",
            "persons": [{"id": str(p.id), "full_name": p.full_name, "aliases": p.aliases,
                         "sensitivity": p.sensitivity} for p in persons],
            "phones": [{"number": x.number, "person_id": str(x.person_id)} for x in ph],
            "emails": [{"email": x.email, "person_id": str(x.person_id)} for x in em],
            "notes": [{"id": str(x.id), "title": x.title, "person_id": str(x.person_id)} for x in no]}
