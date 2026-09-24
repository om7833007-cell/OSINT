import asyncio
import socket

import httpx

from .base import OsintModule


class GeolocationModule(OsintModule):
    """Resolves a domain/IP to a location. Powers the globe view on the frontend."""

    name = "geolocation"
    applies_to = ("domain", "ip")

    async def run(self, target: str) -> dict:
        ip = target
        if not self._is_ip(target):
            ip = await asyncio.to_thread(self._resolve, target)
            if not ip:
                return {"error": "could not resolve host"}
        return await self._lookup(ip)

    def _is_ip(self, value: str) -> bool:
        parts = value.split(".")
        return len(parts) == 4 and all(p.isdigit() for p in parts)

    def _resolve(self, domain: str):
        try:
            return socket.gethostbyname(domain)
        except Exception:
            return None

    async def _lookup(self, ip: str) -> dict:
        url = f"http://ip-api.com/json/{ip}"
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(url)
                data = resp.json()
                if data.get("status") != "success":
                    return {"error": data.get("message", "lookup failed")}
                return {
                    "ip": ip,
                    "country": data.get("country"),
                    "region": data.get("regionName"),
                    "city": data.get("city"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                    "isp": data.get("isp"),
                    "org": data.get("org"),
                    "timezone": data.get("timezone"),
                }
        except Exception as exc:
            return {"error": str(exc)}
