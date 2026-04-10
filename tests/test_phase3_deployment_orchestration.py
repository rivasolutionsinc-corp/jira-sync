#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Suite for Phase 3: Deployment-Aware Orchestration

Tests deployment event handling for Jenkins/GitFlow alignment:
- Push events to deployment branches (develop, stage, main)
- Tag creation events for production releases
- Jira state mapping for deployment lifecycle
- Deployment metadata in comments

Test Date: 2026-04-10
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jira_integration_script as jira_script


class TestDeploymentPushEvents(unittest.TestCase):
    """Test push event handling for deployment branches."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_args = MagicMock()
        self.mock_args.jira_url = "https://jira.example.com"
        self.mock_args.jira_token = "test-token"
        self.mock_args.project_key = "CLOUD"
    
    @patch('jira_integration_script.change_issue_status')
    @patch('jira_integration_script.add_comment')
    @patch('jira_integration_script.extract_jira_key_from_branch')
    def test_develop_branch_push_in_development(self, mock_extract, mock_comment, mock_transition):
        """Test push to develop branch transitions to 'In Development'."""
        mock_extract.return_value = "CLOUD-1234"
        mock_comment.return_value = True
        mock_transition.return_value = True
        
        self.mock_args.push_branch = "develop"
        self.mock_args.target_branch = "develop"
        self.mock_args.transition_tag = "In Development"
        self.mock_args.deployment_stage = "development"
        self.mock_args.deployment_branch = "develop"
        
        result = jira_script.handle_push_event(self.mock_args)
        
        self.assertTrue(result)
        mock_extract.assert_called_once_with("develop")
        mock_comment.assert_called_once()
        mock_transition.assert_called_once_with("CLOUD-1234", "In Development")
    
    @patch('jira_integration_script.change_issue_status')
    @patch('jira_integration_script.add_comment')
    @patch('jira_integration_script.extract_jira_key_from_branch')
    def test_stage_branch_push_in_qa(self, mock_extract, mock_comment, mock_transition):
        """Test push to stage branch transitions to 'In QA'."""
        mock_extract.return_value = "CLOUD-1235"
        mock_comment.return_value = True
        mock_transition.return_value = True
        
        self.mock_args.push_branch = "stage"
        self.mock_args.target_branch = "stage"
        self.mock_args.transition_tag = "In QA"
        self.mock_args.deployment_stage = "staging"
        self.mock_args.deployment_branch = "stage"
        
        result = jira_script.handle_push_event(self.mock_args)
        
        self.assertTrue(result)
        mock_extract.assert_called_once_with("stage")
        mock_transition.assert_called_once_with("CLOUD-1235", "In QA")
    
    @patch('jira_integration_script.change_issue_status')
    @patch('jira_integration_script.add_comment')
    @patch('jira_integration_script.extract_jira_key_from_branch')
    def test_main_branch_push_deployed(self, mock_extract, mock_comment, mock_transition):
        """Test push to main branch transitions to 'Deployed'."""
        mock_extract.return_value = "CLOUD-1236"
        mock_comment.return_value = True
        mock_transition.return_value = True
        
        self.mock_args.push_branch = "main"
        self.mock_args.target_branch = "main"
        self.mock_args.transition_tag = "Deployed"
        self.mock_args.deployment_stage = "production"
        self.mock_args.deployment_branch = "main"
        
        result = jira_script.handle_push_event(self.mock_args)
        
        self.assertTrue(result)
        mock_extract.assert_called_once_with("main")
        mock_transition.assert_called_once_with("CLOUD-1236", "Deployed")
    
    @patch('jira_integration_script.extract_jira_key_from_branch')
    def test_push_branch_mismatch_skipped(self, mock_extract):
        """Test push to non-target branch is skipped."""
        self.mock_args.push_branch = "feature/CLOUD-1234"
        self.mock_args.target_branch = "develop"
        self.mock_args.transition_tag = "In Development"
        
        result = jira_script.handle_push_event(self.mock_args)
        
        self.assertTrue(result)  # Not an error, just skipped
        mock_extract.assert_not_called()
    
    @patch('jira_integration_script.extract_jira_key_from_branch')
    def test_push_no_jira_key_skipped(self, mock_extract):
        """Test push with no Jira key in branch is skipped."""
        mock_extract.return_value = None
        
        self.mock_args.push_branch = "develop"
        self.mock_args.target_branch = "develop"
        self.mock_args.transition_tag = "In Development"
        
        result = jira_script.handle_push_event(self.mock_args)
        
        self.assertTrue(result)  # Not an error, just skipped
        mock_extract.assert_called_once_with("develop")
    
    @patch('jira_integration_script.add_comment')
    @patch('jira_integration_script.extract_jira_key_from_branch')
    def test_deployment_metadata_comment_added(self, mock_extract, mock_comment):
        """Test deployment metadata is added as comment."""
        mock_extract.return_value = "CLOUD-1234"
        mock_comment.return_value = True
        
        self.mock_args.push_branch = "stage"
        self.mock_args.target_branch = "stage"
        self.mock_args.transition_tag = "In QA"
        self.mock_args.deployment_stage = "staging"
        self.mock_args.deployment_branch = "stage"
        
        with patch('jira_integration_script.change_issue_status', return_value=True):
            result = jira_script.handle_push_event(self.mock_args)
        
        self.assertTrue(result)
        mock_comment.assert_called_once()
        
        # Verify comment contains deployment metadata
        comment_call = mock_comment.call_args[0][1]
        self.assertIn("STAGING", comment_call)
        self.assertIn("stage", comment_call)


class TestDeploymentTagEvents(unittest.TestCase):
    """Test tag creation event handling for production releases."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_args = MagicMock()
        self.mock_args.jira_url = "https://jira.example.com"
        self.mock_args.jira_token = "test-token"
        self.mock_args.project_key = "CLOUD"
    
    @patch('jira_integration_script.change_issue_status')
    @patch('jira_integration_script.add_comment')
    @patch('jira_integration_script.extract_jira_key_from_branch')
    def test_tag_creation_deployed(self, mock_extract, mock_comment, mock_transition):
        """Test tag creation transitions to 'Deployed'."""
        mock_extract.return_value = "CLOUD-1234"
        mock_comment.return_value = True
        mock_transition.return_value = True
        
        self.mock_args.tag_name = "v1.2.3-CLOUD-1234"
        self.mock_args.tag_ref = "main"
        self.mock_args.transition_tag = "Deployed"
        self.mock_args.deployment_tag = "v1.2.3-CLOUD-1234"
        
        result = jira_script.handle_tag_event(self.mock_args)
        
        self.assertTrue(result)
        mock_extract.assert_called_once_with("v1.2.3-CLOUD-1234")
        mock_comment.assert_called_once()
        mock_transition.assert_called_once_with("CLOUD-1234", "Deployed")
    
    @patch('jira_integration_script.extract_jira_key_from_branch')
    def test_tag_invalid_pattern_skipped(self, mock_extract):
        """Test tag not matching v*.*.* pattern is skipped."""
        self.mock_args.tag_name = "release-1.2.3"
        self.mock_args.tag_ref = "main"
        self.mock_args.transition_tag = "Deployed"
        
        result = jira_script.handle_tag_event(self.mock_args)
        
        self.assertTrue(result)  # Not an error, just skipped
        mock_extract.assert_not_called()
    
    @patch('jira_integration_script.extract_jira_key_from_branch')
    def test_tag_no_jira_key_skipped(self, mock_extract):
        """Test tag with no Jira key is skipped."""
        mock_extract.return_value = None
        
        self.mock_args.tag_name = "v1.2.3"
        self.mock_args.tag_ref = "main"
        self.mock_args.transition_tag = "Deployed"
        
        result = jira_script.handle_tag_event(self.mock_args)
        
        self.assertTrue(result)  # Not an error, just skipped
        mock_extract.assert_called_once_with("v1.2.3")
    
    @patch('jira_integration_script.add_comment')
    @patch('jira_integration_script.extract_jira_key_from_branch')
    def test_production_deployment_metadata_comment(self, mock_extract, mock_comment):
        """Test production deployment metadata is added as comment."""
        mock_extract.return_value = "CLOUD-1234"
        mock_comment.return_value = True
        
        self.mock_args.tag_name = "v2.0.0-CLOUD-1234"
        self.mock_args.tag_ref = "main"
        self.mock_args.transition_tag = "Deployed"
        self.mock_args.deployment_tag = "v2.0.0-CLOUD-1234"
        
        with patch('jira_integration_script.change_issue_status', return_value=True):
            result = jira_script.handle_tag_event(self.mock_args)
        
        self.assertTrue(result)
        mock_comment.assert_called_once()
        
        # Verify comment contains production deployment metadata
        comment_call = mock_comment.call_args[0][1]
        self.assertIn("Production Release", comment_call)
        self.assertIn("v2.0.0-CLOUD-1234", comment_call)
        self.assertIn("Deployed to Production", comment_call)
    
    @patch('jira_integration_script.extract_jira_key_from_branch')
    def test_tag_no_name_skipped(self, mock_extract):
        """Test tag event with no tag name is skipped."""
        self.mock_args.tag_name = None
        self.mock_args.tag_ref = "main"
        
        result = jira_script.handle_tag_event(self.mock_args)
        
        self.assertTrue(result)  # Not an error, just skipped
        mock_extract.assert_not_called()


