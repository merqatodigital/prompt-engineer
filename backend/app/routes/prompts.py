import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Prompt, PromptTest
from ..schemas import PromptCreate, PromptRead, PromptTestRead, PromptTestRequest, PromptUpdate
from ..agents.prompt_engineer import validate_output_checks
from ..services import active_setting, provider_from_setting


router = APIRouter(prefix="/api/prompts", tags=["prompts"])


def get_prompt_or_404(db: Session, prompt_id: str) -> Prompt:
    prompt = db.get(Prompt, prompt_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


def increment_version(version: str) -> str:
    match = re.fullmatch(r"v(\d+)\.(\d+)", version)
    if not match:
        return "v1.1"
    return f"v{match.group(1)}.{int(match.group(2)) + 1}"


@router.get("", response_model=list[PromptRead])
def list_prompts(
    search: str | None = None,
    category: str | None = None,
    prompt_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[Prompt]:
    query = select(Prompt).order_by(Prompt.updated_at.desc())
    if search:
        query = query.where(Prompt.name.ilike(f"%{search}%"))
    if category:
        query = query.where(Prompt.category == category)
    if prompt_status:
        query = query.where(Prompt.status == prompt_status)
    return list(db.scalars(query))


@router.post("", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
def create_prompt(payload: PromptCreate, db: Session = Depends(get_db)) -> Prompt:
    prompt = Prompt(**payload.model_dump())
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.get("/{prompt_id}", response_model=PromptRead)
def get_prompt(prompt_id: str, db: Session = Depends(get_db)) -> Prompt:
    return get_prompt_or_404(db, prompt_id)


@router.patch("/{prompt_id}", response_model=PromptRead)
def update_prompt(prompt_id: str, payload: PromptUpdate, db: Session = Depends(get_db)) -> Prompt:
    prompt = get_prompt_or_404(db, prompt_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(prompt, field, value)
    prompt.version = increment_version(prompt.version)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.post("/{prompt_id}/duplicate", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
def duplicate_prompt(prompt_id: str, db: Session = Depends(get_db)) -> Prompt:
    source = get_prompt_or_404(db, prompt_id)
    duplicate = Prompt(
        name=f"{source.name} Copy", category=source.category, version="v1.0", content=source.content,
        project_context=source.project_context, target_model=source.target_model,
        target_environment=source.target_environment, model_id=source.model_id, status="Draft",
    )
    db.add(duplicate)
    db.commit()
    db.refresh(duplicate)
    return duplicate


@router.post("/{prompt_id}/test", response_model=PromptTestRead)
async def test_prompt(prompt_id: str, payload: PromptTestRequest, db: Session = Depends(get_db)) -> PromptTest:
    prompt = get_prompt_or_404(db, prompt_id)
    provider, _, model_id = provider_from_setting(active_setting(db))
    output = await provider.generate(model_id, prompt.content, payload.test_input)

    # Run the same contract validation used by the generation pipeline so "test"
    # proves the prompt produces a well-formed result, not just any text.
    artifact_type = prompt.category
    checks = validate_output_checks(output, artifact_type)
    # Cloud/Ollama output is graded against the deterministic contract checklist;
    # the builtin provider is itself the contract, so a clean output scores 100.
    is_builtin = getattr(provider, "temperature", None) == 0.0 and not getattr(provider, "model_id", None)
    score = 100 if not checks else (None if is_builtin else max(0, 100 - min(60, 12 * len(checks))))
    record = PromptTest(
        prompt_id=prompt.id, model_id=model_id, test_input=payload.test_input,
        model_output=output, passed=bool(output.strip()) and not checks, quality_score=score,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(prompt_id: str, db: Session = Depends(get_db)) -> None:
    prompt = get_prompt_or_404(db, prompt_id)
    db.delete(prompt)
    db.commit()

