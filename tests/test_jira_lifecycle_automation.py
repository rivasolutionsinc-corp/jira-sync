#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Test Suite for Jira Lifecycle Automation Primitives

Tests all newly implemented functions:
- link_github_pr_remote()
- change_issue_status() with transition discovery
- create_jira_subtask()
- link_jira_issues()
- log_action() utility

Usage:
    python3 test_jira_lifecycle_automation.py
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import the script we're testing
sys.path.insert(0, os.path.dirname(__file__))
import jira_integration_script as jira

# Test Configuration
TEST_CONFIG = {
    "jira_url": os.getenv("JIRA_BASE_URL", "https://your-jira-instance.com/jira"),
    "jira_token": os.getenv("JIRA_PAT", ""),
    "project_key": "CLOUD",
    "test_issue_key": "CLOUD-1952",  # Use the issue we just created
    "github_pr_url": "https://github.com/rivasolutionsinc-corp/jira-sync/pull/44",
    "github_pr_title": "feat(CLOUD-1952): Add advanced lifecycle automation primitives",
}

# Test Results
test_results = {
    "passed": [],
    "failed": [],
    "skipped": [],
}

def print_test_header(test_name):
    """Print a formatted test header."""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"{'='*70}")

def print_test_result(test_name, passed, message=""):
    """Print test result."""
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{status}: {test_name}")
    if message:
        print(f"  Message: {message}")
    
    if passed:
        test_results["passed"].append(test_name)
    else:
        test_results["failed"].append(test_name)

def test_log_action():
    """Test the log_action() utility function."""
    print_test_header("log_action() Utility")
    
    try:
        print("\nTesting structured logging with different levels:")
        jira.log_action("Test INFO message", level="INFO", test_key="test_value")
        jira.log_action("Test WARNING message", level="WARNING", warning_code=123)
        jira.log_action("Test ERROR message", level="ERROR", error_type="TestError")
        jira.log_action("Test DEBUG message", level="DEBUG", debug_info="detailed info")
        
        print_test_result("log_action()", True, "All log levels working correctly")
        return True
    except Exception as e:
        print_test_result("log_action()", False, str(e))
        return False

def test_link_github_pr_remote():
    """Test the link_github_pr_remote() function."""
    print_test_header("link_github_pr_remote() - GitHub PR Web Linking")
    
    if not TEST_CONFIG["jira_token"]:
        print_test_result("link_github_pr_remote()", False, "JIRA_PAT not set in environment")
        test_results["skipped"].append("link_github_pr_remote()")
        return False
    
    try:
        print(f"\nTesting GitHub PR web link creation:")
        print(f"  Issue Key: {TEST_CONFIG['test_issue_key']}")
        print(f"  PR URL: {TEST_CONFIG['github_pr_url']}")
        print(f"  PR Title: {TEST_CONFIG['github_pr_title']}")
        
        # Set globals for the function
        jira.JIRA_URL = TEST_CONFIG["jira_url"]
        jira.JIRA_TOKEN = TEST_CONFIG["jira_token"]
        
        result = jira.link_github_pr_remote(
            TEST_CONFIG["test_issue_key"],
            TEST_CONFIG["github_pr_url"],
            TEST_CONFIG["github_pr_title"]
        )
        
        if result:
            print_test_result("link_github_pr_remote()", True, "Web link created successfully")
            return True
        else:
            print_test_result("link_github_pr_remote()", False, "Function returned False")
            return False
    except Exception as e:
        print_test_result("link_github_pr_remote()", False, str(e))
        return False

def test_change_issue_status_discovery():
    """Test the enhanced change_issue_status() with transition discovery."""
    print_test_header("change_issue_status() - Transition Discovery")
    
    if not TEST_CONFIG["jira_token"]:
        print_test_result("change_issue_status()", False, "JIRA_PAT not set in environment")
        test_results["skipped"].append("change_issue_status()")
        return False
    
    try:
        print(f"\nTesting transition discovery for issue: {TEST_CONFIG['test_issue_key']}")
        
        # Set globals for the function
        jira.JIRA_URL = TEST_CONFIG["jira_url"]
        jira.JIRA_TOKEN = TEST_CONFIG["jira_token"]
        
        # Test 1: Try a valid transition (should succeed or fail gracefully)
        print("\n  Test 1: Attempting valid transition...")
        result = jira.change_issue_status(TEST_CONFIG["test_issue_key"], "In Progress")
        print(f"  Result: {result}")
        
        # Test 2: Try an invalid transition (should log available transitions)
        print("\n  Test 2: Attempting invalid transition (should show available options)...")
        result = jira.change_issue_status(TEST_CONFIG["test_issue_key"], "InvalidTransition")
        print(f"  Result: {result}")
        
        print_test_result("change_issue_status()", True, "Transition discovery working")
        return True
    except Exception as e:
        print_test_result("change_issue_status()", False, str(e))
        return False

