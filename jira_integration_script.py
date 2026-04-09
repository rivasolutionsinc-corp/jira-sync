# -*- coding: utf-8 -*-
"""Jira Integration Script

Refactored to use Atlassian MCP tools via mcp_client wrapper.
Maintains backward compatibility with existing function signatures.

Original file: https://colab.research.google.com/drive/1vykBrsFixtw9MSv5sC6vE5wbqkvmw85b
"""

import requests
import json
import sys
import os
import time
import re
import argparse
from datetime import datetime

# Configuration - Use environment variables for security
JIRA_URL = os.getenv("JIRA_URL", "https://cmext.ahrq.gov/jira")
JIRA_TOKEN = os.getenv(
    "JIRA_TOKEN",
    os.getenv("JIRA_API_TOKEN", os.getenv("JIRA_PAT", "YOUR_PAT_HERE"))
)

# Import MCP client
try:
    from mcp_client import atlassian_mcp
    MCP_AVAILABLE = True
except Exception as e:
    MCP_AVAILABLE = False
    print(f"[WARNING] MCP client initialization failed: {e}. Falling back to REST API.")


def create_jira_issue(project_key, summary, description, issue_type="Task"):
    """Creates a new Jira issue via Atlassian MCP or REST API."""
    if MCP_AVAILABLE:
        try:
            result = atlassian_mcp.jira_create_issue(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type
            )
            # Parse issue key from MCP response
            match = re.search(r'([A-Z]+-\d+)', result)
            if match:
                issue_key = match.group(1)
                print(f"Successfully created issue: {issue_key}")
                return issue_key
            else:
                print(f"Failed to parse issue key from response: {result}")
                return None
        except Exception as e:
            print(f"[WARNING] MCP call failed: {e}. Falling back to REST API.")
    
    # Fallback to direct REST API
    url = f"{JIRA_URL}/rest/api/2/issue"
    headers = {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type}
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 201:
        print(f"Successfully created issue: {response.json()['key']}")
        return response.json()['key']
    else:
        print(f"Failed to create issue. Status code: {response.status_code}")
        print(response.text)
        return None


