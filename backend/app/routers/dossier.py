"""محرك الدوسية: HTML للطباعة + PDF عبر WeasyPrint مع فلاتر تعقيم."""
import uuid
from pathlib import Path

import bleach
import markdown
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from jinja2 import Environment, FileSystemLoader, select_jinja_autoescape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Person, Relationship
from ..security import require_token

router = APIRouter(prefix="/api/dossier", tags=["دوسية"], dependencies=[Depends(require_token)])
TPL_DIR = Path(__file__).parent.parent / "templates"
jinja = Environment(loader=FileSystemLoader(str(TPL_DIR)),
                    autoescape=select_jinja_autoescape(["html"]))

SENS_LABEL = {"public": "عام", "confidential": "سرّي", "top_secret": "سرّي للغاية"}
REL_LABEL = {"lawyer": "محامٍ", "partner": "شريك عمل", "relative": "قريب", "accomplice": "شريك",
             "adversary": "خصم", "whistleblower": "مُبلّغ", "friend": "صديق", "colleague": "زميل"}


async def _load(pid: uuid.UUID, db: AsyncSession, exclude_confidential: bool, exclude_media: bool):
    p = (await db.execute(select(Person).where(Person.id == pid).options(
        selectinload(Person.phones), selectinload(Person.emails), selectinload(Person.socials),
        selectinload(Person.notes), selectinload(Person.documents)))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "الشخص غير موجود")
    notes = [n for n in (p.notes or []) if not (exclude_confidential and n.is_confidential)]
    notes = sorted(notes, key=lambda n: str(n.event_date or n.created_at))
    for n in notes:  # Markdown → HTML معقّم
        html = markdown.markdown(n.content or "", extensions=["extra"])
        n.rendered = bleach.clean(html, tags=["p", "br", "b", "strong", "i", "em", "u", "ul", "ol", "li",
                                              "h3", "h4", "blockquote", "code", "pre", "a", "hr", "table",
                                              "thead", "tbody", "tr", "th", "td"],
                                  attributes={"a": ["href", "title"]}, strip=True)
    rels = (await db.execute(select(Relationship).where(
        (Relationship.source_id == pid) | (Relationship.target_id == pid)))).scalars().all()
    rel_rows = []
    for r in rels:
        other_id = r.target_id if r.source_id == pid else r.source_id
        other = await db.get(Person, other_id)
        rel_rows.append({"name": other.full_name if other else "— محذوف —",
                         "type": REL_LABEL.get(r.rel_type, r.rel_type),
                         "confidence": "مؤكد" if r.confidence == "confirmed" else "مشتبه",
                         "notes": r.notes})
    docs = [] if exclude_media else (p.documents or [])
    return p, notes, rel_rows, docs


@router.get("/{pid}", response_class=HTMLResponse)
async def dossier_html(pid: uuid.UUID, exclude_confidential: bool = Query(default=False),
                       exclude_media: bool = Query(default=False),
                       db: AsyncSession = Depends(get_db)):
    from datetime import datetime
    p, notes, rel_rows, docs = await _load(pid, db, exclude_confidential, exclude_media)
    tpl = jinja.get_template("dossier.html")
    return tpl.render(person=p, notes=notes, relations=rel_rows, documents=docs,
                      sens_label=SENS_LABEL.get(p.sensitivity, p.sensitivity),
                      generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
                      exclude_confidential=exclude_confidential, exclude_media=exclude_media)


@router.get("/{pid}/pdf")
async def dossier_pdf(pid: uuid.UUID, exclude_confidential: bool = Query(default=False),
                      exclude_media: bool = Query(default=False),
                      db: AsyncSession = Depends(get_db)):
    from weasyprint import HTML
    html = await dossier_html(pid, exclude_confidential, exclude_media, db)
    pdf = HTML(string=html, base_url=str(TPL_DIR)).write_pdf()
    kind = "full" if not (exclude_confidential or exclude_media) else "filtered"
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="dossier-{pid}-{kind}.pdf"'})
