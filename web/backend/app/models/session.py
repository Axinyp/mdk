from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class GenSession(Base):
    __tablename__ = "gen_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="created")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    join_registry: Mapped[str | None] = mapped_column(Text, nullable=True)
    xml_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    cht_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class SessionMessage(Base):
    __tablename__ = "session_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("gen_sessions.id"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ParseRevision(Base):
    __tablename__ = "parse_revisions"
    __table_args__ = (
        UniqueConstraint("session_id", "revision", name="uq_parse_revisions_session_revision"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("gen_sessions.id"), index=True, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    parsed_data: Mapped[str] = mapped_column(Text, nullable=False)
    missing_info: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
