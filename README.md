# CutPoint — AI Hairstyle Recommendation & Salon Booking

> Upload a photo → get your face shape (geometry-based, works on bald & short hair) → see recommended styles from four angles → try one on your own photo → book a salon appointment.

**Status:** 🚧 Built and verified locally, phase by phase. (Live demo + screenshots land after deployment.)

---

## What it does

**Part A — AI Hairstyle Recommendation + Virtual Try-On**
- Analyses **face shape** from facial bone-structure geometry (round, oval, square, heart, oblong, diamond, triangle) — independent of hair, so it works on bald and short-haired users.
- Recommends flattering hairstyles for that face shape + user preferences.
- Shows each style from **four reference angles** (front / left / right / back).
- **Virtual try-on**: overlays the chosen style onto the user's own front photo, anchored to facial landmarks. Download the result or try another instantly.

**Part B — Salon Appointment Booking**
- Browse services, stylists, and conflict-free time slots.
- Book / reschedule / cancel; "my appointments" view; optionally link a saved look to a booking.

---

## Architecture

> Mermaid diagrams (high-level architecture, recommendation data flow, booking sequence, deployment topology) are added as the corresponding phases land.

_Coming in later phases._

---

## How the AI works (plain English)

> Filled in as Phases 1–4 land. Summary: face-shape detection uses **geometric ratios from MediaPipe's 468 facial landmarks** (jaw width, cheekbone width, face length, forehead/temple width, jaw angle) rather than a CNN — it's explainable, reliable, and robust to baldness/short hair because it measures bone structure, not hair. Recommendations come from a structured knowledge base filtered by user inputs, with natural-language explanations from an LLM (graceful rule-based fallback when no key is present).

---

## Tech stack

| Layer | Choice | Why |
| --- | --- | --- |
| Frontend | Next.js (App Router) + TypeScript, Tailwind, shadcn/ui | Modern React, type-safe, fast UI |
| Computer vision | MediaPipe Tasks Vision (Face Landmarker), in-browser | Heavy CV runs on the user's device — no ML server cost |
| Try-on | HTML Canvas | Landmark-anchored overlay + PNG export |
| Backend | Python + FastAPI, Pydantic v2, SQLModel | Strong AI/ML portfolio signal; typed, well-structured API |
| LLM | Groq (OpenAI-compatible) | Very fast inference; graceful fallback to templated text |
| Database | PostgreSQL (local Docker; Neon in prod) | Relational integrity for bookings |
| Auth | Self-hosted JWT | No external dependency; demonstrates backend auth |

---

## Local setup

Prerequisites: **Node 18+**, **Python 3.11+**, **Docker** (for Postgres), **Git**.

```bash
# 1. Clone
git clone <repo-url> && cd the_cut_point

# 2. Start Postgres
cp .env.example .env          # adjust if you like
docker compose up -d

# 3. Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example .env        # backend reads its own .env
uvicorn app.main:app --reload  # http://localhost:8000  (docs at /docs)

# 4. Frontend (new terminal)
cd frontend
npm install
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local
npm run dev                         # http://localhost:3000
```

Open http://localhost:3000 — the landing page shows a live **API status badge** confirming the frontend ↔ backend wire.

### Running tests

```bash
# Backend
cd backend && pytest

# Frontend (added in later phases)
cd frontend && npm run lint
```

---

## Project structure

```
the_cut_point/
├─ frontend/            # Next.js app (UI, MediaPipe, try-on canvas)
│  ├─ app/              # routes
│  ├─ components/       # UI components
│  ├─ lib/              # api client, geometry, mediapipe helpers
│  └─ public/assets/    # per-style hair reference images
├─ backend/             # FastAPI app
│  ├─ app/
│  │  ├─ api/           # routers: recommend, booking, auth
│  │  ├─ core/          # config, db
│  │  ├─ models/        # SQLModel entities
│  │  ├─ services/      # recommendation, llm, availability
│  │  └─ knowledge/     # face-shape → styles knowledge base
│  └─ tests/
├─ docs/                # diagrams, screenshots
├─ docker-compose.yml   # local Postgres
└─ .github/workflows/   # CI (runs once pushed)
```

---

## Scope & limitations (honest)

- The virtual try-on is a **2D landmark-anchored overlay**, not a neural hair-synthesis render.
- The four-angle views are **reference images of each hairstyle**, not a reconstruction of the user's own head/back — a single front photo cannot yield a real back-of-head view, so we don't fabricate one.
- Single primary face assumed; clear messaging for no-face / multiple-faces / low-quality / not-front-facing photos.

---

## Roadmap

- [x] Phase 0 — Scaffold (local)
- [x] Phase 1 — Face analysis + bald/short-hair accuracy
- [x] Phase 2 — Recommendation engine + knowledge base
- [x] Phase 3 — Multi-angle style views
- [x] Phase 4 — LLM explanation layer (Groq)
- [x] Phase 5 — Virtual try-on + download + try-another
- [ ] Phase 6 — Database + booking backend
- [ ] Phase 7 — Auth + booking UI + "bring this look"
- [ ] Phase 8 — Polish
- [ ] Phase 9 — Local acceptance
- [ ] Phase 10–12 — GitHub, deploy, final README

---

## Challenges & learnings

_Filled in as the build progresses._
