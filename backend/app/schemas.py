"""سكيمات Pydantic — تحقق صارم + منع XSS عبر التقليم."""
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

Sensitivity = Literal["public", "confidential", "top_secret"]


class PhoneIn(BaseModel):
    number: str = Field(min_length=4, max_length=32)
    label: Literal["personal", "work", "burner", "other"] = "personal"
    has_whatsapp: bool = False
    has_signal: bool = False
    has_telegram: bool = False
    carrier_notes: str = ""


class EmailIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    kind: Literal["primary", "leaked", "secure"] = "primary"
    pgp_key: str = ""


class SocialIn(BaseModel):
    platform: str = Field(min_length=2, max_length=64)
    handle: str = Field(min_length=1, max_length=255)
    url: str = ""


class PersonCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    aliases: str = ""
    date_of_birth: date | None = None
    nationality: str = ""
    occupation: str = ""
    address: str = ""
    reliability: int = Field(default=3, ge=1, le=5)
    sensitivity: Sensitivity = "confidential"
    summary: str = ""
    phones: list[PhoneIn] = []
    emails: list[EmailIn] = []
    socials: list[SocialIn] = []


class PersonUpdate(BaseModel):
    full_name: str | None = None
    aliases: str | None = None
    date_of_birth: date | None = None
    nationality: str | None = None
    occupation: str | None = None
    address: str | None = None
    reliability: int | None = Field(default=None, ge=1, le=5)
    sensitivity: Sensitivity | None = None
    summary: str | None = None


class NoteCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    content: str = ""
    category: Literal["meeting", "financial", "background", "leak", "other"] = "meeting"
    event_date: date | None = None
    is_confidential: bool = False


class RelationCreate(BaseModel):
    target_id: UUID
    rel_type: str = Field(min_length=2, max_length=64)
    confidence: Literal["confirmed", "suspected"] = "suspected"
    notes: str = ""

    @field_validator("rel_type")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()
