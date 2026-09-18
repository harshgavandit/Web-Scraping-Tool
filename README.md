# Brand Chatter — Google Brand Intelligence

An end-to-end brand intelligence dashboard for marketing teams, demonstrated with **Nike**. It collects only real, publicly accessible pages through Google Search, Google News RSS, and curated publisher RSS/Atom feeds; it preserves original links and evidence, extracts product feedback, and turns it into auditable recommendations.

The platform transforms noisy public-web coverage and customer feedback into **one unified, actionable dashboard** centered around a core intelligence table, compact KPI metrics, and an executive AI brand pulse.

---

## Architecture Diagram

```
                              ┌──────────────────────────────────────────────────────────┐
                              │                    PUBLIC WEB SOURCES                    │
                              │ Google Search API | Google News | Curated publisher RSS │
                              └────────────────────────────┬─────────────────────────────┘
                                                           │
                                                           ▼
                              ┌──────────────────────────────────────────────────────────┐
                              │                    MODULAR COLLECTORS                    │
                              │ Google Search + Google News + publisher RSS/Atom adapters│
                              └────────────────────────────┬─────────────────────────────┘
                                                           │
                                                           ▼
                              ┌──────────────────────────────────────────────────────────┐
                              │                COST-OPTIMIZED PIPELINE                   │
                              │ 1. Normalize Text & URLs (strip utm_*, fbclid tracking)  │
                              │ 2. Deduplicate (source+id, canonical URL, SHA-256 hash)  │
                              │ 3. Relevance Filter (keyword/product/competitor context) │
                              │ 4. Local Sentiment (Free VADER - 0 API cost)             │
                              │ 5. Product/aspect evidence + observable attention score  │
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
                              │ /api/intelligence, /api/alerts, /api/audit, exports     │
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

- **The Main Intelligence Table**: Preserves publisher, publication date, original URL, topic, product, competitor, sentiment, AI summary, and recommended action while retaining server-side filters and pagination.
- **Evidence-Backed Executive Pulse**: Synthesizes sentiment, top risks, source quotations, recommendation ownership, and P0/P1/P2 priority with data-version caching.
- **Product and Reputation Intelligence**: Extracts product-level praise and complaints, aspect evidence, independent-source corroboration, attention, and reputation-risk clusters.
- **Local + Gemini 3.8 Flash Analysis**: Employs free local VADER for sentiment, reserving Gemini for batched summaries, topics, and actionable recommendations with a deterministic local fallback.
- **Real Google Discovery**: Google Search and Google News query brand presence, feedback, reviews, complaints, trending coverage, blogs, competitor comparisons, and configured products. No synthetic conversations are generated.
- **Original-Page Evidence**: Respectful page fetching checks public-network targets and robots rules, validates every redirect, extracts canonical page content and structured review data, and stores immutable snapshots.
- **Enterprise Workflow**: Team saved views, SMTP email alerts, in-app acknowledgement/resolution, CSV/PDF exports, discovery audit records, and per-analysis AI provider/model/status trails.
- **Actionable Navigation & Filters**: Dashboard quick filters and sidebar views reset conflicting criteria, apply the appropriate server-side filters/sort order, and focus the conversation table. Topic and competitor chips can be toggled directly.
- **Editable Brand Portfolio**: Brand Settings can add or remove tracked competitors, products, campaigns, and keywords. Duplicate entries are rejected case-insensitively and all mutations are persisted through the API.
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
| **Primary AI / LLM** | **Google Gemini 3.5 Flash** (`gemini-3.5-flash` via REST API) |
| **Secondary AI Fallback**| OpenAI API (`gpt-4o-mini`) / Local Heuristic Parser |
| **Scheduling / Alerts** | APScheduler + SMTP email delivery |

---

## Cost-Saving Strategy

Sending every discovered page individually to a cloud LLM is prohibitively expensive. This platform enforces strict sequential processing to reduce AI inference costs:

```text
Collect
→ Clean
→ Deduplicate
→ Relevance filter
→ Local sentiment
→ Original-page evidence extraction
→ Product/aspect and attention scoring
→ Select important posts
→ Batch posts (AI_BATCH_SIZE = 20)
→ Gemini 3.5 Flash (Low thinking/reasoning for bulk)
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

# Seed only the Nike brand, competitors, and tracked keywords
python backend/seed_data.py

# Start FastAPI development server
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

FastAPI will be running at `http://localhost:8000`.
- API Health: `http://localhost:8000/api/health`
- Interactive Swagger Docs: `http://localhost:8000/docs`

