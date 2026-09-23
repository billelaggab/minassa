"""شبكة العلاقات Many-to-Many ذاتية المرجع."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Person, Relationship
from ..schemas import RelationCreate
from ..security import require_token

router = APIRouter(prefix="/api/relations", tags=["علاقات"], dependencies=[Depends(require_token)])


@router.get("/{pid}")
async def list_relations(pid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Relationship).where(
        or_(Relationship.source_id == pid, Relationship.target_id == pid)))).scalars().all()
    out = []
    for r in rows:
        other_id = r.target_id if r.source_id == pid else r.source_id
        other = await db.get(Person, other_id)
        out.append({"id": str(r.id), "other_id": str(other_id),
                    "other_name": other.full_name if other else "— محذوف —",
                    "rel_type": r.rel_type, "confidence": r.confidence,
                    "notes": r.notes, "direction": "out" if r.source_id == pid else "in"})
    return out


@router.post("/{pid}", status_code=201)
async def add_relation(pid: uuid.UUID, payload: RelationCreate, db: AsyncSession = Depends(get_db)):
    if payload.target_id == pid:
        raise HTTPException(400, "لا يمكن ربط الشخص بنفسه")
    for _id in (pid, payload.target_id):
        if not await db.get(Person, _id):
            raise HTTPException(404, "أحد الطرفين غير موجود")
    r = Relationship(source_id=pid, target_id=payload.target_id, rel_type=payload.rel_type,
                     confidence=payload.confidence, notes=payload.notes or "")
    db.add(r)
    await db.commit()
    return {"id": str(r.id)}


@router.delete("/{rid}")
async def remove_relation(rid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    r = await db.get(Relationship, rid)
    if not r:
        raise HTTPException(404, "العلاقة غير موجودة")
    await db.delete(r)
    await db.commit()
    return {"deleted": True}
