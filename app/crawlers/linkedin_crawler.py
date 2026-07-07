import re
import os
import json
import logging
import urllib.request
import urllib.parse
from groq import Groq
from app.agents.query_agent import generate_linkedin_query
from app.app_utils.pipeline_logger import pipeline_logger

logger = logging.getLogger("job_finder.linkedin_crawler")

def is_date_in_24h_to_48h(date_str: str) -> bool:
    """
    Validates if the parsed date string falls strictly in the 24h to 48h range.
    Returns True if date_str is None (until parsed).
    """
    if not date_str:
        return True
    date_lower = date_str.lower().strip()
    
    keep_terms = ["1 day ago", "2 days ago", "24 hours ago", "48 hours ago", "yesterday", "1d ago", "2d ago"]
    if any(term in date_lower for term in keep_terms):
        return True
        
    discard_terms = [
        "hour", "hours", "minute", "minutes", "second", "seconds", "today", "now", "just now", "h ago", "m ago",
        "3 days", "4 days", "5 days", "6 days", "7 days", "week", "weeks", "month", "months", "year", "years",
        "3d ago", "4d ago", "5d ago", "6d ago", "w ago", "mo ago", "yr ago"
    ]
    if any(term in date_lower for term in discard_terms):
        return False
        
    return True

def filter_linkedin_job(title: str, snippet: str, recommended_roles: list[str], date_posted: str = None) -> bool:
    title_lower = title.lower()
    snippet_lower = snippet.lower()
    
    # 1. Role Match Check
    if not any(role.lower() in title_lower for role in recommended_roles) and not any(role.lower() in snippet_lower for role in recommended_roles):
        return False
        
    # 2. Strict Fresher/0-Year Experience Exclusion Filter
    experience_exclude_pattern = re.compile(
        r"\b(?:1|2|3|4|5|6|7|8|9|10)\+?\s*(?:years?|yrs?)\b", 
        re.IGNORECASE
    )
    title_exclude_terms = [
        "senior", "lead", "staff", "manager", "principal", "sr.", "head", "architect",
        "sde-ii", "sde-2", "sde-iii", "sde-3", "ii", "iii", "lead", "experienced"
    ]
    if any(term in title_lower for term in title_exclude_terms) or experience_exclude_pattern.search(title_lower) or experience_exclude_pattern.search(snippet_lower):
        return False
        
    # 3. Time Windows Exclusions (using raw texts)
    old_indicators = [
        "year ago", "years ago", "month ago", "months ago", 
        "weeks ago", "week ago", "30+ days ago", "15+ days ago",
        "3+ weeks ago", "4+ weeks ago"
    ]
    if any(ind in title_lower or ind in snippet_lower for ind in old_indicators):
        return False
        
    # 4. Strict 24h-48h Date Validation
    if not is_date_in_24h_to_48h(date_posted):
        return False
        
    pipeline_logger.log("linkedin", f"Job '{title}' matches all filters!")
    return True

