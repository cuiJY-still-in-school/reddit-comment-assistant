import httpx
import json
from typing import Optional
from app.config import settings


class RedditScraper:
    def __init__(self, cookie: Optional[str] = None):
        self.cookie = cookie
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        if cookie:
            self.headers["Cookie"] = cookie

    async def get_posts(self, subreddit: str, sort: str = "hot", limit: int = 10) -> list[dict]:
        sort_map = {"hot": ".json?raw_json=1", "new": "/new/.json", "top": "/top/.json"}
        endpoint = sort_map.get(sort, ".json")

        url = f"https://www.reddit.com/r/{subreddit}{endpoint}"
        params = {"limit": min(limit, 25), "raw_json": 1}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=self.headers, params=params)
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
            return []

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
        url = "https://www.reddit.com/subreddits/.json?limit=20"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()

            subs = []
            for child in data.get("data", {}).get("children", []):
                d = child.get("data", {})
                subs.append({
                    "name": d.get("display_name", ""),
                    "title": d.get("title", ""),
                    "subscribers": d.get("subscribers", 0),
                    "description": d.get("public_description", ""),
                })
            return subs
        except Exception as e:
            print(f"[RedditScraper] Error fetching subreddits: {e}")
            return []


reddit_scraper = RedditScraper()