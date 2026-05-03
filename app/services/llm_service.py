import httpx
import json
import asyncio
from app.config import settings
from app.utils.circuit_breaker import llm_circuit_breaker, llm_queue
from typing import Optional


MOCK_COMMENTS = [
    {"content": "Great post! I totally agree with your perspective on this.", "suggestion": "Consider adding a personal anecdote to make it more engaging."},
    {"content": "This is really insightful. Thanks for sharing your thoughts!", "suggestion": "You could add a question to encourage more interaction."},
    {"content": "I had a similar experience. Thanks for bringing this up!", "suggestion": "Keep it concise - Reddit users love short, punchy comments."},
]


class LLMService:
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.api_base = settings.deepseek_api_base
        self.model = settings.deepseek_model
        self.timeout = settings.deepseek_timeout

    async def generate_comments(self, post_content: str, persona_description: Optional[str]) -> list[dict]:
        if not self.api_key:
            return MOCK_COMMENTS

        if not llm_circuit_breaker.can_execute():
            return MOCK_COMMENTS

        async with llm_queue:
            try:
                result = await self._call_deepseek(post_content, persona_description)
                llm_circuit_breaker.record_success()
                return result
            except Exception as e:
                llm_circuit_breaker.record_failure()
                return MOCK_COMMENTS

    async def _call_deepseek(self, post_content: str, persona_description: Optional[str]) -> list[dict]:
        if persona_description:
            system_prompt = f"You are a Reddit user with the following persona: {persona_description}. You MUST respond in English only."
            user_prompt = f"Generate 3 natural Reddit comments in English for the following post. Reply ONLY with valid JSON array like [{{\"content\": \"comment1\", \"suggestion\": \"tip1\"}}, ...]:\n\n{post_content}"
        else:
            system_prompt = "You are a friendly Reddit user who writes natural, authentic comments. You MUST respond in English only."
            user_prompt = f"Generate 3 natural, authentic English Reddit comments for the following post. Reply ONLY with valid JSON array like [{{\"content\": \"comment1\", \"suggestion\": \"tip1\"}}, ...]:\n\n{post_content}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.8,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            comments = json.loads(content)
            return comments


llm_service = LLMService()
