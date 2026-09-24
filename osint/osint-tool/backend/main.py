import asyncio
import uuid
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import session_store as store
from correlation import correlate
from detector import detect_target_type
from rate_limiter import RateLimiter
from modules.breach_lookup import BreachLookupModule
from modules.domain_recon import DomainReconModule
from modules.geolocation import GeolocationModule
from modules.username_search import UsernameSearchModule

app = FastAPI(title="OSINT Recon Tool API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

store.init_db()
rate_limiter = RateLimiter(max_concurrent=5)

# Which modules run for which target type. Add new modules here.
MODULES = {
    "domain": [DomainReconModule(), GeolocationModule()],
    "ip": [GeolocationModule()],
    "username": [UsernameSearchModule()],
    "email": [BreachLookupModule()],
}

# In-memory job tracker so the frontend can poll for progressive results.
# Swap for Redis/a proper queue if you deploy this beyond a single process.
JOBS: Dict[str, dict] = {}


class SearchRequest(BaseModel):
    target: str
    case_id: Optional[str] = None
    purpose: str  # required scope/consent note, logged with the case


class CaseRequest(BaseModel):
    name: str
    purpose: str


@app.post("/api/case")
def create_case(req: CaseRequest):
    case_id = store.create_case(req.name, req.purpose)
    return {"case_id": case_id}


@app.get("/api/case")
def list_cases():
    return store.list_cases()


@app.get("/api/case/{case_id}")
def get_case(case_id: str):
    case = store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")
    return case


@app.post("/api/search")
async def start_search(req: SearchRequest):
    if not req.purpose or not req.purpose.strip():
        raise HTTPException(
            status_code=400,
            detail="A purpose/scope note is required before running a search. "
                   "It's logged locally with your case for accountability, not sent anywhere external.",
        )

    target_type = detect_target_type(req.target)
    if target_type == "unknown":
        raise HTTPException(status_code=400, detail="Could not determine target type.")

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "status": "running",
        "target": req.target,
        "target_type": target_type,
        "results": {},
        "flags": [],
    }

    asyncio.create_task(_run_modules(job_id, req.target, target_type, req.case_id))
    return {"job_id": job_id, "target_type": target_type}


@app.get("/api/search/{job_id}")
def get_search_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


async def _run_modules(job_id: str, target: str, target_type: str, case_id: Optional[str]):
    job = JOBS[job_id]
    modules = MODULES.get(target_type, [])

    async def run_one(module):
        result = await rate_limiter.run(module.name, module.run, target)
        job["results"][module.name] = result

    await asyncio.gather(*(run_one(m) for m in modules))

    job["flags"] = correlate(job["results"])
    job["status"] = "done"

    if case_id:
        store.add_search(case_id, target, target_type, {
            "results": job["results"],
            "flags": job["flags"],
        })


@app.get("/api/health")
def health():
    return {"status": "ok"}
