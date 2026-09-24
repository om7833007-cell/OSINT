import asyncio

import httpx

from .base import OsintModule

# Starter platform set. Each entry is just a public profile URL pattern —
# no login, scraping, or auth involved, only checking whether a page exists.
#
# LIMITATION: HTTP status code alone is not 100% reliable (some sites return
# 200 for both real and missing profiles). If you extend this, add a
# `not_found_text` per platform and check the response body for it to raise
# confidence — that's the biggest open contribution area in this module.
PLATFORMS = {
    "GitHub": "https://github.com/{}",
    "Twitter/X": "https://x.com/{}",
    "Instagram": "https://www.instagram.com/{}/",
    "Reddit": "https://www.reddit.com/user/{}/",
    "YouTube": "https://www.youtube.com/@{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "Pinterest": "https://www.pinterest.com/{}/",
    "Twitch": "https://www.twitch.tv/{}",
    "Medium": "https://medium.com/@{}",
    "GitLab": "https://gitlab.com/{}",
    "Dev.to": "https://dev.to/{}",
    "Keybase": "https://keybase.io/{}",
    "HackerNews": "https://news.ycombinator.com/user?id={}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Telegram": "https://t.me/{}",
}


class UsernameSearchModule(OsintModule):
    name = "username_search"
    applies_to = ("username",)

    def __init__(self, max_concurrent: int = 8):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def run(self, target: str) -> dict:
        tasks = [self._check(platform, url.format(target)) for platform, url in PLATFORMS.items()]
        results = await asyncio.gather(*tasks)
        found = [r for r in results if r["exists"]]
        return {"target": target, "checked": len(results), "found": found, "all": results}

    async def _check(self, platform: str, url: str) -> dict:
        async with self.semaphore:
            try:
                async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
                    resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                    exists = resp.status_code == 200
                    return {
                        "platform": platform,
                        "url": url,
                        "exists": exists,
                        "status_code": resp.status_code,
                        "confidence": "low",  # status-code-only check; see module docstring
                    }
            except Exception as exc:
                return {"platform": platform, "url": url, "exists": False, "error": str(exc)}
