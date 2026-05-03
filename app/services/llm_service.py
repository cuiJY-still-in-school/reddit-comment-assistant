import httpx
import json
import asyncio
from app.config import settings
from app.utils.circuit_breaker import llm_circuit_breaker, llm_queue
from typing import Optional


MOCK_COMMENTS = [
    {"content": "Great post! I totally agree with your perspective on this.", "translation": "好帖！我完全同意你的观点。", "suggestion": "Consider adding a personal anecdote."},
    {"content": "This is really insightful. Thanks for sharing!", "translation": "这真的很有见地。谢谢分享！", "suggestion": "Add a question to encourage interaction."},
    {"content": "I had a similar experience. Thanks for bringing this up!", "translation": "我有类似的经历。", "suggestion": "Keep it concise."},
]


class LLMService:
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.api_base = settings.deepseek_api_base
        self.model = settings.deepseek_model
        self.timeout = settings.deepseek_timeout

    async def generate_comments(self, post_content: str, persona_description: Optional[str]) -> list[dict]:
        if not self.api_key:
            print("[LLM] No API key, using mock")
            return MOCK_COMMENTS

        try:
            result = await self._call_deepseek(post_content, persona_description)
            print(f"[LLM] DeepSeek returned {len(result)} comments")
            for i, c in enumerate(result):
                print(f"[LLM]   [{i}] translation={c.get('translation', 'MISSING')[:30] if c.get('translation') else 'MISSING'}...")
            llm_circuit_breaker.record_success()
            return result
        except Exception as e:
            print(f"[LLM] Error: {e}")
            llm_circuit_breaker.record_failure()
            return MOCK_COMMENTS

    async def _call_deepseek(self, post_content: str, persona_description: Optional[str]) -> list[dict]:
        system_msg = "You are a Reddit comment generator. Generate comments in English. For each comment, provide: content (English), translation (Chinese), suggestion (English)."
        user_msg = f"""Generate 3 Reddit comments. Each comment must have:
- "content": English text
- "translation": Chinese translation of content
- "suggestion": English tip

Output as JSON array. No markdown. No code blocks. Just plain JSON.

Post: {post_content}"""

        print(f"[LLM] Calling {self.model} at {self.api_base}")
        print(f"[LLM] API key prefix: {self.api_key[:15]}...")

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
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                    ],
                    "temperature": 0.8,
                },
            )
            print(f"[LLM] Response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            raw = data["choices"][0]["message"]["content"]
            print(f"[LLM] Raw response length: {len(raw)}")
            print(f"[LLM] Raw response preview: {raw[:150]}...")
            raw = raw.strip().strip("```").strip("json").strip()
            result = json.loads(raw)
            return result


llm_service = LLMService()