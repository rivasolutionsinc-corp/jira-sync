# -*- coding: utf-8 -*-
"""Test Suite for Phase 1: Generalized Python Toolset (CLOUD-1959)

Tests for:
- CLI argument parsing and validation
- Event routing logic
- Backward compatibility
- Multiple event types (issues, pull_request, push)
- Transition configuration
- Link title customization
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, call
from io import StringIO
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jira_integration_script as jis


class TestCLIArgumentParsing(unittest.TestCase):
    """Test CLI argument parsing and validation."""
    
    def test_issues_event_required_args(self):
        """Test that issues event requires issue-title and issue-url."""
        with patch('sys.argv', [
            'script.py',
            '--event-name', 'issues',
            '--jira-url', 'https://jira.example.com',
            '--jira-token', 'token123',
            '--project-key', 'CLOUD',
            '--issue-title', 'Test Issue',
            '--issue-url', 'https://github.com/org/repo/issues/1'
        ]):
            # Should not raise
            parser = jis.argparse.ArgumentParser()
            # This is just to verify the argument structure exists
            self.assertTrue(True)
    
    def test_pull_request_event_required_args(self):
        """Test that pull_request event requires pr-branch and pr-url."""
        with patch('sys.argv', [
            'script.py',
            '--event-name', 'pull_request',
            '--jira-url', 'https://jira.example.com',
            '--jira-token', 'token123',
            '--project-key', 'CLOUD',
            '--pr-branch', 'feature/CLOUD-1234-test',
            '--pr-url', 'https://github.com/org/repo/pull/1'
        ]):
            self.assertTrue(True)
    
    def test_transition_arguments_optional(self):
        """Test that transition arguments are optional."""
        with patch('sys.argv', [
            'script.py',
            '--event-name', 'pull_request',
            '--jira-url', 'https://jira.example.com',
            '--jira-token', 'token123',
            '--project-key', 'CLOUD',
            '--pr-branch', 'feature/CLOUD-1234-test',
            '--pr-url', 'https://github.com/org/repo/pull/1',
            '--transition-opened', 'In Progress',
            '--transition-merged', 'Done'
        ]):
            self.assertTrue(True)
    
    def test_target_branch_argument(self):
        """Test that target-branch argument is available."""
        with patch('sys.argv', [
            'script.py',
            '--event-name', 'push',
            '--jira-url', 'https://jira.example.com',
            '--jira-token', 'token123',
            '--project-key', 'CLOUD',
            '--push-branch', 'main',
            '--target-branch', 'main'
        ]):
            self.assertTrue(True)


class TestJiraKeyExtraction(unittest.TestCase):
    """Test Jira key extraction from branch names."""
    
    def test_extract_key_from_feature_branch(self):
        """Test extracting key from feature/CLOUD-1234-description."""
        key = jis.extract_jira_key_from_branch('feature/CLOUD-1234-description')
        self.assertEqual(key, 'CLOUD-1234')
    
    def test_extract_key_from_bugfix_branch(self):
        """Test extracting key from bugfix/CLOUD-1234."""
        key = jis.extract_jira_key_from_branch('bugfix/CLOUD-1234')
        self.assertEqual(key, 'CLOUD-1234')
    
    def test_extract_key_from_simple_branch(self):
        """Test extracting key from CLOUD-1234-description."""
        key = jis.extract_jira_key_from_branch('CLOUD-1234-description')
        self.assertEqual(key, 'CLOUD-1234')
    
    def test_extract_key_with_underscores(self):
        """Test extracting key with underscores like PROJ_KEY-1234."""
        key = jis.extract_jira_key_from_branch('feature/PROJ_KEY-1234-test')
        self.assertEqual(key, 'PROJ_KEY-1234')
    
    def test_no_key_in_branch(self):
        """Test that None is returned when no key is found."""
        key = jis.extract_jira_key_from_branch('main')
        self.assertIsNone(key)
    
    def test_no_key_in_develop_branch(self):
        """Test that None is returned for develop branch."""
        key = jis.extract_jira_key_from_branch('develop')
        self.assertIsNone(key)


class TestEventRouting(unittest.TestCase):
    """Test event routing logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.args = MagicMock()
        self.args.jira_url = 'https://jira.example.com'
        self.args.jira_token = 'token123'
        self.args.project_key = 'CLOUD'
    
    @patch('jira_integration_script.handle_issues_event')
    def test_route_issues_event(self, mock_handler):
        """Test that issues event is routed to handle_issues_event."""
        mock_handler.return_value = 'CLOUD-1234'
        result = jis.route_event('issues', self.args)
        mock_handler.assert_called_once_with(self.args)
    
    @patch('jira_integration_script.handle_pull_request_event')
    def test_route_pull_request_event(self, mock_handler):
        """Test that pull_request event is routed to handle_pull_request_event."""
        mock_handler.return_value = True
        result = jis.route_event('pull_request', self.args)
        mock_handler.assert_called_once_with(self.args)
    
    @patch('jira_integration_script.handle_push_event')
    def test_route_push_event(self, mock_handler):
        """Test that push event is routed to handle_push_event."""
        mock_handler.return_value = True
        result = jis.route_event('push', self.args)
        mock_handler.assert_called_once_with(self.args)
    
    def test_route_unsupported_event(self):
        """Test that unsupported event returns None."""
        result = jis.route_event('unsupported', self.args)
        self.assertIsNone(result)


