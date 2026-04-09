# -*- coding: utf-8 -*-
"""
Atlassian MCP Client Wrapper

Provides a unified interface for calling Atlassian MCP tools.
Handles MCP tool invocation, response parsing, and error handling.

This module bridges direct REST API calls to standardized Atlassian MCP tool calls.
"""

import json
import os
import re
from typing import Dict, Any, Optional


class AtlassianMCPClient:
    """Wrapper for Atlassian MCP tool calls
    
    Provides methods for Jira and Confluence operations via MCP tools.
    Falls back to direct REST API for operations without MCP equivalents.
    """
    
    def __init__(self):
        """Initialize MCP client with environment variables"""
        # Jira configuration
        self.jira_url = os.getenv('JIRA_URL', 'https://cmext.ahrq.gov/jira')
        self.jira_token = os.getenv('JIRA_TOKEN') or os.getenv('JIRA_API_TOKEN')
        self.jira_username = os.getenv('JIRA_USERNAME')
        
        # Confluence configuration
        self.confluence_url = os.getenv('CONFLUENCE_URL', 'https://cmext.ahrq.gov/confluence')
        self.confluence_token = os.getenv('CONFLUENCE_API_TOKEN')
        self.confluence_username = os.getenv('CONFLUENCE_USERNAME')
        
        # Validate Jira credentials
        if not self.jira_token:
            raise ValueError("JIRA_TOKEN or JIRA_API_TOKEN environment variable not set")
    
    def _call_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> str:
        """
        Call an Atlassian MCP tool.
        
        NOTE: This is a placeholder implementation. In production, this would:
        1. Connect to the MCP server via stdio or HTTP
        2. Invoke the tool with the given parameters
        3. Return the tool's response
        
        For now, this raises NotImplementedError to indicate MCP SDK integration is required.
        
        Args:
            tool_name: Name of the MCP tool (e.g., 'jira_create_issue')
            params: Dictionary of tool parameters
            
        Returns:
            Tool response as string
            
        Raises:
            NotImplementedError: MCP SDK integration required
        """
        raise NotImplementedError(
            f"MCP tool '{tool_name}' integration required. "
            "Implement _call_mcp_tool() with actual MCP SDK integration."
        )
    
    def jira_search(self, jql: str, max_results: int = 10) -> str:
        """
        Search Jira issues using JQL (Jira Query Language).
        
        Args:
            jql: JQL query string (e.g., 'project = "AQD" AND issuetype = Bug')
            max_results: Maximum number of results to return (default: 10)
            
        Returns:
            JSON string with search results
            
        Example:
            >>> client.jira_search(jql='project = "CLOUD" AND status = "To Do"', max_results=20)
        """
        return self._call_mcp_tool('jira_search', {
            'jql': jql,
            'max_results': max_results
        })
    
    def jira_get_issue(self, issue_key: str) -> str:
        """
        Get Jira issue details.
        
        Args:
            issue_key: Issue key (e.g., 'CLOUD-1925')
            
        Returns:
            JSON string with issue details
            
        Example:
            >>> client.jira_get_issue(issue_key='CLOUD-1925')
        """
        return self._call_mcp_tool('jira_get_issue', {
            'issue_key': issue_key
        })
    
    def jira_create_issue(self, project_key: str, summary: str, 
                         description: str, issue_type: str = "Task") -> str:
        """
        Create a new Jira issue.
        
        Args:
            project_key: Project key (e.g., 'CLOUD', 'AQD')
            summary: Issue title
            description: Issue description
            issue_type: Issue type (default: 'Task'; also: 'Bug', 'Story', 'Sub-task')
            
        Returns:
            Issue key on success (e.g., 'CLOUD-1926')
            
        Example:
            >>> client.jira_create_issue(
            ...     project_key='CLOUD',
            ...     summary='E2E Test: Atlassian MCP Integration',
            ...     description='Testing Atlassian MCP server integration',
            ...     issue_type='Task'
            ... )
        """
        return self._call_mcp_tool('jira_create_issue', {
            'project_key': project_key,
            'summary': summary,
            'description': description,
            'issue_type': issue_type
        })
    
    def jira_add_comment(self, issue_key: str, comment: str) -> str:
        """
        Add a comment to a Jira issue.
        
        Args:
            issue_key: Issue key (e.g., 'CLOUD-1925')
            comment: Comment text (supports Markdown)
            
        Returns:
            Success message
            
        Example:
            >>> client.jira_add_comment(
            ...     issue_key='CLOUD-1925',
            ...     comment='PR #42 merged to main\\nMerge commit: abc123def456'
            ... )
        """
        return self._call_mcp_tool('jira_add_comment', {
            'issue_key': issue_key,
            'comment': comment
        })
    
    def jira_list_transitions(self, issue_key: str) -> str:
        """
        List available workflow transitions for a Jira issue.
        
        Args:
            issue_key: Issue key (e.g., 'CLOUD-1925')
            
        Returns:
            JSON string with available transitions
            
        Example:
            >>> client.jira_list_transitions(issue_key='CLOUD-1925')
            # Returns: [{"id": "11", "name": "Start Progress"}, {"id": "21", "name": "Done"}]
        """
        return self._call_mcp_tool('jira_list_transitions', {
            'issue_key': issue_key
        })
    
    def jira_transition_issue(self, issue_key: str, transition_name: str) -> str:
        """
        Transition a Jira issue to a new status.
        
        Args:
            issue_key: Issue key (e.g., 'CLOUD-1925')
            transition_name: Transition name (e.g., 'Start Progress', 'Done')
            
        Returns:
            Success message
            
        Example:
            >>> client.jira_transition_issue(issue_key='CLOUD-1925', transition_name='Done')
        """
        return self._call_mcp_tool('jira_transition_issue', {
            'issue_key': issue_key,
            'transition_name': transition_name
        })
    
    def confluence_search(self, query: str, max_results: int = 10) -> str:
        """
        Search Confluence pages and spaces.
        
        Args:
            query: Search query (CQL or text)
            max_results: Maximum number of results (default: 10)
            
        Returns:
            JSON string with search results
            
        Example:
            >>> client.confluence_search(query='Drupal deployment guide', max_results=5)
        """
        return self._call_mcp_tool('confluence_search', {
            'query': query,
            'max_results': max_results
        })
    
    def confluence_get_page(self, page_id: str) -> str:
        """
        Retrieve full content of a Confluence page.
        
        Args:
            page_id: Page ID (numeric)
            
        Returns:
            JSON string with page content
            
        Example:
            >>> client.confluence_get_page(page_id='123456')
        """
        return self._call_mcp_tool('confluence_get_page', {
            'page_id': page_id
        })
    
    def jira_link_issues(self, issue_key1: str, issue_key2: str, 
                        link_type: str = "relates to") -> bool:
        """
        Link two Jira issues together.
        
        NOTE: Atlassian MCP does not provide a tool for linking issues.
        This method uses direct REST API access as a fallback.
        
        Args:
            issue_key1: First issue key (e.g., 'AQD-1234')
            issue_key2: Second issue key (e.g., 'AQD-1235')
            link_type: Link type (e.g., 'relates to', 'blocks', 'is blocked by')
            
        Returns:
            True on success, False on failure
            
        Example:
            >>> client.jira_link_issues('CLOUD-1925', 'CLOUD-1926', 'relates to')
        """
        import requests
        
        try:
            url = f"{self.jira_url}/rest/api/2/issueLink"
            headers = {
                "Authorization": f"Bearer {self.jira_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            payload = {
                "type": {"name": link_type},
                "inwardIssue": {"key": issue_key1},
                "outwardIssue": {"key": issue_key2}
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 201:
                return True
            else:
                print(f"Failed to link issues. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"Exception linking issues: {e}")
            return False


_atlassian_mcp: Optional[AtlassianMCPClient] = None


def get_atlassian_mcp() -> AtlassianMCPClient:
    """Return a lazily initialized global Atlassian MCP client."""
    global _atlassian_mcp
    if _atlassian_mcp is None:
        _atlassian_mcp = AtlassianMCPClient()
    return _atlassian_mcp


class _LazyAtlassianMCPClient:
    """Proxy that defers AtlassianMCPClient construction until first use."""

    def __getattr__(self, name: str) -> Any:
        return getattr(get_atlassian_mcp(), name)


# Global instance for backward compatibility
atlassian_mcp = _LazyAtlassianMCPClient()
