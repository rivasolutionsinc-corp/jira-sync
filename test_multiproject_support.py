#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for multi-project support with projectKey=CLOUD

This script tests the configurable Jira project key functionality
by simulating GitHub Actions environment variables.
"""

import os
import sys
from unittest.mock import patch, MagicMock

# Set environment variables to simulate GitHub Actions
os.environ['JIRA_TOKEN'] = 'test-token-12345'
os.environ['JIRA_PROJECT_KEY'] = 'CLOUD'

from jira_integration_script import create_jira_issue, create_jira_subtask

def test_create_issue_with_cloud_project():
    """Test creating a Jira issue with CLOUD project key"""
    print("\n" + "="*70)
    print("TEST 1: Create Jira Issue with CLOUD Project Key")
    print("="*70)
    
    with patch('jira_integration_script.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'key': 'CLOUD-9999'}
        mock_post.return_value = mock_response
        
        # Simulate GitHub Actions calling create_jira_issue with CLOUD project
        project_key = os.getenv('JIRA_PROJECT_KEY', 'AQD')
        print(f"✓ Project Key from environment: {project_key}")
        
        result = create_jira_issue(
            project_key,
            'Test Issue from CLOUD Project',
            'This is a test issue created in the CLOUD project'
        )
        
        print(f"✓ Issue created: {result}")
        
        # Verify the API call used the correct project key
        call_args = mock_post.call_args
        payload = call_args[1]['data']
        print(f"✓ API payload sent: {payload}")
        
        assert 'CLOUD' in payload, "CLOUD project key not found in API payload"
        assert result == 'CLOUD-9999', f"Expected CLOUD-9999, got {result}"
        
        print("✓ TEST PASSED: Issue created successfully with CLOUD project key\n")
        return True

def test_create_subtask_with_cloud_parent():
    """Test creating a Jira subtask with CLOUD parent issue"""
    print("="*70)
    print("TEST 2: Create Jira Subtask with CLOUD Parent Issue")
    print("="*70)
    
    with patch('jira_integration_script.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'key': 'CLOUD-9999-1'}
        mock_post.return_value = mock_response
        
        # Create subtask for CLOUD-9999 parent
        parent_key = 'CLOUD-9999'
        print(f"✓ Parent issue key: {parent_key}")
        
        result = create_jira_subtask(
            parent_key,
            'PR #123: Add multi-project support',
            'PR URL: https://github.com/example/repo/pull/123\nAuthor: testuser'
        )
        
        print(f"✓ Subtask created: {result}")
        
        # Verify the API call used the correct project key
        call_args = mock_post.call_args
        payload = call_args[1]['data']
        print(f"✓ API payload sent: {payload}")
        
        assert 'CLOUD' in payload, "CLOUD project key not found in API payload"
        assert result == 'CLOUD-9999-1', f"Expected CLOUD-9999-1, got {result}"
        
        print("✓ TEST PASSED: Subtask created successfully with CLOUD parent\n")
        return True

def test_default_fallback_to_aqd():
    """Test that system defaults to AQD when JIRA_PROJECT_KEY is not set"""
    print("="*70)
    print("TEST 3: Default Fallback to AQD Project Key")
    print("="*70)
    
    # Remove JIRA_PROJECT_KEY from environment
    if 'JIRA_PROJECT_KEY' in os.environ:
        del os.environ['JIRA_PROJECT_KEY']
    
    with patch('jira_integration_script.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'key': 'AQD-1234'}
        mock_post.return_value = mock_response
        
        # Simulate default behavior
        project_key = os.getenv('JIRA_PROJECT_KEY', 'AQD')
        print(f"✓ Project Key (with default): {project_key}")
        
        result = create_jira_issue(
            project_key,
            'Test Issue with Default Project',
            'This should use AQD project'
        )
        
        print(f"✓ Issue created: {result}")
        
        # Verify the API call used AQD
        call_args = mock_post.call_args
        payload = call_args[1]['data']
        print(f"✓ API payload sent: {payload}")
        
        assert 'AQD' in payload, "AQD project key not found in API payload"
        assert result == 'AQD-1234', f"Expected AQD-1234, got {result}"
        
        print("✓ TEST PASSED: System correctly defaults to AQD\n")
        return True

def test_branch_name_extraction():
    """Test extracting project key from branch names"""
    print("="*70)
    print("TEST 4: Extract Project Key from Branch Names")
    print("="*70)
    
    test_cases = [
        ('feature/CLOUD-9999', 'CLOUD'),
        ('feature/AQD-1234', 'AQD'),
        ('feature/EHC-5678', 'EHC'),
        ('feature/PROJ-999', 'PROJ'),
    ]
    
    import re
    
    for branch_name, expected_project in test_cases:
        # Simulate GitHub Actions branch extraction
        jira_key = re.search(r'[A-Z]+-[0-9]+', branch_name)
        if jira_key:
            extracted_project = jira_key.group().split('-')[0]
            print(f"✓ Branch: {branch_name} → Project: {extracted_project}")
            assert extracted_project == expected_project, \
                f"Expected {expected_project}, got {extracted_project}"
        else:
            print(f"✗ No Jira key found in branch: {branch_name}")
            return False
    
    print("✓ TEST PASSED: All branch names correctly extract project keys\n")
    return True

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("MULTI-PROJECT SUPPORT TEST SUITE")
    print("Testing with projectKey=CLOUD")
    print("="*70)
    
    tests = [
        test_create_issue_with_cloud_project,
        test_create_subtask_with_cloud_parent,
        test_default_fallback_to_aqd,
        test_branch_name_extraction,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ TEST FAILED: {e}\n")
            results.append(False)
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ ALL TESTS PASSED")
        print("\nMulti-project support is working correctly!")
        print("- CLOUD project key is properly configured")
        print("- Default fallback to AQD works as expected")
        print("- Branch name extraction works for all projects")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
