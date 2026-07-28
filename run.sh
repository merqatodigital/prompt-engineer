#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
export npm_config_cache="$ROOT/.npm-cache"

for command_name in python3 npm curl; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    exit 1
  fi
done

if [[ ! -f .env ]]; then
  app_secret="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
  admin_password="$(python3 -c 'import secrets; print(secrets.token_urlsafe(14))')"
  cp .env.example .env
  python3 - "$app_secret" "$admin_password" <<'PY'
from pathlib import Path
import sys

path = Path(".env")
text = path.read_text()
text = text.replace("APP_SECRET=replace-with-a-long-random-value", f"APP_SECRET={sys.argv[1]}")
text = text.replace("ADMIN_PASSWORD=replace-me", f"ADMIN_PASSWORD={sys.argv[2]}")
path.write_text(text)
PY
  chmod 600 .env
  echo "Created secure local configuration."
  echo "Admin password: $admin_password"
  echo "It is stored in $ROOT/.env"
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "Creating Python environment..."
  python3 -m venv --clear --copies .venv
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "Python created an incomplete virtual environment at $ROOT/.venv" >&2
  exit 1
fi

if [[ "${SKIP_INSTALL:-0}" != "1" ]]; then
  echo "Installing backend dependencies..."
  .venv/bin/python -m pip install -q -e backend
  echo "Installing frontend dependencies..."
  npm --prefix frontend --cache "$ROOT/.npm-cache" ci --no-audit --no-fund
fi

if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  echo "Building production frontend..."
  npm --prefix frontend --cache "$ROOT/.npm-cache" run build
fi

api_log="$ROOT/backend.log"
web_log="$ROOT/frontend.log"

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  [[ -n "${api_pid:-}" ]] && kill "$api_pid" 2>/dev/null || true
  [[ -n "${web_pid:-}" ]] && kill "$web_pid" 2>/dev/null || true
  wait "${api_pid:-}" "${web_pid:-}" 2>/dev/null || true
  exit "$status"
}
trap cleanup EXIT INT TERM

echo "Starting Prompt Engineer..."
.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 >"$api_log" 2>&1 &
api_pid=$!
npm --prefix frontend --cache "$ROOT/.npm-cache" run start -- --hostname 127.0.0.1 --port 3000 >"$web_log" 2>&1 &
web_pid=$!

ready=0
for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/api/health >/dev/null 2>&1 && curl -fsS http://127.0.0.1:3000/ >/dev/null 2>&1; then
    ready=1
    break
  fi
  if ! kill -0 "$api_pid" 2>/dev/null || ! kill -0 "$web_pid" 2>/dev/null; then
    break
  fi
  sleep 1
done

if [[ "$ready" != "1" ]]; then
  echo "Prompt Engineer did not start correctly." >&2
  echo "Backend log:" >&2
  tail -40 "$api_log" >&2 || true
  echo "Frontend log:" >&2
  tail -40 "$web_log" >&2 || true
  exit 1
fi

echo
echo "Prompt Engineer is ready: http://localhost:3000"
echo "Model settings: http://localhost:3000/admin/models"

if [[ "${SELF_TEST:-0}" == "1" ]]; then
  smoke_file="$(mktemp)"
  curl -fsS -X POST http://127.0.0.1:8000/api/chat \
    -H 'Content-Type: application/json' \
    --data '{"request":"make me a professional direct-booking website for my micro resort","artifact_type":"Landing Page"}' >"$smoke_file"
  .venv/bin/python - "$smoke_file" <<'PY'
import json
import sys

result = json.load(open(sys.argv[1]))
content = result.get("content") or ""
required = [
    "Resort Direct-Booking Experience",
    "Arrival Journal",
    "### Page architecture",
    "### Responsive transformations",
    "### Visual acceptance checks",
    "390px",
    "768px",
    "1440px",
    "WCAG AA",
]
assert result.get("status") == "ready", result.get("validation_errors")
assert result.get("quality_score") == 100, "Offline contract QA did not pass"
assert result.get("generation_config", {}).get("prompt_version") == "v1.2.0", "Unexpected prompt contract version"
assert all(marker in content for marker in required), "Generated prompt missed a design-quality marker"
assert len(content.split()) >= 650, "Generated prompt was too shallow"
print(f"Agent generation passed ({len(content.split())} words, design QA ready).")
PY
  rm -f "$smoke_file"
  for route in / /prompts /admin/models; do
    curl -fsS "http://127.0.0.1:3000$route" >/dev/null
  done
  echo "UI routes passed (landing page, prompt library, model settings)."
  echo "SELF TEST PASSED"
  exit 0
fi

echo "Press Ctrl+C to stop both services."
wait "$api_pid" "$web_pid"
