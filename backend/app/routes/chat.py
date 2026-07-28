import asyncio
import json
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..agents.graph import build_prompt_engineer_graph
from ..database import get_db
from ..agents.prompt_engineer import PROJECT_CONTEXT_LIMIT, PROMPT_VERSION, REFERENCE_CONTEXT_LIMIT
from ..models import Conversation, GenerationRun
from ..schemas import ChatRequest, ChatResponse
from ..services import active_setting, provider_from_setting
from ..config import get_settings
from ..providers.prompts_chat import PromptsChatClient, reference_context


router = APIRouter(prefix="/api", tags=["chat"])


async def _run_pipeline(payload: ChatRequest, db: Session):
    """Build provider + graph and run the full prompt-engineer pipeline.

    Yields (stage_event_dict | None, final_result_dict). The first yielded item
    is the final result; intermediate items are stage event dicts. We implement
    this by collecting stage events via the graph's on_event callback.
    """
    provider, provider_name, model_id = provider_from_setting(active_setting(db))
    config = get_settings()
    references: list[dict] = []
    try:
        references = await PromptsChatClient(config.prompts_chat_mcp_url, config.prompts_chat_api_key).search(payload.request, 3)
    except Exception:
        references = []

    async def generate(system_prompt: str, user_prompt: str) -> str:
        return await provider.generate(model_id, system_prompt, user_prompt)

    stage_events: list[dict] = []
    conversation_id = payload.conversation_id or str(uuid4())
    graph = build_prompt_engineer_graph(generate, on_event=lambda ev: stage_events.append(ev))

    result = await graph.ainvoke({
        "request": payload.request,
        "conversation_id": conversation_id,
        "artifact_type": payload.artifact_type,
        "project_context": payload.project_context,
        "reference_context": reference_context(references),
        "references": references,
        "provider": provider_name,
        "model_id": model_id,
    })

    generation_config = {
        "prompt_version": PROMPT_VERSION,
        "temperature": float(getattr(provider, "temperature", 0.2)),
        "max_output_tokens": int(getattr(provider, "max_output_tokens", 4096)),
        "project_context_limit": PROJECT_CONTEXT_LIMIT,
        "reference_context_limit": REFERENCE_CONTEXT_LIMIT,
    }
    content = result.get("generated_prompt")
    db.add(Conversation(
        id=conversation_id,
        provider=provider_name,
        model_id=model_id,
        user_message=payload.request,
        assistant_message=content or result.get("clarification_question") or "",
        validation_status=result.get("status", "unknown"),
    ))
    db.add(GenerationRun(
        conversation_id=conversation_id,
        provider=provider_name,
        model_id=model_id,
        prompt_version=PROMPT_VERSION,
        temperature=generation_config["temperature"],
        max_output_tokens=generation_config["max_output_tokens"],
        context_chars=min(len(payload.project_context or ""), PROJECT_CONTEXT_LIMIT),
        reference_count=len(references),
        quality_score=result.get("quality_score"),
    ))
    db.commit()

    response = ChatResponse(
        conversation_id=conversation_id,
        status=result.get("status", "unknown"),
        provider=provider_name,
        model_id=model_id,
        content=content,
        clarification_question=result.get("clarification_question"),
        validation_errors=result.get("validation_errors", []),
        references=references,
        generation_config=generation_config,
        quality_score=result.get("quality_score"),
        critique_summary=result.get("critique_summary"),
    )
    return stage_events, response


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    _, response = await _run_pipeline(payload, db)
    return response


@router.post("/chat/stream")
async def chat_stream(payload: ChatRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    """Server-sent events: streams stage progress, then the final result as one event."""

    async def event_generator():
        # Run the pipeline; stage events were captured during graph execution.
        # Because the graph runs to completion before we return, we replay the
        # captured stage events first, then emit the final result.
        stage_events, response = await _run_pipeline(payload, db)
        for ev in stage_events:
            yield f"event: stage\ndata: {json.dumps(ev)}\n\n"
            await asyncio.sleep(0)  # yield control so the client receives promptly
        yield f"event: result\ndata: {response.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
