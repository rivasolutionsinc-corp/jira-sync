# Jira & GitHub Workflow Automation

Automated integration between GitHub and self-hosted Jira (cmext.ahrq.gov/jira) for the AHRQ Drupal ecosystem using MCP (Model Context Protocol) Atlassian container.

## Overview

This project automates the lifecycle between GitHub and Jira, enabling seamless synchronization of issues and pull requests. It uses a containerized MCP Atlassian server for reliable, stateless JSON-RPC communication with Jira.

**Current Status:** ✅ Production-Ready (CLOUD-1927 E2E tested)

## Features

### Current Implementation (Phase 1)
- **GitHub Issue Opened** → Automatically creates a Jira Task in CLOUD project
- **GitHub PR Opened/Synchronized** → Automatically adds comments to linked Jira issue with PR details
- **Jira Key Extraction** → Automatically extracts Jira key from branch name (e.g., `feature/CLOUD-1927`)

### Technology Stack
- **Container:** `ghcr.io/sooperset/mcp-atlassian:latest`
- **Transport:** Streamable HTTP with stateless mode
- **Protocol:** JSON-RPC 2.0
- **Authentication:** Jira Personal Access Token
- **CI/CD:** GitHub Actions

## Quick Start

### Prerequisites
1. **GitHub Repository Secrets:**
   - `JIRA_TOKEN`: Jira Personal Access Token (Server/Data Center)
   - `JIRA_PROJECT_KEY` (optional): Jira project key (defaults to `CLOUD`)

2. **Jira Configuration:**
   - Project key (e.g., `CLOUD`)
   - Personal Access Token with API access
   - Sufficient permissions to create issues and add comments

3. **GitHub Actions:**
   - Workflow file: `.github/workflows/jira-sync.yml`
   - Triggers on: issues opened, PR opened/synchronized

### Branch Naming Convention

All feature branches **must** follow this naming pattern:

```
feature/PROJECT-KEY-ISSUE-NUMBER
```

**Examples:**
- `feature/CLOUD-1927` - Links to Jira issue CLOUD-1927
- `feature/AQD-1234` - Links to Jira issue AQD-1234

**Important:** Branches not matching this pattern will not trigger Jira automation.

## Architecture

### System Components

```
GitHub Repository
    ↓
GitHub Actions Workflow (.github/workflows/jira-sync.yml)
    ↓
MCP Atlassian Container (ghcr.io/sooperset/mcp-atlassian:latest)
    ↓
Jira Server (cmext.ahrq.gov/jira)
```

### Workflow Execution Flow

1. **Event Trigger** - GitHub issue opened or PR opened/synchronized
2. **Container Start** - MCP Atlassian container starts with streamable-http transport
3. **Health Check** - Validates service readiness with JSON-RPC tools/list call
4. **Jira Operation** - Calls appropriate Jira tool (jira_create_issue or jira_add_comment)
5. **Result** - Issue created or comment added to Jira

### Key Configuration

**Transport:** `streamable-http --port 8080 --path /mcp --stateless`
- Stateless mode eliminates session management complexity
- Suitable for ephemeral GitHub Actions runners
- Requires Accept header: `application/json, text/event-stream`

**Authentication:** `JIRA_PERSONAL_TOKEN` environment variable
- Maps to `--jira-personal-token` flag
- Correct for Jira Server/Data Center (not Cloud)

## Workflow File

### `.github/workflows/jira-sync.yml`

Main workflow file that orchestrates Jira integrations:

**Triggers:**
- `issues.opened` - GitHub issue created
- `pull_request.opened` - PR created
- `pull_request.synchronize` - New commits pushed to PR

**Jobs:**
1. `sync-to-jira` - Handles GitHub issues and PRs

**Steps:**
1. Start MCP Atlassian container
2. Wait for service readiness (health check)
3. Create Jira ticket (on issue opened)
4. Add comment to Jira (on PR opened/synchronized)

## Setup & Configuration

### Step 1: Create GitHub Secrets

1. Go to repository → Settings → Secrets and variables → Actions
2. Create `JIRA_TOKEN`:
   - Generate Personal Access Token in Jira
   - Copy token value
   - Paste into GitHub secret
3. (Optional) Create `JIRA_PROJECT_KEY`:
   - Set to your Jira project key (e.g., `CLOUD`)
   - Defaults to `CLOUD` if not set

### Step 2: Verify Jira Configuration

1. Ensure Jira project exists (e.g., `CLOUD`)
2. Verify Personal Access Token has:
   - API access permission
   - Issue creation permission
   - Comment creation permission
3. Test token: `curl -H "Authorization: Bearer $TOKEN" https://cmext.ahrq.gov/jira/rest/api/2/myself`