With the backend running, collect current public news and web feedback from another terminal (or use the dashboard's **Data Collectors** dialog):

```bash
curl -X POST http://localhost:8000/api/collection/run -H "Content-Type: application/json" -d '{"source":"all","brand_id":1}'
```

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
| `GEMINI_MODEL` | `gemini-3.5-flash` | Configurable Gemini model identifier |
| `AI_BATCH_SIZE` | `20` | Maximum posts per batch inference call |
| `AI_ANALYSIS_ENABLED` | `true` | Enable or disable LLM enrichment |
| `OPENAI_API_KEY` | *Empty* | Optional secondary fallback OpenAI API Key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Configurable OpenAI fallback model name |
| `RSS_ENABLED` | `true` | Enable Google News RSS collector |
| `PUBLISHER_RSS_ENABLED` | `true` | Enable the curated Nike publisher RSS/Atom collector |
| `PUBLISHER_RSS_FEEDS` | *Empty* | Optional newline-separated `Publisher name|feed URL` entries; overrides the curated Nike feeds |
| `GOOGLE_SEARCH_ENABLED` | `false` | Enable the Google Search collector after API credentials are configured |
| `GOOGLE_SEARCH_API_KEY` | *Empty* | Google Custom Search JSON API key (backend-only) |
| `GOOGLE_SEARCH_ENGINE_ID` | *Empty* | Programmable Search Engine identifier (`cx`) |
| `GOOGLE_SEARCH_COUNTRY` | `US` | Country used for Google discovery |
| `GOOGLE_SEARCH_LANGUAGE` | `en` | Language used for Google discovery |
| `PAGE_FETCH_ENABLED` | `true` | Fetch eligible original public pages for evidence extraction |
| `PAGE_FETCH_LIMIT_PER_RUN` | `30` | Maximum original pages enriched during one collector run |
| `EMAIL_ALERTS_ENABLED` | `false` | Enable reputation-risk email delivery |
| `EMAIL_ALERT_RECIPIENTS` | *Empty* | Comma-separated brand/PR recipients |
| `SMTP_HOST` | *Empty* | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_USERNAME` | *Empty* | SMTP login username, when required |
| `SMTP_PASSWORD` | *Empty* | SMTP login password or app password |
| `SMTP_FROM_EMAIL` | *Empty* | Verified sender address |
| `SMTP_USE_TLS` | `true` | Upgrade the SMTP connection with STARTTLS |
| `APP_PUBLIC_URL` | `http://localhost:5173` | Dashboard URL placed in alert emails |
| `COLLECTION_INTERVAL_MINUTES` | `60` | Background scheduler collection interval |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed CORS origins (comma-separated) |

---

## Attention and Reputation Risk

Google-indexed pages do not provide uniform likes, comments, or shares. The platform therefore avoids fabricated virality and calculates **attention** from observable signals: publication recency, Google result position, and published review volume where structured page data exposes it. Reputation risk is calculated only from negative evidence, independent-source diversity, growth, and extraction confidence. The exact reasons are stored with every score.

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

### Data provenance and audits

- Every Google query and run is stored with category, locale, status, result counts, and errors; `/api/audit` exposes the source trail.
- Each discovered result retains its Google rank, query, category, displayed domain, discovery timestamps, and original HTTP(S) URL.
- Original-page documents record canonical URL, publisher, content status, robots decision, HTTP status, extracted structured review data, and content-hash snapshots.
- Each AI result records provider, model, completion/fallback status, analysis version, source URL, and analysis timestamp. The post drawer displays this audit metadata.
- Google News and Search do not consistently expose social engagement. Missing engagement remains zero and is never fabricated; those pages use observable attention signals such as recency, search position, and published review count.
- Failed source, page, AI, and email operations are retained as operational/audit state rather than silently replaced with fake data.

### Email alerts

Email is disabled by default. Configure the `SMTP_*` fields, `EMAIL_ALERT_RECIPIENTS`, and `EMAIL_ALERTS_ENABLED=true`. After a collection run rebuilds reputation clusters, **Elevated** and **Critical** risks create alerts and send one email per severity level. Delivery status, recipients, timestamp, and failure reason are retained. If an Elevated issue later becomes Critical, a new escalation email is sent; repeated runs at the same level are deduplicated.

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
- **Google API availability**: Google Search collection requires an eligible Custom Search JSON API / Programmable Search Engine configuration; Google News RSS and the curated publisher RSS/Atom feeds remain available independently.
- **Page access**: Paywalls, robots exclusions, private-network targets, unsupported content types, and unreachable sites remain snippet-only or blocked by design.
- **Alert channels**: SMTP email is implemented; Slack/Teams/webhook channels are not included.
