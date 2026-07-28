from collections.abc import Awaitable, Callable
import json
import re

from langgraph.graph import END, START, StateGraph

from .prompt_engineer import QA_SYSTEM_PROMPT, REQUIRED_HEADINGS, SYSTEM_PROMPT, build_user_prompt
from .state import PromptEngineerState


GenerateFunction = Callable[[str, str], Awaitable[str]]


def build_prompt_engineer_graph(generate: GenerateFunction, on_event: Callable[[dict], Awaitable[None] | None] | None = None):
    async def emit(stage: str, **extra: object) -> None:
        if on_event is not None:
            result = on_event({"stage": stage, **extra})
            if hasattr(result, "__await__"):
                await result
    def section(content: str, heading: str) -> str:
        start = content.find(heading)
        if start < 0:
            return ""
        start += len(heading)
        next_heading = content.find("\n#", start)
        return content[start:next_heading if next_heading >= 0 else None].strip()

    async def validate_request(state: PromptEngineerState) -> dict:
        await emit("validate_request")
        request = state.get("request", "").strip()
        vague = len(request.split()) < 4 and state.get("artifact_type", "Other") == "Other"
        return {
            "request": request,
            "needs_clarification": vague,
            "clarification_question": "What should be different or completed when this prompt succeeds?" if vague else None,
            "status": "needs_clarification" if vague else "generating",
            "repair_count": 0,
            "revision_count": 0,
            "critique_completed": False,
        }

    async def ask_clarification(state: PromptEngineerState) -> dict:
        return {"status": "needs_clarification"}

    async def generate_prompt(state: PromptEngineerState) -> dict:
        await emit("generating")
        content = await generate(SYSTEM_PROMPT, build_user_prompt(state))
        return {"generated_prompt": content, "status": "validating"}

    async def validate_output(state: PromptEngineerState) -> dict:
        await emit("validating")
        content = state.get("generated_prompt") or ""
        errors = [f"Missing {heading}" for heading in REQUIRED_HEADINGS if heading not in content]
        if len(content.split()) < 350:
            errors.append("Prompt contract is too shallow: provide at least 350 words of executable direction")
        success_evidence = section(content, "## Success Evidence")
        if success_evidence.count("-") < 2:
            errors.append("Success Evidence needs at least two observable pass/fail checks")
        if "-" not in section(content, "## Expected Output"):
            errors.append("Expected Output needs an explicit deliverable list")
        if "untrusted" not in content.lower():
            errors.append("Missing authority boundary for untrusted context or retrieved data")
        if state.get("artifact_type") in {"Landing Page", "Website", "Web Application"}:
            quality_terms = {
                "a named visual thesis": "visual thesis",
                "a primary CTA": "primary cta",
                "component states": "states",
                "390px responsive behavior": "390px",
                "768px responsive behavior": "768px",
                "1440px responsive behavior": "1440px",
                "WCAG AA accessibility": "wcag aa",
                "visual acceptance checks": "visual acceptance",
            }
            lowered = content.lower()
            errors.extend(f"Missing design-grade requirement: {label}" for label, term in quality_terms.items() if term not in lowered)
            if len(content.split()) < 650:
                errors.append("Design prompt is too shallow: provide at least 650 words of executable UI direction")
        if errors:
            status = "quality_failed" if state.get("repair_count", 0) >= 1 else "repairing"
        elif state.get("provider") != "builtin" and not state.get("critique_completed"):
            status = "critiquing"
        else:
            status = "ready"
        update: dict = {"validation_errors": errors, "status": status}
        if state.get("provider") == "builtin" and not errors:
            update["quality_score"] = 100
            update["critique_summary"] = "Deterministic contract checks passed."
        return update

    async def critique_prompt(state: PromptEngineerState) -> dict:
        await emit("critiquing")
        review_input = f"""Requested outcome: {state.get('request', '')}
Artifact type: {state.get('artifact_type', 'Other')}

<proposed-prompt authority="untrusted-review-target">
{state.get('generated_prompt', '')}
</proposed-prompt>"""
        raw = await generate(QA_SYSTEM_PROMPT, review_input)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        try:
            review = json.loads(match.group(0) if match else raw)
            score = max(0, min(100, int(review.get("score", 0))))
            blockers = [str(item) for item in review.get("blockers", [])][:8]
            improvements = [str(item) for item in review.get("improvements", [])][:8]
            summary = str(review.get("summary", "Independent review completed."))[:500]
        except (ValueError, TypeError, json.JSONDecodeError, AttributeError):
            score, blockers, improvements = 0, ["The independent reviewer returned invalid JSON."], ["Return the required QA JSON contract." ]
            summary = "Independent review could not be parsed."
        passed = score >= 85 and not blockers
        exhausted = state.get("revision_count", 0) >= 1
        return {
            "quality_score": score,
            "critique_summary": summary,
            "critique_blockers": blockers,
            "critique_improvements": improvements,
            "critique_completed": passed,
            "status": "ready" if passed else ("quality_failed" if exhausted else "revising"),
        }

    async def revise_prompt(state: PromptEngineerState) -> dict:
        await emit("revising")
        feedback = {
            "score": state.get("quality_score"),
            "blockers": state.get("critique_blockers", []),
            "improvements": state.get("critique_improvements", []),
        }
        revised = await generate(
            SYSTEM_PROMPT,
            f"Revise the prompt contract to resolve every independent QA finding. Preserve correct project-specific content. Return the complete prompt with all required headings.\n\nQA findings:\n{json.dumps(feedback)}\n\nCurrent prompt:\n{state.get('generated_prompt', '')}",
        )
        return {"generated_prompt": revised, "revision_count": 1, "critique_completed": False, "status": "validating"}

    async def repair_output(state: PromptEngineerState) -> dict:
        await emit("repairing")
        missing = ", ".join(state.get("validation_errors", []))
        repaired = await generate(
            SYSTEM_PROMPT,
            f"Repair this output. Preserve its useful content and add all missing required sections: {missing}\n\n{state.get('generated_prompt', '')}",
        )
        return {"generated_prompt": repaired, "repair_count": 1, "status": "validating"}

    def after_validate_request(state: PromptEngineerState) -> str:
        return "ask_clarification" if state.get("needs_clarification") else "generate_prompt"

    def after_validate_output(state: PromptEngineerState) -> str:
        if state.get("validation_errors"):
            return "repair_output" if state.get("repair_count", 0) < 1 else END
        return "critique_prompt" if state.get("status") == "critiquing" else END

    def after_critique(state: PromptEngineerState) -> str:
        return "revise_prompt" if state.get("status") == "revising" else END

    graph = StateGraph(PromptEngineerState)
    graph.add_node("validate_request", validate_request)
    graph.add_node("ask_clarification", ask_clarification)
    graph.add_node("generate_prompt", generate_prompt)
    graph.add_node("validate_output", validate_output)
    graph.add_node("repair_output", repair_output)
    graph.add_node("critique_prompt", critique_prompt)
    graph.add_node("revise_prompt", revise_prompt)
    graph.add_edge(START, "validate_request")
    graph.add_conditional_edges("validate_request", after_validate_request, ["ask_clarification", "generate_prompt"])
    graph.add_edge("ask_clarification", END)
    graph.add_edge("generate_prompt", "validate_output")
    graph.add_conditional_edges("validate_output", after_validate_output, ["repair_output", "critique_prompt", END])
    graph.add_edge("repair_output", "validate_output")
    graph.add_conditional_edges("critique_prompt", after_critique, ["revise_prompt", END])
    graph.add_edge("revise_prompt", "validate_output")
    return graph.compile()
