import re

DOMAIN_RE = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})+$")
IP_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,40}$")


def detect_target_type(raw: str) -> str:
    """Guess whether the input is a domain, IP, email, or username."""
    value = raw.strip()

    if EMAIL_RE.match(value):
        return "email"
    if IP_RE.match(value):
        return "ip"
    if DOMAIN_RE.match(value) and "." in value:
        return "domain"
    if USERNAME_RE.match(value):
        return "username"
    return "unknown"
