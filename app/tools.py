import os
import json
import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger("job_finder.tools")

GREENHOUSE_COMPANIES_FILE = os.path.join(os.path.dirname(__file__), "greenhouse_companies.json")
LEVER_COMPANIES_FILE = os.path.join(os.path.dirname(__file__), "lever_companies.json")

def read_profile() -> Dict[str, Any]:
    """
    Returns dummy profile credentials for testing compatibility.
    """
    return {
        "name": "aditya yadav",
        "email": "aditya@example.com",
        "skills": ["Python", "React"],
        "projects": ["Job Finder App"]
    }

def read_greenhouse_companies() -> List[Dict[str, str]]:
    try:
        if os.path.exists(GREENHOUSE_COMPANIES_FILE):
            with open(GREENHOUSE_COMPANIES_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error reading Greenhouse companies list: {e}")
    return []

def read_lever_companies() -> List[Dict[str, str]]:
    try:
        if os.path.exists(LEVER_COMPANIES_FILE):
            with open(LEVER_COMPANIES_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error reading Lever companies list: {e}")
    return []

def read_companies() -> List[Dict[str, str]]:
    """
    Backwards-compatible union of Greenhouse and Lever lists.
    """
    gh = read_greenhouse_companies()
    for item in gh:
        item["type"] = "greenhouse"
        
    lev = read_lever_companies()
    for item in lev:
        item["type"] = "lever"
        
    return gh + lev

def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    return re.sub(cleanr, '', raw_html)
