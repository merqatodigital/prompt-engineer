# Prompt Engineer

> A **first-class Prompt Engineer agent** — an outcome-first AI that turns a one-line
> goal into a production-grade, contract-checked prompt for Lovable, Cursor, v0, or
> Claude. Built on **LangGraph + FastAPI** (backend) and **Next.js** (frontend), with a
> research backbone distilled from the leading prompt-engineering canon.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Stack: LangGraph](https://img.shields.io/badge/Stack-LangGraph-0055ff.svg)](#architecture)
[![Stack: FastAPI + Next.js](https://img.shields.io/badge/Stack-FastAPI%20%2B%20Next.js-000000.svg)](#architecture)

---

## Why this exists

Most "prompt generators" copy a template. This one runs a **multi-stage agent
pipeline** that *validates* and *critiques* its own output before handing it back:

```
validate → generate → validate → (repair) → critique → (revise) → ready
```

Every generated prompt must pass a strict **18-section contract** (intended outcome,
success evidence, authority boundaries, design-grade UI spec, tests, known risks, …)
or the agent loops to fix it. It works **offline with zero API keys** and upgrades to
OpenRouter / Ollama when you connect a model.

---

## Features

- **Outcome-first agent** — you describe the *result*, not the recipe.
- **LangGraph pipeline** — generate → validate → repair → critique → revise, with
  bounded loops and a quality gate (score ≥ 85, no blockers).
- **Research backbone** — every contract lists the applied prompt-engineering
  techniques (role/persona, STCO framing, output contracts, guardrails, ReAct,
  few-shot, …) drawn from the compiled 11-repo canon.
- **Built-in deterministic provider** — full prompts with no API key; real models
  available via OpenRouter or local Ollama.
- **Prompt-injection defense** — retrieved text is wrapped as `authority="untrusted-data"`
  and can never override governing instructions.
- **Streaming UI** — live stage indicator ("Writing the prompt contract…",
  "Independent QA review…") over Server-Sent Events.
- **Prompt library** — create, edit, version, duplicate, **test**, search, filter, delete.
- **Validate-on-test** — the test endpoint runs the same contract checks as generation
  and stores a real `quality_score`.
- **Encrypted key storage** + admin-gated model settings (OpenRouter live catalog,
  Ollama auto-detect).

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/merqatodigital/prompt-engineer.git
cd prompt-engineer

# 2. One-command launcher (creates secrets, installs deps, builds, runs both services)
chmod +x run.sh
./run.sh
# → open http://localhost:3000
```

To run the **end-to-end self-test** instead of the live app:

```bash
SELF_TEST=1 ./run.sh
```

---

## Manual setup (terminal commands)

### Backend (FastAPI + LangGraph)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e '.[test]'

# configure
cp ../.env.example .env            # then edit APP_SECRET + ADMIN_PASSWORD

# run
uvicorn app.main:app --reload --port 8000

# smoke test the API
curl -fsS http://127.0.0.1:8000/api/health
curl -fsS -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  --data '{"request":"build a booking agent that confirms reservations by SMS","artifact_type":"Agent Workflow"}'
```

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev                        # → http://localhost:3000
```

### Run both with Docker

```bash
docker compose up --build
# backend :8000 · frontend :3000
```

### Tests / verification

```bash
# backend
cd backend && pytest -q

# frontend
cd frontend && npm run lint && npm run typecheck && npm run build
```

---

## Architecture

```
prompt-engineer/
├── backend/                     # FastAPI + LangGraph
│   ├── app/
│   │   ├── main.py              # app, CORS, /api/health, routers
│   │   ├── config.py            # settings (env)
│   │   ├── database.py          # SQLAlchemy engine + Base (SQLite)
│   │   ├── models.py            # Prompt, PromptTest, Conversation, GenerationRun
│   │   ├── schemas.py           # Pydantic request/response
│   │   ├── security.py          # Fernet encrypt/decrypt + admin password check
│   │   ├── services.py          # picks provider from active setting
│   │   ├── agents/
│   │   │   ├── state.py         # PromptEngineerState
│   │   │   ├── prompt_engineer.py  # SYSTEM_PROMPT, QA prompt, validate_output_checks
│   │   │   └── graph.py         # the LangGraph state machine (emits stage events)
│   │   ├── data/
│   │   │   └── research.py      # technique + vertical grounding (research backbone)
│   │   ├── providers/
│   │   │   ├── base.py          # ModelProvider Protocol
│   │   │   ├── builtin.py       # deterministic offline generator
│   │   │   ├── openrouter.py    # OpenRouter
│   │   │   ├── ollama.py        # local Ollama
│   │   │   └── prompts_chat.py  # prompts.chat MCP reference search
│   │   └── routes/              # chat.py (SSE), prompts.py, settings.py
│   ├── tests/                   # pytest: api, graph, prompt_contract, prompts_chat
│   └── pyproject.toml
├── frontend/                    # Next.js (App Router, TypeScript)
│   ├── app/                     # page.tsx, prompts/, admin/models/
│   ├── components/              # agent-chat (SSE), model-settings, prompt-table
│   └── lib/api.ts
├── docker-compose.yml           # backend :8000 + frontend :3000
├── run.sh                       # one-command launcher / self-test
├── .env.example
├── .gitignore
├── LICENSE                      # MIT
└── README.md
```

### The generation pipeline (`backend/app/agents/graph.py`)

| Stage | Purpose |
|-------|---------|
| `validate_request` | Reject vague input; ask a clarifying question if needed |
| `generate` | Produce the full prompt contract via the active provider |
| `validate` | Enforce the 18-section contract + word floors + design-grade rules |
| `repair` | If sections are missing, regenerate with explicit fixes |
| `critique` | Independent QA model scores 0–100 against blockers |
| `revise` | Apply QA feedback; loop back to `validate` (capped) |
| `ready` | Hand back the final, validated prompt + quality score |

Stage transitions are streamed to the UI as SSE events, so the user watches the
agent think.

---

## Configuration

Copy `.env.example` → `.env` and set:

| Variable | Meaning |
|----------|---------|
| `APP_SECRET` | Secret used for Fernet key encryption (change in prod) |
| `ADMIN_PASSWORD` | Password that gates model settings |
| `PROMPTS_CHAT_API_KEY` | Optional; public reference search works without it |

Connect a model under **Models** in the UI: OpenRouter (live catalog) or Ollama
(auto-detected on the local network). The built-in provider needs neither.

---

## License

Released under the **MIT License** — see [LICENSE](LICENSE).
Free for commercial and personal use.
