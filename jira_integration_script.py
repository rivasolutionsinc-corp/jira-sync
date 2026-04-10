# -*- coding: utf-8 -*-
"""Jira Integration Script - Phase 2: Production-Ready REST API

Pure REST API implementation for GitHub-to-Jira synchronization.
Removes all MCP code and implements production hardening with validation,
rate limiting, retry logic, and comprehensive error handling.

Original file: https://colab.research.google.com/drive/1vykBrsFixtw9MSv5sC6vE5wbqkvmw85b
Phase 1 (CLOUD-1959): Generalize CLI arguments and event routing
Phase 2 (CLOUD-1961): Remove MCP code and production hardening
"""

import requests
import json
import sys
import os
import time
import re
import argparse
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urljoin

# Configuration - Use environment variables for security
JIRA_URL = os.getenv("JIRA_URL", "https://cmext.ahrq.gov/jira")
JIRA_TOKEN = os.getenv(
    "JIRA_TOKEN",
    os.getenv("JIRA_PERSONAL_TOKEN",
        os.getenv("JIRA_API_TOKEN", os.getenv("JIRA_PAT", "YOUR_PAT_HERE")))
)

# Production hardening constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
BACKOFF_FACTOR = 2
RATE_LIMIT_DELAY = 0.5  # seconds between API calls
MAX_COMMENT_LENGTH = 32767  # Jira API limit

# Request session with connection pooling
_session = None

def get_session() -> requests.Session:
    """Get or create a requests session with connection pooling."""
    global _session
    if _session is None:
        _session = requests.Session()
        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(
                total=MAX_RETRIES,
                backoff_factor=BACKOFF_FACTOR,
                status_forcelist=[429, 500, 502, 503, 504]
            )
        )
        _session.mount('http://', adapter)
        _session.mount('https://', adapter)
    return _session


# Structured Logging Utility
def log_action(action: str, level: str = "INFO", **kwargs) -> None:
    """Structured logging for Jira actions.
    
    Args:
        action (str): Action description
        level (str): Log level (INFO, WARNING, ERROR, DEBUG)
        **kwargs: Additional key-value pairs to log
    """
    timestamp = datetime.now().isoformat()
    message = f"[{timestamp}] [{level}] {action}"
    for key, value in kwargs.items():
        message += f" | {key}={value}"
    print(message)


def validate_jira_url(url: str) -> bool:
    """Validate Jira URL format.
    
    Args:
        url (str): Jira URL to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    return url.startswith(('http://', 'https://')) and len(url) > 10


def validate_jira_token(token: str) -> bool:
    """Validate Jira API token format.
    
    Args:
        token (str): Jira API token to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not token or token == "YOUR_PAT_HERE":
        return False
    return len(token) > 10


def validate_issue_key(issue_key: str) -> bool:
    """Validate Jira issue key format.
    
    Args:
        issue_key (str): Issue key to validate (e.g., 'CLOUD-1234')
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not issue_key or not isinstance(issue_key, str):
        return False
    return bool(re.match(r'^[A-Z][A-Z0-9_]+-\d+$', issue_key))


def validate_project_key(project_key: str) -> bool:
    """Validate Jira project key format.
    
    Args:
        project_key (str): Project key to validate (e.g., 'CLOUD')
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not project_key or not isinstance(project_key, str):
        return False
    return bool(re.match(r'^[A-Z][A-Z0-9_]*$', project_key))