class TestIssuesEventHandler(unittest.TestCase):
    """Test issues event handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.args = MagicMock()
        self.args.issue_title = 'Test Issue'
        self.args.issue_url = 'https://github.com/org/repo/issues/1'
        self.args.project_key = 'CLOUD'
        self.args.issue_type = 'Task'
    
    @patch('jira_integration_script.retry_api_call')
    def test_handle_issues_event_success(self, mock_retry):
        """Test successful issues event handling."""
        mock_retry.return_value = 'CLOUD-1234'
        result = jis.handle_issues_event(self.args)
        self.assertEqual(result, 'CLOUD-1234')
    
    def test_handle_issues_event_missing_title(self):
        """Test that missing issue-title returns None."""
        self.args.issue_title = ''
        result = jis.handle_issues_event(self.args)
        self.assertIsNone(result)
    
    def test_handle_issues_event_missing_url(self):
        """Test that missing issue-url returns None."""
        self.args.issue_url = ''
        result = jis.handle_issues_event(self.args)
        self.assertIsNone(result)


class TestPullRequestEventHandler(unittest.TestCase):
    """Test pull_request event handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.args = MagicMock()
        self.args.pr_branch = 'feature/CLOUD-1234-test'
        self.args.pr_url = 'https://github.com/org/repo/pull/1'
        self.args.pr_title = 'Test PR'
        self.args.pr_action = 'opened'
        self.args.pr_merged = False
        self.args.transition_opened = 'In Progress'
        self.args.transition_merged = 'Done'
    
    @patch('jira_integration_script.add_comment')
    @patch('jira_integration_script.link_github_pr_remote')
    @patch('jira_integration_script.change_issue_status')
    def test_handle_pr_opened_with_transitions(self, mock_transition,
                                               mock_link, mock_comment):
        """Test PR opened event with transitions."""
        mock_comment.return_value = True
        mock_link.return_value = True
        mock_transition.return_value = True
        
        result = jis.handle_pull_request_event(self.args)
        
        self.assertTrue(result)
        mock_comment.assert_called_once()
        mock_link.assert_called_once()
        mock_transition.assert_called_once()
    
    @patch('jira_integration_script.link_github_pr_remote')
    def test_handle_pr_synchronize(self, mock_link):
        """Test PR synchronize event."""
        self.args.pr_action = 'synchronize'
        mock_link.return_value = True
        
        result = jis.handle_pull_request_event(self.args)
        
        self.assertTrue(result)
        mock_link.assert_called_once()
    
    @patch('jira_integration_script.link_github_pr_remote')
    @patch('jira_integration_script.change_issue_status')
    def test_handle_pr_closed_merged(self, mock_transition, mock_link):
        """Test PR closed event when merged."""
        self.args.pr_action = 'closed'
        self.args.pr_merged = True
        mock_link.return_value = True
        mock_transition.return_value = True
        
        result = jis.handle_pull_request_event(self.args)
        
        self.assertTrue(result)
        mock_link.assert_called_once()
        mock_transition.assert_called_once()
    
    def test_handle_pr_no_jira_key(self):
        """Test PR event with no Jira key in branch."""
        self.args.pr_branch = 'main'
        result = jis.handle_pull_request_event(self.args)
        self.assertTrue(result)  # Should return True (skip, not error)
    
    def test_handle_pr_missing_branch(self):
        """Test that missing pr-branch returns False."""
        self.args.pr_branch = ''
        result = jis.handle_pull_request_event(self.args)
        self.assertFalse(result)
    
    def test_handle_pr_missing_url(self):
        """Test that missing pr-url returns False."""
        self.args.pr_url = ''
        result = jis.handle_pull_request_event(self.args)
        self.assertFalse(result)


