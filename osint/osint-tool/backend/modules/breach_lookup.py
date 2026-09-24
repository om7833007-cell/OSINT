import os

import httpx

from .base import OsintModule

HIBP_API_KEY = os.environ.get("HIBP_API_KEY")


class BreachLookupModule(OsintModule):
    """Checks an email against Have I Been Pwned's official API.

    https://haveibeenpwned.com/API/v3 — requires a paid HIBP_API_KEY env var.
    Deliberately does NOT scrape leak forums or breach-dump sites: only the
    official, rate-limited HIBP API is used. Set HIBP_API_KEY to enable it.
    """

    name = "breach_lookup"
    applies_to = ("email",)

    async def run(self, target: str) -> dict:
        if not HIBP_API_KEY:
            return {
                "skipped": True,
                "reason": "Set the HIBP_API_KEY environment variable to enable breach "
                          "lookups via haveibeenpwned.com's official API.",
            }
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{target}"
        headers = {"hibp-api-key": HIBP_API_KEY, "user-agent": "osint-tool"}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 404:
                    return {"breached": False, "breaches": []}
                if resp.status_code != 200:
                    return {"error": f"HIBP returned status {resp.status_code}"}
                data = resp.json()
                return {"breached": True, "breaches": [b["Name"] for b in data]}
        except Exception as exc:
            return {"error": str(exc)}
