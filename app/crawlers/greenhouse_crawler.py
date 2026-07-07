import re
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta, timezone
import dateutil.parser
from app.app_utils.pipeline_logger import pipeline_logger

logger = logging.getLogger("job_finder.greenhouse_crawler")

def clean_html(raw_html: str) -> str:
    """
    Strips HTML tags and unescapes text.
    """
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    return re.sub(cleanr, '', raw_html)

def filter_greenhouse_job(job: dict, recommended_roles: list[str]) -> bool:
    title = job.get("title", "")
    location_raw = job.get("location", {}).get("name", "").lower()
    updated_at_str = job.get("updated_at", "")
    
    # 1. Role Match Check using recommendation agent's target roles
    title_lower = title.lower()
    if not any(role.lower() in title_lower for role in recommended_roles):
        pipeline_logger.log("greenhouse", f"Job '{title}' discarded: does not match recommended roles {recommended_roles}")
        return False
        
    # 2. Location Check (Must be India or Remote, exclude foreign non-India remote)
    is_india = any(term in location_raw for term in ["india", "bangalore", "bengaluru", "mumbai", "pune", "delhi", "noida", "gurgaon", "hyderabad", "chennai", "remote", "gift city"])
    is_foreign = any(term in location_raw for term in ["united states", "us", "uk", "london", "canada", "europe", "germany", "singapore"]) and "india" not in location_raw
    if not is_india or is_foreign:
        pipeline_logger.log("greenhouse", f"Job '{title}' discarded: location '{location_raw}' is not India or Remote.")
        return False
        
    # 3. Strict 7-Day Time Check (only jobs updated in the last 7 days)
    if updated_at_str:
        try:
            updated_time = dateutil.parser.isoparse(updated_at_str)
            now = datetime.now(timezone.utc)
            if now - updated_time > timedelta(days=7):
                pipeline_logger.log("greenhouse", f"Job '{title}' discarded: older than 7 days (updated_at: {updated_at_str}).")
                return False
        except Exception as e:
            pipeline_logger.log("greenhouse", f"Job '{title}' discarded: invalid updated_at format '{updated_at_str}'. Error: {e}")
            return False
    else:
        pipeline_logger.log("greenhouse", f"Job '{title}' discarded: updated_at timestamp missing.")
        return False
            
    # 4. Strict Fresher/0-Year Experience Check (Discards 1+ years demands or senior titles)
    experience_exclude_pattern = re.compile(
        r"\b(?:1|2|3|4|5|6|7|8|9|10)\+?\s*(?:years?|yrs?)\b", 
        re.IGNORECASE
    )
    title_exclude_terms = [
        "senior", "lead", "staff", "manager", "principal", "sr.", "head", "architect",
        "sde-ii", "sde-2", "sde-iii", "sde-3", "ii", "iii", "lead", "experienced"
    ]
    if any(term in title_lower for term in title_exclude_terms) or experience_exclude_pattern.search(title_lower):
        pipeline_logger.log("greenhouse", f"Job '{title}' discarded: senior title or experience requirements found.")
        return False
        
    pipeline_logger.log("greenhouse", f"Job '{title}' matches all filters!")
    return True

async def fetch_greenhouse_jobs(session: aiohttp.ClientSession, company_name: str, handle: str, recommended_roles: list[str]) -> list:
    """
    Crawls Greenhouse boards API with error-handling and strict daily filtering.
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{handle}/jobs?content=true"
    pipeline_logger.log("greenhouse", f"Starting crawl for {company_name} ({url})")
    
    jobs = []
    try:
        # Enforce a short 6-second timeout per board
        async with session.get(url, timeout=6) as response:
            if response.status == 200:
                data = await response.json()
                results = data.get("jobs", [])
                pipeline_logger.log("greenhouse", f"Board '{company_name}' returned {len(results)} raw jobs.")
                for rj in results:
                    if filter_greenhouse_job(rj, recommended_roles):
                        jobs.append({
                            "id": f"greenhouse-{rj.get('id')}",
                            "title": rj.get("title"),
                            "company": company_name,
                            "location": rj.get("location", {}).get("name", "India"),
                            "url": rj.get("absolute_url"),
                            "description": clean_html(rj.get("content", "")),
                            "source": "Greenhouse",
                            "source_type": "startup",
                            "easy_apply": False,
                            "date_posted": datetime.now(timezone.utc).strftime("%b %d, %Y")
                        })
            else:
                pipeline_logger.log("greenhouse", f"Board '{company_name}' API returned error code: {response.status}")
    except asyncio.TimeoutError:
        pipeline_logger.log("greenhouse", f"Timeout error crawling board '{company_name}' after 6 seconds.")
    except aiohttp.ClientError as e:
        pipeline_logger.log("greenhouse", f"Client network error crawling board '{company_name}': {e}")
    except Exception as e:
        pipeline_logger.log("greenhouse", f"Unexpected error crawling board '{company_name}': {e}")
        
    return jobs
