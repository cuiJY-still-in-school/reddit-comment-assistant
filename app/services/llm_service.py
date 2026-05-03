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


def contains_chinese(text: str) -> bool:
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False


class LLMService:
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.api_base = settings.deepseek_api_base
        self.model = settings.deepseek_model
        self.timeout = settings.deepseek_timeout

    async def generate_comments(self, post_content: str, persona_description: Optional[str]) -> list[dict]:
        if not self.api_key:
            print("[LLM] No API key, using mock comments")
            return MOCK_COMMENTS

        if not llm_circuit_breaker.can_execute():
            print("[LLM] Circuit breaker open, using mock comments")
            return MOCK_COMMENTS

        async with llm_queue:
            try:
                result = await self._call_deepseek(post_content, persona_description)
                llm_circuit_breaker.record_success()
                return self._ensure_translations(result)
            except Exception as e:
                print(f"[LLM] Error: {e}")
                llm_circuit_breaker.record_failure()
                return MOCK_COMMENTS

    def _ensure_translations(self, comments: list) -> list:
        for c in comments:
            if "translation" not in c or not c["translation"]:
                c["translation"] = "翻译暂不可用"
        return comments

    async def _call_deepseek(self, post_content: str, persona_description: Optional[str]) -> list[dict]:
        system_prompt = """You are a Reddit comment generator.
CRITICAL RULE: The 'content' field MUST be in ENGLISH only. Never write Chinese, Korean, Japanese, or any non-English text in the content field.
The 'translation' field MUST contain Chinese translation of the content.
The 'suggestion' field MUST be in English.

Output ONLY valid JSON array with this exact structure:
[{"content":"ENGLISH TEXT ONLY","translation":"中文翻译","suggestion":"English tip"}, ...]"""

        user_prompt = f"""Generate 3 Reddit comments for this post.

RULES:
- 'content' field: MUST be in English only (no Chinese, no other languages)
- 'translation' field: MUST be Chinese translation of the content field
- 'suggestion' field: MUST be in English

Output format (MUST be valid JSON array, no markdown, no code blocks):
[{{"content":"Your English comment here","translation":"中文翻译在这里","suggestion":"Your English tip here"}}, ...]

Post: {post_content}"""

        print(f"[LLM] Calling model={self.model}")

        try:
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
                print(f"[LLM] Response status: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                print(f"[LLM] Raw response: {content[:200]}...")

                content = content.strip()
                content = content.replace("```json", "").replace("```", "").strip()

                comments = json.loads(content)

                for c in comments:
                    if contains_chinese(c.get("content", "")):
                        print(f"[LLM] WARNING: content contains Chinese: {c.get('content')[:50]}")
                        c["content"] = "This is a test comment."

                return comments

        except Exception as e:
            print(f"[LLM] API call failed: {e}")
            raise


llm_service = LLMService()