def validate_url(url: str) -> bool:
    """Validate URL format.
    
    Args:
        url (str): URL to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    return url.startswith(('http://', 'https://')) and len(url) > 10


def rate_limit_delay() -> None:
    """Apply rate limiting delay between API calls."""
    time.sleep(RATE_LIMIT_DELAY)


def create_jira_issue(project_key: str, summary: str, description: str, 
                     issue_type: str = "Task") -> Optional[str]:
    """Creates a new Jira issue via REST API.
    
    Args:
        project_key (str): Jira project key
        summary (str): Issue summary/title
        description (str): Issue description
        issue_type (str): Jira issue type (default: Task)
    
    Returns:
        str: Created issue key on success, None on failure
    """
    # Validate inputs
    if not validate_project_key(project_key):
        log_action("Invalid project key", level="ERROR", project_key=project_key)
        return None
    
    if not summary or len(summary) > 255:
        log_action("Invalid summary", level="ERROR", length=len(summary) if summary else 0)
        return None
    
    if not description or len(description) > 32767:
        log_action("Invalid description", level="ERROR", length=len(description) if description else 0)
        return None
    
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
    
    try:
        rate_limit_delay()
        response = get_session().post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
        
        if response.status_code == 201:
            issue_key = response.json()['key']
            log_action(f"Successfully created issue: {issue_key}", level="INFO")
            return issue_key
        else:
            log_action(f"Failed to create issue", level="ERROR",
                      http_status=response.status_code, response=response.text[:200])
            return None
    except requests.exceptions.Timeout:
        log_action("Request timeout while creating issue", level="ERROR", timeout=DEFAULT_TIMEOUT)
        return None
    except requests.exceptions.RequestException as e:
        log_action("Request failed while creating issue", level="ERROR", error=str(e))
        return None
    except Exception as e:
        log_action("Unexpected error while creating issue", level="ERROR", error=str(e))
        return None


def add_comment(issue_key: str, comment_body: str) -> bool:
    """Adds a comment to an existing Jira issue via REST API.
    
    Args:
        issue_key (str): Jira issue key
        comment_body (str): Comment text
    
    Returns:
        bool: True on success, False on failure
    """
    # Validate inputs
    if not validate_issue_key(issue_key):
        log_action("Invalid issue key", level="ERROR", issue_key=issue_key)
        return False
    
    if not comment_body or len(comment_body) > MAX_COMMENT_LENGTH:
        log_action("Invalid comment body", level="ERROR", length=len(comment_body) if comment_body else 0)
        return False
    
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/comment"
    headers = {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {"body": comment_body}
    
    try:
        rate_limit_delay()
        response = get_session().post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
        
        if response.status_code == 201:
            log_action(f"Successfully added comment to {issue_key}", level="INFO")
            return True
        else:
            log_action(f"Failed to add comment", level="ERROR",
                      http_status=response.status_code, response=response.text[:200])
            return False
    except requests.exceptions.Timeout:
        log_action("Request timeout while adding comment", level="ERROR", timeout=DEFAULT_TIMEOUT)
        return False
    except requests.exceptions.RequestException as e:
        log_action("Request failed while adding comment", level="ERROR", error=str(e))
        return False
    except Exception as e:
        log_action("Unexpected error while adding comment", level="ERROR", error=str(e))
        return False


def get_issue_details(issue_key: str) -> Optional[Dict[str, Any]]:
    """Retrieves details of a Jira issue via REST API.
    
    Args:
        issue_key (str): Jira issue key
    
    Returns:
        dict: Issue details on success, None on failure
    """
    # Validate input
    if not validate_issue_key(issue_key):
        log_action("Invalid issue key", level="ERROR", issue_key=issue_key)
        return None
    
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}"
    headers = {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        rate_limit_delay()
        response = get_session().get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        
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
            log_action(f"Failed to get issue details", level="ERROR",
                      http_status=response.status_code, response=response.text[:200])
            return None
    except requests.exceptions.Timeout:
        log_action("Request timeout while getting issue details", level="ERROR", timeout=DEFAULT_TIMEOUT)
        return None
    except requests.exceptions.RequestException as e:
        log_action("Request failed while getting issue details", level="ERROR", error=str(e))
        return None
    except Exception as e:
        log_action("Unexpected error while getting issue details", level="ERROR", error=str(e))
        return None


def change_issue_status(issue_key: str, transition_name: str) -> bool:
    """Changes the status of a Jira issue by transitioning it via REST API.
    
    Enhanced with transition discovery logging for debugging.
    
    Args:
        issue_key (str): Jira issue key (e.g., 'CLOUD-1234')
        transition_name (str): Target transition name (e.g., 'Done', 'In Progress')
    
    Returns:
        bool: True on success, False on failure
    """
    # Validate inputs
    if not validate_issue_key(issue_key):
        log_action("Invalid issue key", level="ERROR", issue_key=issue_key)
        return False
    
    if not transition_name or not isinstance(transition_name, str):
        log_action("Invalid transition name", level="ERROR", transition_name=transition_name)
        return False
    
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/transitions"
    headers = {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        # Fetch available transitions
        rate_limit_delay()
        response = get_session().get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        
        if response.status_code != 200:
            log_action(f"Failed to get transitions for {issue_key}", level="ERROR",
                      http_status=response.status_code, response=response.text[:200])
            return False
        
        transitions = response.json().get("transitions", [])
        
        # Log all available transitions for debugging
        log_action(f"Transition discovery for {issue_key}", level="DEBUG",
                  available_count=len(transitions))
        for transition in transitions:
            log_action(f"  Available transition", level="DEBUG",
                      id=transition.get("id"),
                      name=transition.get("name"),
                      to_status=transition.get("to", {}).get("name"))
        
        # Find the transition ID matching the transition name
        transition_id = None
        for transition in transitions:
            if transition.get("name", "").lower() == transition_name.lower():
                transition_id = transition.get("id")
                break
        
        if not transition_id:
            # Provide helpful suggestions
            available_names = [t.get("name") for t in transitions]
            log_action(f"Transition '{transition_name}' not found for {issue_key}", level="ERROR",
                      requested=transition_name, available=", ".join(available_names))
            print(f"Transition '{transition_name}' not found. Available transitions:")
            for transition in transitions:
                print(f"  - {transition.get('name')} (ID: {transition.get('id')})")
            return False
        
        # Perform the transition
        payload = {
            "transition": {
                "id": transition_id
            }
        }
        
        log_action(f"Attempting transition for {issue_key}", level="DEBUG",
                  transition_id=transition_id, transition_name=transition_name)
        
        rate_limit_delay()
        response = get_session().post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
        
        if response.status_code == 204:
            log_action(f"Successfully transitioned {issue_key} to '{transition_name}'", level="INFO")
            return True
        else:
            log_action(f"Failed to transition {issue_key}", level="ERROR",
                      http_status=response.status_code, response=response.text[:200])
            return False
    except requests.exceptions.Timeout:
        log_action("Request timeout while transitioning issue", level="ERROR", timeout=DEFAULT_TIMEOUT)
        return False
    except requests.exceptions.RequestException as e:
        log_action("Request failed while transitioning issue", level="ERROR", error=str(e))
        return False
    except Exception as e:
        log_action("Unexpected error while transitioning issue", level="ERROR", error=str(e))
        return False


def link_github_pr_remote(issue_key: str, pr_url: str, pr_title: str) -> bool:
    """Creates a GitHub PR remote link in Jira.
    
    This creates a "Web Link" that appears in the Jira "Issue Links" panel
    with a GitHub icon, allowing users to navigate directly to the PR.
    
    Args:
        issue_key (str): Jira issue key (e.g., 'CLOUD-1234')
        pr_url (str): GitHub PR URL (e.g., 'https://github.com/AHRQ/repo/pull/123')
        pr_title (str): GitHub PR title for display
    
    Returns:
        bool: True on success, False on failure
    """
    # Validate inputs
    if not validate_issue_key(issue_key):
        log_action("Invalid issue key", level="ERROR", issue_key=issue_key)
        return False
    
    if not validate_url(pr_url):
        log_action("Invalid PR URL", level="ERROR", pr_url=pr_url)
        return False
    
    if not pr_title or len(pr_title) > 255:
        log_action("Invalid PR title", level="ERROR", length=len(pr_title) if pr_title else 0)
        return False
    
    try:
        # Extract PR number from URL for globalId
        pr_match = re.search(r'/pull/(\d+)', pr_url)
        pr_number = pr_match.group(1) if pr_match else "unknown"
        
        url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/remotelink"
        headers = {
            "Authorization": f"Bearer {JIRA_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "globalId": f"github-pr-{pr_number}",
            "application": {
                "name": "GitHub",
                "type": "com.github"
            },
            "relationship": "relates to",
            "object": {
                "url": pr_url,
                "title": pr_title,
                "summary": f"GitHub PR: {pr_title}",
                "icon": {
                    "url16x16": "https://github.com/favicon.ico",
                    "title": "GitHub"
                }
            }
        }
        
        log_action(f"Creating GitHub PR remote link for {issue_key}", level="DEBUG",
                  pr_url=pr_url, pr_number=pr_number)
        
        rate_limit_delay()
        response = get_session().post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
        
        # Accept both 200 and 201 as success (Jira may return either)
        if response.status_code in [200, 201]:
            log_action(f"Successfully linked GitHub PR to {issue_key}", level="INFO",
                      pr_url=pr_url)
            return True
        else:
            log_action(f"Failed to link GitHub PR to {issue_key}", level="ERROR",
                      http_status=response.status_code, response=response.text[:200])
            return False
    except requests.exceptions.Timeout:
        log_action("Request timeout while linking PR", level="ERROR", timeout=DEFAULT_TIMEOUT)
        return False
    except requests.exceptions.RequestException as e:
        log_action("Request failed while linking PR", level="ERROR", error=str(e))
        return False
    except Exception as e:
        log_action("Failed to link GitHub PR due to exception", level="ERROR",
                  issue_key=issue_key, error=str(e))
        return False


def create_jira_subtask(parent_key: str, summary: str, description: str) -> Optional[str]:
    """Creates a Jira subtask linked to a parent issue via REST API.
    
    Args:
        parent_key (str): Parent issue key (e.g., 'AQD-1234')
        summary (str): Subtask summary/title
        description (str): Subtask description
    
    Returns:
        str: Subtask key on success, None on failure
    """
    # Validate inputs
    if not validate_issue_key(parent_key):
        log_action("Invalid parent issue key", level="ERROR", parent_key=parent_key)
        return None
    
    if not summary or len(summary) > 255:
        log_action("Invalid summary", level="ERROR", length=len(summary) if summary else 0)
        return None
    
    if not description or len(description) > 32767:
        log_action("Invalid description", level="ERROR", length=len(description) if description else 0)
        return None
    
    log_action(f"Creating Jira subtask for parent: {parent_key}", level="DEBUG",
              summary=summary)
    
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
    
    try:
        log_action(f"Creating subtask via REST API", level="DEBUG",
                  parent=parent_key, project=project_key)
        
        rate_limit_delay()
        response = get_session().post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
        
        if response.status_code == 201:
            subtask_key = response.json()['key']
            log_action(f"Successfully created subtask: {subtask_key}", level="INFO",
                      parent=parent_key)
            return subtask_key
        else:
            log_action(f"Failed to create subtask", level="ERROR",
                      http_status=response.status_code, response=response.text[:200])
            return None
    except requests.exceptions.Timeout:
        log_action("Request timeout while creating subtask", level="ERROR", timeout=DEFAULT_TIMEOUT)
        return None
    except requests.exceptions.RequestException as e:
        log_action("Request failed while creating subtask", level="ERROR", error=str(e))
        return None
    except Exception as e:
        log_action("Unexpected error while creating subtask", level="ERROR", error=str(e))
        return None


def link_jira_issues(issue_key1: str, issue_key2: str, link_type: str = "relates to") -> bool:
    """Links two Jira issues together via REST API.
    
    Args:
        issue_key1 (str): First issue key (e.g., 'AQD-1234')
        issue_key2 (str): Second issue key (e.g., 'AQD-1235')
        link_type (str): Link type (e.g., 'relates to', 'blocks', 'is blocked by')
    
    Returns:
        bool: True on success, False on failure
    """
    # Validate inputs
    if not validate_issue_key(issue_key1):
        log_action("Invalid first issue key", level="ERROR", issue_key=issue_key1)
        return False
    
    if not validate_issue_key(issue_key2):
        log_action("Invalid second issue key", level="ERROR", issue_key=issue_key2)
        return False
    
    if not link_type or not isinstance(link_type, str):
        log_action("Invalid link type", level="ERROR", link_type=link_type)
        return False
    
    log_action(f"Linking issues: {issue_key1} {link_type} {issue_key2}", level="DEBUG")
    
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
        
        rate_limit_delay()
        response = get_session().post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
        
        if response.status_code == 201:
            log_action(f"Successfully linked issues", level="INFO",
                      issue1=issue_key1, issue2=issue_key2, link_type=link_type)
            return True
        else:
            log_action(f"Failed to link issues", level="ERROR",
                      http_status=response.status_code, response=response.text[:200])
            return False
    except requests.exceptions.Timeout:
        log_action("Request timeout while linking issues", level="ERROR", timeout=DEFAULT_TIMEOUT)
        return False
    except requests.exceptions.RequestException as e:
        log_action("Request failed while linking issues", level="ERROR", error=str(e))
        return False
    except Exception as e:
        log_action("Failed to link issues due to exception", level="ERROR",
                  error_type=type(e).__name__, error=str(e))
        return False


def retry_api_call(func, max_retries: int = MAX_RETRIES, backoff_factor: int = BACKOFF_FACTOR) -> Any:
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
            log_action(f"Attempt {attempt + 1}/{max_retries}", level="DEBUG")
            return func()
        except (requests.exceptions.RequestException, Exception) as e:
            if attempt == max_retries - 1:
                log_action(f"Failed after {max_retries} attempts", level="ERROR", error=str(e))
                return None
            wait_time = backoff_factor ** attempt
            log_action(f"Attempt {attempt + 1} failed. Retrying in {wait_time}s...", level="WARNING",
                      error=str(e))
            time.sleep(wait_time)


def extract_jira_key_from_branch(branch_name: str) -> Optional[str]:
    """Extracts Jira issue key from branch name.
    
    Supports patterns like:
    - feature/CLOUD-1234-description
    - bugfix/CLOUD-1234
    - CLOUD-1234-description
    
    Args:
        branch_name (str): Git branch name
    
    Returns:
        str: Jira issue key (e.g., 'CLOUD-1234') or None if not found
    """
    if not branch_name or not isinstance(branch_name, str):
        return None
    
    match = re.search(r'([A-Z][A-Z0-9_]+-\d+)', branch_name)
    return match.group(1) if match else None


def route_event(event_name: str, args) -> Any:
    """Routes GitHub events to appropriate Jira actions based on configuration.
    
    Supports configurable event routing with transition names and branch matching.
    Handles deployment lifecycle events: issues, pull_request, push, and create (tags).
    
    Args:
        event_name (str): GitHub event type (issues, pull_request, push, create)
        args: Parsed command-line arguments
    
    Returns:
        Any: Result of the routed action
    """
    log_action(f"Routing event", level="DEBUG", event_name=event_name,
              target_branch=args.target_branch, deployment_stage=getattr(args, 'deployment_stage', None))
    
    if event_name == "issues":
        return handle_issues_event(args)
    elif event_name == "pull_request":
        return handle_pull_request_event(args)
    elif event_name == "push":
        return handle_push_event(args)
    elif event_name == "create":
        return handle_tag_event(args)
    else:
        log_action(f"Unsupported event type", level="ERROR", event_name=event_name)
        print(f"Error: Unsupported event '{event_name}'. Expected 'issues', 'pull_request', 'push', or 'create'.", file=sys.stderr)
        return None


def handle_issues_event(args) -> Optional[str]:
    """Handles GitHub issues event.
    
    Creates a new Jira issue when a GitHub issue is opened.
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        str: Created issue key or None on failure
    """
    if not args.issue_title or not args.issue_url:
        print("Error: --issue-title and --issue-url are required for issues events.", file=sys.stderr)
        return None
    
    log_action(f"Handling issues event", level="DEBUG", 
              title=args.issue_title, url=args.issue_url)
    
    result = retry_api_call(
        lambda: create_jira_issue(
            args.project_key,
            args.issue_title,
            f"GitHub issue: {args.issue_url}",
            issue_type=args.issue_type
        )
    )
    
    return result


def handle_pull_request_event(args) -> bool:
    """Handles GitHub pull_request event.
    
    Supports multiple PR actions:
    - Comment on existing issue (if Jira key found in branch)
    - Link PR to issue
    - Transition issue based on PR action
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        bool: True on success, False on failure
    """
    if not args.pr_branch or not args.pr_url:
        print("Error: --pr-branch and --pr-url are required for pull_request events.", file=sys.stderr)
        return False
    
    log_action(f"Handling pull_request event", level="DEBUG",
              branch=args.pr_branch, url=args.pr_url, pr_action=args.pr_action)
    
    # Extract Jira key from branch name
    jira_key = extract_jira_key_from_branch(args.pr_branch)
    
    if not jira_key:
        log_action(f"No Jira key found in branch name", level="INFO",
                  branch=args.pr_branch)
        print("No Jira key found in branch name. Skipping PR sync.")
        return True  # Not an error, just skip
    
    log_action(f"Found Jira key in branch", level="DEBUG",
              jira_key=jira_key, branch=args.pr_branch)
    
    success = True
    
    # Handle PR action-specific logic
    if args.pr_action == "opened":
        # Comment on issue and link PR
        comment_text = f"Pull Request opened: {args.pr_url}"
        if not retry_api_call(lambda: add_comment(jira_key, comment_text)):
            log_action(f"Failed to comment on issue", level="ERROR", issue_key=jira_key)
            success = False
        
        # Link PR to issue (always do this for all PR events)
        pr_title = args.pr_title or "GitHub PR"
        if not link_github_pr_remote(jira_key, args.pr_url, pr_title):
            log_action(f"Failed to link PR to issue", level="ERROR", issue_key=jira_key)
            success = False
        
        # Transition issue if configured
        if args.transition_opened:
            if not change_issue_status(jira_key, args.transition_opened):
                log_action(f"Failed to transition issue on PR opened", level="ERROR",
                          issue_key=jira_key, transition=args.transition_opened)
                success = False
    
    elif args.pr_action == "synchronize":
        # Link PR to issue (always do this for all PR events)
        pr_title = args.pr_title or "GitHub PR"
        if not link_github_pr_remote(jira_key, args.pr_url, pr_title):
            log_action(f"Failed to link PR to issue", level="ERROR", issue_key=jira_key)
            success = False
    
    elif args.pr_action == "closed":
        # Link PR to issue (always do this for all PR events)
        pr_title = args.pr_title or "GitHub PR"
        if not link_github_pr_remote(jira_key, args.pr_url, pr_title):
            log_action(f"Failed to link PR to issue", level="ERROR", issue_key=jira_key)
            success = False
        
        # Transition issue if PR was merged
        if args.pr_merged and args.transition_merged:
            if not change_issue_status(jira_key, args.transition_merged):
                log_action(f"Failed to transition issue on PR merged", level="ERROR",
                          issue_key=jira_key, transition=args.transition_merged)
                success = False
    
    return success


def handle_push_event(args) -> bool:
    """Handles GitHub push event for deployment branches.
    
    Maps branch pushes to Jira state transitions:
    - develop → In Development
    - stage → In QA
    - main → Deployed
    
    Supports tagging issues when commits are pushed to specific branches.
    Adds deployment metadata to Jira comments.
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        bool: True on success, False on failure
    """
    if not args.push_branch:
        print("Error: --push-branch is required for push events.", file=sys.stderr)
        return False
    
    log_action(f"Handling push event", level="DEBUG",
              branch=args.push_branch, target_branch=args.target_branch,
              deployment_stage=getattr(args, 'deployment_stage', None))
    
    # Check if push branch matches target branch
    if args.target_branch and args.push_branch != args.target_branch:
        log_action(f"Push branch does not match target branch", level="INFO",
                  push_branch=args.push_branch, target_branch=args.target_branch)
        print(f"Push to {args.push_branch} does not match target branch {args.target_branch}. Skipping.")
        return True  # Not an error, just skip
    
    # Extract Jira key from branch name
    jira_key = extract_jira_key_from_branch(args.push_branch)
    
    if not jira_key:
        log_action(f"No Jira key found in branch name", level="INFO",
                  branch=args.push_branch)
        print("No Jira key found in branch name. Skipping push sync.")
        return True  # Not an error, just skip
    
    log_action(f"Found Jira key in branch", level="DEBUG",
              jira_key=jira_key, branch=args.push_branch)
    
    success = True
    
    # Add deployment metadata comment
    deployment_stage = getattr(args, 'deployment_stage', 'unknown')
    deployment_branch = getattr(args, 'deployment_branch', args.push_branch)
    commit_sha = os.getenv('GITHUB_SHA', 'unknown')[:7]
    
    deployment_comment = (
        f"🚀 Deployment Event: {deployment_stage.upper()}\n"
        f"Branch: {deployment_branch}\n"
        f"Commit: {commit_sha}\n"
        f"Timestamp: {datetime.now().isoformat()}"
    )
    
    if not retry_api_call(lambda: add_comment(jira_key, deployment_comment)):
        log_action(f"Failed to add deployment comment", level="WARNING", issue_key=jira_key)
        success = False
    
    # Transition issue if configured
    if args.transition_tag:
        if not change_issue_status(jira_key, args.transition_tag):
            log_action(f"Failed to transition issue on push", level="ERROR",
                      issue_key=jira_key, transition=args.transition_tag)
            return False
    
    return success


def handle_tag_event(args) -> bool:
    """Handles GitHub tag creation event (create event with ref_type=tag).
    
    Maps tag creation to production deployment:
    - Tag pattern: v*.*.* → Deployed
    
    Extracts Jira key from commit message or branch and transitions to Deployed state.
    Adds deployment metadata including tag name and commit information.
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        bool: True on success, False on failure
    """
    tag_name = getattr(args, 'tag_name', None)
    
    if not tag_name:
        log_action(f"No tag name provided for create event", level="INFO")
        print("No tag name provided. Skipping tag sync.")
        return True  # Not an error, just skip
    
    log_action(f"Handling tag creation event", level="DEBUG",
              tag_name=tag_name, deployment_stage='production')
    
    # Validate tag pattern (v*.*.*)
    if not re.match(r'^v\d+\.\d+\.\d+', tag_name):
        log_action(f"Tag does not match production release pattern", level="INFO",
                  tag_name=tag_name, pattern='v*.*.*')
        print(f"Tag '{tag_name}' does not match production release pattern (v*.*.*). Skipping.")
        return True  # Not an error, just skip
    
    log_action(f"Tag matches production release pattern", level="DEBUG",
              tag_name=tag_name)
    
    # Try to extract Jira key from tag name (e.g., v1.2.3-CLOUD-1234)
    jira_key = extract_jira_key_from_branch(tag_name)
    
    if not jira_key:
        log_action(f"No Jira key found in tag name", level="INFO",
                  tag_name=tag_name)
        print("No Jira key found in tag name. Skipping tag sync.")
        return True  # Not an error, just skip
    
    log_action(f"Found Jira key in tag", level="DEBUG",
              jira_key=jira_key, tag_name=tag_name)
    
    success = True
    
    # Add deployment metadata comment
    deployment_tag = getattr(args, 'deployment_tag', tag_name)
    tag_ref = getattr(args, 'tag_ref', 'main')
    
    deployment_comment = (
        f"🚀 Production Release: {deployment_tag}\n"
        f"Branch: {tag_ref}\n"
        f"Timestamp: {datetime.now().isoformat()}\n"
        f"Status: Deployed to Production"
    )
    
    if not retry_api_call(lambda: add_comment(jira_key, deployment_comment)):
        log_action(f"Failed to add production deployment comment", level="WARNING", issue_key=jira_key)
        success = False
    
    # Transition issue to Deployed if configured
    transition_tag = getattr(args, 'transition_tag', 'Deployed')
    if transition_tag:
        if not change_issue_status(jira_key, transition_tag):
            log_action(f"Failed to transition issue on tag creation", level="ERROR",
                      issue_key=jira_key, transition=transition_tag)
            return False
    
    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Jira Integration Script for GitHub-to-Jira sync (Phase 3: Deployment Orchestration)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Handle GitHub issue creation
  python jira_integration_script.py \\
    --event-name issues \\
    --jira-url https://jira.example.com \\
    --jira-token YOUR_TOKEN \\
    --project-key CLOUD \\
    --issue-title "New Feature Request" \\
    --issue-url https://github.com/org/repo/issues/123

  # Handle GitHub PR with transitions
  python jira_integration_script.py \\
    --event-name pull_request \\
    --jira-url https://jira.example.com \\
    --jira-token YOUR_TOKEN \\
    --project-key CLOUD \\
    --pr-branch feature/CLOUD-1234-description \\
    --pr-url https://github.com/org/repo/pull/456 \\
    --pr-title "Implement feature" \\
    --pr-action opened \\
    --transition-opened "In Progress" \\
    --transition-merged "Done"

  # Handle push event to develop branch (In Development)
  python jira_integration_script.py \\
    --event-name push \\
    --jira-url https://jira.example.com \\
    --jira-token YOUR_TOKEN \\
    --project-key CLOUD \\
    --push-branch develop \\
    --target-branch develop \\
    --transition-tag "In Development" \\
    --deployment-stage development \\
    --deployment-branch develop

  # Handle push event to stage branch (In QA)
  python jira_integration_script.py \\
    --event-name push \\
    --jira-url https://jira.example.com \\
    --jira-token YOUR_TOKEN \\
    --project-key CLOUD \\
    --push-branch stage \\
    --target-branch stage \\
    --transition-tag "In QA" \\
    --deployment-stage staging \\
    --deployment-branch stage

  # Handle tag creation event (Deployed)
  python jira_integration_script.py \\
    --event-name create \\
    --jira-url https://jira.example.com \\
    --jira-token YOUR_TOKEN \\
    --project-key CLOUD \\
    --tag-name v1.2.3-CLOUD-1234 \\
    --tag-ref main \\
    --transition-tag "Deployed" \\
    --deployment-stage production \\
    --deployment-tag v1.2.3-CLOUD-1234
        """
    )
    
    # Core arguments
    parser.add_argument("--event-name", required=True,
                       choices=["issues", "pull_request", "push", "create"],
                       help="GitHub event name")
    parser.add_argument("--jira-url", required=True, help="Jira instance URL")
    parser.add_argument("--jira-token", required=True, help="Jira API token")
    parser.add_argument("--project-key", required=True, help="Jira project key")
    
    # Issues event arguments
    parser.add_argument("--issue-title", default="", help="GitHub issue title")
    parser.add_argument("--issue-url", default="", help="GitHub issue URL")
    parser.add_argument("--issue-type", default="Task", help="Jira issue type (default: Task)")
    
    # Pull request event arguments
    parser.add_argument("--pr-branch", default="", help="PR source branch name")
    parser.add_argument("--pr-url", default="", help="PR URL")
    parser.add_argument("--pr-title", default="", help="PR title for linking")
    parser.add_argument("--pr-action", default="opened",
                       choices=["opened", "synchronize", "closed"],
                       help="PR action (default: opened)")
    parser.add_argument("--pr-merged", action="store_true",
                       help="Flag indicating PR was merged (for closed action)")
    
    # Push event arguments
    parser.add_argument("--push-branch", default="", help="Branch name for push event")
    
    # Tag/Create event arguments (Phase 3: Deployment Orchestration)
    parser.add_argument("--tag-name", default="", help="Tag name for create event (e.g., v1.2.3-CLOUD-1234)")
    parser.add_argument("--tag-ref", default="main", help="Reference branch for tag (default: main)")
    
    # Transition arguments (Phase 1 generalization)
    parser.add_argument("--transition-opened", default="",
                       help="Jira transition name when PR is opened (e.g., 'In Progress')")
    parser.add_argument("--transition-merged", default="",
                       help="Jira transition name when PR is merged (e.g., 'Done')")
    parser.add_argument("--transition-tag", default="",
                       help="Jira transition name when pushed to target branch or tag created (e.g., 'Deployed')")
    
    # Event routing arguments (Phase 1 generalization)
    parser.add_argument("--target-branch", default="",
                       help="Target branch for push event matching (e.g., 'main', 'develop', 'stage')")
    
    # Deployment metadata arguments (Phase 3: Deployment Orchestration)
    parser.add_argument("--deployment-stage", default="",
                       help="Deployment stage (development, staging, production)")
    parser.add_argument("--deployment-branch", default="",
                       help="Deployment branch name for metadata")
    parser.add_argument("--deployment-tag", default="",
                       help="Deployment tag for metadata")
    
    # Link arguments (Phase 1 generalization)
    parser.add_argument("--link-title", default="GitHub PR",
                       help="Custom title for GitHub PR links (default: 'GitHub PR')")
    
    args = parser.parse_args()

    # Validate critical configuration
    if not validate_jira_url(args.jira_url):
        print("Error: Invalid Jira URL. Must start with http:// or https://", file=sys.stderr)
        sys.exit(1)
    
    if not validate_jira_token(args.jira_token):
        print("Error: Invalid Jira API token. Token is required and must not be placeholder.", file=sys.stderr)
        sys.exit(1)
    
    if not validate_project_key(args.project_key):
        print("Error: Invalid Jira project key. Must be uppercase alphanumeric.", file=sys.stderr)
        sys.exit(1)

    # Apply CLI configuration so helper functions use the requested Jira target.
    # These assignments update the module-level globals used by REST API helpers.
    JIRA_URL = args.jira_url
    JIRA_TOKEN = args.jira_token
    PROJECT_KEY = args.project_key

    # Route event to appropriate handler
    result = route_event(args.event_name, args)
    
    if result is None or (isinstance(result, bool) and not result):
        print("Error: Jira sync failed.", file=sys.stderr)
        sys.exit(1)

    print("Jira sync completed successfully.")
