import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import ModelSetting
from ..providers.ollama import OllamaProvider
from ..providers.openrouter import OpenRouterProvider
from ..schemas import ModelSettingsRead, OllamaSettingsRequest, OpenRouterSettingsRequest, ProviderTestRequest
from ..security import decrypt_secret, encrypt_secret, require_admin
from ..services import activate_setting, active_setting


router = APIRouter(prefix="/api", tags=["model settings"])


def provider_error(exc: Exception, provider: str) -> HTTPException:
    if isinstance(exc, httpx.HTTPStatusError):
        if exc.response.status_code in (401, 403):
            return HTTPException(status_code=401, detail=f"{provider} rejected the credentials.")
        if exc.response.status_code == 429:
            return HTTPException(status_code=429, detail=f"{provider} rate limit reached.")
    return HTTPException(status_code=503, detail=f"{provider} is unavailable: {type(exc).__name__}")


@router.get("/settings/model", response_model=ModelSettingsRead)
def get_model_setting(db: Session = Depends(get_db)) -> ModelSettingsRead:
    setting = active_setting(db)
    return ModelSettingsRead(
        provider=setting.provider if setting else "builtin",
        model_id=setting.model_id if setting else "prompt-engineer-starter-v1",
        has_api_key=bool(setting and setting.encrypted_api_key) or bool(get_settings().openrouter_api_key),
        ollama_base_url=setting.ollama_base_url if setting else get_settings().ollama_base_url,
        updated_at=setting.updated_at if setting else None,
    )


@router.get("/providers/openrouter/models")
async def openrouter_models(db: Session = Depends(get_db)) -> list[dict]:
    setting = active_setting(db)
    encrypted = setting.encrypted_api_key if setting and setting.provider == "openrouter" else None
    key = decrypt_secret(encrypted) if encrypted else get_settings().openrouter_api_key
    if not key:
        raise HTTPException(status_code=400, detail="Enter and save an OpenRouter API key first.")
    try:
        return await OpenRouterProvider(key, get_settings().openrouter_base_url).list_models()
    except Exception as exc:
        raise provider_error(exc, "OpenRouter") from exc


@router.post("/providers/openrouter/test")
async def test_openrouter(payload: ProviderTestRequest, db: Session = Depends(get_db)) -> dict:
    setting = active_setting(db)
    saved = decrypt_secret(setting.encrypted_api_key) if setting and setting.encrypted_api_key else ""
    key = payload.api_key or saved or get_settings().openrouter_api_key
    model_id = payload.model_id or (setting.model_id if setting else "openrouter/free")
    if not key:
        raise HTTPException(status_code=400, detail="OpenRouter API key is required.")
    try:
        return await OpenRouterProvider(key, get_settings().openrouter_base_url).test(model_id)
    except Exception as exc:
        raise provider_error(exc, "OpenRouter") from exc


@router.put("/settings/openrouter", response_model=ModelSettingsRead)
async def save_openrouter(payload: OpenRouterSettingsRequest, db: Session = Depends(get_db)) -> ModelSettingsRead:
    current = active_setting(db)
    existing_key = current.encrypted_api_key if current and current.provider == "openrouter" else None
    encrypted_key = encrypt_secret(payload.api_key) if payload.api_key else existing_key
    if not encrypted_key and not get_settings().openrouter_api_key:
        raise HTTPException(status_code=400, detail="OpenRouter API key is required.")
    key = payload.api_key or (decrypt_secret(existing_key) if existing_key else get_settings().openrouter_api_key)
    model_id = payload.model_id or "openrouter/free"
    if payload.model_id:
        try:
            await OpenRouterProvider(key, get_settings().openrouter_base_url).test(payload.model_id)
        except Exception as exc:
            raise provider_error(exc, "OpenRouter") from exc
    setting = activate_setting(db, ModelSetting(provider="openrouter", model_id=model_id, encrypted_api_key=encrypted_key))
    return ModelSettingsRead(provider=setting.provider, model_id=setting.model_id, has_api_key=True, ollama_base_url=None, updated_at=setting.updated_at)


@router.get("/providers/ollama/models")
async def ollama_models(base_url: str | None = None) -> list[dict]:
    try:
        return await OllamaProvider(base_url or get_settings().ollama_base_url).list_models()
    except Exception as exc:
        raise provider_error(exc, "Ollama") from exc


@router.post("/providers/ollama/test")
async def test_ollama(payload: ProviderTestRequest) -> dict:
    if not payload.model_id:
        raise HTTPException(status_code=400, detail="Select an installed Ollama model.")
    try:
        return await OllamaProvider(payload.base_url or get_settings().ollama_base_url).test(payload.model_id)
    except Exception as exc:
        raise provider_error(exc, "Ollama") from exc


@router.put("/settings/ollama", response_model=ModelSettingsRead)
async def save_ollama(payload: OllamaSettingsRequest, db: Session = Depends(get_db)) -> ModelSettingsRead:
    provider = OllamaProvider(payload.base_url)
    try:
        models = await provider.list_models()
    except Exception as exc:
        raise provider_error(exc, "Ollama") from exc
    if payload.model_id not in {item.get("name") or item.get("model") for item in models}:
        raise HTTPException(status_code=400, detail="Selected Ollama model is not installed at this address.")
    setting = activate_setting(db, ModelSetting(provider="ollama", model_id=payload.model_id, ollama_base_url=payload.base_url))
    return ModelSettingsRead(provider=setting.provider, model_id=setting.model_id, has_api_key=False, ollama_base_url=setting.ollama_base_url, updated_at=setting.updated_at)
