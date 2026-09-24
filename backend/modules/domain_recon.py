import asyncio
import re

import httpx
import whois as pywhois
import dns.resolver

from .base import OsintModule


class DomainReconModule(OsintModule):
    name = "domain_recon"
    applies_to = ("domain",)

    async def run(self, target: str) -> dict:
        result = {"target": target}
        result["whois"] = await asyncio.to_thread(self._get_whois, target)
        result["dns"] = await asyncio.to_thread(self._get_dns, target)
        result["subdomains"] = await self._get_subdomains(target)
        result["headers"] = await self._get_headers(target)
        return result

    def _get_whois(self, domain: str) -> dict:
        try:
            w = pywhois.whois(domain)
            return {
                "registrar": w.registrar,
                "creation_date": str(w.creation_date),
                "expiration_date": str(w.expiration_date),
                "name_servers": w.name_servers,
                "org": getattr(w, "org", None),
            }
        except Exception as exc:
            return {"error": str(exc)}

    def _get_dns(self, domain: str) -> dict:
        records = {}
        for rtype in ("A", "MX", "TXT", "NS"):
            try:
                answers = dns.resolver.resolve(domain, rtype, lifetime=5)
                records[rtype] = [str(r) for r in answers]
            except Exception:
                records[rtype] = []
        return records

    async def _get_subdomains(self, domain: str) -> list:
        """Pulls subdomains from certificate transparency logs (crt.sh) — public data only."""
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                names = {entry["name_value"] for entry in data if "name_value" in entry}
                subs = set()
                for n in names:
                    for line in n.split("\n"):
                        subs.add(line.strip())
                return sorted(subs)
        except Exception:
            return []

    async def _get_headers(self, domain: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(f"https://{domain}")
                return {
                    "status_code": resp.status_code,
                    "server": resp.headers.get("server"),
                    "powered_by": resp.headers.get("x-powered-by"),
                    "title": self._extract_title(resp.text),
                }
        except Exception as exc:
            return {"error": str(exc)}

    def _extract_title(self, html: str) -> str:
        match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""
