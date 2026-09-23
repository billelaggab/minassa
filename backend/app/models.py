"""نماذج قاعدة البيانات — SQLAlchemy 2.0 (async).

الكيانات: Person + Phones + Emails + Socials + Notes + Relationships + Documents
"""
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _uuid():
    return uuid.uuid4()


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    aliases: Mapped[str] = mapped_column(Text, default="", nullable=False)  # أسماء مستعارة مفصولة بفواصل/أسطر
    avatar_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    reliability: Mapped[int] = mapped_column(Integer, default=3)  # 1..5
    sensitivity: Mapped[str] = mapped_column(String(32), default="confidential")  # public|confidential|top_secret
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    phones: Mapped[list["Phone"]] = relationship(back_populates="person", cascade="all, delete-orphan")
    emails: Mapped[list["Email"]] = relationship(back_populates="person", cascade="all, delete-orphan")
    socials: Mapped[list["SocialAccount"]] = relationship(back_populates="person", cascade="all, delete-orphan")
    notes: Mapped[list["IntelNote"]] = relationship(back_populates="person", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="person", cascade="all, delete-orphan")


class Phone(Base):
    __tablename__ = "phones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), index=True)
    number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # سلسلة E.164
    label: Mapped[str] = mapped_column(String(32), default="personal")  # personal|work|burner|other
    has_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False)
    has_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    has_telegram: Mapped[bool] = mapped_column(Boolean, default=False)
    carrier_notes: Mapped[str] = mapped_column(Text, default="")

    person: Mapped[Person] = relationship(back_populates="phones")


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(32), default="primary")  # primary|leaked|secure
    pgp_key: Mapped[str] = mapped_column(Text, default="")

    person: Mapped[Person] = relationship(back_populates="emails")


class SocialAccount(Base):
    __tablename__ = "socials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)  # twitter|facebook|telegram|...
    handle: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(512), default="")

    person: Mapped[Person] = relationship(back_populates="socials")


class IntelNote(Base):
    __tablename__ = "intel_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")  # Markdown — يُعقّم عند العرض بـ bleach
    category: Mapped[str] = mapped_column(String(64), default="meeting")  # meeting|financial|background|leak|other
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    person: Mapped[Person] = relationship(back_populates="notes")


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), index=True)
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), index=True)
    rel_type: Mapped[str] = mapped_column(String(64), nullable=False)  # lawyer|partner|relative|accomplice|...
    confidence: Mapped[str] = mapped_column(String(32), default="suspected")  # confirmed|suspected
    notes: Mapped[str] = mapped_column(Text, default="")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    person_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), nullable=True, index=True)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)  # اسم UUID معقّم على القرص
    original_name: Mapped[str] = mapped_column(String(512), nullable=False)
    mime: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(64), default="", index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    person: Mapped[Person | None] = relationship(back_populates="documents")
