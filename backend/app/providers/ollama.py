import time

import httpx


class OllamaProvider:
    temperature = 0.2
    max_output_tokens = 4096

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url.rstrip("/")

    async def list_models(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
        return response.json().get("models", [])

    async def generate(self, model_id: str, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": model_id,
            "stream": False,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "options": {"temperature": self.temperature, "num_predict": self.max_output_tokens},
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
        return response.json()["message"]["content"]

    async def test(self, model_id: str) -> dict:
        started = time.perf_counter()
        result = await self.generate(model_id, "Reply with exactly READY.", "Connection test")
        return {"ok": True, "latency_ms": round((time.perf_counter() - started) * 1000), "response": result[:100]}
