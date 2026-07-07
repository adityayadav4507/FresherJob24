import os
from datetime import datetime, timedelta, timezone
from app.tools import read_profile, read_companies, clean_html

def test_read_profile():
    profile = read_profile()
    assert isinstance(profile, dict)
    assert "name" in profile
    assert profile["name"].lower() == "aditya yadav"
    assert "email" in profile
    assert "skills" in profile
    assert "projects" in profile

def test_read_companies():
    companies = read_companies()
    assert isinstance(companies, list)
    assert len(companies) > 0
    assert "handle" in companies[0]
    assert "type" in companies[0]
    assert "name" in companies[0]

def test_clean_html():
    raw_html = "<p>Software Engineer <strong>Job Description</strong></p>"
    clean_text = clean_html(raw_html)
    assert "Software Engineer" in clean_text
    assert "Job Description" in clean_text
    assert "<p>" not in clean_text
