# -*- coding: utf-8 -*-
"""Test Suite for Phase 2: Production-Ready REST API

Comprehensive tests for jira_integration_script.py Phase 2 implementation.
Tests cover:
- Input validation
- Rate limiting
- Retry logic with exponential backoff
- Timeout handling
- Error handling
- Event routing
- Phase 1 features (configurable transitions, event routing, link logic)
"""

import pytest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
import requests
from requests.exceptions import Timeout, ConnectionError

# Import the script module
sys.path.insert(0, os.path.dirname(__file__))
import jira_integration_script as jis


class TestInputValidation:
    """Test input validation functions."""
    
    def test_validate_jira_url_valid(self):
        """Test valid Jira URL validation."""
        assert jis.validate_jira_url("https://jira.example.com") is True
        assert jis.validate_jira_url("http://jira.local:8080") is True
    
    def test_validate_jira_url_invalid(self):
        """Test invalid Jira URL validation."""
        assert jis.validate_jira_url("") is False
        assert jis.validate_jira_url("not-a-url") is False
        assert jis.validate_jira_url("ftp://jira.example.com") is False
        assert jis.validate_jira_url(None) is False
        assert jis.validate_jira_url(123) is False
    
    def test_validate_jira_token_valid(self):
        """Test valid Jira token validation."""
        assert jis.validate_jira_token("valid_token_1234567890") is True
    
    def test_validate_jira_token_invalid(self):
        """Test invalid Jira token validation."""
        assert jis.validate_jira_token("") is False
        assert jis.validate_jira_token("YOUR_PAT_HERE") is False
        assert jis.validate_jira_token("short") is False
        assert jis.validate_jira_token(None) is False
    
    def test_validate_issue_key_valid(self):
        """Test valid issue key validation."""
        assert jis.validate_issue_key("CLOUD-1234") is True
        assert jis.validate_issue_key("AQD-999") is True
        assert jis.validate_issue_key("TEST_KEY-1") is True
    
    def test_validate_issue_key_invalid(self):
        """Test invalid issue key validation."""
        assert jis.validate_issue_key("") is False
        assert jis.validate_issue_key("cloud-1234") is False  # lowercase
        assert jis.validate_issue_key("CLOUD1234") is False  # no dash
        assert jis.validate_issue_key("1234-CLOUD") is False  # wrong order
        assert jis.validate_issue_key(None) is False
    
    def test_validate_project_key_valid(self):
        """Test valid project key validation."""
        assert jis.validate_project_key("CLOUD") is True
        assert jis.validate_project_key("AQD") is True
        assert jis.validate_project_key("TEST_KEY") is True
    
    def test_validate_project_key_invalid(self):
        """Test invalid project key validation."""
        assert jis.validate_project_key("") is False
        assert jis.validate_project_key("cloud") is False  # lowercase
        assert jis.validate_project_key("123") is False  # starts with number
        assert jis.validate_project_key(None) is False
    
    def test_validate_url_valid(self):
        """Test valid URL validation."""
        assert jis.validate_url("https://github.com/org/repo/pull/123") is True
        assert jis.validate_url("http://example.com") is True
    
    def test_validate_url_invalid(self):
        """Test invalid URL validation."""
        assert jis.validate_url("") is False
        assert jis.validate_url("not-a-url") is False
        assert jis.validate_url(None) is False


class TestExtractJiraKey:
    """Test Jira key extraction from branch names."""
    
    def test_extract_from_feature_branch(self):
        """Test extraction from feature branch."""
        assert jis.extract_jira_key_from_branch("feature/CLOUD-1234-description") == "CLOUD-1234"
    
    def test_extract_from_bugfix_branch(self):
        """Test extraction from bugfix branch."""
        assert jis.extract_jira_key_from_branch("bugfix/CLOUD-1234") == "CLOUD-1234"
    
    def test_extract_from_simple_branch(self):
        """Test extraction from simple branch."""
        assert jis.extract_jira_key_from_branch("CLOUD-1234-description") == "CLOUD-1234"
    
    def test_extract_no_key(self):
        """Test extraction when no key present."""
        assert jis.extract_jira_key_from_branch("main") is None
        assert jis.extract_jira_key_from_branch("develop") is None
    
    def test_extract_invalid_input(self):
        """Test extraction with invalid input."""
        assert jis.extract_jira_key_from_branch("") is None
        assert jis.extract_jira_key_from_branch(None) is None


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @patch('time.sleep')
    def test_rate_limit_delay(self, mock_sleep):
        """Test rate limit delay is applied."""
        jis.rate_limit_delay()
        mock_sleep.assert_called_once_with(jis.RATE_LIMIT_DELAY)


