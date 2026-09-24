from typing import Any, Dict, List


def correlate(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Lightweight heuristic correlation engine.

    Flags *possible* (never certain) links between findings across modules.
    These are suggestions for a human to verify manually, not conclusions.
    Extend this as your own correlation ideas come up (e.g. avatar image
    hashing, bio text similarity, matching display names).
    """
    flags: List[Dict[str, Any]] = []

    username_result = results.get("username_search")
    domain_result = results.get("domain_recon")

    if username_result and username_result.get("found"):
        platforms = [f["platform"] for f in username_result["found"]]
        if len(platforms) >= 3:
            flags.append({
                "type": "cross_platform_presence",
                "confidence": "low",
                "detail": (
                    f"Same username found on {len(platforms)} platforms: "
                    f"{', '.join(platforms)}. Could be the same person, or just "
                    f"a common handle reused independently — verify manually."
                ),
            })

    if domain_result and username_result:
        who = domain_result.get("whois", {}) or {}
        org = (who.get("org") or "").lower()
        target = (username_result.get("target") or "").lower()
        if org and target and target in org:
            flags.append({
                "type": "username_in_whois_org",
                "confidence": "medium",
                "detail": "The searched username appears in the domain's WHOIS organization field.",
            })

    return flags
