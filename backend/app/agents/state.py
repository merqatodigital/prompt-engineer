from typing_extensions import TypedDict


class PromptEngineerState(TypedDict, total=False):
    request: str
    conversation_id: str
    artifact_type: str
    target_model: str | None
    target_environment: str | None
    project_context: str | None
    reference_context: str | None
    references: list[dict]
    provider: str
    model_id: str
    assumptions: list[str]
    needs_clarification: bool
    clarification_question: str | None
    generated_prompt: str | None
    validation_errors: list[str]
    repair_count: int
    revision_count: int
    critique_completed: bool
    quality_score: int | None
    critique_summary: str | None
    critique_blockers: list[str]
    critique_improvements: list[str]
    status: str
