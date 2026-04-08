#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script to create a Jira issue in ADO project"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from config/.env BEFORE importing
env_path = Path(__file__).parent / "config" / ".env"
load_dotenv(env_path)

# Set JIRA_TOKEN from JIRA_PAT before importing
jira_pat = os.getenv("JIRA_PAT")
if jira_pat:
    os.environ["JIRA_TOKEN"] = jira_pat

# Now import the Jira integration functions
from jira_integration_script import create_jira_issue, get_issue_details, add_comment, change_issue_status

def main():
    """Create a test issue in ADO project"""
    
    # Verify JIRA_PAT is set
    jira_pat = os.getenv("JIRA_PAT")
    
    if not jira_pat or jira_pat == "your_jira_pat_here":
        print("ERROR: JIRA_PAT not configured in config/.env")
        print("Please update config/.env with your actual Jira Personal Access Token")
        sys.exit(1)
    
    # Create a test issue
    print("Creating test issue in ADO project...")
    issue_key = create_jira_issue(
        project_key="ADO",
        summary="Test Issue - Jira Integration",
        description="This is a test issue created via the Jira integration script to verify API connectivity.",
        issue_type="Task"
    )
    
    if not issue_key:
        print("✗ Failed to create test issue")
        return 1
    
    print(f"✓ Test issue created successfully: {issue_key}")
    
    # Get issue details
    print(f"\nRetrieving details for {issue_key}...")
    details = get_issue_details(issue_key)
    if details:
        print(f"  Summary: {details['summary']}")
        print(f"  Status: {details['status']}")
        print(f"  Type: {details['issue_type']}")
        print(f"  Created: {details['created']}")
    else:
        print("✗ Failed to retrieve issue details")
        return 1
    
    # Add a comment to the issue
    print(f"\nAdding comment to {issue_key}...")
    comment_text = "This is a test comment added via the Jira integration script."
    add_comment(issue_key, comment_text)
    
    # Change the issue status
    print(f"\nChanging status of {issue_key} to 'Start Progress'...")
    if change_issue_status(issue_key, "Start Progress"):
        # Get updated details
        updated_details = get_issue_details(issue_key)
        if updated_details:
            print(f"  New Status: {updated_details['status']}")
    else:
        print("✗ Failed to change issue status")
        return 1
    
    print(f"\n✓ All operations completed successfully for {issue_key}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
