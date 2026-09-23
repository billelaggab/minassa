"""أدوات أمنية: توكن، تعقيم أسماء الملفات، منع traversal، تعقيم HTML."""
import re
import uuid
from pathlib import Path

import bleach
from fastapi import Header, HTTPException

from .config import settings

ALLOWED_TAGS = ["p", "br", "b", "strong", "i", "em", "u", "ul", "ol", "li", "h3", "h4", "blockquote", "code", "pre", "a"]
ALLOWED_ATTRS = {"a": ["href", "title"]}


def require_token(x_api_token: str | None = Header(default=None, alias="X-API-Token")) -> None:
    if settings.API_TOKEN and x_api_token != settings.API_TOKEN:
        raise HTTPException(status_code=401, detail="رمز الدخول غير صالح")


def sanitize_filename(original: str) -> str:
    """يمنع Path Traversal: يتجاهل أي مسار ويبقي امتدادا آمنا فقط."""
    base = Path(original).name  # يزيل أي ../../
    base = re.sub(r"[^A-Za-z0-9._\- \u0600-\u06FF]", "_", base).strip(" .")[:180]
    ext = "".join(Path(base).suffixes)[:20]
    ext = re.sub(r"[^A-Za-z0-9.]", "", ext)
    return f"{uuid.uuid4().hex}{ext.lower()}" if ext else f"{uuid.uuid4().hex}.bin"


def clean_html(raw: str) -> str:
    return bleach.clean(raw, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def is_safe_path(root: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False
