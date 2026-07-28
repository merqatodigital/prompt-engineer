from typing import Protocol


class ModelProvider(Protocol):
    async def generate(self, model_id: str, system_prompt: str, user_prompt: str) -> str: ...

    async def test(self, model_id: str) -> dict: ...