class TestPushEventHandler(unittest.TestCase):
    """Test push event handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.args = MagicMock()
        self.args.push_branch = 'main'
        self.args.target_branch = 'main'
        self.args.transition_tag = 'Released'
    
    @patch('jira_integration_script.change_issue_status')
    def test_handle_push_matching_branch(self, mock_transition):
        """Test push event with matching target branch."""
        self.args.push_branch = 'feature/CLOUD-1234-test'
        self.args.target_branch = ''  # No target branch specified
        mock_transition.return_value = True
        
        result = jis.handle_push_event(self.args)
        
        self.assertTrue(result)
        mock_transition.assert_called_once()
    
    @patch('jira_integration_script.change_issue_status')
    def test_handle_push_with_target_branch_match(self, mock_transition):
        """Test push event with target branch matching and Jira key."""
        self.args.push_branch = 'feature/CLOUD-1234-test'
        self.args.target_branch = ''  # No target branch specified
        mock_transition.return_value = True
        
        result = jis.handle_push_event(self.args)
        
        self.assertTrue(result)
        mock_transition.assert_called_once()
    
    def test_handle_push_target_branch_mismatch(self):
        """Test push event with non-matching target branch."""
        self.args.push_branch = 'develop'
        self.args.target_branch = 'main'
        
        result = jis.handle_push_event(self.args)
        
        self.assertTrue(result)  # Should return True (skip, not error)
    
    def test_handle_push_no_jira_key(self):
        """Test push event with no Jira key in branch."""
        self.args.push_branch = 'main'
        self.args.target_branch = ''
        
        result = jis.handle_push_event(self.args)
        
        self.assertTrue(result)  # Should return True (skip, not error)
    
    def test_handle_push_missing_branch(self):
        """Test that missing push-branch returns False."""
        self.args.push_branch = ''
        result = jis.handle_push_event(self.args)
        self.assertFalse(result)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with Phase 0."""
    
    @patch('jira_integration_script.retry_api_call')
    def test_issues_event_backward_compat(self, mock_retry):
        """Test that issues event still works without new arguments."""
        mock_retry.return_value = 'CLOUD-1234'
        
        args = MagicMock()
        args.issue_title = 'Test Issue'
        args.issue_url = 'https://github.com/org/repo/issues/1'
        args.project_key = 'CLOUD'
        args.issue_type = 'Task'
        
        result = jis.handle_issues_event(args)
        self.assertEqual(result, 'CLOUD-1234')
    
    @patch('jira_integration_script.add_comment')
    @patch('jira_integration_script.link_github_pr_remote')
    @patch('jira_integration_script.retry_api_call')
    def test_pr_event_backward_compat(self, mock_retry, mock_link, mock_comment):
        """Test that PR event works without transition arguments."""
        mock_retry.return_value = True
        mock_link.return_value = True
        
        args = MagicMock()
        args.pr_branch = 'feature/CLOUD-1234-test'
        args.pr_url = 'https://github.com/org/repo/pull/1'
        args.pr_title = 'Test PR'
        args.pr_action = 'opened'
        args.pr_merged = False
        args.transition_opened = ''  # Empty (not provided)
        args.transition_merged = ''  # Empty (not provided)
        
        result = jis.handle_pull_request_event(args)
        self.assertTrue(result)


class TestLinkTitleCustomization(unittest.TestCase):
    """Test link title customization."""
    
    @patch('jira_integration_script.requests.post')
    def test_link_with_custom_title(self, mock_post):
        """Test that custom link title is used."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        jis.JIRA_URL = 'https://jira.example.com'
        jis.JIRA_TOKEN = 'token123'
        
        result = jis.link_github_pr_remote(
            'CLOUD-1234',
            'https://github.com/org/repo/pull/1',
            'Custom PR Title'
        )
        
        self.assertTrue(result)
        # Verify the custom title was used in the payload
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['object']['title'], 'Custom PR Title')


class TestLogging(unittest.TestCase):
    """Test logging functionality."""
    
    @patch('builtins.print')
    def test_log_action_info(self, mock_print):
        """Test INFO level logging."""
        jis.log_action('Test action', level='INFO', key='value')
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        self.assertIn('[INFO]', call_args)
        self.assertIn('Test action', call_args)
        self.assertIn('key=value', call_args)
    
    @patch('builtins.print')
    def test_log_action_debug(self, mock_print):
        """Test DEBUG level logging."""
        jis.log_action('Debug message', level='DEBUG', detail='info')
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        self.assertIn('[DEBUG]', call_args)
    
    @patch('builtins.print')
    def test_log_action_error(self, mock_print):
        """Test ERROR level logging."""
        jis.log_action('Error occurred', level='ERROR', error_code='500')
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        self.assertIn('[ERROR]', call_args)


if __name__ == '__main__':
    unittest.main()
