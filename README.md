# Prompt Engineer

A focused Prompt Engineer agent built with LangGraph, FastAPI, Next.js, OpenRouter, Ollama, and optional prompts.chat reference search.

## Run the product

```bash
chmod +x run.sh
./run.sh
```

Open `http://localhost:3000`. On first run, the launcher creates secure local configuration, prints the generated administrator password, installs dependencies, builds the production frontend, and starts both services. Press `Ctrl+C` to stop everything cleanly.

To run the complete product self-test instead:

```bash
SELF_TEST=1 ./run.sh
```

This starts the production services, submits a deliberately weak resort request, requires a design-grade validated result, verifies all application routes, and then shuts down.

## What works

- Outcome-first agent for landing pages, websites, web applications, agent workflows, and prompt improvement
- Built-in deterministic provider, so the agent works before an API key or local model is configured
- Automatic prompts.chat pattern search with fail-open behavior and visible source references
- Retrieved prompt text is bounded and treated as untrusted data, never as governing instructions
- Brand-specific Creative Contracts and anti-template design rules
- Design-grade validation for visual thesis, page hierarchy, UI states, responsive transformations, WCAG AA, performance, and visual acceptance evidence
- Authority-separated prompt assembly for governing instructions, user tasks, durable facts, and untrusted retrieved data
- Bounded context and durable generation records with prompt version, model, temperature, token limit, and reference count
- Multi-stage agent workflow: generate, deterministic contract validation, independent model critique, targeted revision, second critique, and save gating
- One validation and repair pass through LangGraph
- Prompt library with create, edit, version, duplicate, test, search, filter, and delete
- OpenRouter live model catalog with free-model filtering
- Ollama detection for models installed on the same machine or reachable server
- Encrypted OpenRouter key storage and administrator-protected settings

## Manual setup

1. Copy `.env.example` to `.env` and change `APP_SECRET` and `ADMIN_PASSWORD`.
2. Backend:

   ```bash
   cd backend
   python -m venv .venv
   .venv/bin/pip install -e '.[test]'
   .venv/bin/uvicorn app.main:app --reload --port 8000
   ```

3. Frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. Open `http://localhost:3000`. The built-in starter works immediately; configure OpenRouter or Ollama under **Models** for model-driven generation.

`PROMPTS_CHAT_API_KEY` is optional. Public reference search works without it. If prompts.chat is unavailable, generation continues without references.

## Verification

```bash
cd backend && pytest -q
cd frontend && npm run lint && npm run typecheck && npm run build
```

Ollama detection works only when the backend can reach the configured Ollama address. A remote cloud backend cannot inspect a user's personal computer without a local companion connection.
