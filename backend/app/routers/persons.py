"""CRUD الأشخاص + الملاحظات + جهات الاتصال المتداخلة."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Email, IntelNote, Person, Phone, SocialAccount
from ..schemas import NoteCreate, PersonCreate, PersonUpdate
from ..search import delete_person, person_doc, upsert_person
from ..security import require_token

router = APIRouter(prefix="/api/persons", tags=["أشخاص"], dependencies=[Depends(require_token)])


def _dump(p: Person) -> dict:
    return {
        "id": str(p.id),
        "full_name": p.full_name,
        "aliases": p.aliases,
        "avatar_path": p.avatar_path,
        "date_of_birth": str(p.date_of_birth) if p.date_of_birth else None,
        "nationality": p.nationality,
        "occupation": p.occupation,
        "address": p.address,
        "reliability": p.reliability,
        "sensitivity": p.sensitivity,
        "summary": p.summary,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "phones": [{"id": str(x.id), "number": x.number, "label": x.label,
                    "has_whatsapp": x.has_whatsapp, "has_signal": x.has_signal,
                    "has_telegram": x.has_telegram, "carrier_notes": x.carrier_notes} for x in (p.phones or [])],
        "emails": [{"id": str(x.id), "email": x.email, "kind": x.kind} for x in (p.emails or [])],
        "socials": [{"id": str(x.id), "platform": x.platform, "handle": x.handle, "url": x.url} for x in (p.socials or [])],
    }


async def _sync_index(p: Person, db: AsyncSession):
    notes = (await db.execute(select(IntelNote).where(IntelNote.person_id == p.id))).scalars().all()
    upsert_person(person_doc(
        p,
        phones=[x.number for x in (p.phones or [])],
        emails=[x.email for x in (p.emails or [])],
        notes_text=" ".join(f"{n.title} {n.content}" for n in notes),
    ))


@router.get("")
async def list_persons(q: str = "", limit: int = 50, db: AsyncSession = Depends(get_db)):
    stmt = select(Person).options(selectinload(Person.phones), selectinload(Person.emails), selectinload(Person.socials))
    if q:
        stmt = stmt.where(Person.full_name.ilike(f"%{q}%"))
    stmt = stmt.order_by(Person.updated_at.desc()).limit(min(limit, 200))
    rows = (await db.execute(stmt)).scalars().all()
    return [_dump(p) for p in rows]


@router.post("", status_code=201)
async def create_person(payload: PersonCreate, db: AsyncSession = Depends(get_db)):
    p = Person(
        full_name=payload.full_name.strip(), aliases=payload.aliases or "",
        date_of_birth=payload.date_of_birth, nationality=payload.nationality or "",
        occupation=payload.occupation or "", address=payload.address or "",
        reliability=payload.reliability, sensitivity=payload.sensitivity,
        summary=payload.summary or "",
    )
    for ph in payload.phones:
        p.phones.append(Phone(number=ph.number.strip(), label=ph.label, has_whatsapp=ph.has_whatsapp,
                              has_signal=ph.has_signal, has_telegram=ph.has_telegram, carrier_notes=ph.carrier_notes))
    for em in payload.emails:
        p.emails.append(Email(email=em.email.strip(), kind=em.kind, pgp_key=em.pgp_key))
    for so in payload.socials:
        p.socials.append(SocialAccount(platform=so.platform.strip(), handle=so.handle.strip(), url=so.url or ""))
    db.add(p)
    await db.commit()
    await db.refresh(p, attribute_names=["phones", "emails", "socials"])
    await _sync_index(p, db)
    return _dump(p)


@router.get("/{pid}")
async def get_person(pid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    p = (await db.execute(
        select(Person).where(Person.id == pid).options(
            selectinload(Person.phones), selectinload(Person.emails),
            selectinload(Person.socials), selectinload(Person.notes), selectinload(Person.documents))
    )).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "الشخص غير موجود")
    d = _dump(p)
    d["notes"] = [{"id": str(n.id), "title": n.title, "content": n.content, "category": n.category,
                   "event_date": str(n.event_date) if n.event_date else None,
                   "is_confidential": n.is_confidential,
                   "created_at": n.created_at.isoformat() if n.created_at else None} for n in sorted(p.notes or [], key=lambda x: str(x.created_at or ""), reverse=True)]
    d["documents"] = [{"id": str(x.id), "original_name": x.original_name, "mime": x.mime,
                       "size_bytes": x.size_bytes, "sha256": x.sha256,
                       "description": x.description, "uploaded_at": x.uploaded_at.isoformat() if x.uploaded_at else None} for x in (p.documents or [])]
    rels = await db.execute(select(Person.full_name)  # إحصاء سريع للعلاقات
                            .where(False))
    d["relations_url"] = f"/api/relations/{p.id}"
    return d


@router.put("/{pid}")
async def update_person(pid: uuid.UUID, payload: PersonUpdate, db: AsyncSession = Depends(get_db)):
    p = await db.get(Person, pid)
    if not p:
        raise HTTPException(404, "الشخص غير موجود")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    await db.commit()
    await db.refresh(p, attribute_names=["phones", "emails", "socials"])
    await _sync_index(p, db)
    return _dump(p)


@router.delete("/{pid}")
async def remove_person(pid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    p = await db.get(Person, pid)
    if not p:
        raise HTTPException(404, "الشخص غير موجود")
    await db.delete(p)
    await db.commit()
    delete_person(str(pid))
    return {"deleted": True}


# ---- ملاحظات ----
@router.post("/{pid}/notes", status_code=201)
async def add_note(pid: uuid.UUID, payload: NoteCreate, db: AsyncSession = Depends(get_db)):
    p = await db.get(Person, pid)
    if not p:
        raise HTTPException(404, "الشخص غير موجود")
    n = IntelNote(person_id=pid, title=payload.title.strip(), content=payload.content or "",
                  category=payload.category, event_date=payload.event_date,
                  is_confidential=payload.is_confidential)
    db.add(n)
    await db.commit()
    await db.refresh(n)
    await db.refresh(p, attribute_names=["phones", "emails", "socials"])
    await _sync_index(p, db)
    return {"id": str(n.id), "title": n.title}
