import re
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta, timezone
from app.app_utils.pipeline_logger import pipeline_logger

logger = logging.getLogger("job_finder.lever_crawler")

def clean_html(raw_html: str) -> str:
    """
    Strips HTML tags and unescapes text.
    """
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    return re.sub(cleanr, '', raw_html)

def filter_lever_job(posting: dict, recommended_roles: list[str]) -> bool:
    title = posting.get("text") or posting.get("title") or ""
    location_raw = posting.get("categories", {}).get("location", "").lower()
    created_at_epoch = posting.get("createdAt")
    
    # 1. Role Match Check using recommendation agent's target roles
    title_lower = title.lower()
    if not any(role.lower() in title_lower for role in recommended_roles):
        pipeline_logger.log("lever", f"Job '{title}' discarded: does not match recommended roles {recommended_roles}")
        return False
        
    # 2. Location Check
    is_india = any(term in location_raw for term in ["india", "bangalore", "bengaluru", "mumbai", "pune", "delhi", "noida", "gurgaon", "hyderabad", "chennai", "remote", "gift city"])
    is_foreign = any(term in location_raw for term in ["united states", "us", "uk", "london", "canada", "europe", "germany", "singapore"]) and "india" not in location_raw
    if not is_india or is_foreign:
        pipeline_logger.log("lever", f"Job '{title}' discarded: location '{location_raw}' is not India or Remote.")
        return False
        
    # 3. Strict 7-Day Time Check (only jobs created in the last 7 days)
    if created_at_epoch:
        try:
            created_time = datetime.fromtimestamp(created_at_epoch / 1000.0, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            if now - created_time > timedelta(days=7):
                pipeline_logger.log("lever", f"Job '{title}' discarded: older than 7 days (created_at: {created_time}).")
                return False
        except Exception as e:
            pipeline_logger.log("lever", f"Job '{title}' discarded: invalid created_at timestamp '{created_at_epoch}'. Error: {e}")
            return False
    else:
        pipeline_logger.log("lever", f"Job '{title}' discarded: createdAt timestamp missing.")
        return False
            
    # 4. Strict Fresher/0-Year Experience Check
    experience_exclude_pattern = re.compile(
        r"\b(?:1|2|3|4|5|6|7|8|9|10)\+?\s*(?:years?|yrs?)\b", 
        re.IGNORECASE
    )
    title_exclude_terms = [
        "senior", "lead", "staff", "manager", "principal", "sr.", "head", "architect",
        "sde-ii", "sde-2", "sde-iii", "sde-3", "ii", "iii", "lead", "experienced"
    ]
    if any(term in title_lower for term in title_exclude_terms) or experience_exclude_pattern.search(title_lower):
        pipeline_logger.log("lever", f"Job '{title}' discarded: senior title or experience requirements found.")
        return False
        
    pipeline_logger.log("lever", f"Job '{title}' matches all filters!")
    return True

async def fetch_lever_jobs(session: aiohttp.ClientSession, company_name: str, handle: str, recommended_roles: list[str]) -> list:
    """
    Crawls Lever board postings API with error-handling and strict daily filtering.
    """
    url = f"https://api.lever.co/v0/postings/{handle}?mode=json"
    pipeline_logger.log("lever", f"Starting crawl for {company_name} ({url})")
    
    jobs = []
    try:
        async with session.get(url, timeout=6) as response:
            if response.status == 200:
                results = await response.json()
                pipeline_logger.log("lever", f"Board '{company_name}' returned {len(results)} raw jobs.")
                for rj in results:
                    if filter_lever_job(rj, recommended_roles):
                        jobs.append({
                            "id": f"lever-{rj.get('id')}",
                            "title": rj.get("text") or rj.get("title") or "Position",
                            "company": company_name,
                            "location": rj.get("categories", {}).get("location", "India"),
                            "url": rj.get("hostedUrl"),
                            "description": clean_html(rj.get("description", "") + " " + rj.get("requirements", "")),
                            "source": "Lever",
                            "source_type": "startup",
                            "easy_apply": False,
                            "date_posted": datetime.now(timezone.utc).strftime("%b %d, %Y")
                        })
            else:
                pipeline_logger.log("lever", f"Board '{company_name}' API returned error code: {response.status}")
    except asyncio.TimeoutError:
        pipeline_logger.log("lever", f"Timeout error crawling board '{company_name}' after 6 seconds.")
    except aiohttp.ClientError as e:
        pipeline_logger.log("lever", f"Client network error crawling board '{company_name}': {e}")
    except Exception as e:
        pipeline_logger.log("lever", f"Unexpected error crawling board '{company_name}': {e}")
        
    return jobs
