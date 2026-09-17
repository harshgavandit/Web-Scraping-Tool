# Brand Chatter & Social Listening Platform

An end-to-end, low-cost social listening and brand intelligence dashboard designed for brand managers and marketing teams (demonstrated with **Nike** and its primary competitors: **Adidas, Puma, New Balance, and Under Armour**).

The platform transforms thousands of noisy social conversations into **one unified, actionable dashboard** centered around a core hero table, compact KPI metrics, and an executive AI brand pulse.

---

## Architecture Diagram

```
                              ┌──────────────────────────────────────────────────────────┐
                              │                    SOCIAL DATA SOURCES                   │
                              │   Reddit API/Public | Facebook API/Mock | RSS / Web Feeds│
                              └────────────────────────────┬─────────────────────────────┘
                                                           │
                                                           ▼
                              ┌──────────────────────────────────────────────────────────┐
                              │                    MODULAR COLLECTORS                    │
                              │   app/collectors/ (reddit, facebook, rss, web, mock)     │
                              └────────────────────────────┬─────────────────────────────┘
                                                           │
                                                           ▼
                              ┌──────────────────────────────────────────────────────────┐
                              │                COST-OPTIMIZED PIPELINE                   │
                              │ 1. Normalize Text & URLs (strip utm_*, fbclid tracking)  │
                              │ 2. Deduplicate (source+id, canonical URL, SHA-256 hash)  │
                              │ 3. Relevance Filter (keyword/product/competitor context) │
                              │ 4. Local Sentiment (Free VADER - 0 API cost)             │
                              │ 5. Virality Velocity Engine (momentum scoring 0-100)     │
                              │ 6. Batch High-Value Posts (configurable batch size = 20) │
                              │ 7. Gemini 3.8 Flash Analysis (structured JSON output)    │
                              │    ↳ Fallbacks: OpenAI (optional) or Local Heuristics    │
                              └────────────────────────────┬─────────────────────────────┘
                                                           │
                                                           ▼
                              ┌──────────────────────────────────────────────────────────┐
                              │                    DATABASE LAYER                        │
                              │   PostgreSQL / Supabase (SQLAlchemy 2.0 + Alembic)       │
                              │   Zero-daemon local SQLite fallback supported            │
                              └────────────────────────────┬─────────────────────────────┘
                                                           │
                                                           ▼
                              ┌──────────────────────────────────────────────────────────┐
                              │                   FASTAPI REST API                       │
                              │   /api/posts, /api/dashboard/summary, /api/topics        │
                              │   /api/collection/run, /api/brands, /api/health          │
                              └────────────────────────────┬─────────────────────────────┘
                                                           │
                                                           ▼
                              ┌──────────────────────────────────────────────────────────┐
                              │                 REACT + VITE DASHBOARD                   │
                              │   KPI Cards | Executive AI Summary | MAIN HERO TABLE     │
                              │   Filter Bar | Search | Server Pagination | Drawer       │
                              └──────────────────────────────────────────────────────────┘
```

---

## Key Features

- **The Main Hero Table**: Single source of truth displaying Source, Published Date, Post Content, Brand, Competitor, Topic, Sentiment, Engagement Breakdown, Virality Score, Trend Direction, AI Summary, and Actionable Marketing Recommendations.
- **Executive AI Brand Pulse**: Automatically synthesizes brand sentiment distribution, fastest growing topic, and recommended strategic actions with intelligent caching (zero LLM calls on dashboard refresh).
- **Virality Scoring Algorithm**: Identifies rapidly accelerating posts by analyzing engagement velocity per hour ($\text{engagement} / \text{age}$), volume, and debate ratios.
- **Local + Gemini 3.8 Flash Sentiment**: Employs free local VADER for 90%+ of social volume, reserving Gemini 3.8 Flash for batched summaries, topics, and actionable recommendations with low-reasoning configuration.
- **Modular Collector Architecture**: Pluggable adapters for Reddit, Facebook, RSS Feeds, Generic Web scraping, and high-fidelity mock feeds.
- **3-Layer Deduplication**: Prevents reprocessing via external IDs, normalized canonical URLs, and SHA-256 content hashing.
- **Sub-150ms Performance**: Handles 10,000+ posts with server-side pagination, indexed joins, and zero N+1 queries.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, Lucide Icons |
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic |
| **Database** | PostgreSQL (Supabase compatible) / SQLite fallback |
| **Sentiment** | VADER (`vaderSentiment`) + retail domain cues |
| **Primary AI / LLM** | **Google Gemini 3.8 Flash** (`gemini-3.8-flash` via REST API) |
| **Secondary AI Fallback**| OpenAI API (`gpt-4o-mini`) / Local Heuristic Parser |
| **Scheduling** | APScheduler (in-process background scheduler) |

---

## Cost-Saving Strategy

Sending every single raw social post individually to a cloud LLM is prohibitively expensive. This platform enforces strict sequential processing to reduce AI inference costs by up to **95%**:

```text
Collect
→ Clean
→ Deduplicate
→ Relevance filter
→ Local sentiment
→ Virality calculation
→ Select important posts
→ Batch posts (AI_BATCH_SIZE = 20)
→ Gemini 3.8 Flash (Low thinking/reasoning for bulk)
→ Store results
→ Dashboard (Cached serving)
```

