# CutPoint — AI Hairstyle Recommendation & Salon Booking

> Upload a photo → get your face shape (geometry-based, works on bald & short hair) → see recommended styles from four angles → try one on your own photo → find a nearby salon and book an appointment.

**An individual project designed and built by [Ramdas Chaugale](https://github.com/) — sole author.**

**Status:** 🚧 Built and verified locally, phase by phase. (Live demo + screenshots land after deployment.)

---

## What it does

**Part A — AI Hairstyle Recommendation + Virtual Try-On**
- Analyses **face shape** from facial bone-structure geometry (round, oval, square, heart, oblong, diamond, triangle) — independent of hair, so it works on bald and short-haired users.
- Recommends flattering hairstyles for that face shape + user preferences.
- Shows each style from **four reference angles** (front / left / right / back).
- **Virtual try-on**: overlays the chosen style onto the user's own front photo, anchored to facial landmarks. Download the result or try another instantly.

**Part B — Style catalogue, search and stylist assistant**
- **Search the catalogue in plain English**: "something low maintenance that works with curls" is parsed into the catalogue's own vocabulary (length, hair type, upkeep, presentation, face shape), then used to rank and filter. Each result lists the reasons it matched, so the ranking is inspectable rather than opaque.
- **Ask the stylist**: a question box answered only from the hairstyle knowledge base, with the entries it used shown beneath the answer. Grounding it this way stops the model describing a cut the catalogue does not contain.
- Both degrade cleanly: with no API key the search falls back to a deterministic synonym table and the assistant assembles its answer from the retrieved entries directly.

**Part C — Salon Appointment Booking (two-sided)**
- **Clients**: find nearby salons (geolocation), browse each salon's menu & rates, request a time slot, and track requests in "my appointments" — optionally attaching a saved look ("bring this look").
- **Salons/barbers**: register a shop, then accept / decline (with a suggested time) incoming requests from a dashboard showing revenue, upcoming/completed appointments and clients.
- Conflict-free by design (a salon's chairs can't be over-booked); email notifications on request and accept/decline.

---

## Architecture

> Mermaid diagrams (high-level architecture, recommendation data flow, booking sequence, deployment topology) are added as the corresponding phases land.

_Coming in later phases._

---

## How the AI works (plain English)

There are four distinct pieces, and none of them is a black box.

**1. Face shape, from geometry.** Detection uses **geometric ratios over MediaPipe's 468 facial landmarks** (jaw width, cheekbone width, face length, forehead and temple width, jaw angle) rather than a CNN. That choice is deliberate: the ratios are explainable, they need no training data, and because they measure bone structure rather than hair they stay accurate on bald and short-haired faces, which is exactly where a hair-trained classifier fails. All of it runs in the browser, so no photo is uploaded.

**2. Recommendation, from a curated knowledge base.** 21 styles are described in a validated YAML file with controlled vocabularies. Ranking scores each style against the detected face shape and the stated preferences, and reports which preferences it satisfied.

**3. Natural-language search, with a deterministic core.** A free-text query is turned into those same controlled vocabularies. A language model does the parsing when a key is configured, because it handles phrasings no keyword table will cover; anything it returns outside the vocabulary is discarded rather than trusted. Retrieval itself is a **TF-IDF index built over the catalogue** at startup. A corpus of 21 documents does not need a vector database, and an in-process index keeps the whole feature deployable with no extra service.

**4. A grounded assistant.** Questions are answered by retrieving the most relevant catalogue entries and giving the model those entries and nothing else. The entries used are returned with the answer and shown in the UI. This is the difference between a chatbot and a product feature: the answer can be checked.

Every LLM call has a deterministic fallback and swallows its own failures, so a missing key, a rate limit or a decommissioned model degrades the experience rather than breaking it.

---

## Tech stack

| Layer | Choice | Why |
| --- | --- | --- |
| Frontend | Next.js 16 (App Router) + TypeScript + Tailwind v4 | Modern React, type-safe, fast UI |
| Computer vision | MediaPipe Tasks Vision (Face Landmarker), in-browser | Heavy CV runs on the user's device — no ML server cost |
| 2D try-on | HTML Canvas | Landmark-anchored overlay + PNG export |
| Backend | Python + FastAPI, Pydantic v2, SQLModel, Alembic | Strong AI/ML portfolio signal; typed, migration-managed API |
| LLM | Groq (`openai/gpt-oss-120b`) | Sub-second inference; every call has a deterministic fallback |
| Retrieval | In-process TF-IDF over the style catalogue | 21 documents; a vector DB would be weight without benefit |
| Realistic AI try-on | fal.ai Flux Kontext *(optional)* | Photorealistic hair editing; degrades off without a key |
| 3D avatar | Ready Player Me + `<model-viewer>` *(optional)* | Free selfie→3D avatar showcase |
| Email | Gmail SMTP (background tasks) | Request/accept/decline notifications; no-op without creds |
| Database | PostgreSQL (local Docker; Neon in prod) | Relational integrity for bookings |
| Auth | Self-hosted JWT + bcrypt, two roles | No external dependency; demonstrates backend auth |

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
# Backend: 127 tests
cd backend && pytest

# Backend quality gates
ruff check app tests && black --check app tests && mypy app

# Frontend
cd frontend && npx eslint app components lib && npm run build
```

---

## Project structure

```
the_cut_point/
├─ frontend/            # Next.js app (UI, MediaPipe, try-on canvas)
│  ├─ app/              # routes (incl. /styles catalogue + search)
│  ├─ components/       # UI components
│  ├─ lib/              # api client, geometry, mediapipe helpers
│  └─ public/assets/    # per-style hair reference images (generated)
├─ backend/             # FastAPI app
│  ├─ app/
│  │  ├─ api/           # routers: recommend, search, booking, auth, tryon
│  │  ├─ core/          # config, db
│  │  ├─ models/        # SQLModel entities + API schemas
│  │  ├─ services/      # recommendation, llm, style_search, assistant, email
│  │  └─ knowledge/     # face-shape → styles knowledge base (YAML)
│  └─ tests/
├─ tools/               # asset generator for the style silhouettes
├─ docs/                # diagrams, screenshots
├─ docker-compose.yml   # local Postgres
└─ .github/workflows/   # CI (runs once pushed)
```

---

## Try-on modes

CutPoint offers three honest ways to visualise a style:

1. **2D overlay** — instant, free, schematic; a hairstyle silhouette anchored to your facial landmarks (bald-safe).
2. **Realistic AI try-on** *(optional add-on)* — a photorealistic edit of your own photo via a generative image model (fal.ai Flux Kontext). Fully implemented and tested; it runs on a **paid** model, so it's disabled by default and lights up when a funded `FAL_KEY` is provided. Swappable for another provider (e.g. Google Gemini image) via one service module.
3. **3D avatar** *(optional)* — a Ready Player Me avatar of you, as a separate showcase.

## Scope & limitations (honest)

- The 2D try-on is a **landmark-anchored overlay**, not a neural render.
- The four-angle views are **reference images of each hairstyle**, not a reconstruction of the user's own head/back — a single front photo cannot yield a real back-of-head view, so we don't fabricate one.
- The realistic AI try-on and 3D avatar are **optional, provider-backed add-ons** (documented above); the core app is fully functional without them.
- Single primary face assumed; clear messaging for no-face / multiple-faces / low-quality / not-front-facing photos.

---

## Roadmap

- [x] Phase 0 — Scaffold (local)
- [x] Phase 1 — Face analysis + bald/short-hair accuracy
- [x] Phase 2 — Recommendation engine + knowledge base
- [x] Phase 3 — Multi-angle style views
- [x] Phase 4 — LLM explanation layer (Groq)
- [x] Phase 5 — Virtual try-on + download + try-another
- [x] Phase 6 — Database + booking backend
- [x] Phase 7 — Two-sided auth (client + saloon) + multi-salon request/approve model
- [x] Phase 8 — Client journey: nearby salons, booking + my-appointments, "bring this look"
- [x] Phase 9 — Saloon/barber dashboard (requests, accept/decline, revenue, clients)
- [x] Phase 10 — Email notifications (Gmail SMTP)
- [x] Phase 11 — Realistic AI try-on (fal.ai Flux Kontext)
- [x] Phase 12 — 3D avatar (Ready Player Me)
- [x] Phase 13 — Polish (landing page, mobile nav, 404/500, consistency)
- [x] Phase 14 — Design system (semantic colour tokens, typography, one accent)
- [x] Phase 15 — Natural-language catalogue search + grounded stylist assistant
- [ ] Phase 16 — Local acceptance
- [ ] GitHub, deploy, final README

---

## Challenges & learnings

_Filled in as the build progresses._

---

## Author & license

Designed and built by **Ramdas Chaugale** as an individual portfolio project.
Licensed under the [MIT License](LICENSE) — © 2026 Ramdas Chaugale.