def add_comment(issue_key, comment_body):
    """Adds a comment to an existing Jira issue via Atlassian MCP or REST API."""
    if MCP_AVAILABLE:
        try:
            result = atlassian_mcp.jira_add_comment(
                issue_key=issue_key,
                comment=comment_body
            )
            print(f"Successfully added comment to {issue_key}")
            return True
        except Exception as e:
            print(f"[WARNING] MCP call failed: {e}. Falling back to REST API.")
    
    # Fallback to direct REST API
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/comment"
    headers = {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {"body": comment_body}
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 201:
        print(f"Successfully added comment to {issue_key}")
        return True
    else:
        print(f"Failed to add comment. Status code: {response.status_code}")
        print(response.text)
        return False


def get_issue_details(issue_key):
    """Retrieves details of a Jira issue via Atlassian MCP or REST API."""
    if MCP_AVAILABLE:
        try:
            result = atlassian_mcp.jira_get_issue(issue_key=issue_key)
            # MCP returns JSON string, parse it
            if isinstance(result, str):
                issue_data = json.loads(result)
            else:
                issue_data = result
            
            return {
                "key": issue_data.get("key"),
                "summary": issue_data.get("summary"),
                "description": issue_data.get("description"),
                "status": issue_data.get("status"),
                "assignee": issue_data.get("assignee"),
                "created": issue_data.get("created"),
                "updated": issue_data.get("updated"),
                "issue_type": issue_data.get("issue_type"),
                "priority": issue_data.get("priority")
            }
        except Exception as e:
            print(f"[WARNING] MCP call failed: {e}. Falling back to REST API.")
    
    # Fallback to direct REST API
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}"
    headers = {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        issue_data = response.json()
        return {
            "key": issue_data.get("key"),
            "summary": issue_data.get("fields", {}).get("summary"),
            "description": issue_data.get("fields", {}).get("description"),
            "status": issue_data.get("fields", {}).get("status", {}).get("name"),
            "assignee": issue_data.get("fields", {}).get("assignee", {}).get("displayName"),
            "created": issue_data.get("fields", {}).get("created"),
            "updated": issue_data.get("fields", {}).get("updated"),
            "issue_type": issue_data.get("fields", {}).get("issuetype", {}).get("name"),
            "priority": issue_data.get("fields", {}).get("priority", {}).get("name")
        }
    else:
        print(f"Failed to get issue details. Status code: {response.status_code}")
        print(response.text)
        return None


def change_issue_status(issue_key, transition_name):
    """Changes the status of a Jira issue by transitioning it via Atlassian MCP or REST API."""
    if MCP_AVAILABLE:
        try:
            result = atlassian_mcp.jira_transition_issue(
                issue_key=issue_key,
                transition_name=transition_name
            )
            # Check if transition was successful
            if "Successfully transitioned" in result or "successfully" in result.lower():
                print(f"Successfully transitioned {issue_key} to '{transition_name}'")
                return True
            else:
                print(f"Failed to transition: {result}")
                return False
        except Exception as e:
            print(f"[WARNING] MCP call failed: {e}. Falling back to REST API.")
    
    # Fallback to direct REST API
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/transitions"
    headers = {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to get transitions. Status code: {response.status_code}")
        print(response.text)
        return False
    
    transitions = response.json().get("transitions", [])
    
    # Find the transition ID matching the transition name
    transition_id = None
    for transition in transitions:
        if transition.get("name").lower() == transition_name.lower():
            transition_id = transition.get("id")
            break
    
    if not transition_id:
        print(f"Transition '{transition_name}' not found. Available transitions:")
        for transition in transitions:
            print(f"  - {transition.get('name')}")
        return False
    
    # Perform the transition
    payload = {
        "transition": {
            "id": transition_id
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 204:
        print(f"Successfully transitioned {issue_key} to '{transition_name}'")
        return True
    else:
        print(f"Failed to transition issue. Status code: {response.status_code}")
        print(response.text)
        return False

def create_jira_subtask(parent_key, summary, description):
    """Creates a Jira subtask linked to a parent issue via Atlassian MCP or REST API.
    
    Args:
        parent_key (str): Parent issue key (e.g., 'AQD-1234')
        summary (str): Subtask summary/title
        description (str): Subtask description
    
    Returns:
        str: Subtask key on success, None on failure
    """
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] Creating Jira subtask for parent: {parent_key}")
    
    project_key = parent_key.split('-')[0]
    
    if MCP_AVAILABLE:
        try:
            result = atlassian_mcp.jira_create_issue(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type="Sub-task"
            )
            # Parse subtask key from response
            match = re.search(r'([A-Z]+-\d+)', result)
            if match:
                subtask_key = match.group(1)
                print(f"[{timestamp}] Successfully created subtask: {subtask_key}")
                return subtask_key
            else:
                print(f"[{timestamp}] Failed to parse subtask key from response: {result}")
                return None
        except Exception as e:
            print(f"[{timestamp}] [WARNING] MCP call failed: {e}. Falling back to REST API.")
    
    # Fallback to direct REST API
    url = f"{JIRA_URL}/rest/api/2/issue"
    headers = {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "fields": {
            "project": {"key": project_key},
            "parent": {"key": parent_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Sub-task"}
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 201:
        subtask_key = response.json()['key']
        print(f"[{timestamp}] Successfully created subtask: {subtask_key}")
        return subtask_key
    else:
        print(f"[{timestamp}] Failed to create subtask. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def link_jira_issues(issue_key1, issue_key2, link_type="relates to"):
    """Links two Jira issues together.
    
    NOTE: Atlassian MCP does not provide a tool for linking issues.
    This function uses direct REST API access as a fallback.
    
    Args:
        issue_key1 (str): First issue key (e.g., 'AQD-1234')
        issue_key2 (str): Second issue key (e.g., 'AQD-1235')
        link_type (str): Link type (e.g., 'relates to', 'blocks', 'is blocked by')
    
    Returns:
        bool: True on success, False on failure
    """
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] Linking issues: {issue_key1} {link_type} {issue_key2}")
    
    try:
        url = f"{JIRA_URL}/rest/api/2/issueLink"
        headers = {
            "Authorization": f"Bearer {JIRA_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "type": {"name": link_type},
            "inwardIssue": {"key": issue_key1},
            "outwardIssue": {"key": issue_key2}
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        
        if response.status_code == 201:
            print(f"[{timestamp}] Successfully linked issues")
            return True
        else:
            print(f"[{timestamp}] Failed to link issues. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"[{timestamp}] Exception linking issues: {e}")
        return False

def retry_api_call(func, max_retries=3, backoff_factor=2):
    """Retry wrapper for Jira API calls with exponential backoff.
    
    Works with both REST API and MCP tool calls.
    
    Args:
        func (callable): Function to retry
        max_retries (int): Maximum number of retry attempts
        backoff_factor (int): Exponential backoff multiplier
    
    Returns:
        Any: Result of func() on success, None on failure after max retries
    """
    timestamp = datetime.now().isoformat()
    
    for attempt in range(max_retries):
        try:
            print(f"[{timestamp}] Attempt {attempt + 1}/{max_retries}")
            return func()
        except (requests.exceptions.RequestException, Exception) as e:
            if attempt == max_retries - 1:
                print(f"[{timestamp}] Failed after {max_retries} attempts: {e}")
                return None
            wait_time = backoff_factor ** attempt
            print(f"[{timestamp}] Attempt {attempt + 1} failed. Retrying in {wait_time}s...")
            time.sleep(wait_time)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jira Integration Script for GitHub-to-Jira sync")
    parser.add_argument("--event-name", required=True, help="GitHub event name (issues or pull_request)")
    parser.add_argument("--jira-url", required=True, help="Jira instance URL")
    parser.add_argument("--jira-token", required=True, help="Jira API token")
    parser.add_argument("--project-key", required=True, help="Jira project key")
    parser.add_argument("--issue-title", default="", help="GitHub issue title")
    parser.add_argument("--issue-url", default="", help="GitHub issue URL")
    parser.add_argument("--pr-branch", default="", help="PR branch name")
    parser.add_argument("--pr-url", default="", help="PR URL")
    parser.add_argument("--issue-type", default="Task", help="Jira issue type (default: Task)")
    
    args = parser.parse_args()
    
    # TODO: Implement event routing logic here
    # For now, this is a placeholder for the main execution logic
    print(f"Event: {args.event_name}")
    print(f"Project: {args.project_key}")
    print(f"Issue Type: {args.issue_type}")