class TestRetryLogic:
    """Test retry logic with exponential backoff."""
    
    @patch('time.sleep')
    def test_retry_success_first_attempt(self, mock_sleep):
        """Test successful call on first attempt."""
        func = Mock(return_value="success")
        result = jis.retry_api_call(func, max_retries=3, backoff_factor=2)
        
        assert result == "success"
        assert func.call_count == 1
        mock_sleep.assert_not_called()
    
    @patch('time.sleep')
    def test_retry_success_after_failures(self, mock_sleep):
        """Test successful call after retries."""
        func = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        result = jis.retry_api_call(func, max_retries=3, backoff_factor=2)
        
        assert result == "success"
        assert func.call_count == 3
        assert mock_sleep.call_count == 2
    
    @patch('time.sleep')
    def test_retry_max_retries_exceeded(self, mock_sleep):
        """Test failure after max retries exceeded."""
        func = Mock(side_effect=Exception("fail"))
        result = jis.retry_api_call(func, max_retries=3, backoff_factor=2)
        
        assert result is None
        assert func.call_count == 3
        assert mock_sleep.call_count == 2
    
    @patch('time.sleep')
    def test_retry_exponential_backoff(self, mock_sleep):
        """Test exponential backoff timing."""
        func = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        jis.retry_api_call(func, max_retries=3, backoff_factor=2)
        
        # Should sleep for 2^0=1 and 2^1=2 seconds
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)


class TestCreateJiraIssue:
    """Test create_jira_issue function."""
    
    @patch('jira_integration_script.get_session')
    def test_create_issue_success(self, mock_get_session):
        """Test successful issue creation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"key": "CLOUD-1234"}
        
        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_get_session.return_value = mock_session
        
        result = jis.create_jira_issue("CLOUD", "Test Issue", "Test Description")
        
        assert result == "CLOUD-1234"
        mock_session.post.assert_called_once()
    
    @patch('jira_integration_script.get_session')
    def test_create_issue_invalid_project_key(self, mock_get_session):
        """Test issue creation with invalid project key."""
        result = jis.create_jira_issue("invalid", "Test Issue", "Test Description")
        assert result is None
        mock_get_session.assert_not_called()
    
    @patch('jira_integration_script.get_session')
    def test_create_issue_invalid_summary(self, mock_get_session):
        """Test issue creation with invalid summary."""
        result = jis.create_jira_issue("CLOUD", "", "Test Description")
        assert result is None
        mock_get_session.assert_not_called()
    
    @patch('jira_integration_script.get_session')
    def test_create_issue_timeout(self, mock_get_session):
        """Test issue creation with timeout."""
        mock_session = Mock()
        mock_session.post.side_effect = Timeout("Request timeout")
        mock_get_session.return_value = mock_session
        
        result = jis.create_jira_issue("CLOUD", "Test Issue", "Test Description")
        assert result is None
    
    @patch('jira_integration_script.get_session')
    def test_create_issue_http_error(self, mock_get_session):
        """Test issue creation with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        
        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_get_session.return_value = mock_session
        
        result = jis.create_jira_issue("CLOUD", "Test Issue", "Test Description")
        assert result is None


