# Funscript Forge — Deployment Architecture

## Deployment Targets

Funscript Forge supports three deployment modes that share the same core pipeline:

| Mode | Audience | Tech stack |
| --- | --- | --- |
| **Local Streamlit** | Single user, offline | Python + Streamlit, filesystem |
| **Self-hosted API + UI** | Small team / advanced user | FastAPI + React/Streamlit, Docker |
| **Cloud SaaS** | Public, paid tiers | FastAPI + React, cloud-managed infra |

---

## Local Mode (current)

```
┌─────────────────────────────────────────────┐
│  User machine                               │
│                                             │
│  Browser ──► Streamlit (localhost:8501)     │
│                   │                         │
│                   ▼                         │
│         ui/streamlit/app.py                 │
│                   │                         │
│         ┌─────────┴──────────┐              │
│         ▼                    ▼              │
│   assessment/          pattern_catalog/     │
│   classifier.py        phrase_transforms.py │
│         │                    │              │
│         └─────────┬──────────┘              │
│                   ▼                         │
│         user_customization/                 │
│                   │                         │
│                   ▼                         │
│         output/  (local filesystem)         │
└─────────────────────────────────────────────┘
```

No network required. State lives in `st.session_state` and local JSON files.

---

## Self-Hosted / Docker Mode (Phase 2)

```
┌──────────────────────────────────────────────────────┐
│  Docker Compose                                      │
│                                                      │
│  ┌──────────────┐    ┌───────────────────────────┐   │
│  │  frontend    │    │  api (FastAPI)             │   │
│  │  Streamlit   │───►│  POST /assess             │   │
│  │  or React    │    │  POST /transform           │   │
│  │  :8501/:3000 │    │  POST /phrase-transform    │   │
│  └──────────────┘    │  POST /export              │   │
│                      │  GET  /transforms          │   │
│                      │  GET  /catalog             │   │
│                      └────────────┬──────────────┘   │
│                                   │                  │
│                      ┌────────────▼──────────────┐   │
│                      │  Core pipeline             │   │
│                      │  (assessment, transforms,  │   │
│                      │   customization)           │   │
│                      └────────────┬──────────────┘   │
│                                   │                  │
│                      ┌────────────▼──────────────┐   │
│                      │  storage                   │   │
│                      │  MinIO (S3-compatible)     │   │
│                      │  SQLite or Postgres        │   │
│                      └───────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

Single `docker compose up` spins up all services. Suitable for a home server or
a single cloud VM.

---

## Cloud SaaS Mode (Phase 3)

```
                          ┌──────────────────┐
                          │   CDN / Edge     │
                          │  (CloudFront /   │
                          │   Cloudflare)    │
                          └────────┬─────────┘
                                   │
              ┌────────────────────▼──────────────────────┐
              │            Load Balancer (ALB)            │
              └──────┬──────────────────────┬─────────────┘
                     │                      │
         ┌───────────▼──────┐   ┌───────────▼──────────┐
         │  UI Service      │   │  API Service          │
         │  React / Next.js │   │  FastAPI workers      │
         │  (ECS / Cloud    │   │  (ECS / Cloud Run)    │
         │   Run)           │   │  Autoscaling group    │
         └──────────────────┘   └───────────┬──────────┘
                                            │
                    ┌───────────────────────▼───────────────┐
                    │           Task Queue (Celery + Redis) │
                    │   Long assessments run as async jobs  │
                    └───────────────────────┬───────────────┘
                                            │
              ┌──────────────┬──────────────┼──────────────┐
              │              │              │              │
    ┌─────────▼──┐  ┌────────▼───┐  ┌──────▼──────┐ ┌────▼──────┐
    │ PostgreSQL │  │  S3 /      │  │  Redis      │ │  Stripe   │
    │ (users,    │  │  Object    │  │  (session   │ │  (billing)│
    │  projects, │  │  Storage   │  │   cache,    │ └───────────┘
    │  billing)  │  │ (funscript │  │   queue)    │
    └────────────┘  │  uploads,  │  └─────────────┘
                    │  results)  │
                    └────────────┘

Auth: Auth0 / Cognito (OAuth2 + JWT)
Secrets: AWS Secrets Manager / GCP Secret Manager
Observability: OpenTelemetry → Grafana / Datadog
```

### Key design decisions

- **Stateless API workers** — all state in S3 + Postgres; workers can scale to zero
- **Async jobs** — assessments on large files (>10 min) are queued, not blocking
- **Tenant isolation** — each user's uploads and results in a prefixed S3 path
- **CDN** — static UI assets and cached assessment results served from edge

---

## Data Flow (all modes)

```
User uploads .funscript
       │
       ▼
  Validate & store ──────────────────────► S3 / local fs
       │
       ▼
  POST /assess (or direct call)
       │
       ▼
  FunscriptAnalyzer
  (phases→cycles→patterns→phrases→BPM transitions)
       │
       ▼
  BehavioralClassifier (tag phrases)
       │
       ▼
  Assessment JSON ────────────────────────► S3 / local fs
       │
       ▼
  User reviews in UI
  Applies transforms (Phrase Editor / Pattern Editor)
       │
       ▼
  POST /export
       │
       ▼
  FunscriptTransformer + WindowCustomizer
  + blend_seams + final_smooth
       │
       ▼
  Output .funscript ──────────────────────► S3 / download
```

---

## Security Boundaries

| Boundary | Control |
| --- | --- |
| Public internet → API | TLS 1.3, rate limiting, API key or JWT |
| API → pipeline workers | Internal VPC only; no public exposure |
| User data | Tenant-scoped S3 paths; Postgres row-level security |
| File uploads | Max size enforced; MIME type validated; virus scan (ClamAV) in SaaS |
| Secrets | Never in code; injected via environment / secrets manager |

---

## Recommended Stack by Tier

| Tier | Frontend | Backend | Storage | Auth | Hosting |
| --- | --- | --- | --- | --- | --- |
| Local | Streamlit | Python direct | Filesystem | None | localhost |
| Self-hosted | Streamlit or React | FastAPI + Uvicorn | MinIO + SQLite | None / basic | Docker |
| SaaS MVP | React / Next.js | FastAPI + Celery | S3 + Postgres | Auth0 | AWS ECS / GCP Cloud Run |
| SaaS scale | React / Next.js | FastAPI + Celery | S3 + Postgres + Redis | Auth0 + RBAC | Kubernetes (EKS/GKE) |
