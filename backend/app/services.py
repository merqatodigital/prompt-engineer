from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .config import get_settings
from .models import ModelSetting
from .providers.ollama import OllamaProvider
from .providers.openrouter import OpenRouterProvider
from .providers.builtin import BuiltinPromptEngineer
from .security import decrypt_secret


def active_setting(db: Session) -> ModelSetting | None:
    return db.scalar(select(ModelSetting).where(ModelSetting.is_active.is_(True)).order_by(ModelSetting.updated_at.desc()))


def activate_setting(db: Session, setting: ModelSetting) -> ModelSetting:
    db.execute(update(ModelSetting).values(is_active=False))
    setting.is_active = True
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def provider_from_setting(setting: ModelSetting | None):
    config = get_settings()
    if setting is None:
        if config.openrouter_api_key:
            return OpenRouterProvider(config.openrouter_api_key, config.openrouter_base_url), "openrouter", "openrouter/free"
        return BuiltinPromptEngineer(), "builtin", "prompt-engineer-starter-v1"
    if setting.provider == "openrouter":
        key = decrypt_secret(setting.encrypted_api_key) if setting.encrypted_api_key else config.openrouter_api_key
        if not key:
            raise HTTPException(status_code=503, detail="The active OpenRouter configuration has no API key.")
        return OpenRouterProvider(key, config.openrouter_base_url), setting.provider, setting.model_id
    if setting.provider == "ollama":
        return OllamaProvider(setting.ollama_base_url or config.ollama_base_url), setting.provider, setting.model_id
    raise HTTPException(status_code=503, detail=f"Unsupported provider: {setting.provider}")
