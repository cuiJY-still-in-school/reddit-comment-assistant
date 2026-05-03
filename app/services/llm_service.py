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
            if not c.get("translation"):
                c["translation"] = self._simple_translate(c.get("content", ""))
        return comments

    def _simple_translate(self, text: str) -> str:
        translations = {
            "great": "太棒了", "good": "好的", "nice": "不错",
            "thanks": "谢谢", "thank": "谢谢", "appreciate": "感谢",
            "interesting": "有趣", "insightful": "有见地",
            "agree": "同意", "totally": "完全", "really": "真的",
            "post": "帖", "comment": "评论", "share": "分享",
            "think": "认为", "know": "知道", "people": "人们",
            "like": "像", "love": "爱", "best": "最好",
            "wow": "哇", "lol": "笑死", "haha": "哈哈",
        }
        words = text.lower().split()
        result = []
        for w in words[:5]:
            if w in translations:
                result.append(translations[w])
        return " ".join(result) if result else "翻译暂不可用"

    async def _call_deepseek(self, post_content: str, persona_description: Optional[str]) -> list[dict]:
        if persona_description:
            system_prompt = f"""You are a Reddit user with the following persona: {persona_description}.
IMPORTANT: Every comment you generate MUST have a Chinese translation in the 'translation' field. The 'content' and 'suggestion' fields must be in English ONLY."""
            user_prompt = f"""Generate 3 Reddit comments. Each must be JSON with 3 fields:
- content: English comment (REQUIRED, must be in English)
- translation: Chinese translation of content (REQUIRED)
- suggestion: English usage tip (REQUIRED)

Output format (MUST be valid JSON array):
[{{"content":"ENGLISH TEXT","translation":"中文翻译","suggestion":"English tip"}}, ...]

Post: {post_content}"""
        else:
            system_prompt = """You are a friendly Reddit user.
IMPORTANT: Every comment you generate MUST have a Chinese translation in the 'translation' field. The 'content' and 'suggestion' fields must be in English ONLY."""
            user_prompt = f"""Generate 3 Reddit comments. Each must be JSON with 3 fields:
- content: English comment (REQUIRED, must be in English)
- translation: Chinese translation of content (REQUIRED)  
- suggestion: English usage tip (REQUIRED)

Output format (MUST be valid JSON array):
[{{"content":"ENGLISH TEXT","translation":"中文翻译","suggestion":"English tip"}}, ...]

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
                print(f"[LLM] Raw response: {content[:300]}...")
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                content = content.strip()
                comments = json.loads(content)
                return comments
        except Exception as e:
            print(f"[LLM] API call failed: {e}")
            raise


llm_service = LLMService()