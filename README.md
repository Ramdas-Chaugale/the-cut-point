# CutPoint

> Upload a photo → get your face shape (geometry based, works on bald and short hair), see recommended styles from four angles, try one on your own photo, then find a nearby salon and book.

Face shape analysis, hairstyle recommendation and salon booking. Built by [Ramdas Chaugale](https://github.com/Ramdas-Chaugale) as an individual project.

**Status:** built and running. Backend, frontend and database all run locally from the steps below. Not deployed publicly, because the booking side stores real salon and client records and I would rather not host that without a reason to.

---

## What it does

**Part A. Hairstyle recommendation and virtual try on**
- Analyses **face shape** from facial bone-structure geometry (round, oval, square, heart, oblong, diamond, triangle). It is independent of hair, so it works on bald and short haired users.
- Recommends flattering hairstyles for that face shape + user preferences.
- Shows each style from **four reference angles** (front / left / right / back).
- **Virtual try-on**: overlays the chosen style onto the user's own front photo, anchored to facial landmarks. Download the result or try another instantly.

**Part B. Style catalogue, search and stylist assistant**
- **Search the catalogue in plain English**: "something low maintenance that works with curls" is parsed into the catalogue's own vocabulary (length, hair type, upkeep, presentation, face shape), then used to rank and filter. Each result lists the reasons it matched, so the ranking is inspectable rather than opaque.
- **Ask the stylist**: a question box answered only from the hairstyle knowledge base, with the entries it used shown beneath the answer. Grounding it this way stops the model describing a cut the catalogue does not contain.
- Both degrade cleanly: with no API key the search falls back to a deterministic synonym table and the assistant assembles its answer from the retrieved entries directly.

**Part C. Salon appointment booking, two sided**
- **Clients**: find nearby salons (geolocation), browse each salon's menu & rates, request a time slot, and track requests in "my appointments", optionally attaching a saved look ("bring this look").
- **Salons/barbers**: register a shop, then accept / decline (with a suggested time) incoming requests from a dashboard showing revenue, upcoming/completed appointments and clients.
- Conflict-free by design (a salon's chairs can't be over-booked); email notifications on request and accept/decline.

---

## Architecture

Three pieces. A Next.js frontend that does all the face work in the browser, a FastAPI backend holding the catalogue, the booking logic and the model calls, and PostgreSQL behind it.

The split matters in one place: face landmarks never leave the browser, so the backend never receives a photograph unless you ask for an AI try-on, and then it receives only that one image.

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
| Computer vision | MediaPipe Tasks Vision (Face Landmarker), in-browser | Heavy CV runs on the user's device, so no ML server cost |
| 2D try-on | HTML Canvas | Landmark anchored overlay and PNG export |
| Backend | Python + FastAPI, Pydantic v2, SQLModel, Alembic | Strong AI/ML portfolio signal; typed, migration-managed API |
| LLM | Groq (`openai/gpt-oss-120b`) | Sub-second inference; every call has a deterministic fallback |
| Retrieval | In-process TF-IDF over the style catalogue | 21 documents; a vector DB would be weight without benefit |
| Realistic AI try-on | Cloudflare Workers AI inpainting, fal.ai optional | Cloudflare is free and inpaints the hair region only; fal.ai edits the whole photo but bills per image |
| 3D avatar | Ready Player Me + `<model-viewer>` *(optional)* | Free selfie to 3D avatar showcase |
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

Open http://localhost:3000. The landing page shows a live **API status badge** confirming the frontend and backend are talking.

### Running tests

```bash
# Backend: 139 tests
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

1. **2D overlay**: instant, free and schematic. A hairstyle silhouette anchored to your facial landmarks, and it works on a bald head.
2. **Realistic AI try-on**: a photorealistic edit of your own photo. Two providers sit behind one service module. Cloudflare Workers AI inpaints the hair region and is free, so it is the default when credentials are present. fal.ai Flux Kontext edits the whole photo with a stronger model but bills per image, so it stays optional.
3. **3D avatar** (optional): a Ready Player Me avatar of you, as a separate showcase.

## Scope & limitations (honest)

- The 2D try-on is a **landmark-anchored overlay**, not a neural render.
- The four-angle views are **reference images of each hairstyle**, not a reconstruction of your own head. A single front photo cannot give a real back of head view, so the app does not invent one.
- The realistic AI try-on and 3D avatar are **optional, provider-backed add-ons** (documented above); the core app is fully functional without them.
- Single primary face assumed; clear messaging for no-face / multiple-faces / low-quality / not-front-facing photos.

---

## Build order

Built in phases, each one finished and verified before the next started: scaffold, face analysis, recommendation engine, multi-angle views, LLM explanations, virtual try-on, database and booking, two sided auth, client journey, salon dashboard, email notifications, realistic AI try-on, 3D avatar, polish, design system, and natural language search with the grounded assistant.

---

## What was hard

**Anchoring the overlay.** The first version pinned the hairstyle to the top of the head and it sat over the face. Anchoring to the two cheekbone landmarks instead, and solving a similarity transform between those and two fixed points in the artwork, puts it where hair actually sits.

**Knowing when a result is not worth showing.** The AI try-on costs real inference time, so the UI has to say what it is doing and let you fall back to the instant overlay. A feature that takes six seconds without saying so reads as broken.

**Keeping the LLM optional.** Every model call has a deterministic fallback, which meant writing each feature twice. It is why the app still works with no API keys at all.

---

## Author & license

Designed and built by **Ramdas Chaugale** as an individual portfolio project.
Licensed under the [MIT License](LICENSE). Copyright 2026 Ramdas Chaugale.
