# Funscript Forge — Compute & Effort Estimates

All cost figures are approximate (2025 USD). Cloud pricing varies by region and negotiated rates.

---

## a. REST API over existing features

### What it involves
Wrap the existing Python pipeline in FastAPI endpoints. The core modules
(`assessment/`, `pattern_catalog/`, `user_customization/`) are already
framework-agnostic — this is a thin adapter layer.

### Development effort
| Task | Estimate |
| --- | --- |
| FastAPI app scaffold + route handlers | 1–2 days |
| Pydantic request/response schemas | 1 day |
| File upload handling (multipart) | 0.5 day |
| Auth middleware (API key) | 0.5 day |
| OpenAPI docs + integration tests | 1 day |
| Docker image + compose file | 0.5 day |
| **Total** | **~5–6 dev days** |

### Compute cost (self-hosted, single VM)
| Instance | vCPU | RAM | Monthly cost |
| --- | --- | --- | --- |
| AWS t3.medium | 2 | 4 GB | ~$30 |
| AWS t3.large | 2 | 8 GB | ~$60 |
| GCP e2-medium | 2 | 4 GB | ~$25 |

A single t3.medium handles typical workloads. Large funscripts (>30 min, 100k+
actions) may need t3.large to avoid OOM during assessment.

### Compute cost (serverless / on-demand)
| Service | Basis | Est. cost per 1,000 assessments |
| --- | --- | --- |
| AWS Lambda (1 GB, ~10 s avg) | Pay per invocation | ~$0.17 |
| GCP Cloud Run (1 vCPU, 2 GB) | Pay per request | ~$0.10 |

For low volume (< 500 assessments/day), serverless is cheapest. Above ~2,000/day
a persistent container is more economical.

---

## b. UI that runs locally — recommended stack

### Stack recommendation
| Layer | Choice | Reason |
| --- | --- | --- |
| UI framework | **Streamlit** (current) | Zero build step; Python-native; good for data tools |
| Packaging | **PyInstaller** or **Briefcase** | Bundle into a single executable for non-technical users |
| Alternative | **Electron + FastAPI** | Better offline UX; larger download; more engineering effort |

**Streamlit is already implemented and is the right choice for local use.**
The main gap is packaging: users currently need Python + pip install.

### Packaging effort
| Task | Estimate |
| --- | --- |
| PyInstaller spec + CI build | 1–2 days |
| Windows installer (NSIS/Inno) | 1 day |
| macOS .app bundle + notarize | 1–2 days |
| **Total** | **~3–5 dev days** |

### Ongoing compute cost
Zero — runs on user's machine.

---

## c. UI that runs at scale in the cloud

### Stack recommendation
| Layer | Choice |
| --- | --- |
| Frontend | **React + Next.js** (TypeScript) |
| Charts | **Plotly.js** (mirrors existing Python Plotly) |
| Backend API | **FastAPI** (Python) |
| Task queue | **Celery + Redis** (async assessment jobs) |
| Database | **PostgreSQL** (users, projects, billing) |
| Object storage | **S3** (funscript uploads + results) |
| Auth | **Auth0** or **Clerk** |
| Hosting | **AWS ECS Fargate** or **GCP Cloud Run** |
| CDN | **CloudFront** or **Cloudflare** |

### Development effort
| Task | Estimate |
| --- | --- |
| React + Next.js project scaffold | 2 days |
| Auth integration (Auth0) | 1–2 days |
| File upload + progress UI | 1 day |
| Assessment result viewer (charts) | 3–5 days |
| Phrase Editor port to React | 5–8 days |
| Pattern Editor port to React | 5–8 days |
| Export tab port to React | 2–3 days |
| API layer (see section a) | 5–6 days |
| Billing integration (Stripe) | 2–3 days |
| Infrastructure as code (Terraform) | 2–3 days |
| CI/CD pipeline | 1–2 days |
| **Total** | **~30–45 dev days (6–9 weeks solo / 3–5 weeks with 2 devs)** |

