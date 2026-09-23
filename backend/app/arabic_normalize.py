"""تطبيع اللغة العربية للبحث: أ/إ/آ→ا، ة→ه، ى→ي، إزالة التشكيل، توحيد ك/ك."""
import re

# التشكيل العربي + أحرف التحكم
TASHKEEL = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8]")
TATWEEL = "\u0640"


def normalize_arabic(text: str | None) -> str:
    if not text:
        return ""
    s = text
    s = s.replace(TATWEEL, "")
    s = TASHKEEL.sub("", s)
    # توحيد الهمزات
    s = re.sub(r"[أإآٱ]", "ا", s)
    # ة ↔ ه
    s = s.replace("ة", "ه")
    # ى → ي
    s = s.replace("ى", "ي")
    # ك الفارسية / ي الفارسية
    s = s.replace("گ", "ك").replace("چ", "ج").replace("پ", "ب").replace("ڤ", "ف")
    s = s.replace("ﮎ", "ك").replace("ﻛ", "ك")
    s = s.replace("ې", "ي").replace("ے", "ي").replace("ۀ", "ه")
    # إزالة علامات الترقيم الزائدة وتوحيد المسافات
    s = re.sub(r"\s+", " ", s).strip()
    return s


def fold_variants(term: str) -> list[str]:
    """توليد بدائل للبحث الاحتياطي عند غياب Meilisearch (يستخدم في LIKE)."""
    n = normalize_arabic(term)
    return list({term.strip(), n})
