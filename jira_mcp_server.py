# -*- coding: utf-8 -*-
"""Jira MCP server tools.

This module exposes Jira search, issue retrieval, issue creation, commenting,
and workflow transition operations through a FastMCP server.

Configuration:
- `JIRA_TOKEN` must be set in the environment for authenticated Jira API access.
- `JIRA_URL` is currently configured in this module.

Run this module directly to verify Jira access and start the MCP server.
"""

import os
import json
import sys
import requests
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Jira Skills")

# Configuration from environment (Roo passes these via mcp_settings.json)
JIRA_URL = "https://cmext.ahrq.gov/jira"
JIRA_TOKEN = os.getenv("JIRA_TOKEN")

def get_headers():
    """Standard headers for Jira API calls."""
    return {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

@mcp.tool()
def search_jira_issues(jql: str, max_results: int = 10) -> str:
    """
    Search for Jira issues using JQL (Jira Query Language).
    Example JQL: 'project = AQD AND text ~ "scaffolding"' or 'assignee = currentUser()'
    """
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {
        "jql": jql,
        "maxResults": max_results,
        "fields": "summary,status,assignee"
    }

    response = requests.get(url, headers=get_headers(), params=params)

    if response.status_code == 200:
        data = response.json()
        issues = data.get("issues", [])
        if not issues:
            return "No issues found matching that query."

        results = []
        for issue in issues:
            fields = issue.get("fields", {})
            results.append({
                "key": issue.get("key"),
                "summary": fields.get("summary"),
                "status": fields.get("status", {}).get("name"),
                "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned"
            })
        return json.dumps(results, indent=2)
    return f"Error searching issues: {response.status_code} - {response.text}"

@mcp.tool()
def get_jira_issue(issue_key: str) -> str:
    """Retrieve full details of a Jira issue by its key (e.g., AQD-1234)."""
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}"
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        data = response.json()
        fields = data.get("fields", {})
        result = {
            "key": data.get("key"),
            "summary": fields.get("summary"),
            "status": fields.get("status", {}).get("name"),
            "description": fields.get("description"),
            "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned"
        }
        return json.dumps(result, indent=2)
    return f"Error: {response.status_code} - {response.text}"

@mcp.tool()
def create_jira_issue(project_key: str, summary: str, description: str, issue_type: str = "Task") -> str:
    """Create a new Jira issue in a specific project."""
    url = f"{JIRA_URL}/rest/api/2/issue"
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type}
        }
    }
    response = requests.post(url, headers=get_headers(), json=payload)
    if response.status_code == 201:
        return f"Issue created successfully: {response.json()['key']}"
    return f"Error: {response.status_code} - {response.text}"

@mcp.tool()
def add_jira_comment(issue_key: str, comment: str) -> str:
    """Add a comment to an existing Jira issue."""
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/comment"
    payload = {"body": comment}
    response = requests.post(url, headers=get_headers(), json=payload)
    if response.status_code == 201:
        return f"Comment added to {issue_key}"
    return f"Error: {response.status_code} - {response.text}"

@mcp.tool()
def list_jira_transitions(issue_key: str) -> str:
    """List all available status transitions for a specific Jira issue."""
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/transitions"
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        transitions = response.json().get("transitions", [])
        if not transitions:
            return f"No available transitions found for {issue_key}."

        result = [{"id": t["id"], "name": t["name"]} for t in transitions]
        return json.dumps(result, indent=2)
    return f"Error fetching transitions: {response.status_code} - {response.text}"

@mcp.tool()
def transition_jira_issue(issue_key: str, transition_name: str) -> str:
    """Transition a Jira issue to a new status (e.g., 'Start Progress', 'Done')."""
    # 1. Get transitions
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/transitions"
    res = requests.get(url, headers=get_headers())
    if res.status_code != 200: return "Could not fetch transitions."

    transitions = res.json().get("transitions", [])
    tid = next((t["id"] for t in transitions if t["name"].lower() == transition_name.lower()), None)

    if not tid:
        available = ", ".join([t["name"] for t in transitions])
        return f"Transition '{transition_name}' not found. Available: {available}"

    # 2. Post transition
    response = requests.post(url, headers=get_headers(), json={"transition": {"id": tid}})
    if response.status_code == 204:
        return f"Successfully transitioned {issue_key} to {transition_name}"
    return f"Error: {response.status_code} - {response.text}"

def verify_access():
    """Startup check to verify project access and authentication."""
    print("Verifying Jira access...", file=sys.stderr)
    if not JIRA_TOKEN:
        print("Error: JIRA_TOKEN environment variable is not set.", file=sys.stderr)
        return False

    try:
        # Test 1: Auth check
        me_res = requests.get(f"{JIRA_URL}/rest/api/2/myself", headers=get_headers())
        if me_res.status_code != 200:
            print(f"Auth failed: {me_res.status_code}", file=sys.stderr)
            return False

        user = me_res.json().get("displayName")
        print(f"Authenticated as: {user}", file=sys.stderr)

        # Test 2: Project check (ADO & AQD)
        for pk in ["ADO", "AQD"]:
            p_res = requests.get(f"{JIRA_URL}/rest/api/2/project/{pk}", headers=get_headers())
            if p_res.status_code == 200:
                print(f"Access to {pk}: OK", file=sys.stderr)
            else:
                print(f"Access to {pk}: FAILED ({p_res.status_code})", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Connection error during startup: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if verify_access():
        mcp.run()
    else:
        sys.exit(1)