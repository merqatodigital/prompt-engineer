from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ChatRequest(BaseModel):
    request: str = Field(min_length=1, max_length=12000)
    artifact_type: str = "Web Application"
    conversation_id: str | None = None
    project_context: str | None = Field(default=None, max_length=8000)


class ChatResponse(BaseModel):
    conversation_id: str
    status: str
    provider: str
    model_id: str
    content: str | None = None
    clarification_question: str | None = None
    validation_errors: list[str] = Field(default_factory=list)
    references: list[dict] = Field(default_factory=list)
    generation_config: dict[str, str | int | float] = Field(default_factory=dict)
    quality_score: int | None = None
    critique_summary: str | None = None


class PromptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    category: str = "Other"
    content: str = Field(min_length=1)
    project_context: str | None = None
    target_model: str | None = None
    target_environment: str | None = None
    model_id: str | None = None
    status: str = "Draft"


class PromptUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    content: str | None = None
    project_context: str | None = None
    target_model: str | None = None
    target_environment: str | None = None
    status: str | None = None


class PromptRead(PromptCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    version: str
    created_at: datetime
    updated_at: datetime


class PromptTestRequest(BaseModel):
    test_input: str = Field(min_length=1, max_length=8000)


class PromptTestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    prompt_id: str
    model_id: str
    test_input: str
    model_output: str
    passed: bool
    quality_score: int | None = None
    created_at: datetime


class OpenRouterSettingsRequest(BaseModel):
    api_key: str | None = Field(default=None, min_length=10)
    model_id: str = Field(min_length=1)


class OllamaSettingsRequest(BaseModel):
    base_url: str = "http://localhost:11434"
    model_id: str = Field(min_length=1)


class ProviderTestRequest(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    model_id: str | None = None


class ModelSettingsRead(BaseModel):
    provider: str | None
    model_id: str | None
    has_api_key: bool
    ollama_base_url: str | None
    updated_at: datetime | None
