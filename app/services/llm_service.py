import httpx
import json
import asyncio
from app.config import settings
from app.utils.circuit_breaker import llm_circuit_breaker, llm_queue
from typing import Optional


MOCK_COMMENTS = [
    {"content": "Great post! I totally agree with your perspective on this.", "translation": "好帖！我完全同意你的观点。", "suggestion": "Consider adding a personal anecdote to make it more engaging."},
    {"content": "This is really insightful. Thanks for sharing your thoughts!", "translation": "这真的很有见地。谢谢分享你的想法！", "suggestion": "You could add a question to encourage more interaction."},
    {"content": "I had a similar experience. Thanks for bringing this up!", "translation": "我有类似的经历。谢谢你提出这个话题！", "suggestion": "Keep it concise - Reddit users love short, punchy comments."},
]


class LLMService:
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.api_base = settings.deepseek_api_base
        self.model = settings.deepseek_model
        self.timeout = settings.deepseek_timeout

    async def generate_comments(self, post_content: str, persona_description: Optional[str]) -> list[dict]:
        if not self.api_key:
            print("[LLM] No API key, using mock comments")
            return self._ensure_translations(MOCK_COMMENTS)

        if not llm_circuit_breaker.can_execute():
            print("[LLM] Circuit breaker open, using mock comments")
            return self._ensure_translations(MOCK_COMMENTS)

        async with llm_queue:
            try:
                result = await self._call_deepseek(post_content, persona_description)
                llm_circuit_breaker.record_success()
                return self._ensure_translations(result)
            except Exception as e:
                print(f"[LLM] Error: {e}")
                llm_circuit_breaker.record_failure()
                return self._ensure_translations(MOCK_COMMENTS)

    def _ensure_translations(self, comments: list) -> list:
        for c in comments:
            if "translation" not in c or not c["translation"]:
                c["translation"] = "翻译暂不可用"
        return comments

    async def _call_deepseek(self, post_content: str, persona_description: Optional[str]) -> list[dict]:
        if persona_description:
            system_prompt = f"You are a Reddit user with the following persona: {persona_description}. You MUST respond in English only."
            user_prompt = f"""Generate EXACTLY 3 natural Reddit comments in English for the following post. You MUST include Chinese translations for EVERY comment.

For EACH comment, provide:
- content: the English comment
- translation: the Chinese translation  
- suggestion: a usage tip

Output format - JSON array with EXACTLY this structure:
[{{"content": "English comment here", "translation": "中文翻译在这里", "suggestion": "tip here"}}, ...]

Post: {post_content}"""
        else:
            system_prompt = "You are a friendly Reddit user who writes natural, authentic comments. You MUST respond in English only."
            user_prompt = f"""Generate EXACTLY 3 natural Reddit comments in English for the following post. You MUST include Chinese translations for EVERY comment.

For EACH comment, provide:
- content: the English comment
- translation: the Chinese translation
- suggestion: a usage tip

Output format - JSON array with EXACTLY this structure:
[{{"content": "English comment here", "translation": "中文翻译在这里", "suggestion": "tip here"}}, ...]

Post: {post_content}"""

        print(f"[LLM] Calling DeepSeek model={self.model}")
        print(f"[LLM] API Base: {self.api_base}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key[:20]}...",
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
            print(f"[LLM] Response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print(f"[LLM] Raw response: {content[:500]}...")
            comments = json.loads(content)
            for c in comments:
                if "translation" not in c or not c["translation"]:
                    c["translation"] = "翻译暂不可用"
            return comments


llm_service = LLMService()