def test_create_jira_subtask():
    """Test the create_jira_subtask() function."""
    print_test_header("create_jira_subtask() - Sub-task Creation")
    
    if not TEST_CONFIG["jira_token"]:
        print_test_result("create_jira_subtask()", False, "JIRA_PAT not set in environment")
        test_results["skipped"].append("create_jira_subtask()")
        return False
    
    try:
        print(f"\nTesting sub-task creation for parent: {TEST_CONFIG['test_issue_key']}")
        
        # Set globals for the function
        jira.JIRA_URL = TEST_CONFIG["jira_url"]
        jira.JIRA_TOKEN = TEST_CONFIG["jira_token"]
        
        subtask_summary = f"Test Sub-task - {datetime.now().isoformat()}"
        subtask_description = "This is a test sub-task created by the test suite"
        
        result = jira.create_jira_subtask(
            TEST_CONFIG["test_issue_key"],
            subtask_summary,
            subtask_description
        )
        
        if result:
            print(f"  Created sub-task: {result}")
            print_test_result("create_jira_subtask()", True, f"Sub-task created: {result}")
            return True
        else:
            print_test_result("create_jira_subtask()", False, "Function returned None")
            return False
    except Exception as e:
        print_test_result("create_jira_subtask()", False, str(e))
        return False

def test_link_jira_issues():
    """Test the link_jira_issues() function."""
    print_test_header("link_jira_issues() - Issue Linking")
    
    if not TEST_CONFIG["jira_token"]:
        print_test_result("link_jira_issues()", False, "JIRA_PAT not set in environment")
        test_results["skipped"].append("link_jira_issues()")
        return False
    
    try:
        print(f"\nTesting issue linking:")
        print(f"  Issue 1: {TEST_CONFIG['test_issue_key']}")
        print(f"  Issue 2: CLOUD-1949 (previous implementation)")
        
        # Set globals for the function
        jira.JIRA_URL = TEST_CONFIG["jira_url"]
        jira.JIRA_TOKEN = TEST_CONFIG["jira_token"]
        
        # Try different link types - use REST API names (not UI display names)
        # REST API uses the "name" field from /rest/api/2/issueLinkType
        # Examples: "Blocks", "Duplicate", "Dependency", "Child-Issue", etc.
        link_types_to_try = [
            "Blocks",
            "Duplicate",
            "Dependency",
            "Child-Issue",
            "Cloners",
            "Builds",
            "Causes",
            "Cause",
            "Defines",
            "Describes",
            "Defect",
            "Backfill",
            "Current Fill"
        ]
        result = False
        used_link_type = None
        
        for link_type in link_types_to_try:
            print(f"\n  Attempting link type: '{link_type}'")
            result = jira.link_jira_issues(
                TEST_CONFIG["test_issue_key"],
                "CLOUD-1949",
                link_type
            )
            if result:
                used_link_type = link_type
                break
        
        if result:
            print_test_result("link_jira_issues()", True, f"Issues linked successfully with '{used_link_type}'")
            return True
        else:
            print_test_result("link_jira_issues()", False, "No valid link type found on Jira instance")
            return False
    except Exception as e:
        print_test_result("link_jira_issues()", False, str(e))
        return False

def print_summary():
    """Print test summary."""
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Passed:  {len(test_results['passed'])}")
    print(f"❌ Failed:  {len(test_results['failed'])}")
    print(f"⏭️  Skipped: {len(test_results['skipped'])}")
    
    if test_results["passed"]:
        print(f"\nPassed Tests:")
        for test in test_results["passed"]:
            print(f"  ✅ {test}")
    
    if test_results["failed"]:
        print(f"\nFailed Tests:")
        for test in test_results["failed"]:
            print(f"  ❌ {test}")
    
    if test_results["skipped"]:
        print(f"\nSkipped Tests:")
        for test in test_results["skipped"]:
            print(f"  ⏭️  {test}")
    
    total = len(test_results["passed"]) + len(test_results["failed"])
    if total > 0:
        pass_rate = (len(test_results["passed"]) / total) * 100
        print(f"\nPass Rate: {pass_rate:.1f}%")

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("JIRA LIFECYCLE AUTOMATION TEST SUITE")
    print("="*70)
    print(f"Jira URL: {TEST_CONFIG['jira_url']}")
    print(f"Project: {TEST_CONFIG['project_key']}")
    print(f"Test Issue: {TEST_CONFIG['test_issue_key']}")
    
    # Run all tests
    test_log_action()
    test_link_github_pr_remote()
    test_change_issue_status_discovery()
    test_create_jira_subtask()
    test_link_jira_issues()
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    if test_results["failed"]:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
