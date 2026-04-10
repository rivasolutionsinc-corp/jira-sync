#!/usr/bin/env python3
"""
MCP Lifecycle Client for Jira Sync

Manages the stdio connection to the Atlassian MCP Docker container,
performs the JSON-RPC initialize handshake, executes tool calls,
and safely terminates the connection.
"""

import json
import sys
import subprocess
import argparse
import time
from typing import Optional, Dict, Any


class MCPLifecycleClient:
    """Manages MCP server lifecycle and JSON-RPC communication."""
    
    def __init__(self, jira_url: str, jira_username: str, jira_personal_token: str):
        """Initialize the MCP client with Jira credentials."""
        self.jira_url = jira_url
        self.jira_username = jira_username
        self.jira_personal_token = jira_personal_token
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 1
    
    def start_server(self) -> bool:
        """Start the MCP server Docker container."""
        try:
            print("Starting MCP server...")
            self.process = subprocess.Popen(
                [
                    "docker", "run",
                    "-i", "--rm",
                    "-e", f"JIRA_URL={self.jira_url}",
                    "-e", f"JIRA_USERNAME={self.jira_username}",
                    "-e", f"JIRA_PERSONAL_TOKEN={self.jira_personal_token}",
                    "ghcr.io/sooperset/mcp-atlassian:latest"
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            print("✓ MCP server started")
            return True
        except Exception as e:
            print(f"✗ Failed to start MCP server: {e}", file=sys.stderr)
            return False
    
    def send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a JSON-RPC request and read the response."""
        if not self.process or not self.process.stdin or not self.process.stdout:
            print("✗ MCP server not running", file=sys.stderr)
            return None
        
        try:
            # Send request
            request_json = json.dumps(request)
            print(f"→ Sending: {request.get('method', 'unknown')}")
            self.process.stdin.write(request_json + "\n")
            self.process.stdin.flush()
            
            # Read response
            response_line = self.process.stdout.readline()
            if not response_line:
                print("✗ No response from MCP server", file=sys.stderr)
                return None
            
            response = json.loads(response_line)
            print(f"← Received: {response.get('result', {}).get('type', 'response')}")
            return response
        except Exception as e:
            print(f"✗ Error communicating with MCP server: {e}", file=sys.stderr)
            return None
    
    def initialize(self) -> bool:
        """Perform the JSON-RPC initialize handshake."""
        print("\n[1/4] Initializing MCP connection...")
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "jira-sync-action",
                    "version": "1.0.0"
                }
            }
        }
        self.request_id += 1
        
        response = self.send_request(init_request)
        if not response or "error" in response:
            print(f"✗ Initialize failed: {response}", file=sys.stderr)
            return False
        
        print("✓ Initialize successful")
        return True
    
    def send_initialized(self) -> bool:
        """Send the notifications/initialized message."""
        print("\n[2/4] Sending initialized notification...")
        
        initialized_msg = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        try:
            if self.process and self.process.stdin:
                msg_json = json.dumps(initialized_msg)
                self.process.stdin.write(msg_json + "\n")
                self.process.stdin.flush()
                print("✓ Initialized notification sent")
                return True
        except Exception as e:
            print(f"✗ Failed to send initialized: {e}", file=sys.stderr)
            return False
        
        return False
    
    def create_jira_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task"
    ) -> Optional[str]:
        """Create a Jira issue via MCP tool call."""
        print("\n[3/4] Creating Jira issue...")
        
        tool_call = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {
                "name": "jira_create_issue",
                "arguments": {
                    "project_key": project_key,
                    "summary": summary,
                    "description": description,
                    "issue_type": issue_type
                }
            }
        }
        self.request_id += 1
        
        response = self.send_request(tool_call)
        if not response or "error" in response:
            print(f"✗ Tool call failed: {response}", file=sys.stderr)
            return None
        
        # Extract issue key from response
        try:
            result = response.get("result", {})
            if isinstance(result, dict):
                content = result.get("content", [])
                if content and isinstance(content, list):
                    text = content[0].get("text", "")
                    # Parse issue key from response text
                    import re
                    match = re.search(r'([A-Z]+-\d+)', text)
                    if match:
                        issue_key = match.group(1)
                        print(f"✓ Issue created: {issue_key}")
                        return issue_key
        except Exception as e:
            print(f"✗ Failed to parse issue key: {e}", file=sys.stderr)
        
        return None
    
    def terminate(self) -> bool:
        """Gracefully terminate the MCP server connection."""
        print("\n[4/4] Terminating MCP connection...")
        
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                print("✓ MCP server terminated")
                return True
            except subprocess.TimeoutExpired:
                print("⚠ MCP server did not terminate gracefully, killing...")
                self.process.kill()
                self.process.wait()
                return True
            except Exception as e:
                print(f"✗ Error terminating MCP server: {e}", file=sys.stderr)
                return False
        
        return True
    
    def run(
        self,
        event_name: str,
        project_key: str,
        issue_title: str = "",
        issue_url: str = "",
        pr_branch: str = "",
        pr_url: str = "",
        issue_type: str = "Task"
    ) -> Optional[str]:
        """Execute the full MCP lifecycle."""
        try:
            # Start server
            if not self.start_server():
                return None
            
            # Initialize
            if not self.initialize():
                self.terminate()
                return None
            
            # Send initialized
            if not self.send_initialized():
                self.terminate()
                return None
            
            # Route event and create issue
            if event_name == "issues":
                summary = issue_title
                description = f"GitHub issue: {issue_url}"
            elif event_name == "pull_request":
                summary = f"PR: {pr_branch}"
                description = f"GitHub pull request: {pr_url}"
            else:
                print(f"✗ Unsupported event type: {event_name}", file=sys.stderr)
                self.terminate()
                return None
            
            # Create issue
            issue_key = self.create_jira_issue(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type
            )
            
            # Terminate
            self.terminate()
            
            return issue_key
        
        except Exception as e:
            print(f"✗ Unexpected error: {e}", file=sys.stderr)
            self.terminate()
            return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Lifecycle Client for Jira Sync"
    )
    parser.add_argument("--jira-url", required=True, help="Jira instance URL")
    parser.add_argument("--jira-username", required=True, help="Jira username")
    parser.add_argument("--jira-personal-token", required=True, help="Jira PAT")
    parser.add_argument("--project-key", required=True, help="Jira project key")
    parser.add_argument("--event-name", required=True, help="GitHub event (issues or pull_request)")
    parser.add_argument("--issue-title", default="", help="GitHub issue title")
    parser.add_argument("--issue-url", default="", help="GitHub issue URL")
    parser.add_argument("--pr-branch", default="", help="PR branch name")
    parser.add_argument("--pr-url", default="", help="PR URL")
    parser.add_argument("--issue-type", default="Task", help="Jira issue type")
    
    args = parser.parse_args()
    
    # Create client and run
    client = MCPLifecycleClient(
        jira_url=args.jira_url,
        jira_username=args.jira_username,
        jira_personal_token=args.jira_personal_token
    )
    
    issue_key = client.run(
        event_name=args.event_name,
        project_key=args.project_key,
        issue_title=args.issue_title,
        issue_url=args.issue_url,
        pr_branch=args.pr_branch,
        pr_url=args.pr_url,
        issue_type=args.issue_type
    )
    
    if issue_key:
        print(f"\n✓ Jira sync completed successfully.")
        print(f"::set-output name=jira-key::{issue_key}")
        sys.exit(0)
    else:
        print(f"\n✗ Jira sync failed.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
