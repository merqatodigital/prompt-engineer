import time

import httpx


class OpenRouterProvider:
    temperature = 0.2
    max_output_tokens = 4096

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def generate(self, model_id: str, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": model_id,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_output_tokens,
        }
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers=self.headers, json=payload)
            response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def list_models(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.base_url}/models", headers=self.headers)
            response.raise_for_status()
        models = []
        for item in response.json().get("data", []):
            pricing = item.get("pricing") or {}
            zero = all(str(pricing.get(key, "1")) in {"0", "0.0"} for key in ("prompt", "completion", "request"))
            model_id = item.get("id", "")
            models.append({
                "id": model_id,
                "name": item.get("name", model_id),
                "context_length": item.get("context_length"),
                "pricing": pricing,
                "is_free": zero or model_id.endswith(":free") or model_id == "openrouter/free",
                "supported_parameters": item.get("supported_parameters", []),
                "architecture": item.get("architecture", {}),
            })
        models.sort(key=lambda model: (not model["is_free"], model["name"].lower()))
        return models

    async def test(self, model_id: str) -> dict:
        started = time.perf_counter()
        result = await self.generate(model_id, "Reply with exactly READY.", "Connection test")
        return {"ok": True, "latency_ms": round((time.perf_counter() - started) * 1000), "response": result[:100]}
