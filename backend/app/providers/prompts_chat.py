import json
from typing import Any

import httpx


class PromptsChatClient:
    def __init__(self, endpoint: str, api_key: str = "", transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.transport = transport

    async def search(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.api_key:
            headers["PROMPTS_API_KEY"] = self.api_key
        payload = {
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "search_prompts", "arguments": {"query": query[:300], "limit": min(limit, 5), "type": "TEXT"}},
        }
        timeout = httpx.Timeout(4.0, connect=2.0)
        async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
            response = await client.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
        body = self._response_json(response)
        blocks = body.get("result", {}).get("content", [])
        text = next((block.get("text") for block in blocks if block.get("type") == "text"), "{}")
        parsed = json.loads(text)
        prompts = parsed.get("prompts", [])
        return [{
            "id": item.get("id"), "slug": item.get("slug"), "title": item.get("title", "Untitled"),
            "description": item.get("description"), "preview": item.get("contentPreview", "")[:300],
            "author": item.get("author"), "category": item.get("category"), "tags": item.get("tags", []),
            "url": f"https://prompts.chat/prompts/{item.get('slug') or item.get('id')}",
        } for item in prompts[:limit]]

    @staticmethod
    def _response_json(response: httpx.Response) -> dict:
        content_type = response.headers.get("content-type", "")
        if "text/event-stream" not in content_type:
            return response.json()
        for line in response.text.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        return {}


def reference_context(references: list[dict]) -> str:
    if not references:
        return "No references found."
    return "\n".join(
        f"- {item['title']}: {item.get('description') or ''} | Preview: {item.get('preview') or ''}"
        for item in references
    )
