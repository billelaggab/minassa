"""طبقة Meilisearch: فهرسة + بحث عربي متسامح مع الأخطاء.

- الفهرس: persons (id, full_name, aliases, phones, emails, notes, national_id...)
- التطبيع العربي يُخزّن في حقل search_blob مطبّع لتسريع المطابقة.
"""
import meilisearch

from .arabic_normalize import normalize_arabic
from .config import settings

INDEX = "persons"


def client():
    return meilisearch.Client(settings.MEILI_HOST, settings.MEILI_MASTER_KEY)


def ensure_index():
    c = client()
    try:
        c.get_index(INDEX)
    except Exception:
        c.create_index(INDEX, {"primaryKey": "id"})
    idx = c.index(INDEX)
    try:
        idx.update_searchable_attributes(["full_name", "aliases", "search_blob"])
        idx.update_filterable_attributes(["sensitivity", "reliability"])
        idx.update_typo_tolerance({"enabled": True, "minWordSizeForTypos": {"oneTypo": 4, "twoTypos": 8}})
    except Exception:
        pass


def person_doc(p, phones=(), emails=(), notes_text="") -> dict:
    blob_src = " ".join([
        p.full_name or "", p.aliases or "", p.nationality or "",
        p.occupation or "", p.address or "", p.summary or "",
        " ".join(phones), " ".join(emails), notes_text or "",
    ])
    return {
        "id": str(p.id),
        "full_name": p.full_name,
        "aliases": p.aliases,
        "sensitivity": p.sensitivity,
        "reliability": p.reliability,
        "search_blob": normalize_arabic(blob_src),
        "search_blob_raw": blob_src[:4000],
    }


def upsert_person(doc: dict):
    try:
        client().index(INDEX).add_documents([doc])
    except Exception:
        pass  # يعمل النظام حتى لو تعطل البحث — يسقط إلى LIKE في Postgres


def delete_person(pid: str):
    try:
        client().index(INDEX).delete_document(pid)
    except Exception:
        pass


def global_search(query: str, limit: int = 20) -> list[dict]:
    from .arabic_normalize import normalize_arabic as nz
    c = client()
    for q in ({query, nz(query)} - {""}):
        try:
            res = c.index(INDEX).search(q, {"limit": limit, "attributesToHighlight": ["full_name", "aliases", "search_blob_raw"]})
            hits = res.get("hits", []) if isinstance(res, dict) else res.hits
            if hits:
                return hits if isinstance(hits, list) else [h.__dict__ for h in hits]
        except Exception:
            continue
    return []
