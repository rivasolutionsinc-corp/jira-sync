# Jira Manager Skill

Specialized skill for Jira issue management and automation using the jira-sync MCP server.

## When to Use

Use this skill when you need to:
- Search for Jira issues using JQL queries
- Create new Jira issues
- Update and transition issue status
- Add comments to issues
- Link Jira issues together
- Link GitHub PRs to Jira issues
- Create and manage subtasks
- Retrieve issue details and transitions

## Available Tools

All tools use the `@jira-sync` MCP server which connects to the Docker image at `ghcr.io/riva-solutions/jira-sync:latest`.

### Search & Retrieve
- **search_jira_issues** — Search for issues using JQL
  ```
  @jira-sync search_jira_issues project=CLOUD AND status=Open
  ```

- **get_jira_issue** — Get details of a specific issue
  ```
  @jira-sync get_jira_issue CLOUD-1952
  ```

- **list_jira_transitions** — List available transitions for an issue
  ```
  @jira-sync list_jira_transitions CLOUD-1952
  ```

### Create & Modify
- **create_jira_issue** — Create a new issue
  ```
  @jira-sync create_jira_issue project_key=CLOUD issue_type=Bug summary="Fix authentication issue"
  ```

- **add_jira_comment** — Add a comment to an issue
  ```
  @jira-sync add_jira_comment issue_key=CLOUD-1952 comment="Working on this now"
  ```

- **transition_jira_issue** — Transition an issue to a new status
  ```
  @jira-sync transition_jira_issue issue_key=CLOUD-1952 transition_name="In Progress"
  ```

### Advanced Operations
- **link_jira_issues** — Link two Jira issues
  ```
  @jira-sync link_jira_issues issue_key1=CLOUD-1952 issue_key2=CLOUD-1953 link_type="relates to"
  ```

- **create_jira_subtask** — Create a subtask for an issue
  ```
  @jira-sync create_jira_subtask parent_issue_key=CLOUD-1952 summary="Implement authentication"
  ```

- **link_github_pr_remote** — Link a GitHub PR to a Jira issue
  ```
  @jira-sync link_github_pr_remote issue_key=CLOUD-1952 pr_url="https://github.com/rivasolutionsinc-corp/jira-sync/pull/44"
  ```

- **change_issue_status** — Change issue status with automatic transition discovery
  ```
  @jira-sync change_issue_status issue_key=CLOUD-1952 new_status="Done"
  ```

## Configuration

The skill uses the following environment variables from `.env`:
- `JIRA_URL` — Jira instance URL (e.g., https://cmext.ahrq.gov/jira)
- `JIRA_TOKEN` — Jira API token for authentication
- `JIRA_PROJECT_KEY` — Default project key (e.g., CLOUD)

## Example Workflows

### Workflow 1: Create Issue and Link PR

1. **Create a new issue:**
   ```
   @jira-sync create_jira_issue project_key=CLOUD issue_type=Task summary="Implement new feature"
   ```

2. **Link GitHub PR:**
   ```
   @jira-sync link_github_pr_remote issue_key=CLOUD-1952 pr_url="https://github.com/rivasolutionsinc-corp/jira-sync/pull/44"
   ```

3. **Transition to In Progress:**
   ```
   @jira-sync transition_jira_issue issue_key=CLOUD-1952 transition_name="In Progress"
   ```

### Workflow 2: Search and Update Issues

1. **Search for open issues:**
   ```
   @jira-sync search_jira_issues project=CLOUD AND status=Open
   ```

2. **Get issue details:**
   ```
   @jira-sync get_jira_issue CLOUD-1952
   ```

3. **Add a comment:**
   ```
   @jira-sync add_jira_comment issue_key=CLOUD-1952 comment="This is ready for review"
   ```

4. **Transition to In Review:**
   ```
   @jira-sync transition_jira_issue issue_key=CLOUD-1952 transition_name="In Review"
   ```

### Workflow 3: Create Issue with Subtasks

1. **Create parent issue:**
   ```
   @jira-sync create_jira_issue project_key=CLOUD issue_type=Epic summary="Q2 Development Sprint"
   ```

2. **Create subtask 1:**
   ```
   @jira-sync create_jira_subtask parent_issue_key=CLOUD-1952 summary="Backend API implementation"
   ```

3. **Create subtask 2:**
   ```
   @jira-sync create_jira_subtask parent_issue_key=CLOUD-1952 summary="Frontend UI implementation"
   ```

4. **Link subtasks:**
   ```
   @jira-sync link_jira_issues issue_key1=CLOUD-1953 issue_key2=CLOUD-1954 link_type="relates to"
   ```

### Workflow 4: Bulk Issue Management

1. **Search for issues in a sprint:**
   ```
   @jira-sync search_jira_issues project=CLOUD AND sprint="Sprint 1" AND status!=Done
   ```

2. **For each issue, add comment and transition:**
   ```
   @jira-sync add_jira_comment issue_key=CLOUD-1952 comment="Sprint review completed"
   @jira-sync transition_jira_issue issue_key=CLOUD-1952 transition_name="Done"
   ```

## Docker Image Details

**Registry:** GitHub Container Registry (GHCR)  
**Image:** ghcr.io/riva-solutions/jira-sync:latest  
**Tags:** latest, v1.0.0  
**Base:** python:3.11-slim  
**Size:** 234MB (50.9MB compressed)  

The image is built from `.github/actions/jira-sync/Dockerfile` and includes:
- `jira_integration_script.py` — Core Jira integration logic
- `entrypoint.sh` — Container entry point
- `requirements.txt` — Python dependencies (pinned versions)

## Authentication

The skill uses Jira API token authentication. Ensure your `.env` file contains:

```bash
JIRA_URL=https://cmext.ahrq.gov/jira
JIRA_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=CLOUD
```

Generate a Jira API token at: https://id.atlassian.com/manage-profile/security/api-tokens

## Troubleshooting

### Issue: "Docker image not found"
- Ensure Docker is installed and running
- Verify GHCR authentication: `docker login ghcr.io`
- Pull the image manually: `docker pull ghcr.io/riva-solutions/jira-sync:latest`

### Issue: "Authentication failed"
- Verify JIRA_TOKEN is correct and not expired
- Check JIRA_URL is accessible
- Ensure token has appropriate Jira permissions

### Issue: "Issue not found"
- Verify issue key is correct (e.g., CLOUD-1952)
- Check project key matches JIRA_PROJECT_KEY
- Ensure you have permission to view the issue

## Best Practices

1. **Always verify issue keys** before performing operations
2. **Use descriptive comments** when adding notes to issues
3. **Link related issues** to maintain traceability
4. **Transition issues through proper workflow states** for audit trails
5. **Create subtasks** for complex issues to break down work
6. **Link GitHub PRs** to maintain code-to-issue mapping

## Integration with Other Tools

The jira-sync MCP server integrates with:
- **Roo Code** — Use @jira-sync commands in any conversation
- **GitHub Actions** — Use in CI/CD workflows
- **Docker Compose** — Run as a service
- **CLI** — Execute directly with docker run

## References

- **Jira API Documentation:** https://developer.atlassian.com/cloud/jira/rest/v3/
- **MCP Specification:** https://modelcontextprotocol.io/
- **Docker Image:** ghcr.io/riva-solutions/jira-sync
- **GitHub Repository:** https://github.com/rivasolutionsinc-corp/jira-sync
