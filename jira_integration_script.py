# -*- coding: utf-8 -*-
"""Jira Integration Script - Phase 1: Generalized Python Toolset

Pure REST API implementation for GitHub-to-Jira synchronization.
Removes project-specific hardcoding and enables configurable event routing.

Original file: https://colab.research.google.com/drive/1vykBrsFixtw9MSv5sC6vE5wbqkvmw85b
Phase 1 (CLOUD-1959): Generalize CLI arguments and event routing
"""

import requests
import json
import sys
import os
import time
import re
import argparse
from datetime import datetime

# MCP Availability Check
try:
    import atlassian_mcp
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    atlassian_mcp = None

# Configuration - Use environment variables for security
JIRA_URL = os.getenv("JIRA_URL", "https://cmext.ahrq.gov/jira")
JIRA_TOKEN = os.getenv(
    "JIRA_TOKEN",
    os.getenv("JIRA_PERSONAL_TOKEN",
        os.getenv("JIRA_API_TOKEN", os.getenv("JIRA_PAT", "YOUR_PAT_HERE")))
)

# Structured Logging Utility
def log_action(action, level="INFO", **kwargs):
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
        print(f"Failed to create issue. HTTP {response.status_code}: Unable to create issue in Jira. Check project key and issue type.")
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
        print(f"Failed to add comment. HTTP {response.status_code}: Unable to add comment to issue. Check issue key and permissions.")
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
        print(f"Failed to get issue details. HTTP {response.status_code}: Unable to retrieve issue. Check issue key and permissions.")
        return None


