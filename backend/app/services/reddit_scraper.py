import httpx
import json
from typing import Optional
from app.core.config import settings


class RedditScraper:
    def __init__(self, cookie: Optional[str] = None):
        self.cookie = cookie
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        if cookie:
            self.headers["Cookie"] = cookie

    async def get_posts(self, subreddit: str, sort: str = "hot", limit: int = 10) -> list[dict]:
        sort_map = {"hot": "/hot/.json", "new": "/new/.json", "top": "/top/.json"}
        endpoint = sort_map.get(sort, "/hot/.json")

        url = f"https://www.reddit.com/r/{subreddit}{endpoint}"
        params = {"limit": min(limit, 25)}

        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers, params=params)
                print(f"[RedditScraper] Status: {response.status_code}")
                if response.status_code == 429:
                    print("[RedditScraper] Rate limited by Reddit")
                    return self._get_mock_posts(subreddit)
                if response.status_code == 403:
                    print("[RedditScraper] Access forbidden")
                    return self._get_mock_posts(subreddit)
                response.raise_for_status()
                data = response.json()

            posts = []
            children = data.get("data", {}).get("children", [])

            for child in children:
                post_data = child.get("data", {})
                posts.append({
                    "id": post_data.get("id", ""),
                    "title": post_data.get("title", ""),
                    "content": post_data.get("selftext", ""),
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                    "score": post_data.get("score", 0),
                    "num_comments": post_data.get("num_comments", 0),
                    "subreddit": post_data.get("subreddit", subreddit),
                    "created_utc": post_data.get("created_utc", 0),
                    "author": post_data.get("author", ""),
                    "thumbnail": post_data.get("thumbnail", ""),
                    "link_flair_text": post_data.get("link_flair_text", ""),
                })

            return posts

        except Exception as e:
            print(f"[RedditScraper] Error fetching posts: {e}")
            return self._get_mock_posts(subreddit)

    def _get_mock_posts(self, subreddit: str) -> list[dict]:
        return [
            {
                "id": "mock1",
                "title": f"What's your unpopular opinion about {subreddit}?",
                "content": "Share your controversial take that might get you downvoted.",
                "url": f"https://reddit.com/r/{subreddit}/comments/mock1",
                "score": 1234,
                "num_comments": 456,
                "subreddit": subreddit,
                "author": "reddit_user",
            },
            {
                "id": "mock2",
                "title": f"What's the best {subreddit.replace('askreddit', 'advice')} you've ever received?",
                "content": "Looking for wisdom from the community.",
                "url": f"https://reddit.com/r/{subreddit}/comments/mock2",
                "score": 5678,
                "num_comments": 789,
                "subreddit": subreddit,
                "author": "another_user",
            },
            {
                "id": "mock3",
                "title": f"If you could change one thing about {subreddit}, what would it be?",
                "content": "Let's discuss improvements and changes.",
                "url": f"https://reddit.com/r/{subreddit}/comments/mock3",
                "score": 2345,
                "num_comments": 321,
                "subreddit": subreddit,
                "author": "observer",
            },
            {
                "id": "mock4",
                "title": "What's a skill you learned that surprisingly helped in an unrelated area?",
                "content": "Sometimes learning one thing opens doors we didn't expect.",
                "url": f"https://reddit.com/r/{subreddit}/comments/mock4",
                "score": 8765,
                "num_comments": 543,
                "subreddit": subreddit,
                "author": "curious_mind",
            },
            {
                "id": "mock5",
                "title": "What's something you wish more people knew about?",
                "content": "Share knowledge that deserves to be more well-known.",
                "url": f"https://reddit.com/r/{subreddit}/comments/mock5",
                "score": 4321,
                "num_comments": 654,
                "subreddit": subreddit,
                "author": "knowledge_seeker",
            },
        ]

    async def get_post_by_url(self, url: str) -> Optional[dict]:
        if not url.endswith(".json"):
            url = f"{url.rstrip('/')}.json"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()

            post_data = data[0]["data"]["children"][0]["data"]
            return {
                "id": post_data.get("id", ""),
                "title": post_data.get("title", ""),
                "content": post_data.get("selftext", ""),
                "url": f"https://reddit.com{post_data.get('permalink', '')}",
                "score": post_data.get("score", 0),
                "num_comments": post_data.get("num_comments", 0),
                "subreddit": post_data.get("subreddit", ""),
                "author": post_data.get("author", ""),
            }
        except Exception as e:
            print(f"[RedditScraper] Error fetching post: {e}")
            return None

    async def get_popular_subreddits(self) -> list[dict]:
        return [
            {"name": "askreddit", "title": "Ask Reddit", "subscribers": 45000000, "description": "The most popular subreddit for questions"},
            {"name": "funny", "title": "Funny", "subscribers": 42000000, "description": "Funny posts and memes"},
            {"name": "gaming", "title": "Gaming", "subscribers": 38000000, "description": "Video games discussion"},
            {"name": "worldnews", "title": "World News", "subscribers": 28000000, "description": "News from around the world"},
            {"name": "todayilearned", "title": "Today I Learned", "subscribers": 29000000, "description": "Interesting facts and trivia"},
        ]


reddit_scraper = RedditScraper()