from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class ModelSetting(Base):
    __tablename__ = "model_settings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    provider: Mapped[str] = mapped_column(String(32))
    model_id: Mapped[str] = mapped_column(String(255))
    encrypted_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    ollama_base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(180))
    category: Mapped[str] = mapped_column(String(60), default="Other")
    version: Mapped[str] = mapped_column(String(20), default="v1.0")
    content: Mapped[str] = mapped_column(Text)
    project_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_environment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    tests: Mapped[list["PromptTest"]] = relationship(back_populates="prompt", cascade="all, delete-orphan")


class PromptTest(Base):
    __tablename__ = "prompt_tests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    prompt_id: Mapped[str] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"))
    model_id: Mapped[str] = mapped_column(String(255))
    test_input: Mapped[str] = mapped_column(Text)
    model_output: Mapped[str] = mapped_column(Text)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    prompt: Mapped[Prompt] = relationship(back_populates="tests")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    provider: Mapped[str] = mapped_column(String(32))
    model_id: Mapped[str] = mapped_column(String(255))
    user_message: Mapped[str] = mapped_column(Text)
    assistant_message: Mapped[str] = mapped_column(Text)
    validation_status: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class GenerationRun(Base):
    __tablename__ = "generation_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    conversation_id: Mapped[str] = mapped_column(String, index=True)
    provider: Mapped[str] = mapped_column(String(32))
    model_id: Mapped[str] = mapped_column(String(255))
    prompt_version: Mapped[str] = mapped_column(String(32))
    temperature: Mapped[float] = mapped_column(Float)
    max_output_tokens: Mapped[int] = mapped_column(Integer)
    context_chars: Mapped[int] = mapped_column(Integer)
    reference_count: Mapped[int] = mapped_column(Integer)
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