def change_issue_status(issue_key, transition_name):
    """Changes the status of a Jira issue by transitioning it via Atlassian MCP or REST API.
    
    Enhanced with transition discovery logging for debugging.
    
    Args:
        issue_key (str): Jira issue key (e.g., 'CLOUD-1234')
        transition_name (str): Target transition name (e.g., 'Done', 'In Progress')
    
    Returns:
        bool: True on success, False on failure
    """
    if MCP_AVAILABLE:
        try:
            result = atlassian_mcp.jira_transition_issue(
                issue_key=issue_key,
                transition_name=transition_name
            )
            # Check if transition was successful
            if "Successfully transitioned" in result or "successfully" in result.lower():
                log_action(f"Successfully transitioned {issue_key}", level="INFO", transition=transition_name)
                return True
            else:
                log_action(f"Failed to transition {issue_key}", level="ERROR", result=result)
                return False
        except Exception as e:
            log_action(f"MCP call failed, falling back to REST API", level="WARNING", error=str(e))
    
    # Fallback to direct REST API
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/transitions"
    headers = {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Fetch available transitions
    response = requests.get(url, headers=headers)
    
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
        if transition.get("name").lower() == transition_name.lower():
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
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 204:
        log_action(f"Successfully transitioned {issue_key} to '{transition_name}'", level="INFO")
        return True
    else:
        log_action(f"Failed to transition {issue_key}", level="ERROR",
                   http_status=response.status_code, response=response.text[:200])
        return False

def link_github_pr_remote(issue_key, pr_url, pr_title):
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
        
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        
        # Accept both 200 and 201 as success (Jira may return either)
        if response.status_code in [200, 201]:
            log_action(f"Successfully linked GitHub PR to {issue_key}", level="INFO",
                       pr_url=pr_url)
            return True
        else:
            log_action(f"Failed to link GitHub PR to {issue_key}", level="ERROR",
                       http_status=response.status_code, response=response.text[:200])
            return False
    except Exception as e:
        log_action(f"Failed to link GitHub PR due to exception", level="ERROR",
                   issue_key=issue_key, error=str(e))
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
    log_action(f"Creating Jira subtask for parent: {parent_key}", level="DEBUG",
               summary=summary)
    
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
                log_action(f"Successfully created subtask: {subtask_key}", level="INFO",
                           parent=parent_key)
                return subtask_key
            else:
                log_action(f"Failed to parse subtask key from MCP response", level="ERROR",
                           response=result[:200])
                return None
        except Exception as e:
            log_action(f"MCP call failed, falling back to REST API", level="WARNING",
                       error=str(e))
    
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
    
    log_action(f"Creating subtask via REST API", level="DEBUG",
               parent=parent_key, project=project_key)
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 201:
        subtask_key = response.json()['key']
        log_action(f"Successfully created subtask: {subtask_key}", level="INFO",
                   parent=parent_key)
        return subtask_key
    else:
        log_action(f"Failed to create subtask", level="ERROR",
                   http_status=response.status_code, response=response.text[:200])
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
        
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        
        if response.status_code == 201:
            log_action(f"Successfully linked issues", level="INFO",
                       issue1=issue_key1, issue2=issue_key2, link_type=link_type)
            return True
        else:
            log_action(f"Failed to link issues", level="ERROR",
                       http_status=response.status_code, response=response.text[:200])
            return False
    except Exception as e:
        log_action(f"Failed to link issues due to exception", level="ERROR",
                   error_type=type(e).__name__, error=str(e))
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


def extract_jira_key_from_branch(branch_name):
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
    match = re.search(r'([A-Z][A-Z0-9_]+-\d+)', branch_name)
    return match.group(1) if match else None


def route_event(event_name, args):
    """Routes GitHub events to appropriate Jira actions based on configuration.
    
    Supports configurable event routing with transition names and branch matching.
    
    Args:
        event_name (str): GitHub event type (issues, pull_request, push)
        args: Parsed command-line arguments
    
    Returns:
        Any: Result of the routed action
    """
    log_action(f"Routing event", level="DEBUG", event_name=event_name, 
               target_branch=args.target_branch)
    
    if event_name == "issues":
        return handle_issues_event(args)
    elif event_name == "pull_request":
        return handle_pull_request_event(args)
    elif event_name == "push":
        return handle_push_event(args)
    else:
        log_action(f"Unsupported event type", level="ERROR", event_name=event_name)
        print(f"Error: Unsupported event '{event_name}'. Expected 'issues', 'pull_request', or 'push'.", file=sys.stderr)
        return None


def handle_issues_event(args):
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


def handle_pull_request_event(args):
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


def handle_push_event(args):
    """Handles GitHub push event.
    
    Supports tagging issues when commits are pushed to specific branches.
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        bool: True on success, False on failure
    """
    if not args.push_branch:
        print("Error: --push-branch is required for push events.", file=sys.stderr)
        return False
    
    log_action(f"Handling push event", level="DEBUG",
               branch=args.push_branch, target_branch=args.target_branch)
    
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
    
    # Transition issue if configured
    if args.transition_tag:
        if not change_issue_status(jira_key, args.transition_tag):
            log_action(f"Failed to transition issue on push", level="ERROR",
                      issue_key=jira_key, transition=args.transition_tag)
            return False
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Jira Integration Script for GitHub-to-Jira sync (Phase 1: Generalized)",
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

  # Handle push event with target branch matching
  python jira_integration_script.py \\
    --event-name push \\
    --jira-url https://jira.example.com \\
    --jira-token YOUR_TOKEN \\
    --project-key CLOUD \\
    --push-branch main \\
    --target-branch main \\
    --transition-tag "Released"
        """
    )
    
    # Core arguments
    parser.add_argument("--event-name", required=True, 
                       choices=["issues", "pull_request", "push"],
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
    
    # Transition arguments (Phase 1 generalization)
    parser.add_argument("--transition-opened", default="", 
                       help="Jira transition name when PR is opened (e.g., 'In Progress')")
    parser.add_argument("--transition-merged", default="", 
                       help="Jira transition name when PR is merged (e.g., 'Done')")
    parser.add_argument("--transition-tag", default="", 
                       help="Jira transition name when pushed to target branch (e.g., 'Released')")
    
    # Event routing arguments (Phase 1 generalization)
    parser.add_argument("--target-branch", default="", 
                       help="Target branch for push event matching (e.g., 'main', 'develop')")
    
    # Link arguments (Phase 1 generalization)
    parser.add_argument("--link-title", default="GitHub PR",
                       help="Custom title for GitHub PR links (default: 'GitHub PR')")
    
    args = parser.parse_args()

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
