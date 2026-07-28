import asyncio

from app.agents.graph import build_prompt_engineer_graph
from app.agents.prompt_engineer import REQUIRED_HEADINGS


def design_grade_content() -> str:
    parts = []
    for heading in REQUIRED_HEADINGS:
        parts.append(heading)
        if heading == "## Success Evidence":
            parts.append("- Primary journey passes its observable completion check.\n- Failure behavior is verified without fabricated facts.")
        elif heading == "## Expected Output":
            parts.append("- Complete executable deliverables with an explicit output contract.")
        else:
            parts.append("Executable project direction with untrusted context kept outside the instruction boundary.")
    requirements = " visual thesis primary CTA states 390px 768px 1440px WCAG AA visual acceptance "
    return "\n".join(parts) + requirements + (" executable direction" * 700)


def test_graph_returns_valid_prompt_without_repair():
    content = design_grade_content()

    async def generate(_: str, __: str) -> str:
        return content

    result = asyncio.run(build_prompt_engineer_graph(generate).ainvoke({
        "request": "Build a distinctive editorial resort landing page",
        "artifact_type": "Landing Page",
        "provider": "builtin",
    }))
    assert result["status"] == "ready"
    assert result["validation_errors"] == []


def test_graph_repairs_once():
    calls = 0

    async def generate(_: str, __: str) -> str:
        nonlocal calls
        calls += 1
        return "Incomplete" if calls == 1 else design_grade_content()

    result = asyncio.run(build_prompt_engineer_graph(generate).ainvoke({
        "request": "Build a useful prompt engineering web application",
        "artifact_type": "Web Application",
        "provider": "builtin",
    }))
    assert result["status"] == "ready"
    assert calls == 2


def test_graph_rejects_shallow_visual_prompt_after_repair():
    calls = 0

    async def generate(_: str, __: str) -> str:
        nonlocal calls
        calls += 1
        return "\n".join(REQUIRED_HEADINGS)

    result = asyncio.run(build_prompt_engineer_graph(generate).ainvoke({
        "request": "Build a resort landing page",
        "artifact_type": "Landing Page",
        "provider": "builtin",
    }))
    assert result["status"] == "quality_failed"
    assert calls == 2
    assert any("too shallow" in error for error in result["validation_errors"])


def test_connected_model_is_criticized_revised_and_rechecked():
    calls = 0

    async def generate(_: str, __: str) -> str:
        nonlocal calls
        calls += 1
        if calls in {1, 3}:
            return design_grade_content()
        if calls == 2:
            return '{"score": 72, "summary": "Needs stronger evidence.", "blockers": ["Acceptance evidence is vague."], "improvements": ["Make verification observable."]}'
        return '{"score": 93, "summary": "Production contract passed.", "blockers": [], "improvements": []}'

    result = asyncio.run(build_prompt_engineer_graph(generate).ainvoke({
        "request": "Build a distinctive resort landing page",
        "artifact_type": "Landing Page",
        "provider": "openrouter",
    }))
    assert result["status"] == "ready"
    assert result["quality_score"] == 93
    assert result["revision_count"] == 1
    assert calls == 4