class TestAddComment:
    """Test add_comment function."""
    
    @patch('jira_integration_script.get_session')
    def test_add_comment_success(self, mock_get_session):
        """Test successful comment addition."""
        mock_response = Mock()
        mock_response.status_code = 201
        
        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_get_session.return_value = mock_session
        
        result = jis.add_comment("CLOUD-1234", "Test comment")
        
        assert result is True
        mock_session.post.assert_called_once()
    
    @patch('jira_integration_script.get_session')
    def test_add_comment_invalid_issue_key(self, mock_get_session):
        """Test comment addition with invalid issue key."""
        result = jis.add_comment("invalid", "Test comment")
        assert result is False
        mock_get_session.assert_not_called()
    
    @patch('jira_integration_script.get_session')
    def test_add_comment_invalid_body(self, mock_get_session):
        """Test comment addition with invalid body."""
        result = jis.add_comment("CLOUD-1234", "")
        assert result is False
        mock_get_session.assert_not_called()
    
    @patch('jira_integration_script.get_session')
    def test_add_comment_timeout(self, mock_get_session):
        """Test comment addition with timeout."""
        mock_session = Mock()
        mock_session.post.side_effect = Timeout("Request timeout")
        mock_get_session.return_value = mock_session
        
        result = jis.add_comment("CLOUD-1234", "Test comment")
        assert result is False


