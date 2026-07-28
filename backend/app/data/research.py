"""Research backbone for the offline (builtin) Prompt Engineer.

Distilled, accurate grounding drawn from the 11-repo prompt-engineering canon
compiled for this project (promptslab/Awesome-Prompt-Engineering, dair-ai/
Prompt-Engineering-Guide, f/awesome-chatgpt-prompts, LouisShark/chatgpt_system_
prompt, anthropics/prompt-library, openai/codex, getcursor/cursor, anthropics/
claude-code, langchain-ai/langsmith-sdk, prompt-hub/prompt-hub, elevenlabs/
elevenlabs-docs). These are technique names + one-line DO/DON'T guidance, not
copy-pasted text. The builtin provider uses them to enrich the deterministic
contract so it is strong for every artifact type, not only hospitality.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Technique:
    name: str
    guidance: str  # concrete DO/DON'T the offline generator can apply


# Core techniques (well-established in the literature; phrased as applied rules).
TECHNIQUES: list[Technique] = [
    Technique("Role / Persona", "Assign one narrow expert role with a bounded mandate; do not pile on conflicting personas."),
    Technique("Task framing (STCO)", "State System/Task/Context/Output explicitly; the Output section must list concrete deliverables."),
    Technique("Zero / Few-shot", "Show 1-3 real exemplars of the desired output shape instead of describing it abstractly."),
    Technique("Chain-of-Thought", "For reasoning tasks, ask for step-by-step working before the final answer; forbid skipping steps."),
    Technique("Delimiters", "Wrap untrusted or structured input in explicit tags (e.g. <task>, <reference>) and name its authority."),
    Technique("Output contracts", "Pin the response format (Markdown headings, JSON schema, or table) so it is machine-checkable."),
    Technique("Constraints & guardrails", "List hard MUST / MUST NOT rules (no fabrication, no secrets in client code, authority order)."),
    Technique("Self-consistency", "For high-stakes output, generate, critique against fixed criteria, then revise once."),
    Technique("Least-to-most", "Break a large build into ordered sub-tasks; finish each before naming the next."),
    Technique("ReAct (Reason+Act)", "For agent workflows, alternate thought and tool call; define stops, retries, and approvals."),
    Technique("Negative prompting", "State what the output must NOT be (generic template, lorem ipsum, fake claims)."),
    Technique("Meta-prompting", "Treat the prompt itself as the artifact to be specified, versioned, and tested."),
    Technique("Structured evaluation", "Define observable pass/fail checks up front; grade on evidence, not vibes."),
    Technique("Context budgeting", "Cap project context and references; discard irrelevant context rather than appending it."),
]


# Vertical/domain grounding: each maps artifact types to the techniques that matter most.
VERTICALS: dict[str, list[str]] = {
    "Landing Page": ["Role / Persona", "Output contracts", "Negative prompting", "Constraints & guardrails", "Structured evaluation"],
    "Website": ["Role / Persona", "Output contracts", "Negative prompting", "Constraints & guardrails", "Structured evaluation"],
    "Web Application": ["Role / Persona", "Task framing (STCO)", "Output contracts", "ReAct (Reason+Act)", "Constraints & guardrails"],
    "Agent Workflow": ["Role / Persona", "Task framing (STCO)", "ReAct (Reason+Act)", "Delimiters", "Output contracts", "Structured evaluation"],
    "Improve Existing Prompt": ["Meta-prompting", "Self-consistency", "Output contracts", "Constraints & guardrails"],
    "Other": ["Task framing (STCO)", "Output contracts", "Constraints & guardrails", "Structured evaluation"],
}


def techniques_for(artifact_type: str) -> list[Technique]:
    """Return the techniques most relevant to an artifact type, then the rest."""
    names = VERTICALS.get(artifact_type, VERTICALS["Other"])
    ranked = [t for t in TECHNIQUES if t.name in names]
    ranked += [t for t in TECHNIQUES if t.name not in names]
    return ranked


def technique_bullets(artifact_type: str, limit: int = 6) -> str:
    return "\n".join(f"- {t.name}: {t.guidance}" for t in techniques_for(artifact_type)[:limit])


# Non-hospitality creative direction so the builtin provider is not resort-only.
CREATIVE_BY_VERTICAL: dict[str, str] = {
    "Web Application": (
        "- Visual thesis: Surface the product's working mechanism immediately—let the interface demonstrate the "
        "outcome rather than describe it. Avoid dashboard-of-cards as the default.\n"
        "- Distinctive mechanism: one dominant primary action per viewport; progressive disclosure for depth.\n"
        "- Typography: two families max; fluid sizes with clamp(); 65-75 char measure.\n"
        "- Motion: 160-280ms orientation/feedback only; honor prefers-reduced-motion."
    ),
    "Agent Workflow": (
        "- Visual thesis: make the agent's reasoning legible—show thought, tool call, and result as a visible sequence.\n"
        "- Distinctive mechanism: a persistent run timeline with explicit approval/stop controls; never hide failure.\n"
        "- Typography: monospace for tool I/O, readable sans for narrative; clear status hierarchy.\n"
        "- Motion: restrained; surface state changes, not decoration."
    ),
    "Improve Existing Prompt": (
        "- Visual thesis: preserve the original intent; show the delta (what changed and why) as the unit of value.\n"
        "- Distinctive mechanism: side-by-side before/after with the removed ambiguity called out.\n"
        "- Typography: call out added constraints and output-contract changes in a diff-like view.\n"
        "- Motion: none required; clarity over flourish."
    ),
}


def creative_direction(artifact_type: str, outcome: str) -> str:
    """Return a vertical-appropriate creative direction, or the generic strong one."""
    if any(w in outcome.lower() for w in ("resort", "hotel", "cabin", "villa", "stay", "lodge")):
        return ""  # builtin already specializes hospitality inline
    return CREATIVE_BY_VERTICAL.get(artifact_type, CREATIVE_BY_VERTICAL["Web Application"])
