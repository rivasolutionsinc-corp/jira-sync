#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple test to verify token loading"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from config/.env
env_path = Path(__file__).parent / "config" / ".env"
print(f"Loading from: {env_path}")
print(f"File exists: {env_path.exists()}")

load_dotenv(env_path)

# Check what's loaded
jira_pat = os.getenv("JIRA_PAT")
print(f"JIRA_PAT from env: {jira_pat[:30]}..." if jira_pat else "JIRA_PAT: NOT SET")

# Now set JIRA_TOKEN
os.environ["JIRA_TOKEN"] = jira_pat
jira_token = os.getenv("JIRA_TOKEN")
print(f"JIRA_TOKEN set to: {jira_token[:30]}..." if jira_token else "JIRA_TOKEN: NOT SET")

# Import and check
from jira_integration_script import JIRA_TOKEN
print(f"JIRA_TOKEN in script: {JIRA_TOKEN[:30]}..." if JIRA_TOKEN else "JIRA_TOKEN in script: NOT SET")
