# -*- coding: utf-8 -*-
"""Jira Integration Script

Pure REST API implementation for GitHub-to-Jira synchronization.

Original file: https://colab.research.google.com/drive/1vykBrsFixtw9MSv5sC6vE5wbqkvmw85b
"""

import requests
import json
import sys
import os
import time
import argparse
from datetime import datetime

# Configuration - Use environment variables for security
JIRA_URL = os.getenv("JIRA_URL", "https://cmext.ahrq.gov/jira")
JIRA_TOKEN = os.getenv(
    "JIRA_TOKEN",
    os.getenv("JIRA_PERSONAL_TOKEN",
        os.getenv("JIRA_API_TOKEN", os.getenv("JIRA_PAT", "YOUR_PAT_HERE")))
)


def create_jira_issue(project_key, summary, description, issue_type="Task"):
    """Creates a new Jira issue via REST API."""
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
        print(f"Failed to create issue. HTTP {response.status_code}: Unable to create issue in Jira. Check project key and issue type.")
        return None


def add_comment(issue_key, comment_body):
    """Adds a comment to an existing Jira issue via REST API."""
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
        print(f"Failed to add comment. HTTP {response.status_code}: Unable to add comment to issue. Check issue key and permissions.")
        return False


def get_issue_details(issue_key):
    """Retrieves details of a Jira issue via REST API."""
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
        print(f"Failed to get issue details. HTTP {response.status_code}: Unable to retrieve issue. Check issue key and permissions.")
        return None


def change_issue_status(issue_key, transition_name):
    """Changes the status of a Jira issue by transitioning it via REST API."""
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/transitions"
    headers = {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to get transitions. HTTP {response.status_code}: Unable to retrieve available transitions. Check issue key and permissions.")
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
        print(f"Failed to transition issue. HTTP {response.status_code}: Unable to transition issue. Check transition ID and issue state.")
        return False

def create_jira_subtask(parent_key, summary, description):
    """Creates a Jira subtask linked to a parent issue via REST API.
    
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
        print(f"[{timestamp}] Failed to create subtask. HTTP {response.status_code}: Unable to create subtask. Check parent issue key and permissions.")
        return None

def link_jira_issues(issue_key1, issue_key2, link_type="relates to"):
    """Links two Jira issues together via REST API.
    
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
            print(f"[{timestamp}] Failed to link issues. HTTP {response.status_code}: Unable to link issues. Check issue keys and link type.")
            return False
    except Exception as e:
        print(f"[{timestamp}] Failed to link issues due to {type(e).__name__}")
        return False

def retry_api_call(func, max_retries=3, backoff_factor=2):
    """Retry wrapper for Jira API calls with exponential backoff.
    
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

    # Apply CLI configuration so helper functions use the requested Jira target.
    # These assignments update the module-level globals used by REST API helpers.
    JIRA_URL = args.jira_url
    JIRA_TOKEN = args.jira_token
    PROJECT_KEY = args.project_key

    if args.event_name == "issues":
        if not args.issue_title or not args.issue_url:
            print("Error: --issue-title and --issue-url are required for issues events.", file=sys.stderr)
            sys.exit(1)

        result = retry_api_call(
            lambda: create_jira_issue(
                args.project_key,
                args.issue_title,
                f"GitHub issue: {args.issue_url}",
                issue_type=args.issue_type
            )
        )
    elif args.event_name == "pull_request":
        if not args.pr_branch or not args.pr_url:
            print("Error: --pr-branch and --pr-url are required for pull_request events.", file=sys.stderr)
            sys.exit(1)

        result = retry_api_call(
            lambda: create_jira_issue(
                args.project_key,
                f"PR: {args.pr_branch}",
                f"GitHub pull request: {args.pr_url}",
                issue_type=args.issue_type
            )
        )
    else:
        print(f"Error: Unsupported event '{args.event_name}'. Expected 'issues' or 'pull_request'.", file=sys.stderr)
        sys.exit(1)

    if result is None:
        print("Error: Jira sync failed.", file=sys.stderr)
        sys.exit(1)

    print("Jira sync completed successfully.")