### Monthly cloud cost — MVP (low traffic, ~100 active users)
| Service | Config | Monthly |
| --- | --- | --- |
| ECS Fargate (API, 0.5 vCPU / 1 GB, 2 tasks) | On demand | ~$30 |
| ECS Fargate (UI/Next.js, 0.25 vCPU / 0.5 GB) | On demand | ~$10 |
| RDS Postgres (db.t3.micro) | Single AZ | ~$15 |
| ElastiCache Redis (cache.t3.micro) | Single node | ~$15 |
| S3 (100 GB storage + transfer) | Standard | ~$5 |
| CloudFront | 1 TB transfer | ~$10 |
| ALB | — | ~$20 |
| **Total MVP** | | **~$105/month** |

### Monthly cloud cost — Growth (1,000 active users, ~5,000 assessments/day)
| Service | Config | Monthly |
| --- | --- | --- |
| ECS Fargate (API, auto-scaling 2–10 tasks) | — | ~$150–400 |
| ECS Fargate (UI) | — | ~$30 |
| RDS Postgres (db.t3.small, Multi-AZ) | — | ~$80 |
| ElastiCache Redis (cache.t3.small) | — | ~$50 |
| S3 (1 TB + transfer) | — | ~$30 |
| CloudFront | 10 TB transfer | ~$90 |
| ALB | — | ~$25 |
| **Total growth** | | **~$455–735/month** |

---

## d. Effort to containerise

The codebase is pure Python with no native extensions, making containerisation straightforward.

| Task | Estimate |
| --- | --- |
| Dockerfile for API/pipeline | 0.5 day |
| Dockerfile for Streamlit UI | 0.5 day |
| Docker Compose (local dev) | 0.5 day |
| `.dockerignore` + layer optimisation | 0.5 day |
| GitHub Actions build + push to registry | 0.5 day |
| **Total** | **~2–3 dev days** |

Key considerations:
- Base image: `python:3.11-slim` (~60 MB compressed)
- Dependencies: `requirements.txt` already exists; pin versions for reproducibility
- No GPU required — all processing is CPU-bound
- Container memory: 512 MB minimum; 2 GB recommended for large funscripts

---

## e. Effort to support multiple users

### What needs to change
| Concern | Current state | What's needed |
| --- | --- | --- |
| Authentication | None | Auth middleware (API key or OAuth2 JWT) |
| Session isolation | Streamlit `st.session_state` (single user) | Per-user session keys in Redis or DB |
| File storage | Local `test_funscript/` + `output/` | Per-user S3 paths or namespaced local dirs |
| Concurrency | Single process | Async FastAPI workers + Celery for long jobs |
| Pattern catalog | Shared single JSON file | Per-user or opt-in shared catalog in DB |
| Project persistence | Local JSON | DB-backed project store |
| Rate limiting | None | Per-user rate limits on API |

### Effort breakdown
| Task | Estimate |
| --- | --- |
| Auth layer (JWT + user model) | 2–3 days |
| Per-user file namespacing | 1 day |
| Session isolation refactor | 1–2 days |
| Async job queue (Celery) | 2–3 days |
| DB-backed project/catalog store | 3–5 days |
| Rate limiting + abuse protection | 1 day |
| Admin dashboard (basic) | 2–3 days |
| **Total** | **~12–18 dev days (2.5–4 weeks)** |

This is the highest-leverage investment — it unlocks the SaaS deployment target.

---

## Summary

| Work item | Dev effort | Monthly cloud cost |
| --- | --- | --- |
| a. REST API | 5–6 days | $25–60 (VM) or near-zero (serverless) |
| b. Local UI (current Streamlit) | 3–5 days (packaging only) | $0 |
| c. Cloud-scale UI | 30–45 days | $105 (MVP) → $500–700 (growth) |
| d. Containerise | 2–3 days | — |
| e. Multi-user | 12–18 days | Included in (c) |
| **Full SaaS (a+c+d+e)** | **~50–70 days** | **$105–700/month** |
