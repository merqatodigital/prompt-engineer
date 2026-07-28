from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def test_health():
    assert client.get("/api/health").json() == {"ok": True}


def test_prompt_crud_and_duplicate():
    created = client.post("/api/prompts", json={
        "name": "Editorial Lodge", "category": "Landing Page", "content": "System prompt",
    })
    assert created.status_code == 201
    prompt = created.json()
    assert prompt["version"] == "v1.0"
    updated = client.patch(f"/api/prompts/{prompt['id']}", json={"status": "Approved"})
    assert updated.json()["version"] == "v1.1"
    duplicated = client.post(f"/api/prompts/{prompt['id']}/duplicate")
    assert duplicated.status_code == 201
    assert duplicated.json()["status"] == "Draft"
    assert len(client.get("/api/prompts", params={"search": "Editorial"}).json()) == 2
    assert client.delete(f"/api/prompts/{prompt['id']}").status_code == 204


def test_admin_is_protected():
    response = client.get("/api/providers/openrouter/models")
    assert response.status_code == 401


def test_chat_works_without_provider_configuration(monkeypatch):
    async def no_references(*_args, **_kwargs):
        return []

    monkeypatch.setattr("app.routes.chat.PromptsChatClient.search", no_references)
    response = client.post("/api/chat", json={
        "request": "Create a distinctive direct-booking landing page for a small island resort",
        "artifact_type": "Landing Page",
    })
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "ready"
    assert result["provider"] == "builtin"
    assert result["model_id"] == "prompt-engineer-starter-v1"
    assert "## Creative Contract" in result["content"]
    assert "## UI Specification" in result["content"]
    assert "Resort Direct-Booking Experience" in result["content"]
    assert "### Visual acceptance checks" in result["content"]
    assert "390px" in result["content"] and "768px" in result["content"] and "1440px" in result["content"]
    assert "WCAG AA" in result["content"]
    assert result["references"] == []
    assert result["quality_score"] == 100
    assert result["generation_config"]["prompt_version"] == "v1.2.0"
    assert result["generation_config"]["temperature"] == 0.0
    assert result["generation_config"]["max_output_tokens"] == 4096
