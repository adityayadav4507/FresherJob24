import os
import logging
import asyncio
import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from app.app_utils.pipeline_logger import pipeline_logger

# Setup load environment variables
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(ENV_FILE)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("job_finder.fast_api_app")

app = FastAPI(title="JobFinder API")

# Add CORS Middleware
allow_origins = os.getenv("ALLOW_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RecommendRequest(BaseModel):
    job_role: str

class SearchRequest(BaseModel):
    job_role: str
    recommended_roles: Optional[List[str]] = None

@app.post("/api/recommendations")
async def get_recommendations(payload: RecommendRequest):
    """
    Runs Recommendation Agent exactly once per query to determine target roles.
    """
    from app.agents.recommendation_agent import recommend_roles_with_llm
    job_role = payload.job_role.strip()
    roles = recommend_roles_with_llm(job_role)
    return {"recommended_roles": roles}

@app.post("/api/jobs/search/greenhouse")
async def search_greenhouse(payload: SearchRequest):
    """
    Crawls Greenhouse startup boards sequentially for the target role.
    """
    pipeline_logger.clear("greenhouse")
    pipeline_logger.log("greenhouse", f"Greenhouse Pipeline initiated for query role: '{payload.job_role}'")
    
    from app.crawlers.greenhouse_crawler import fetch_greenhouse_jobs
    from app.agents.query_agent import recommend_related_roles
    from app.tools import read_greenhouse_companies
    
    companies = read_greenhouse_companies()
    job_role = payload.job_role.strip()
    
    # Use recommended roles from payload if provided to avoid redundant agent calls
    recommended_roles = payload.recommended_roles
    if not recommended_roles:
        recommended_roles = recommend_related_roles(job_role)
        
    greenhouse_jobs = []
    async with aiohttp.ClientSession() as session:
        # Crawl company boards one-by-one sequentially
        for comp in companies:
            handle = comp.get("handle")
            name = comp.get("name")
            if not handle:
                continue
            try:
                res = await fetch_greenhouse_jobs(session, name, handle, recommended_roles)
                if isinstance(res, list):
                    greenhouse_jobs.extend(res)
            except Exception as e:
                pipeline_logger.log("greenhouse", f"Exception crawling board '{name}': {e}")
                
    pipeline_logger.log("greenhouse", f"Greenhouse Pipeline completed. Discovered {len(greenhouse_jobs)} filtered jobs.")
    return {"greenhouse": greenhouse_jobs[:30]}

@app.post("/api/jobs/search/lever")
async def search_lever(payload: SearchRequest):
    """
    Crawls Lever startup boards sequentially for the target role.
    """
    pipeline_logger.clear("lever")
    pipeline_logger.log("lever", f"Lever Pipeline initiated for query role: '{payload.job_role}'")
    
    from app.crawlers.lever_crawler import fetch_lever_jobs
    from app.agents.query_agent import recommend_related_roles
    from app.tools import read_lever_companies
    
    companies = read_lever_companies()
    job_role = payload.job_role.strip()
    
    recommended_roles = payload.recommended_roles
    if not recommended_roles:
        recommended_roles = recommend_related_roles(job_role)
        
    lever_jobs = []
    async with aiohttp.ClientSession() as session:
        # Crawl company boards one-by-one sequentially
        for comp in companies:
            handle = comp.get("handle")
            name = comp.get("name")
            if not handle:
                continue
            try:
                res = await fetch_lever_jobs(session, name, handle, recommended_roles)
                if isinstance(res, list):
                    lever_jobs.extend(res)
            except Exception as e:
                pipeline_logger.log("lever", f"Exception crawling board '{name}': {e}")
                
    pipeline_logger.log("lever", f"Lever Pipeline completed. Discovered {len(lever_jobs)} filtered jobs.")
    return {"lever": lever_jobs[:30]}

@app.post("/api/jobs/search/linkedin")
async def search_linkedin(payload: SearchRequest):
    """
    Crawls LinkedIn job view pages using Google Search / Bing fallback.
    """
    pipeline_logger.clear("linkedin")
    pipeline_logger.log("linkedin", f"LinkedIn Pipeline initiated for query role: '{payload.job_role}'")
    
    from app.crawlers.linkedin_crawler import fetch_linkedin_jobs
    from app.agents.query_agent import recommend_related_roles
    
    job_role = payload.job_role.strip()
    
    recommended_roles = payload.recommended_roles
    if not recommended_roles:
        recommended_roles = recommend_related_roles(job_role)
        
    loop = asyncio.get_event_loop()
    linkedin_jobs = await loop.run_in_executor(None, fetch_linkedin_jobs, job_role, recommended_roles)
    
    pipeline_logger.log("linkedin", f"LinkedIn Pipeline completed. Discovered {len(linkedin_jobs)} filtered jobs.")
    return {"linkedin": linkedin_jobs[:30]}

@app.get("/api/logs/{pipeline}")
async def get_pipeline_logs(pipeline: str):
    """
    Returns step-by-step logs for a specific pipeline.
    """
    if pipeline not in ["greenhouse", "lever", "linkedin"]:
        raise HTTPException(status_code=400, detail="Invalid pipeline name")
    return {"pipeline": pipeline, "logs": pipeline_logger.get_logs(pipeline)}

# --- STATIC FILES SERVICE MOUNT ---
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    static_dir = frontend_dist
    logger.info(f"Serving compiled React frontend from {static_dir}")
else:
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    logger.info(f"Serving fallback static assets from {static_dir}")

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

# Main execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.fast_api_app:app", host="0.0.0.0", port=8000, reload=True)
