import logging
from datetime import datetime, timedelta, timezone
from app.app_utils.pipeline_logger import pipeline_logger

logger = logging.getLogger("job_finder.query_agent")

def generate_linkedin_query_with_llm(job_role: str, recommended_roles: list[str]) -> str:
    """
    Query Agent: Dynamically structures a strict Google Search query targeting fresher listings in India from 24h to 48h ago.
    """
    # Calculate date for 2 days ago
    two_days_ago = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
    
    # Format recommended roles list, e.g. ("SDE" OR "Software Engineer")
    roles_subquery = " OR ".join([f'"{role}"' for role in recommended_roles])
    
    # Construct strict query format targeting the last 2 days
    query = (
        f'site:linkedin.com "India" ({roles_subquery}) '
        f'("Fresher" OR "0-1 years" OR "Entry Level" OR "Graduate") '
        f'after:{two_days_ago} -"years ago" -"months ago" -"3+ years" -"5+ years" -"No longer accepting applications"'
    )
    
    pipeline_logger.log("linkedin", f"Query Agent: Generated advanced Google/LinkedIn search query:\n{query}")
    logger.info(f"Query Agent generated advanced query: {query}")
    return query

def generate_linkedin_query(job_role: str, recommended_roles: list[str]) -> str:
    return generate_linkedin_query_with_llm(job_role, recommended_roles)

def recommend_related_roles(job_role: str) -> list[str]:
    from app.agents.recommendation_agent import recommend_roles_with_llm
    return recommend_roles_with_llm(job_role)