def fetch_serpapi_google_search(query: str) -> str:
    """
    Executes search using the SerpApi Google Search engine directly.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key or api_key == "your_serpapi_key":
        pipeline_logger.log("linkedin", "SERPAPI_API_KEY is missing or set to placeholder in .env. Please configure it to enable LinkedIn search.")
        return ""
        
    url = f"https://serpapi.com/search.json?engine=google&q={urllib.parse.quote(query)}&api_key={api_key}"
    pipeline_logger.log("linkedin", f"Requesting SerpApi Search: https://serpapi.com/search.json?engine=google&q={query}")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                organic_results = data.get("organic_results", [])
                pipeline_logger.log("linkedin", f"SerpApi returned {len(organic_results)} organic search results.")
                
                formatted_text = ""
                for idx, item in enumerate(organic_results, 1):
                    formatted_text += f"{idx}. Title: {item.get('title')}\nLink: {item.get('link')}\nSnippet: {item.get('snippet')}\n\n"
                return formatted_text
            else:
                pipeline_logger.log("linkedin", f"SerpApi API returned HTTP status: {response.status}")
    except Exception as e:
        pipeline_logger.log("linkedin", f"SerpApi API call failed: {e}")
        
    return ""

def fetch_linkedin_jobs(job_role: str, recommended_roles: list[str]) -> list:
    """
    Crawls LinkedIn jobs:
    Exclusively uses the SerpApi Google Search engine directly to retrieve search results.
    Applies strict Groq Llama-3.1 parsing and structures output in JSON format.
    """
    query = generate_linkedin_query(job_role, recommended_roles)
    
    # 1. Direct Search Call using SerpApi Google Search
    raw_search_text = fetch_serpapi_google_search(query)
    
    if not raw_search_text:
        pipeline_logger.log("linkedin", "Search failed to return any results from SerpApi.")
        return []
        
    pipeline_logger.log("linkedin", f"SerpApi Search completed successfully. Raw output:\n{raw_search_text}")
        
    # 2. Formatting and Structuring using Groq API
    api_key_groq = os.getenv("GROQ_API_KEY")
    if not api_key_groq:
        pipeline_logger.log("linkedin", "GROQ_API_KEY missing. Cannot extract structured output.")
        return []
        
    client_groq = Groq(api_key=api_key_groq)
    format_prompt = f"""
Analyze the following raw search output containing LinkedIn job listings:
---
{raw_search_text}
---

Extract the job listings into a structured JSON object with key "jobs" containing a list of job objects.
Each job object must have:
- "title": Job title (e.g. 'Software Engineer Intern')
- "company": Company name (e.g. 'CRED')
- "url": The full LinkedIn URL (or company URL if it's the only one provided)
- "description": Snippet details
- "location": Job location in India or Remote
- "date_posted": Parse the posted date/time if explicitly mentioned in the text (e.g. '2 hours ago', '1 day ago'). STRICTLY set to null if not explicitly mentioned in the text.

Rules:
1. Validate that the URL is a valid LinkedIn domain link (e.g. linkedin.com/jobs, linkedin.com/company, linkedin.com/posts, or in.linkedin.com). Discard other domains.
2. Return ONLY a valid JSON object. Do not include markdown wraps or explanations.
"""
    
    pipeline_logger.log("linkedin", "Calling Groq (llama-3.1-8b-instant) to format raw search results into JSON...")
    try:
        response = client_groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You help extract job listings into a structured JSON schema. Respond only with a valid JSON object."},
                {"role": "user", "content": format_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        json_output = response.choices[0].message.content
        pipeline_logger.log("linkedin", f"Groq JSON formatter returned:\n{json_output}")
        
        jobs_data = json.loads(json_output)
        raw_jobs = jobs_data.get("jobs", [])
        pipeline_logger.log("linkedin", f"Groq formatter extracted {len(raw_jobs)} raw jobs from search.")
        
        filtered_jobs = []
        for idx, job in enumerate(raw_jobs):
            title = job.get("title", "LinkedIn Job Listing")
            company = job.get("company", "LinkedIn Partner Company")
            url = job.get("url", "")
            description = job.get("description", "")
            location = job.get("location", "India")
            date_posted = job.get("date_posted")
            
            if "linkedin.com" not in url:
                continue
                
            snippet = f"{description} | Location: {location} | Posted: {date_posted}"
            if filter_linkedin_job(title, snippet, recommended_roles, date_posted):
                filtered_jobs.append({
                    "id": f"linkedin-adk-{idx}",
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "description": description,
                    "source": "LinkedIn",
                    "source_type": "linkedin",
                    "easy_apply": False,
                    "date_posted": date_posted
                })
                
        pipeline_logger.log("linkedin", f"LinkedIn crawler finished. Found and filtered {len(filtered_jobs)} matching jobs.")
        return filtered_jobs
    except Exception as e:
        pipeline_logger.log("linkedin", f"Groq job formatting or parsing failed: {e}")
        return []

# Alias for backwards compatibility
fetch_linkedin_jobs_via_google = fetch_linkedin_jobs
