import os
import json
import logging
from groq import Groq
from threading import Lock
from app.app_utils.pipeline_logger import pipeline_logger

logger = logging.getLogger("job_finder.recommendation_agent")

# Global thread-safe cache to ensure recommendation agent runs exactly once per job role query
RECOMMENDATION_CACHE = {}
cache_lock = Lock()

def get_indexed_startup_roles() -> list[str]:
    """
    Retriever Tool: Returns a list of active IT engineering roles common in Indian startup boards.
    """
    return [
        "Software Engineer", "Software Developer", "Frontend Developer", "Backend Developer", 
        "Fullstack Developer", "SDE-1", "SDE-2", "Graduate Engineer Trainee", "GET",
        "Systems Engineer", "Developer Associate", "Programmer Analyst", "Application Developer",
        "AI Engineer", "ML Engineer", "Machine Learning Engineer", "NLP Developer", "GenAI Specialist",
        "LLM Engineer", "Deep Learning Scientist", "Data Scientist", "Data Analyst", "Data Engineer",
        "Business Analyst", "DevOps Engineer", "Cloud Engineer", "SRE", "Infrastructure Engineer",
        "Android Developer", "iOS Developer", "Mobile Engineer", "Quality Assurance Engineer",
        "QA Intern", "Software Development Intern", "ML Trainee", "Data Intern"
    ]

def fallback_recommender(job_role: str) -> list[str]:
    role_lower = job_role.lower().strip()
    recommendations = [job_role]
    
    if any(term in role_lower for term in ["sde", "software engineer", "developer", "software developer", "coder", "programmer"]):
        recommendations.extend(["Software Engineer", "Software Developer", "Developer", "SDE", "Programmer", "Coder", "Backend Developer", "Frontend Developer", "Fullstack Developer"])
    elif any(term in role_lower for term in ["ai", "ml", "machine learning", "genai", "artificial intelligence", "nlp", "llm", "agentic"]):
        recommendations.extend(["AI Engineer", "ML Engineer", "Machine Learning Engineer", "GenAI Developer", "NLP Engineer", "LLM Engineer", "Deep Learning Engineer", "Artificial Intelligence", "Agentic Developer"])
    elif any(term in role_lower for term in ["data", "analyst"]):
        recommendations.extend(["Data Engineer", "Data Analyst", "Data Scientist", "Business Analyst", "Database Engineer"])
    elif any(term in role_lower for term in ["devops", "cloud", "sre", "infrastructure"]):
        recommendations.extend(["DevOps Engineer", "Cloud Engineer", "SRE", "Site Reliability Engineer", "Systems Engineer"])
        
    seen = set()
    return [x for x in recommendations if not (x.lower() in seen or seen.add(x.lower()))]

def recommend_roles_with_llm(job_role: str) -> list[str]:
    """
    Recommendation Agent: Queries Groq Llama 3.1 8B to recommend 4 alternative tech job roles.
    Uses the get_indexed_startup_roles retriever tool to get active handles.
    Caches results to ensure the agent runs exactly once per job role query.
    """
    job_role_clean = job_role.strip().lower()
    
    # Check cache first
    with cache_lock:
        if job_role_clean in RECOMMENDATION_CACHE:
            roles = RECOMMENDATION_CACHE[job_role_clean]
            for p in ["greenhouse", "lever", "linkedin"]:
                pipeline_logger.log(p, f"Recommendation Agent: [CACHE HIT] Loaded stored roles for '{job_role}': {roles}")
            return roles

    api_key = os.getenv("GROQ_API_KEY")
    active_titles = get_indexed_startup_roles()
    
    if not api_key:
        logger.warning("GROQ_API_KEY missing. Falling back to programmatic recommender.")
        roles = fallback_recommender(job_role)
        with cache_lock:
            RECOMMENDATION_CACHE[job_role_clean] = roles
        for p in ["greenhouse", "lever", "linkedin"]:
            pipeline_logger.log(p, f"Recommendation Agent: GROQ_API_KEY missing. Stored fallback roles for '{job_role}': {roles}")
        return roles
        
    try:
        client = Groq(api_key=api_key)
        prompt = f"""
You are a job recommendation agent. Your task is to recommend equivalent job titles for a user who searched for the job role: "{job_role}".
Here is a list of active job titles available on startup boards (obtained from your retriever tool):
{active_titles}

Select the 4 most relevant titles from the list that match the user's search query. If none match perfectly, you can suggest appropriate alternative job titles from standard Indian IT job boards.
Return ONLY a valid JSON list of strings, for example: ["Title 1", "Title 2", "Title 3", "Title 4"]. Do not include markdown code block syntax or extra text.
"""
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        response_text = completion.choices[0].message.content.strip()
        
        # Clean markdown if present
        if "```" in response_text:
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        roles = json.loads(response_text)
        if isinstance(roles, list) and len(roles) > 0:
            with cache_lock:
                RECOMMENDATION_CACHE[job_role_clean] = roles
            for p in ["greenhouse", "lever", "linkedin"]:
                pipeline_logger.log(p, f"Recommendation Agent: recommended target roles for '{job_role}' and stored in cache: {roles}")
            return roles
    except Exception as e:
        logger.error(f"Error in LLM Recommendation Agent: {e}. Falling back.")
        
    roles = fallback_recommender(job_role)
    with cache_lock:
        RECOMMENDATION_CACHE[job_role_clean] = roles
    for p in ["greenhouse", "lever", "linkedin"]:
        pipeline_logger.log(p, f"Recommendation Agent: failed or exception encountered. Stored fallback roles for '{job_role}': {roles}")
    return roles