class TestChangeIssueStatus:
    """Test change_issue_status function."""
    
    @patch('jira_integration_script.get_session')
    def test_change_status_success(self, mock_get_session):
        """Test successful status change."""
        # Mock GET transitions response
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "transitions": [
                {"id": "11", "name": "Done", "to": {"name": "Done"}}
            ]
        }
        
        # Mock POST transition response
        mock_post_response = Mock()
        mock_post_response.status_code = 204
        
        mock_session = Mock()
        mock_session.get.return_value = mock_get_response
        mock_session.post.return_value = mock_post_response
        mock_get_session.return_value = mock_session
        
        result = jis.change_issue_status("CLOUD-1234", "Done")
        
        assert result is True
        assert mock_session.get.call_count == 1
        assert mock_session.post.call_count == 1
    
    @patch('jira_integration_script.get_session')
    def test_change_status_transition_not_found(self, mock_get_session):
        """Test status change with transition not found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transitions": [
                {"id": "11", "name": "Done", "to": {"name": "Done"}}
            ]
        }
        
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session
        
        result = jis.change_issue_status("CLOUD-1234", "NonExistent")
        
        assert result is False
        mock_session.post.assert_not_called()
    
    @patch('jira_integration_script.get_session')
    def test_change_status_invalid_issue_key(self, mock_get_session):
        """Test status change with invalid issue key."""
        result = jis.change_issue_status("invalid", "Done")
        assert result is False
        mock_get_session.assert_not_called()


class TestLinkGitHubPR:
    """Test link_github_pr_remote function."""
    
    @patch('jira_integration_script.get_session')
    def test_link_pr_success(self, mock_get_session):
        """Test successful PR linking."""
        mock_response = Mock()
        mock_response.status_code = 201
        
        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_get_session.return_value = mock_session
        
        result = jis.link_github_pr_remote(
            "CLOUD-1234",
            "https://github.com/org/repo/pull/123",
            "Test PR"
        )
        
        assert result is True
        mock_session.post.assert_called_once()
    
    @patch('jira_integration_script.get_session')
    def test_link_pr_invalid_issue_key(self, mock_get_session):
        """Test PR linking with invalid issue key."""
        result = jis.link_github_pr_remote(
            "invalid",
            "https://github.com/org/repo/pull/123",
            "Test PR"
        )
        assert result is False
        mock_get_session.assert_not_called()
    
    @patch('jira_integration_script.get_session')
    def test_link_pr_invalid_url(self, mock_get_session):
        """Test PR linking with invalid URL."""
        result = jis.link_github_pr_remote(
            "CLOUD-1234",
            "not-a-url",
            "Test PR"
        )
        assert result is False
        mock_get_session.assert_not_called()
    
    @patch('jira_integration_script.get_session')
    def test_link_pr_timeout(self, mock_get_session):
        """Test PR linking with timeout."""
        mock_session = Mock()
        mock_session.post.side_effect = Timeout("Request timeout")
        mock_get_session.return_value = mock_session
        
        result = jis.link_github_pr_remote(
            "CLOUD-1234",
            "https://github.com/org/repo/pull/123",
            "Test PR"
        )
        assert result is False


class TestEventRouting:
    """Test event routing logic."""
    
    def test_route_issues_event(self):
        """Test routing of issues event."""
        args = Mock()
        args.event_name = "issues"
        args.issue_title = "Test Issue"
        args.issue_url = "https://github.com/org/repo/issues/123"
        args.project_key = "CLOUD"
        args.issue_type = "Task"
        
        with patch('jira_integration_script.handle_issues_event') as mock_handler:
            mock_handler.return_value = "CLOUD-1234"
            result = jis.route_event("issues", args)
            mock_handler.assert_called_once_with(args)
    
    def test_route_pull_request_event(self):
        """Test routing of pull_request event."""
        args = Mock()
        args.event_name = "pull_request"
        
        with patch('jira_integration_script.handle_pull_request_event') as mock_handler:
            mock_handler.return_value = True
            result = jis.route_event("pull_request", args)
            mock_handler.assert_called_once_with(args)
    
    def test_route_push_event(self):
        """Test routing of push event."""
        args = Mock()
        args.event_name = "push"
        
        with patch('jira_integration_script.handle_push_event') as mock_handler:
            mock_handler.return_value = True
            result = jis.route_event("push", args)
            mock_handler.assert_called_once_with(args)
    
    def test_route_unsupported_event(self):
        """Test routing of unsupported event."""
        args = Mock()
        result = jis.route_event("unsupported", args)
        assert result is None


class TestHandlePullRequestEvent:
    """Test pull request event handling."""
    
    @patch('jira_integration_script.link_github_pr_remote')
    @patch('jira_integration_script.add_comment')
    @patch('jira_integration_script.change_issue_status')
    def test_handle_pr_opened(self, mock_transition, mock_comment, mock_link):
        """Test handling of PR opened event."""
        mock_comment.return_value = True
        mock_link.return_value = True
        mock_transition.return_value = True
        
        args = Mock()
        args.pr_branch = "feature/CLOUD-1234-test"
        args.pr_url = "https://github.com/org/repo/pull/123"
        args.pr_title = "Test PR"
        args.pr_action = "opened"
        args.transition_opened = "In Progress"
        args.transition_merged = ""
        args.pr_merged = False
        
        result = jis.handle_pull_request_event(args)
        
        assert result is True
        mock_comment.assert_called_once()
        mock_link.assert_called_once()
        mock_transition.assert_called_once()
    
    @patch('jira_integration_script.link_github_pr_remote')
    @patch('jira_integration_script.change_issue_status')
    def test_handle_pr_closed_merged(self, mock_transition, mock_link):
        """Test handling of PR closed (merged) event."""
        mock_link.return_value = True
        mock_transition.return_value = True
        
        args = Mock()
        args.pr_branch = "feature/CLOUD-1234-test"
        args.pr_url = "https://github.com/org/repo/pull/123"
        args.pr_title = "Test PR"
        args.pr_action = "closed"
        args.pr_merged = True
        args.transition_merged = "Done"
        
        result = jis.handle_pull_request_event(args)
        
        assert result is True
        mock_link.assert_called_once()
        mock_transition.assert_called_once()
    
    def test_handle_pr_no_jira_key(self):
        """Test handling of PR with no Jira key in branch."""
        args = Mock()
        args.pr_branch = "main"
        args.pr_url = "https://github.com/org/repo/pull/123"
        args.pr_title = "Test PR"
        args.pr_action = "opened"
        
        result = jis.handle_pull_request_event(args)
        
        assert result is True  # Not an error, just skip


class TestHandlePushEvent:
    """Test push event handling."""
    
    @patch('jira_integration_script.change_issue_status')
    def test_handle_push_to_target_branch(self, mock_transition):
        """Test handling of push to target branch."""
        mock_transition.return_value = True
        
        args = Mock()
        args.push_branch = "CLOUD-1234-main"
        args.target_branch = "CLOUD-1234-main"
        args.transition_tag = "Released"
        
        result = jis.handle_push_event(args)
        
        assert result is True
        mock_transition.assert_called_once()
    
    def test_handle_push_to_non_target_branch(self):
        """Test handling of push to non-target branch."""
        args = Mock()
        args.push_branch = "develop"
        args.target_branch = "main"
        args.transition_tag = "Released"
        
        result = jis.handle_push_event(args)
        
        assert result is True  # Not an error, just skip
    
    def test_handle_push_no_jira_key(self):
        """Test handling of push with no Jira key in branch."""
        args = Mock()
        args.push_branch = "main"
        args.target_branch = "main"
        args.transition_tag = "Released"
        
        result = jis.handle_push_event(args)
        
        assert result is True  # Not an error, just skip


class TestLogging:
    """Test logging functionality."""
    
    @patch('builtins.print')
    def test_log_action_info(self, mock_print):
        """Test INFO level logging."""
        jis.log_action("Test action", level="INFO", key="value")
        
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "Test action" in call_args
        assert "INFO" in call_args
        assert "key=value" in call_args
    
    @patch('builtins.print')
    def test_log_action_error(self, mock_print):
        """Test ERROR level logging."""
        jis.log_action("Test error", level="ERROR", error="test_error")
        
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "Test error" in call_args
        assert "ERROR" in call_args
        assert "error=test_error" in call_args


class TestPhase1Features:
    """Test Phase 1 features (configurable transitions, event routing, link logic)."""
    
    def test_configurable_transition_opened(self):
        """Test configurable transition on PR opened."""
        args = Mock()
        args.transition_opened = "Custom In Progress"
        args.pr_branch = "feature/CLOUD-1234-test"
        args.pr_url = "https://github.com/org/repo/pull/123"
        args.pr_title = "Test PR"
        args.pr_action = "opened"
        args.transition_merged = ""
        args.pr_merged = False
        
        with patch('jira_integration_script.change_issue_status') as mock_transition:
            mock_transition.return_value = True
            with patch('jira_integration_script.add_comment'):
                with patch('jira_integration_script.link_github_pr_remote'):
                    jis.handle_pull_request_event(args)
                    
                    # Verify custom transition was used
                    calls = mock_transition.call_args_list
                    assert any("Custom In Progress" in str(call) for call in calls)
    
    def test_configurable_transition_merged(self):
        """Test configurable transition on PR merged."""
        args = Mock()
        args.transition_merged = "Custom Done"
        args.pr_branch = "feature/CLOUD-1234-test"
        args.pr_url = "https://github.com/org/repo/pull/123"
        args.pr_title = "Test PR"
        args.pr_action = "closed"
        args.pr_merged = True
        
        with patch('jira_integration_script.change_issue_status') as mock_transition:
            mock_transition.return_value = True
            with patch('jira_integration_script.link_github_pr_remote'):
                jis.handle_pull_request_event(args)
                
                # Verify custom transition was used
                calls = mock_transition.call_args_list
                assert any("Custom Done" in str(call) for call in calls)
    
    def test_target_branch_matching(self):
        """Test target branch matching for push events."""
        args = Mock()
        args.push_branch = "CLOUD-1234-staging"
        args.target_branch = "CLOUD-1234-staging"
        args.transition_tag = "In QA"
        
        with patch('jira_integration_script.change_issue_status') as mock_transition:
            mock_transition.return_value = True
            jis.handle_push_event(args)
            
            # Verify transition was called (branch matched)
            mock_transition.assert_called_once()
    
    def test_link_pr_for_all_pr_events(self):
        """Test that PR linking happens for all PR events."""
        for action in ["opened", "synchronize", "closed"]:
            args = Mock()
            args.pr_branch = "feature/CLOUD-1234-test"
            args.pr_url = "https://github.com/org/repo/pull/123"
            args.pr_title = "Test PR"
            args.pr_action = action
            args.transition_opened = ""
            args.transition_merged = ""
            args.pr_merged = False
            
            with patch('jira_integration_script.link_github_pr_remote') as mock_link:
                mock_link.return_value = True
                with patch('jira_integration_script.add_comment'):
                    with patch('jira_integration_script.change_issue_status'):
                        jis.handle_pull_request_event(args)
                        
                        # Verify link was called for all actions
                        mock_link.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
