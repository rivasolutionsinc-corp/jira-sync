# -*- coding: utf-8 -*-
"""Unit Tests for Jira Integration Script

Tests for new functions added in Phase 1: Advanced GitHub Actions CI/CD Automation
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jira_integration_script import (
    create_jira_subtask,
    link_jira_issues,
    retry_api_call,
    create_jira_issue,
    add_comment,
    get_issue_details,
    change_issue_status
)


class TestCreateJiraSubtask(unittest.TestCase):
    """Test cases for create_jira_subtask function"""

    @patch('jira_integration_script.requests.post')
    def test_create_subtask_success(self, mock_post):
        """Test successful subtask creation"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'key': 'AQD-1235'}
        mock_post.return_value = mock_response

        result = create_jira_subtask(
            'AQD-1234',
            'Test Subtask',
            'Test Description'
        )

        self.assertEqual(result, 'AQD-1235')
        mock_post.assert_called_once()

    @patch('jira_integration_script.requests.post')
    def test_create_subtask_failure(self, mock_post):
        """Test subtask creation failure"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_post.return_value = mock_response

        result = create_jira_subtask(
            'AQD-1234',
            'Test Subtask',
            'Test Description'
        )

        self.assertIsNone(result)

    @patch('jira_integration_script.requests.post')
    def test_create_subtask_invalid_parent_key(self, mock_post):
        """Test subtask creation with invalid parent key format"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = 'Issue not found'
        mock_post.return_value = mock_response

        result = create_jira_subtask(
            'INVALID',
            'Test Subtask',
            'Test Description'
        )

        self.assertIsNone(result)

    @patch('jira_integration_script.requests.post')
    def test_create_subtask_api_error_500(self, mock_post):
        """Test subtask creation with server error"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response

        result = create_jira_subtask(
            'AQD-1234',
            'Test Subtask',
            'Test Description'
        )

        self.assertIsNone(result)


class TestLinkJiraIssues(unittest.TestCase):
    """Test cases for link_jira_issues function"""

    @patch('jira_integration_script.requests.post')
    def test_link_issues_success(self, mock_post):
        """Test successful issue linking"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        result = link_jira_issues('AQD-1234', 'AQD-1235', 'relates to')

        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch('jira_integration_script.requests.post')
    def test_link_issues_failure(self, mock_post):
        """Test issue linking failure"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_post.return_value = mock_response

        result = link_jira_issues('AQD-1234', 'AQD-1235', 'relates to')

        self.assertFalse(result)

    @patch('jira_integration_script.requests.post')
    def test_link_issues_invalid_link_type(self, mock_post):
        """Test issue linking with invalid link type"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'Invalid link type'
        mock_post.return_value = mock_response

        result = link_jira_issues('AQD-1234', 'AQD-1235', 'invalid_type')

        self.assertFalse(result)


class TestRetryApiCall(unittest.TestCase):
    """Test cases for retry_api_call function"""

    @patch('jira_integration_script.time.sleep')
    def test_retry_success_first_attempt(self, mock_sleep):
        """Test successful API call on first attempt"""
        mock_func = MagicMock(return_value='success')

        result = retry_api_call(mock_func, max_retries=3, backoff_factor=2)

        self.assertEqual(result, 'success')
        mock_func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('jira_integration_script.time.sleep')
    def test_retry_success_after_failures(self, mock_sleep):
        """Test successful API call after retries"""
        mock_func = MagicMock(
            side_effect=[
                Exception('Connection error'),
                Exception('Timeout'),
                'success'
            ]
        )

        result = retry_api_call(mock_func, max_retries=3, backoff_factor=2)

        self.assertEqual(result, 'success')
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('jira_integration_script.time.sleep')
    def test_retry_failure_max_retries(self, mock_sleep):
        """Test API call failure after max retries"""
        mock_func = MagicMock(side_effect=Exception('Connection error'))

        result = retry_api_call(mock_func, max_retries=3, backoff_factor=2)

        self.assertIsNone(result)
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('jira_integration_script.time.sleep')
    def test_retry_exponential_backoff(self, mock_sleep):
        """Test exponential backoff timing"""
        mock_func = MagicMock(
            side_effect=[
                Exception('Error 1'),
                Exception('Error 2'),
                'success'
            ]
        )

        result = retry_api_call(mock_func, max_retries=3, backoff_factor=2)

        self.assertEqual(result, 'success')
        # Verify exponential backoff: 2^0=1, 2^1=2
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)


class TestExistingFunctions(unittest.TestCase):
    """Test cases for existing functions to ensure backward compatibility"""

    @patch('jira_integration_script.requests.post')
    def test_create_jira_issue_success(self, mock_post):
        """Test successful Jira issue creation"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'key': 'AQD-1234'}
        mock_post.return_value = mock_response

        result = create_jira_issue('AQD', 'Test Issue', 'Test Description')

        self.assertEqual(result, 'AQD-1234')

    @patch('jira_integration_script.requests.post')
    def test_add_comment_success(self, mock_post):
        """Test successful comment addition"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        # Should not raise exception
        add_comment('AQD-1234', 'Test comment')
        mock_post.assert_called_once()

    @patch('jira_integration_script.requests.get')
    def test_get_issue_details_success(self, mock_get):
        """Test successful issue details retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'key': 'AQD-1234',
            'fields': {
                'summary': 'Test Issue',
                'description': 'Test Description',
                'status': {'name': 'To Do'},
                'assignee': {'displayName': 'John Doe'},
                'created': '2026-04-08T00:00:00.000Z',
                'updated': '2026-04-08T12:00:00.000Z',
                'issuetype': {'name': 'Task'},
                'priority': {'name': 'Medium'}
            }
        }
        mock_get.return_value = mock_response

        result = get_issue_details('AQD-1234')

        self.assertEqual(result['key'], 'AQD-1234')
        self.assertEqual(result['status'], 'To Do')

    @patch('jira_integration_script.requests.get')
    @patch('jira_integration_script.requests.post')
    def test_change_issue_status_success(self, mock_post, mock_get):
        """Test successful issue status transition"""
        # Mock get transitions
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'transitions': [
                {'id': '1', 'name': 'Start Progress'},
                {'id': '2', 'name': 'Done'}
            ]
        }
        mock_get.return_value = mock_get_response

        # Mock post transition
        mock_post_response = MagicMock()
        mock_post_response.status_code = 204
        mock_post.return_value = mock_post_response

        result = change_issue_status('AQD-1234', 'Start Progress')

        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