1. **Deduplication First**: Duplicate posts, reposts, and syndicated spam are filtered out before sentiment or AI analysis.
2. **Local Lexicon Sentiment**: Free local VADER classifies obvious positive and negative posts at zero marginal cost.
3. **Structured Batching**: Unanalyzed and high-priority posts are batched into requests of 20 posts per prompt.
4. **Intelligent Caching**: Executive summaries and topic trends are cached based on brand, date window, and data version. No AI calls occur on dashboard refreshes.
5. **Configurable Model**: Defaults to `gemini-3.8-flash` via `GEMINI_MODEL`, with seamless fallback to OpenAI or local heuristics if keys are absent or rate-limited.

---

## Quickstart & Local Setup

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** & **npm**
- *(Optional)* **Docker** (if running local PostgreSQL container)

### 1. Database & Environment Configuration

Copy the sample environment file:

```bash
cp .env.example .env
```

To run with PostgreSQL (via Docker Compose):
```bash
docker compose up -d
```
Then configure in `.env`:
```env
DATABASE_URL=postgresql+psycopg2://postgres:postgrespassword@localhost:5432/brand_chatter
```

If local application-control policy blocks the native `psycopg2` extension, use the included pure-Python driver instead:

```env
DATABASE_URL=postgresql+pg8000://postgres:postgrespassword@localhost:5432/brand_chatter
```

To run with zero external daemons (using local SQLite):
```env
DATABASE_URL=sqlite:///./brand_chatter.db
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run database migrations
alembic -c backend/alembic.ini upgrade head

# Seed Nike brand and 80+ realistic social records
python backend/seed_data.py

# Start FastAPI development server
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

FastAPI will be running at `http://localhost:8000`.
- API Health: `http://localhost:8000/api/health`
- Interactive Swagger Docs: `http://localhost:8000/docs`

### 3. Frontend Setup

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The React dashboard will be available at `http://localhost:5173`.

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./brand_chatter.db` | PostgreSQL connection string or SQLite path |
| `AI_PROVIDER` | `gemini` | Primary AI provider (`gemini` or `openai`) |
| `GEMINI_API_KEY` | *Empty* | Google Gemini API Key (backend-only, offline fallback if unset) |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Configurable Gemini model identifier |
| `AI_BATCH_SIZE` | `20` | Maximum posts per batch inference call |
| `AI_ANALYSIS_ENABLED` | `true` | Enable or disable LLM enrichment |
| `OPENAI_API_KEY` | *Empty* | Optional secondary fallback OpenAI API Key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Configurable OpenAI fallback model name |
| `REDDIT_ENABLED` | `false` | Enable live Reddit collection |
| `REDDIT_CLIENT_ID` | *Empty* | Reddit OAuth Client ID |
| `REDDIT_CLIENT_SECRET` | *Empty* | Reddit OAuth Client Secret |
| `REDDIT_USER_AGENT` | `BrandChatterBot/1.0` | Reddit User-Agent header |
| `FACEBOOK_ENABLED` | `false` | Enable Facebook Graph API collection |
| `FACEBOOK_ACCESS_TOKEN` | *Empty* | Facebook Graph API User/Page Token |
| `RSS_ENABLED` | `true` | Enable Google News RSS collector |
| `COLLECTION_INTERVAL_MINUTES` | `60` | Background scheduler collection interval |
| `VIRAL_THRESHOLD` | `85` | Virality score threshold for `is_viral=true` |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed CORS origins (comma-separated) |

---

## Virality Scoring Formula

The platform prioritizes **momentum and engagement velocity** over historical total likes:

$$\text{engagement} = \text{likes} + (2.5 \times \text{comments}) + (3.5 \times \text{shares})$$

$$\text{age\_hours} = \max\left(\frac{\text{now} - \text{published\_at}}{3600}, 0.5\right)$$

$$\text{velocity} = \frac{\text{engagement}}{\text{age\_hours}}$$

- **Velocity Component (70%)**: Log/exponential curve mapping velocity to 0–100 points.
- **Volume Component (30%)**: Logarithmic scaling for absolute size.
- **Virality Levels**:
  - `0 – 39`: **Low**
  - `40 – 64`: **Medium**
  - `65 – 84`: **High**
  - `85 – 100`: **Viral** (`is_viral = true`)

---

## Testing & Verification

### Running Backend Tests
```bash
# Run 22 unit & integration tests
.venv\Scripts\python.exe -m pytest -v backend/tests
```

### Running Frontend Tests
```bash
cd frontend
npm test
```

### Running Frontend Production Build
```bash
cd frontend
npm run build
```

### Benchmarking 10,000+ Records
To test index and pagination responsiveness under heavy loads:
```bash
python backend/generate_bulk_test_data.py 10000
```

---

## Deployment Guide

### Frontend Deployment (Static Hosting)
The frontend builds to static assets in `frontend/dist`. You can deploy it for free or very low cost on:
- **Vercel** / **Netlify** / **Cloudflare Pages**
- Set Build Command: `npm run build`
- Set Output Directory: `dist`
- Configure API proxy or set environment variable for the backend endpoint.

### Backend Deployment (Low-Cost Python Host)
Deploy to Render, Railway, Fly.io, or AWS App Runner:
- Build Command: `pip install -r backend/requirements.txt`
- Start Command: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
- Set environment variables in the host dashboard.

### Database Deployment
- Connect directly to **Supabase**, **Neon**, or **AWS RDS PostgreSQL** by providing the `DATABASE_URL` in the environment variables.

---

## Known Limitations & Future Improvements

- **Authentication**: MVP is designed for single marketing teams; multi-tenant RBAC can be added cleanly via SQLAlchemy Organization relationship.
- **Additional Networks**: Ready for Instagram Graph API, TikTok Creative Center, and YouTube Data API collectors.
- **Alerting**: Webhook and Slack notification triggers for posts surpassing virality score 90+.
