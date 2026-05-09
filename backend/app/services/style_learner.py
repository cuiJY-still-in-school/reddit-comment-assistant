import re
import json
from collections import Counter
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.style_sample_dao import style_sample_dao
from app.dao.style_profile_dao import style_profile_dao
from app.models.style_sample import StyleSample
from app.models.style_profile import StyleProfile


COMMON_WORDS_ENGLISH = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "must", "can", "need", "to", "of", "in", "for", "on", "with",
    "at", "by", "from", "as", "into", "through", "during", "before", "after",
    "and", "but", "or", "nor", "so", "yet", "both", "either", "neither",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their", "mine", "yours", "hers", "ours", "theirs",
    "this", "that", "these", "those", "here", "there", "when", "where", "why", "how",
    "what", "which", "who", "whom", "whose",
    "not", "no", "yes", "all", "some", "any", "each", "every", "few", "more", "most",
    "other", "another", "such", "only", "own", "same", "than", "too", "very",
    "just", "also", "now", "then", "still", "already", "always", "never", "ever",
}

SLANG_PATTERNS = [
    r"\blol\b", r"\bomg\b", r"\bwtf\b", r"\bbrb\b", r"\bimo\b", r"\bimho\b",
    r"\bbtw\b", r"\bfyi\b", r"\bnvm\b", r"\bikr\b", r"\birl\b", r"\blmao\b",
    r"\brofl\b", r"\btryna\b", r"\bgonna\b", r"\bwanna\b", r"\bgotta\b",
    r"\bkinda\b", r"\bsorta\b", r"\bdunno\b", r"\blemme\b", r"\bgimme\b",
]

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"
    "]+", flags=re.UNICODE
)

QUESTION_WORDS = {"?", "??", "???", "how", "what", "why", "when", "where", "who", "which"}


