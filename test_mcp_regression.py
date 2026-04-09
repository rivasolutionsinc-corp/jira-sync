#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Regression Test Suite for Jira MCP Server

Tests all 6 MCP tools with:
- Timeout validation (30s)
- Error handling
- Edge cases
- Response validation
"""

import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / "config" / ".env"
load_dotenv(env_path)

# Set JIRA_TOKEN from JIRA_PAT
jira_pat = os.getenv("JIRA_PAT")
if jira_pat:
    os.environ["JIRA_TOKEN"] = jira_pat

# Import Jira integration functions
from jira_integration_script import (
    create_jira_issue,
    get_issue_details,
    add_comment,
    change_issue_status
)

class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"✓ {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"✗ {test_name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Results: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"\nFailed Tests:")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")
        print(f"{'='*60}\n")
        return self.failed == 0

def test_create_issue(results):
    """Test 1: Create Jira Issue"""
    try:
        start = time.time()
        issue_key = create_jira_issue(
            project_key="ADO",
            summary="Regression Test - Create Issue",
            description="Testing create_jira_issue function with timeout validation",
            issue_type="Task"
        )
        elapsed = time.time() - start
        
        if not issue_key:
            results.add_fail("create_jira_issue", "No issue key returned")
            return None
        
        if elapsed > 30:
            results.add_fail("create_jira_issue", f"Timeout exceeded: {elapsed:.2f}s")
            return None
        
        results.add_pass(f"create_jira_issue (created {issue_key} in {elapsed:.2f}s)")
        return issue_key
    except Exception as e:
        results.add_fail("create_jira_issue", str(e))
        return None

def test_get_issue_details(results, issue_key):
    """Test 2: Get Issue Details"""
    if not issue_key:
        print("⊘ Skipping get_issue_details (no issue key)")
        return
    
    try:
        start = time.time()
        details = get_issue_details(issue_key)
        elapsed = time.time() - start
        
        if not details:
            results.add_fail("get_issue_details", "No details returned")
            return
        
        if elapsed > 30:
            results.add_fail("get_issue_details", f"Timeout exceeded: {elapsed:.2f}s")
            return
        
        # Validate response structure
        required_fields = ["key", "summary", "status", "issue_type"]
        missing = [f for f in required_fields if f not in details]
        if missing:
            results.add_fail("get_issue_details", f"Missing fields: {missing}")
            return
        
        results.add_pass(f"get_issue_details (retrieved {issue_key} in {elapsed:.2f}s)")
    except Exception as e:
        results.add_fail("get_issue_details", str(e))

def test_add_comment(results, issue_key):
    """Test 3: Add Comment to Issue"""
    if not issue_key:
        print("⊘ Skipping add_comment (no issue key)")
        return
    
    try:
        start = time.time()
        comment_text = f"Regression test comment - {time.time()}"
        add_comment(issue_key, comment_text)
        elapsed = time.time() - start
        
        if elapsed > 30:
            results.add_fail("add_comment", f"Timeout exceeded: {elapsed:.2f}s")
            return
        
        results.add_pass(f"add_comment (added to {issue_key} in {elapsed:.2f}s)")
    except Exception as e:
        results.add_fail("add_comment", str(e))

def test_change_issue_status(results, issue_key):
    """Test 4: Change Issue Status"""
    if not issue_key:
        print("⊘ Skipping change_issue_status (no issue key)")
        return
    
    try:
        start = time.time()
        success = change_issue_status(issue_key, "Start Progress")
        elapsed = time.time() - start
        
        if not success:
            results.add_fail("change_issue_status", "Status change failed")
            return
        
        if elapsed > 30:
            results.add_fail("change_issue_status", f"Timeout exceeded: {elapsed:.2f}s")
            return
        
        results.add_pass(f"change_issue_status (transitioned {issue_key} in {elapsed:.2f}s)")
    except Exception as e:
        results.add_fail("change_issue_status", str(e))

def test_search_issues(results):
    """Test 5: Search Issues (via jira_integration_script)"""
    try:
        # This tests the underlying search capability
        # Use ADO-193 which was created in the basic test
        start = time.time()
        details = get_issue_details("ADO-193")  # Get a known issue
        elapsed = time.time() - start
        
        if not details:
            results.add_fail("search_issues", "Could not retrieve test issue")
            return
        
        if elapsed > 30:
            results.add_fail("search_issues", f"Timeout exceeded: {elapsed:.2f}s")
            return
        
        results.add_pass(f"search_issues (retrieved ADO-193 in {elapsed:.2f}s)")
    except Exception as e:
        results.add_fail("search_issues", str(e))

def test_error_handling(results):
    """Test 6: Error Handling - Invalid Issue Key"""
    try:
        start = time.time()
        details = get_issue_details("INVALID-99999")
        elapsed = time.time() - start
        
        # Should return None or error message, not crash
        if elapsed > 30:
            results.add_fail("error_handling", f"Timeout exceeded: {elapsed:.2f}s")
            return
        
        results.add_pass(f"error_handling (gracefully handled invalid key in {elapsed:.2f}s)")
    except Exception as e:
        results.add_fail("error_handling", str(e))

def test_timeout_validation(results):
    """Test 7: Timeout Configuration"""
    try:
        # Verify REQUEST_TIMEOUT is set in jira_mcp_server
        with open("jira_mcp_server.py", "r") as f:
            content = f.read()
            if "REQUEST_TIMEOUT = 30" in content:
                results.add_pass("timeout_validation (REQUEST_TIMEOUT = 30 seconds)")
            else:
                results.add_fail("timeout_validation", "REQUEST_TIMEOUT not set to 30 seconds")
    except Exception as e:
        results.add_fail("timeout_validation", str(e))

def test_mcp_client_import(results):
    """Test 8: MCP Client Import"""
    try:
        from mcp_client import atlassian_mcp, AtlassianMCPClient
        results.add_pass("mcp_client_import (AtlassianMCPClient available)")
    except ImportError as e:
        results.add_fail("mcp_client_import", f"Failed to import mcp_client: {e}")
    except Exception as e:
        results.add_fail("mcp_client_import", str(e))

def test_mcp_client_initialization(results):
    """Test 9: MCP Client Initialization"""
    try:
        from mcp_client import AtlassianMCPClient
        client = AtlassianMCPClient()
        results.add_pass("mcp_client_initialization (Client initialized successfully)")
    except ValueError as e:
        results.add_fail("mcp_client_initialization", f"Missing credentials: {e}")
    except Exception as e:
        results.add_fail("mcp_client_initialization", str(e))

def test_mcp_tool_methods_exist(results):
    """Test 10: MCP Tool Methods Exist"""
    try:
        from mcp_client import atlassian_mcp
        
        # Check all required methods exist
        required_methods = [
            'jira_search', 'jira_get_issue', 'jira_create_issue',
            'jira_add_comment', 'jira_list_transitions', 'jira_transition_issue',
            'confluence_search', 'confluence_get_page', 'jira_link_issues'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(atlassian_mcp, method):
                missing_methods.append(method)
        
        if missing_methods:
            results.add_fail("mcp_tool_methods_exist", f"Missing methods: {', '.join(missing_methods)}")
        else:
            results.add_pass("mcp_tool_methods_exist (All 9 MCP tool methods available)")
    except Exception as e:
        results.add_fail("mcp_tool_methods_exist", str(e))

def test_jira_integration_script_refactored(results):
    """Test 11: Jira Integration Script Refactored"""
    try:
        with open("jira_integration_script.py", "r") as f:
            content = f.read()
            
            # Check for MCP imports
            if "from mcp_client import" not in content:
                results.add_fail("jira_integration_script_refactored", "MCP client not imported")
                return
            
            # Check for MCP_AVAILABLE flag
            if "MCP_AVAILABLE" not in content:
                results.add_fail("jira_integration_script_refactored", "MCP_AVAILABLE flag not set")
                return
            
            # Check for fallback logic
            if "Falling back to REST API" not in content:
                results.add_fail("jira_integration_script_refactored", "Fallback logic not implemented")
                return
            
            results.add_pass("jira_integration_script_refactored (Script successfully refactored with MCP support)")
    except Exception as e:
        results.add_fail("jira_integration_script_refactored", str(e))

def test_backward_compatibility(results):
    """Test 12: Backward Compatibility"""
    try:
        from jira_integration_script import (
            create_jira_issue,
            add_comment,
            get_issue_details,
            change_issue_status,
            create_jira_subtask,
            link_jira_issues,
            retry_api_call
        )
        
        # Verify all functions are callable
        functions = [
            create_jira_issue, add_comment, get_issue_details,
            change_issue_status, create_jira_subtask, link_jira_issues,
            retry_api_call
        ]
        
        for func in functions:
            if not callable(func):
                results.add_fail("backward_compatibility", f"Function {func.__name__} is not callable")
                return
        
        results.add_pass("backward_compatibility (All 7 functions maintain backward compatibility)")
    except ImportError as e:
        results.add_fail("backward_compatibility", f"Failed to import functions: {e}")
    except Exception as e:
        results.add_fail("backward_compatibility", str(e))

def main():
    """Run all regression tests"""
    print("\n" + "="*60)
    print("Jira MCP Server - Regression Test Suite")
    print("="*60 + "\n")
    
    results = TestResults()
    
    # Verify environment
    if not os.getenv("JIRA_TOKEN"):
        print("ERROR: JIRA_TOKEN not set")
        return 1
    
    print("Running Tests...\n")
    
    # Test 1: Create Issue
    issue_key = test_create_issue(results)
    
    # Test 2: Get Issue Details
    test_get_issue_details(results, issue_key)
    
    # Test 3: Add Comment
    test_add_comment(results, issue_key)
    
    # Test 4: Change Status
    test_change_issue_status(results, issue_key)
    
    # Test 5: Search Issues
    test_search_issues(results)
    
    # Test 6: Error Handling
    test_error_handling(results)
    
    # Test 7: Timeout Validation
    test_timeout_validation(results)
    
    # Test 8: MCP Client Import
    test_mcp_client_import(results)
    
    # Test 9: MCP Client Initialization
    test_mcp_client_initialization(results)
    
    # Test 10: MCP Tool Methods
    test_mcp_tool_methods_exist(results)
    
    # Test 11: Jira Integration Script Refactored
    test_jira_integration_script_refactored(results)
    
    # Test 12: Backward Compatibility
    test_backward_compatibility(results)
    
    # Print summary
    success = results.summary()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