### Step 3: Test the Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/CLOUD-1927
   git push origin feature/CLOUD-1927
   ```

2. Open a Pull Request on GitHub

3. Check GitHub Actions workflow logs:
   - Go to Actions tab
   - Click on workflow run
   - Verify all steps completed successfully

4. Verify in Jira:
   - Check CLOUD-1927 for new comment
   - Verify PR URL is in comment

## Troubleshooting

### Common Issues

#### 1. "Jira client not available" Error
**Cause:** Secret not passed to container or authentication failed

**Solution:**
- Verify `JIRA_TOKEN` secret is set in GitHub
- Check secret value is correct (no extra spaces)
- Verify token has API access permissions
- Check container logs: `docker logs mcp-atlassian`

#### 2. "Not Acceptable: Client must accept both application/json and text/event-stream"
**Cause:** Missing Accept header in curl request

**Solution:**
- Verify workflow includes Accept header
- Header should be: `Accept: application/json, text/event-stream`
- Already fixed in current workflow

#### 3. "Bad Request: Missing session ID"
**Cause:** Using stateful transport instead of stateless

**Solution:**
- Verify `--stateless` flag is in container startup
- Current workflow uses correct flag

#### 4. Workflow Fails on First Attempt
**Cause:** Container not ready yet

**Solution:**
- Workflow includes 3-second initial sleep
- Health check retries up to 30 times
- Typical startup time: 8-10 seconds

#### 5. "No Jira key found in branch name"
**Cause:** Branch name doesn't match `feature/PROJECT-KEY` pattern

**Solution:**
- Rename branch to follow convention
- Example: `feature/CLOUD-1927`

### Debug Logging

Enable verbose logging by checking GitHub Actions workflow logs:

1. Go to repository → Actions tab
2. Click on workflow run
3. Expand job logs to see detailed output
4. Look for:
   - Container status checks
   - Health check attempts
   - Jira API responses
   - Error messages

### Manual Testing

Test locally with Docker:

```bash
# Start container
docker run -d --name mcp-test \
  -e JIRA_URL="https://cmext.ahrq.gov/jira" \
  -e JIRA_PERSONAL_TOKEN="your-token" \
  -p 8080:8080 \
  ghcr.io/sooperset/mcp-atlassian:latest \
  --transport streamable-http --port 8080 --path /mcp --stateless

# Test health check
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# Test create issue
curl -s -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "jira_create_issue",
      "arguments": {
        "project_key": "CLOUD",
        "summary": "Test Issue",
        "description": "Test from local",
        "issue_type": "Task"
      }
    },
    "id": 1
  }'

# Cleanup
docker stop mcp-test && docker rm mcp-test
```

## Documentation

Comprehensive documentation is available in `.ai-memory/`:

- **00-DOCUMENTATION-SUMMARY.md** - Quick start guides by role
- **01-ARCHITECTURE-OVERVIEW.md** - System architecture and design
- **02-SETUP-AND-CONFIGURATION.md** - Detailed setup instructions
- **03-WORKFLOW-OPERATION-GUIDE.md** - How the workflow operates
- **04-TROUBLESHOOTING-GUIDE.md** - Common issues and solutions
- **05-FUTURE-ENHANCEMENTS.md** - Roadmap and planned features

## Future Enhancements

### Phase 2: Enhanced Automation
- Automatic issue transitions (In Progress, Done)
- Custom field updates
- Subtask creation for PRs

### Phase 3: Bidirectional Sync
- Jira transitions trigger GitHub actions
- Webhook support
- Conflict resolution

### Phase 4: Analytics & Reporting
- Velocity metrics
- Cycle time tracking
- Dashboard integration

### Phase 5: Multi-Repository Support
- Centralized Jira project
- Multiple GitHub repositories
- Cross-repository linking

See [`05-FUTURE-ENHANCEMENTS.md`](.ai-memory/05-FUTURE-ENHANCEMENTS.md) for detailed roadmap.

## Security & Compliance

### Token Management
- `JIRA_TOKEN` stored in GitHub Secrets (encrypted)
- Never commit tokens to repository
- Rotate tokens regularly (recommended: quarterly)

### Branch Validation
- Branch naming enforced: `feature/PROJECT-KEY`
- Prevents accidental Jira key extraction

### Audit Trail
- All Jira operations logged with:
  - GitHub actor (who triggered)
  - Timestamp (when)
  - Commit SHA (what code)
  - PR number (which PR)

### Rate Limiting
- Jira API rate limits: ~10 requests/second
- Health check includes retry logic with exponential backoff
- Monitors for rate limit errors

## Development

### Adding New Features

1. **Update `.github/workflows/jira-sync.yml`:**
   - Add new trigger event or step
   - Call appropriate Jira tool

2. **Test locally:**
   - Use Docker to test container startup
   - Test JSON-RPC calls manually
   - Verify Jira operations

3. **Create feature branch:**
   ```bash
   git checkout -b feature/CLOUD-XXXX
   git commit -am "Add new feature"
   git push origin feature/CLOUD-XXXX
   ```

4. **Create pull request and merge after review**

## References

- [MCP Atlassian Documentation](https://github.com/sooperset/mcp-atlassian)
- [Jira REST API v2 Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v2/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Webhook Events](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review workflow logs in GitHub Actions
3. Check container logs: `docker logs mcp-atlassian`
4. Review comprehensive documentation in `.ai-memory/`
5. Contact DevOps team

## License

This project is part of the AHRQ Drupal ecosystem and follows AHRQ licensing guidelines.
