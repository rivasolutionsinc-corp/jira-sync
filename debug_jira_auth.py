#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script to test Jira authentication"""

import os
import sys
import requests
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from config/.env
env_path = Path(__file__).parent / "config" / ".env"
load_dotenv(env_path)

JIRA_URL = "https://cmext.ahrq.gov/jira"
JIRA_PAT = os.getenv("JIRA_PAT")
JIRA_USER = os.getenv("JIRA_USER", "")

print(f"JIRA_URL: {JIRA_URL}")
print(f"JIRA_PAT: {JIRA_PAT[:20]}..." if JIRA_PAT else "JIRA_PAT: NOT SET")
print(f"JIRA_USER: {JIRA_USER if JIRA_USER else 'NOT SET'}")
print()

# Test 1: Bearer token
print("Test 1: Bearer Token Authentication")
headers_bearer = {
    "Authorization": f"Bearer {JIRA_PAT}",
    "Content-Type": "application/json",
}
response = requests.get(f"{JIRA_URL}/rest/api/2/myself", headers=headers_bearer)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")
print()

# Test 2: Basic auth with PAT only
print("Test 2: Basic Auth (PAT as password, empty username)")
credentials = base64.b64encode(f":{JIRA_PAT}".encode()).decode()
headers_basic = {
    "Authorization": f"Basic {credentials}",
    "Content-Type": "application/json",
}
response = requests.get(f"{JIRA_URL}/rest/api/2/myself", headers=headers_basic)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")
print()

# Test 3: Basic auth with user and PAT
if JIRA_USER:
    print(f"Test 3: Basic Auth (user: {JIRA_USER}, password: PAT)")
    credentials = base64.b64encode(f"{JIRA_USER}:{JIRA_PAT}".encode()).decode()
    headers_basic_user = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
    }
    response = requests.get(f"{JIRA_URL}/rest/api/2/myself", headers=headers_basic_user)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