class TestEventRouting(unittest.TestCase):
    """Test event routing to appropriate handlers."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_args = MagicMock()
    
    @patch('jira_integration_script.handle_push_event')
    def test_route_push_event(self, mock_handler):
        """Test push event is routed to handle_push_event."""
        mock_handler.return_value = True
        
        result = jira_script.route_event("push", self.mock_args)
        
        self.assertTrue(result)
        mock_handler.assert_called_once_with(self.mock_args)
    
    @patch('jira_integration_script.handle_tag_event')
    def test_route_create_event(self, mock_handler):
        """Test create event is routed to handle_tag_event."""
        mock_handler.return_value = True
        
        result = jira_script.route_event("create", self.mock_args)
        
        self.assertTrue(result)
        mock_handler.assert_called_once_with(self.mock_args)
    
    @patch('jira_integration_script.handle_issues_event')
    def test_route_issues_event(self, mock_handler):
        """Test issues event is routed to handle_issues_event."""
        mock_handler.return_value = "CLOUD-1234"
        
        result = jira_script.route_event("issues", self.mock_args)
        
        self.assertEqual(result, "CLOUD-1234")
        mock_handler.assert_called_once_with(self.mock_args)
    
    @patch('jira_integration_script.handle_pull_request_event')
    def test_route_pull_request_event(self, mock_handler):
        """Test pull_request event is routed to handle_pull_request_event."""
        mock_handler.return_value = True
        
        result = jira_script.route_event("pull_request", self.mock_args)
        
        self.assertTrue(result)
        mock_handler.assert_called_once_with(self.mock_args)


class TestJiraKeyExtraction(unittest.TestCase):
    """Test Jira key extraction from branch and tag names."""
    
    def test_extract_from_feature_branch(self):
        """Test extraction from feature branch."""
        key = jira_script.extract_jira_key_from_branch("feature/CLOUD-1234-description")
        self.assertEqual(key, "CLOUD-1234")
    
    def test_extract_from_develop_branch(self):
        """Test extraction from develop branch with Jira key."""
        key = jira_script.extract_jira_key_from_branch("develop-CLOUD-1234")
        self.assertEqual(key, "CLOUD-1234")
    
    def test_extract_from_tag(self):
        """Test extraction from tag."""
        key = jira_script.extract_jira_key_from_branch("v1.2.3-CLOUD-1234")
        self.assertEqual(key, "CLOUD-1234")
    
    def test_extract_no_key(self):
        """Test extraction returns None when no key found."""
        key = jira_script.extract_jira_key_from_branch("develop")
        self.assertIsNone(key)
    
    def test_extract_multiple_keys_first_match(self):
        """Test extraction returns first matching key."""
        key = jira_script.extract_jira_key_from_branch("CLOUD-1234-CLOUD-1235")
        self.assertEqual(key, "CLOUD-1234")


class TestValidation(unittest.TestCase):
    """Test input validation."""
    
    def test_validate_jira_url_valid(self):
        """Test valid Jira URL validation."""
        self.assertTrue(jira_script.validate_jira_url("https://jira.example.com"))
        self.assertTrue(jira_script.validate_jira_url("http://jira.example.com"))
    
    def test_validate_jira_url_invalid(self):
        """Test invalid Jira URL validation."""
        self.assertFalse(jira_script.validate_jira_url(""))
        self.assertFalse(jira_script.validate_jira_url("jira.example.com"))
        self.assertFalse(jira_script.validate_jira_url("ftp://jira.example.com"))
    
    def test_validate_issue_key_valid(self):
        """Test valid issue key validation."""
        self.assertTrue(jira_script.validate_issue_key("CLOUD-1234"))
        self.assertTrue(jira_script.validate_issue_key("AQD-9999"))
    
    def test_validate_issue_key_invalid(self):
        """Test invalid issue key validation."""
        self.assertFalse(jira_script.validate_issue_key(""))
        self.assertFalse(jira_script.validate_issue_key("cloud-1234"))
        self.assertFalse(jira_script.validate_issue_key("CLOUD1234"))


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestDeploymentPushEvents))
    suite.addTests(loader.loadTestsFromTestCase(TestDeploymentTagEvents))
    suite.addTests(loader.loadTestsFromTestCase(TestEventRouting))
    suite.addTests(loader.loadTestsFromTestCase(TestJiraKeyExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestValidation))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
