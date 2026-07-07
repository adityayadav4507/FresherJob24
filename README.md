# JobFinder: Real-time Isolated Discovery Engine

JobFinder is a progressive job discovery dashboard that crawls active job listings for **fresher (0-1 years of experience) IT engineering roles in India or Remote**. It coordinates multiple crawler pipelines concurrently and traces execution in real-time.

---

## 🛠️ High-Level Design



                 +-----------------------------------+
                 |        Vite React Frontend        |
                 |  (Feeds, Logs Modal, Search Input)|
                 +-----------------+-----------------+
                                   |
                     1. POST /api/recommendations
                                   v
                 +-----------------------------------+
                 |    Recommendation Agent (Cached)  |
                 |     (Groq Llama-3.1, Temp=0.0)    |
                 +-----------------+-----------------+
                                   |
                  2. Returns targets roles list
                                   v
                 +-----------------------------------+
                 |          FastAPI Backend          |
                 +--------+-------+---------+--------+
                          |       |         |
      +-------------------+       |         +-------------------+
      | (POST /search/greenhouse) | (POST /search/lever)        | (POST /search/linkedin)
      v                           v                             v
+-----+---------------+     +-----+---------------+     +-------+-------------+
| Greenhouse Crawler  |     |    Lever Crawler    |     |  LinkedIn Crawler   |
| (Sequentially loop  |     | (Sequentially loop  |     | (Query Agent logic  |
|   60+ boards)       |     |   60+ boards)       |     |   + SerpApi search) |
+-----+---------------+     +-----+---------------+     +-------+-------------+
      |                           |                             |
      | 3. JSON parsed            | 3. JSON parsed              | 3. Organic hits text
      |    & Filtered             |    & Filtered               |    Groq JSON format
      v                           v                             v
+-----+---------------------------+-----------------------------+-------------+
|                         In-Memory Pipeline Logger                           |
|       (Logs matching and discard reasons. Exposes GET /api/logs/{pipeline}) |
+-----------------------------------------------------------------------------+


---

## 📁 Core Modules & Project Structure

The project is structured as follows:

```
job-finder-agent/
├── app/
│   ├── agents/
│   │   ├── recommendation_agent.py   # Alternative job roles recommender (cached, temperature=0.0)
│   │   └── query_agent.py            # Formulates LinkedIn search query strings
│   ├── app_utils/
│   │   └── pipeline_logger.py        # Thread-safe trace logs manager
│   ├── crawlers/
│   │   ├── greenhouse_crawler.py     # Greenhouse job board sequential crawlers & filters
│   │   ├── lever_crawler.py          # Lever job board sequential crawlers & filters
│   │   └── linkedin_crawler.py       # LinkedIn SerpApi & Groq search crawler
│   ├── fast_api_app.py                # FastAPI backend serving api endpoints & frontend static files
│   ├── tools.py                       # Company handles retrieval database helper
│   ├── greenhouse_companies.json      # Database of 60+ Greenhouse company handles
│   └── lever_companies.json          # Database of 60+ Lever company handles
├── frontend/
│   ├── src/
│   │   └── App.jsx                   # React Dashboard with logs viewer and category feeds
│   └── dist/                         # Compiled production frontend build assets
├── tests/                             # Pytest suite
├── .env.example                       # Reference environment variables file
└── pyproject.toml                     # Python dependencies file
```

### 1. Unified Recommendations (`recommendation_agent.py`)
- Initiated exactly once per user query to calculate equivalent IT engineering roles (e.g. searching "SDE" recommends "Software Engineer", "Software Developer", etc.).
- Implements a **thread-safe in-memory caching mechanism** to prevent redundant LLM invocations for duplicate role searches.
- Uses the Groq `llama-3.1-8b-instant` model with strict `temperature=0.0` for deterministic suggestions.

### 2. Sequential Crawling (`greenhouse_crawler.py` & `lever_crawler.py`)
- Loops through 60+ company boards **sequentially (one-by-one)** rather than concurrently to avoid API rate limits and conserve system resources.
- Verifies timestamp criteria (strictly older than 7 days is discarded) and experience patterns (excludes `1+ years` and senior keywords like "Senior", "Lead", "SDE-II", etc.).

### 3. LinkedIn Crawler (`linkedin_crawler.py`)
- Formulates a strict search query (e.g. `site:linkedin.com "India" ("SDE" OR "Software Engineer") ("Fresher" OR "0-1 years") after:YYYY-MM-DD`).
- Google Search is executed directly via the **SerpApi Google Search API** to fetch results.
- The raw search text is structured into a valid JSON object matching our jobs schema via the Groq completions endpoint.

### 4. Real-time Debug Logs (`pipeline_logger.py`)
- Records step-by-step trace events of every pipeline run.
- Log statements specify which jobs matched and precisely why others were filtered out (e.g. location mismatches, experience criteria, stale timestamps).
- Exposed via `GET /api/logs/{pipeline}` and displayed inside a terminal-style modal on the React dashboard.

---

## ⚙️ Environment Configuration

Create a `.env` file in the project root containing:

```env
# Groq API Configuration (Required for recommendations & LinkedIn formatting)
GROQ_API_KEY="your_groq_api_key"

# SerpApi API Configuration (Required for LinkedIn search)
SERPAPI_API_KEY="your_serpapi_api_key"
```

---

## 🚀 How to Run

### 1. Install Dependencies
Make sure you have `uv` installed, then run:
```bash
uv pip install -e .
uv pip install "google-adk[extensions]"
```

### 2. Build Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Start Backend server
```bash
uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser and navigate to `http://localhost:8000` to access the JobFinder dashboard.

### 4. Run Tests
```bash
uv run pytest tests/
```
