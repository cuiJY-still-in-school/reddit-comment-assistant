import httpx
import json
from app.config import settings
from app.utils.circuit_breaker import llm_circuit_breaker, llm_queue
from typing import Optional


MOCK_COMMENTS = [
    {"content": "Great post! I totally agree with your perspective on this.", "translation": "好帖！我完全同意你的观点。", "suggestion": "Consider adding a personal anecdote."},
    {"content": "This is really insightful. Thanks for sharing!", "translation": "这真的很有见地。谢谢分享！", "suggestion": "Add a question to encourage interaction."},
    {"content": "I had a similar experience. Thanks for bringing this up!", "translation": "我有类似的经历。", "suggestion": "Keep it concise."},
]


def build_style_prompt(style_profile: Optional[dict] = None) -> str:
    if not style_profile:
        return ""

    parts = []
    sample_count = style_profile.get("sample_count", 0)

    if sample_count < 3:
        return ""

    parts.append("IMPORTANT: Match this user's writing style:")

    tone = style_profile.get("tone_patterns", [])
    if tone:
        parts.append(f"- Tone: {', '.join(tone)}")

    avg_length = style_profile.get("avg_word_count", 0)
    if avg_length:
        parts.append(f"- Average comment length: ~{avg_length} words")

    formality = style_profile.get("formality_score", 0.5)
    if formality < 0.4:
        parts.append("- Style: Casual, conversational")
    elif formality > 0.6:
        parts.append("- Style: More formal, thoughtful")

    humor = style_profile.get("humor_score", 0.3)
    if humor > 0.4:
        parts.append("- Include light humor when appropriate")

    emoji_rate = style_profile.get("emoji_usage_rate", 0)
    if emoji_rate > 0.2:
        parts.append("- Use occasional emojis (but not too many)")
    elif emoji_rate < 0.1:
        parts.append("- Avoid or minimize emoji usage")

    common_words = style_profile.get("common_words", [])
    if common_words[:5]:
        parts.append(f"- Natural vocabulary to use: {', '.join(common_words[:5])}")

    return "\n".join(parts)


class LLMService:
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.api_base = settings.deepseek_api_base
        self.model = settings.deepseek_model
        self.timeout = settings.deepseek_timeout

    async def generate_comments(
        self,
        post_content: str,
        persona_description: Optional[str] = None,
        style_profile: Optional[dict] = None
    ) -> list[dict]:
        if not self.api_key:
            print("[LLM] No API key, using mock")
            return MOCK_COMMENTS

        try:
            result = await self._call_deepseek(post_content, persona_description, style_profile)
            print(f"[LLM] DeepSeek returned {len(result)} comments")
            for i, c in enumerate(result):
                print(f"[LLM]   [{i}] translation={c.get('translation', 'MISSING')[:30] if c.get('translation') else 'MISSING'}...")
            llm_circuit_breaker.record_success()
            return result
        except Exception as e:
            print(f"[LLM] Error: {e}")
            llm_circuit_breaker.record_failure()
            return MOCK_COMMENTS

    async def _call_deepseek(
        self,
        post_content: str,
        persona_description: Optional[str],
        style_profile: Optional[dict] = None
    ) -> list[dict]:
        system_parts = [
            "You are a Reddit comment generator.",
            "Generate comments in English.",
            "For each comment, provide: content (English), translation (Chinese), suggestion (English)."
        ]

        if persona_description:
            system_parts.append(f"\nPersona: {persona_description}")

        style_prompt = build_style_prompt(style_profile)
        if style_prompt:
            system_parts.append(f"\n{style_prompt}")

        system_msg = "\n".join(system_parts)

        user_msg = f"""Generate 3 Reddit comments. Each comment must have:
- "content": English text
- "translation": Chinese translation of content
- "suggestion": English tip

Output as JSON array. No markdown. No code blocks. Just plain JSON.

Post: {post_content}"""

        print(f"[LLM] Calling {self.model} at {self.api_base}")

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
            raw = raw.strip().strip("```").strip("json").strip()
            result = json.loads(raw)
            return result


llm_service = LLMService()