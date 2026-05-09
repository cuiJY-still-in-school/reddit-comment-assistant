import json
import hashlib
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.post_record import PostRecord
from app.models.comment_result import CommentResult
from app.models.persona import Persona
from app.utils.cache import cache_get, cache_set
from app.core.config import settings
from typing import Optional


CACHE_TTL = 1800


class CommentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _make_cache_key(self, post_content: str, persona_id: Optional[int]) -> str:
        key_str = f"{post_content}:{persona_id}"
        return f"comment_cache:{hashlib.md5(key_str.encode()).hexdigest()}"

    async def _get_or_create_post(self, user_id: int, post_content: str, permalink: Optional[str], post_title: Optional[str] = None) -> PostRecord:
        if permalink:
            result = await self.db.execute(
                select(PostRecord).where(PostRecord.permalink == permalink, PostRecord.user_id == user_id)
            )
            post = result.scalar_one_or_none()
            if post:
                return post

        post = PostRecord(
            user_id=user_id,
            post_content=post_content,
            permalink=permalink,
            post_title=post_title,
        )
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def generate(
        self,
        user_id: int,
        post_content: str,
        permalink: Optional[str],
        persona_id: Optional[int],
        style_profile: Optional[dict] = None,
    ) -> dict:
        cache_key = self._make_cache_key(post_content, persona_id)
        cached = await cache_get(cache_key)
        if cached:
            return {"success": True, "comments": json.loads(cached), "cached": True}

        persona_description = None
        persona_name = None
        if persona_id:
            result = await self.db.execute(
                select(Persona).where(Persona.id == persona_id, Persona.user_id == user_id, Persona.delete_flag == 0)
            )
            persona = result.scalar_one_or_none()
            if persona:
                persona_description = persona.persona_description
                persona_name = persona.persona_name

        post = await self._get_or_create_post(user_id, post_content, permalink)

        comments = await self._call_llm(post_content, persona_description, style_profile)
        print(f"[CommentService] LLM returned {len(comments)} comments")
        for i, c in enumerate(comments):
            print(f"[CommentService]   comment[{i}] translation={c.get('translation', 'MISSING')[:50] if c.get('translation') else 'MISSING'}...")

        saved_comments = []
        for item in comments:
            cr = CommentResult(
                user_id=user_id,
                post_id=post.id,
                persona_id=persona_id,
                content=item["content"],
                translation=item.get("translation"),
                suggestion=item.get("suggestion"),
                status="unused",
            )
            self.db.add(cr)
            saved_comments.append(cr)

        await self.db.commit()
        for cr in saved_comments:
            await self.db.refresh(cr)
            print(f"[CommentService] after refresh: translation={cr.translation[:50] if cr.translation else 'NULL'}...")

        response_data = [
            {"comment_id": cr.id, "content": cr.content, "translation": cr.translation, "suggestion": cr.suggestion}
            for cr in saved_comments
        ]
        print(f"[CommentService] response_data: {response_data[0] if response_data else 'EMPTY'}")
        await cache_set(cache_key, json.dumps(response_data, ensure_ascii=False), CACHE_TTL)

        return {"success": True, "comments": response_data, "persona_name": persona_name, "cached": False}

    async def _call_llm(self, post_content: str, persona_description: Optional[str], style_profile: Optional[dict] = None) -> list[dict]:
        from app.services.llm_service import llm_service
        return await llm_service.generate_comments(post_content, persona_description, style_profile)

    async def mark_used(self, user_id: int, comment_id: int) -> dict:
        result = await self.db.execute(
            select(CommentResult).where(CommentResult.id == comment_id, CommentResult.user_id == user_id)
        )
        comment = result.scalar_one_or_none()
        if not comment:
            return {"success": True}

        comment.status = "used"
        await self.db.commit()

        return {"success": True}