class StyleLearner:
    def __init__(self, db: AsyncSession):
        self.db = db

    def analyze_text(self, text: str) -> dict:
        if not text:
            return {}

        text_lower = text.lower()
        words = re.findall(r"\b\w+\b", text_lower)
        words_filtered = [w for w in words if w not in COMMON_WORDS_ENGLISH and len(w) > 2]

        char_count = len(text)
        word_count = len(words)
        sentence_count = max(1, len(re.split(r"[.!?]+", text)) - 1)

        emoji_count = len(EMOJI_PATTERN.findall(text))
        emoji_usage_rate = emoji_count / max(1, sentence_count)

        slang_matches = sum(1 for p in SLANG_PATTERNS if re.search(p, text_lower))
        slang_ratio = slang_matches / max(1, sentence_count)

        exclamation_count = text.count("!")
        question_count = sum(1 for q in QUESTION_WORDS if q in text_lower)
        question_ratio = question_count / max(1, sentence_count)

        caps_ratio = sum(1 for c in text if c.isupper()) / max(1, char_count)

        avg_word_len = sum(len(w) for w in words) / max(1, word_count)
        avg_sentence_len = word_count / max(1, sentence_count)

        word_freq = Counter(words_filtered)
        top_words = [w for w, _ in word_freq.most_common(20)]

        formality_score = self._calc_formality(text_lower, words, word_count)
        humor_score = self._calc_humor(text_lower, slang_ratio, emoji_count, exclamation_count)
        aggression_score = self._calc_aggression(text_lower, caps_ratio, exclamation_count)

        return {
            "char_count": char_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_word_length": round(avg_word_len, 2),
            "avg_sentence_length": round(avg_sentence_len, 2),
            "emoji_count": emoji_count,
            "emoji_usage_rate": round(emoji_usage_rate, 3),
            "slang_ratio": round(slang_ratio, 3),
            "exclamation_count": exclamation_count,
            "question_ratio": round(question_ratio, 3),
            "caps_ratio": round(caps_ratio, 3),
            "top_words": top_words[:15],
            "formality_score": round(formality_score, 3),
            "humor_score": round(humor_score, 3),
            "aggression_score": round(aggression_score, 3),
        }

    def _calc_formality(self, text_lower: str, words: list, word_count: int) -> float:
        formal_words = {"however", "therefore", "moreover", "furthermore", "nevertheless",
                       "consequently", "regarding", "concerning", "additionally", "thus"}
        informal_words = {"lol", "lmao", "imo", "btw", "kinda", "sorta", "yeah", "nope", "yep"}

        formal_count = sum(1 for w in words if w in formal_words)
        informal_count = sum(1 for w in words if w in informal_words)

        formal_ratio = formal_count / max(1, word_count)
        informal_ratio = informal_count / max(1, word_count)

        score = 0.5 + formal_ratio * 0.3 - informal_ratio * 0.3
        return max(0.0, min(1.0, score))

    def _calc_humor(self, text_lower: str, slang_ratio: float, emoji_count: int, exclamation: int) -> float:
        score = 0.3
        score += slang_ratio * 0.3
        score += min(emoji_count * 0.05, 0.2)
        score += min(exclamation * 0.03, 0.15)
        score += 0.1 if "lol" in text_lower or "lmao" in text_lower else 0
        return max(0.0, min(1.0, score))

    def _calc_aggression(self, text_lower: str, caps_ratio: float, exclamation: int) -> float:
        score = 0.2
        score += caps_ratio * 0.4
        score += min(exclamation * 0.05, 0.2)
        aggressive_words = {"hate", "stupid", "idiot", "dumb", "terrible", "awful", "worst", "pathetic"}
        score += 0.15 if any(w in text_lower for w in aggressive_words) else 0
        return max(0.0, min(1.0, score))

    async def add_sample(self, user_id: int, post_title: str, post_content: str,
                        post_url: str, user_comment: str) -> dict:
        if not user_comment or len(user_comment.strip()) == 0:
            return {"success": False, "code": 30001, "message": "评论内容不能为空"}
        if len(user_comment) > 5000:
            return {"success": False, "code": 30002, "message": "评论内容不能超过5000个字符"}
        if not post_title:
            return {"success": False, "code": 30003, "message": "帖子标题不能为空"}

        analysis = self.analyze_text(user_comment)

        sample = StyleSample(
            user_id=user_id,
            post_title=post_title[:500] if post_title else "",
            post_content=post_content[:2000] if post_content else "",
            post_url=post_url[:500] if post_url else "",
            user_comment=user_comment,
            analysis_data=analysis,
        )
        result = await style_sample_dao.create(self.db, sample)
        if not result:
            return {"success": False, "code": 30004, "message": "添加样本失败"}

        return {"success": True, "code": 0, "message": "样本添加成功", "data": {"sample_id": result.id}}

    async def get_user_samples(self, user_id: int, limit: int = 50, offset: int = 0) -> List[StyleSample]:
        return await style_sample_dao.get_by_user(self.db, user_id, limit, offset)

    async def analyze_user_style(self, user_id: int) -> dict:
        samples = await style_sample_dao.get_by_user(self.db, user_id, limit=100)

        if not samples:
            return {"success": False, "code": 30010, "message": "没有样本可供分析"}

        all_analyses = [s.analysis_data for s in samples if s.analysis_data]

        if not all_analyses:
            return {"success": False, "code": 30011, "message": "样本数据不完整"}

        avg_length = sum(a.get("char_count", 0) for a in all_analyses) // len(all_analyses)
        avg_word_count = sum(a.get("word_count", 0) for a in all_analyses) // len(all_analyses)

        all_top_words = []
        for a in all_analyses:
            all_top_words.extend(a.get("top_words", []))

        word_freq = Counter(all_top_words)
        common_words = [w for w, _ in word_freq.most_common(30)]

        formality_scores = [a.get("formality_score", 0.5) for a in all_analyses]
        humor_scores = [a.get("humor_score", 0.3) for a in all_analyses]
        aggression_scores = [a.get("aggression_score", 0.2) for a in all_analyses]

        avg_formality = sum(formality_scores) / len(formality_scores)
        avg_humor = sum(humor_scores) / len(humor_scores)
        avg_aggression = sum(aggression_scores) / len(aggression_scores)

        avg_emoji_rate = sum(a.get("emoji_usage_rate", 0) for a in all_analyses) / len(all_analyses)

        tone_patterns = []
        if avg_formality < 0.4:
            tone_patterns.append("casual")
        elif avg_formality > 0.6:
            tone_patterns.append("formal")
        else:
            tone_patterns.append("neutral")

        if avg_humor > 0.4:
            tone_patterns.append("humorous")
        if avg_aggression > 0.4:
            tone_patterns.append("assertive")

        sentence_style = {
            "avg_length": avg_word_count,
            "emoji_rate": round(avg_emoji_rate, 3),
        }

        result = {
            "sample_count": len(samples),
            "avg_length": avg_length,
            "avg_word_count": avg_word_count,
            "common_words": common_words[:20],
            "tone_patterns": tone_patterns,
            "formality_score": round(avg_formality, 3),
            "humor_score": round(avg_humor, 3),
            "aggression_score": round(avg_aggression, 3),
            "emoji_usage_rate": round(avg_emoji_rate, 3),
            "sentence_style": sentence_style,
        }

        await self._save_profile(user_id, result)

        return {"success": True, "code": 0, "message": f"分析了{len(samples)}个样本", "data": result}

    async def _save_profile(self, user_id: int, analysis: dict):
        profile = StyleProfile(
            user_id=user_id,
            avg_length=analysis.get("avg_length"),
            avg_word_count=analysis.get("avg_word_count"),
            common_words=analysis.get("common_words", []),
            tone_patterns=analysis.get("tone_patterns", []),
            formality_score=analysis.get("formality_score", 0.5),
            humor_score=analysis.get("humor_score", 0.3),
            aggression_score=analysis.get("aggression_score", 0.2),
            emoji_usage_rate=analysis.get("emoji_usage_rate", 0.0),
            sentence_style=analysis.get("sentence_style", {}),
            sample_count=analysis.get("sample_count", 0),
        )
        await style_profile_dao.upsert(self.db, profile)

    async def get_user_profile(self, user_id: int) -> Optional[dict]:
        profile = await style_profile_dao.get_by_user(self.db, user_id)

        if not profile:
            return None

        return {
            "sample_count": profile.sample_count,
            "avg_length": profile.avg_length,
            "avg_word_count": profile.avg_word_count,
            "common_words": profile.common_words or [],
            "tone_patterns": profile.tone_patterns or [],
            "formality_score": profile.formality_score,
            "humor_score": profile.humor_score,
            "aggression_score": profile.aggression_score,
            "emoji_usage_rate": profile.emoji_usage_rate,
            "sentence_style": profile.sentence_style or {},
            "updated_at": profile.update_time.isoformat() if profile.update_time else None,
        }