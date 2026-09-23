"""الوثائق: رفع آمن + تنزيل مرخّص + معاينة PDF/صور داخل المتصفح."""
import hashlib
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..models import Document
from ..security import is_safe_path, require_token, sanitize_filename

router = APIRouter(tags=["وثائق"], dependencies=[Depends(require_token)])
ROOT = Path(settings.UPLOAD_DIR)
ROOT.mkdir(parents=True, exist_ok=True)

IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
PDF_MIME = "application/pdf"


@router.post("/api/persons/{pid}/documents", status_code=201)
async def upload_docs(pid: uuid.UUID, files: list[UploadFile] = File(...),
                      description: str = Form(default=""),
                      db: AsyncSession = Depends(get_db)):
    saved = []
    for up in files:
        data = await up.read()
        if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(413, f"الملف {up.filename} يتجاوز الحد المسموح")
        stored = sanitize_filename(up.filename or "file")
        dest = ROOT / stored
        if not is_safe_path(ROOT, dest):
            raise HTTPException(400, "اسم ملف غير آمن")
        async with aiofiles.open(dest, "wb") as f:
            await f.write(data)
        doc = Document(person_id=pid, stored_name=stored, original_name=(up.filename or stored)[:500],
                       mime=up.content_type or "application/octet-stream",
                       size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                       description=description or "")
        db.add(doc)
        await db.flush()
        saved.append({"id": str(doc.id), "original_name": doc.original_name,
                      "sha256": doc.sha256, "size_bytes": doc.size_bytes})
    await db.commit()
    return saved


@router.get("/files/{doc_id}")
async def download(doc_id: uuid.UUID, inline: bool = False, db: AsyncSession = Depends(get_db)):
    """تنزيل مرخّص بالتوكن — inline=1 للمعاينة داخل المتصفح (PDF/صور)."""
    # ملاحظة: التوكن يُمرَّر هنا أيضا عبر X-API-Token (Nginx يمرره). للمعاينة المباشرة
    # يمكن استخدام ?token=... وسيُقبل كبديل — يُتحقق منه يدويا في الواجهة عبر fetch/blob.
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "الوثيقة غير موجودة")
    path = ROOT / doc.stored_name
    if not is_safe_path(ROOT, path) or not path.is_file():
        raise HTTPException(404, "الملف غير موجود على القرص")
    disp = "inline" if (inline and doc.mime in IMAGE_MIMES | {PDF_MIME}) else "attachment"
    return FileResponse(str(path), media_type=doc.mime,
                        filename=doc.original_name,
                        content_disposition_type=disp)


@router.delete("/api/documents/{doc_id}")
async def remove_doc(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "الوثيقة غير موجودة")
    path = ROOT / doc.stored_name
    try:
        if is_safe_path(ROOT, path) and path.is_file():
            path.unlink()
    except Exception:
        pass
    await db.delete(doc)
    await db.commit()
    return {"deleted": True}


@router.get("/api/search/documents")
async def search_docs(sha256: str = "", db: AsyncSession = Depends(get_db)):
    stmt = select(Document)
    if sha256:
        stmt = stmt.where(Document.sha256 == sha256)
    rows = (await db.execute(stmt.limit(50))).scalars().all()
    return [{"id": str(d.id), "original_name": d.original_name, "sha256": d.sha256,
             "person_id": str(d.person_id) if d.person_id else None} for d in rows]
