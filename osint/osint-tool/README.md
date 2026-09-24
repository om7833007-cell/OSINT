# OSINT Recon

A web-based OSINT aggregator: drop in a domain, IP, email, or username and it
auto-detects the target type, runs the relevant recon modules concurrently,
streams results in live as they complete, and drops any resolved location
onto an interactive 3D globe.

## Features (v1)

- **Auto-detect input** — one search bar, no need to pick a mode
- **Domain recon** — WHOIS, DNS records, subdomains (via crt.sh), tech
  fingerprinting from response headers
- **Username enumeration** — checks a curated set of platforms concurrently
- **Email breach lookup** — via the official Have I Been Pwned API (optional,
  requires your own API key)
- **Geolocation + globe view** — resolved IP/domain locations plotted live
- **Progressive results** — fast checks return first, results stream in as
  modules finish, no blocking spinner
- **Rate-limited & backoff-aware** — per-platform concurrency limits so you
  don't get blocked
- **Correlation flags** — lightweight heuristics surface *possible* links
  between findings (e.g. same username across 3+ platforms) as suggestions
  for a human to verify, never as fact
- **Case/session model** — searches can be grouped into a case and saved to
  SQLite, so an investigation persists across multiple searches
- **Required purpose note** — every search requires a short purpose/scope
  note, logged locally with the case

## Responsible use

This tool surfaces publicly available information. It is intended for
security research, journalism, due diligence, and investigating your own
digital footprint — not for stalking, harassment, or unauthorized
surveillance of individuals. Using it against a specific person without a
legitimate basis and, where applicable, their knowledge may violate
platform terms of service or local law depending on your jurisdiction.

A few things this project deliberately does *not* do, to stay on the right
side of that line:
- No breach-dump scraping — only the official, paid, rate-limited HIBP API
- No torrent/P2P activity monitoring
- Every search requires a stated purpose, logged locally in the case record

If you fork this and add features, keep that spirit: public data only,
official APIs over scraping personal data, and friction (not automation)
around anything that could enable harassment.

## Architecture

```
osint-tool/
├── backend/
│   ├── main.py              # FastAPI app: search dispatch, job polling, case API
│   ├── detector.py          # auto-detects domain / ip / email / username
│   ├── rate_limiter.py      # per-module semaphore + backoff
│   ├── correlation.py       # heuristic cross-finding correlation
│   ├── session_store.py     # SQLite case/search persistence
│   ├── requirements.txt
│   └── modules/
│       ├── base.py          # module interface — implement this to add a source
│       ├── domain_recon.py
│       ├── geolocation.py
│       ├── username_search.py
│       └── breach_lookup.py
└── frontend/
    ├── index.html
    ├── style.css
    ├── app.js                # search, polling, result rendering
    └── globe.js              # globe.gl integration
```

**Adding a new data source:** subclass `OsintModule` in `backend/modules/`,
implement `run(target) -> dict`, then register it in the `MODULES` dict in
`main.py` against the target type(s) it applies to. No other wiring needed —
it'll automatically run concurrently and stream into the frontend.

## Setup

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export HIBP_API_KEY=your_key_here   # optional, enables breach lookups
uvicorn main:app --reload --port 8000
```

**Frontend**

Just open `frontend/index.html` in a browser, or serve it statically:
```bash
cd frontend
python -m http.server 5500
```
Then visit `http://localhost:5500`. Make sure the backend is running on
`localhost:8000` (or update `API_BASE` in `app.js`).

## Roadmap / where this is intentionally incomplete

This is a v1 scaffold, not a finished product. Known gaps, in rough
priority order:

1. **Per-platform verification** — `username_search.py` currently checks
   HTTP status codes only, which gives false positives on some platforms.
   Add per-site `not_found_text` matching to raise confidence.
2. **Human-in-the-loop verification flow** — before deep-scanning a match,
   show a preview (avatar, bio) and require user confirmation it's the
   right target, rather than cascading unverified hits into correlation.
3. **Pivot UI** — clicking a finding (an email found in WHOIS, a linked
   account) should start a new linked search within the same case. Backend
   case model supports this; frontend wiring doesn't exist yet.
4. **Case management UI** — `POST /api/case` exists on the backend but the
   frontend doesn't expose case creation/selection yet; every search is
   currently standalone.
5. **Report export** — PDF/HTML case export isn't built yet.
6. **Stronger correlation** — current heuristics are intentionally basic
   (see `correlation.py`). Avatar image hashing and bio-text similarity
   would meaningfully improve this.

## License

MIT — see [LICENSE](LICENSE).
