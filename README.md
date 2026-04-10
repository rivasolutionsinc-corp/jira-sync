# Jira & GitHub Workflow Automation

Automated integration between GitHub and self-hosted Jira (cmext.ahrq.gov/jira) for the AHRQ Drupal ecosystem using a containerized Docker Action.

## Overview

This project automates the lifecycle between GitHub and Jira, enabling seamless synchronization of issues and pull requests. It uses a containerized Docker Action for reliable, stateless communication with Jira via REST API.

**Current Status:** ✅ Production-Ready (CLOUD-1929 Docker Container Action)

## Features

### Current Implementation (Phase 1: Generalized Python Toolset)
- **GitHub Issue Opened** → Automatically creates a Jira Task in CLOUD project
- **GitHub PR Opened/Synchronized** → Automatically adds comments to linked Jira issue with PR details
- **Configurable Transitions** → Transition issues on PR opened, merged, or push events
- **Push Event Support** → Automatically transition issues when code is pushed to target branches
- **Jira Key Extraction** → Automatically extracts Jira key from branch name (e.g., `feature/CLOUD-1927`)
- **Customizable Link Titles** → Configure custom titles for GitHub PR links in Jira

### Docker Container Action (CLOUD-1929)
- **Containerized Action** - Published to GHCR for cross-repository reusability
- **8–24x Faster Startup** - 5–15 seconds vs 60–120 seconds
- **61% Simpler Workflows** - Reduced complexity from 97 to 38 lines
- **Cross-Organization Reuse** - Use in any GitHub repository

### Technology Stack
- **Container:** `ghcr.io/rivasolutionsinc-corp/jira-sync-action:latest`
- **Transport:** REST API with Bearer token authentication
- **Protocol:** HTTP/JSON
- **Authentication:** Jira Personal Access Token
- **CI/CD:** GitHub Actions with Docker Container Action

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
Docker Container Action (ghcr.io/rivasolutionsinc-corp/jira-sync-action:latest)
    ↓
Jira Server (cmext.ahrq.gov/jira)
```

### Workflow Execution Flow

1. **Event Trigger** - GitHub issue opened or PR opened/synchronized
2. **Action Start** - Docker Container Action starts with environment variables
3. **Jira Operation** - Calls appropriate Jira REST API (create issue or add comment)
4. **Result** - Issue created or comment added to Jira

### Key Configuration

**Container:** `ghcr.io/rivasolutionsinc-corp/jira-sync-action:latest`
- Containerized Python script with Jira integration
- Stateless operation suitable for ephemeral GitHub Actions runners
- REST API communication with Jira

**Authentication:** `JIRA_TOKEN` environment variable
- Bearer token authentication
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
1. Call Docker Container Action with environment variables
2. Create Jira ticket (on issue opened)
3. Add comment to Jira (on PR opened/synchronized)

## Using the Published Action

### In This Repository

```yaml
- uses: ./.github/actions/jira-sync
  with:
    jira-url: 'https://cmext.ahrq.gov/jira'
    jira-token: ${{ secrets.JIRA_TOKEN }}
    project-key: 'CLOUD'
    event-name: ${{ github.event_name }}
    pr-branch: ${{ github.head_ref }}
    pr-url: ${{ github.event.pull_request.html_url }}
```

### In Other Repositories (Using Published Image)

```yaml
- uses: rivasolutionsinc-corp/jira-sync/.github/actions/jira-sync@v1.0.0
  with:
    jira-url: ${{ secrets.JIRA_URL }}
    jira-token: ${{ secrets.JIRA_TOKEN }}
    project-key: ${{ secrets.JIRA_PROJECT_KEY }}
    event-name: ${{ github.event_name }}
    pr-branch: ${{ github.head_ref }}
    pr-url: ${{ github.event.pull_request.html_url }}
```

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
**Cause:** Secret not passed to action or authentication failed

**Solution:**
- Verify `JIRA_TOKEN` secret is set in GitHub
- Check secret value is correct (no extra spaces)
- Verify token has API access permissions
- Check action logs in GitHub Actions

#### 2. "Connection refused" Error
**Cause:** Jira URL is incorrect or Jira is unreachable

**Solution:**
- Verify `JIRA_URL` is correct (e.g., `https://cmext.ahrq.gov/jira`)
- Check network connectivity to Jira server
- Verify firewall rules allow GitHub Actions to reach Jira

#### 3. "No Jira key found in branch name"
**Cause:** Branch name doesn't match `feature/PROJECT-KEY` pattern

**Solution:**
- Rename branch to follow convention
- Example: `feature/CLOUD-1927`

#### 4. Action Fails on First Attempt
**Cause:** Jira server not responding yet

**Solution:**
- Retry the workflow
- Check Jira server status
- Verify network connectivity

### Debug Logging

Enable verbose logging by checking GitHub Actions workflow logs:

1. Go to repository → Actions tab
2. Click on workflow run
3. Expand job logs to see detailed output
4. Look for:
   - Action startup messages
   - Jira API responses
   - Error messages

### Manual Testing

Test locally with Docker:

```bash
# Pull the published image
docker pull ghcr.io/rivasolutionsinc-corp/jira-sync-action:latest

# Run the action
docker run --rm \
  -e JIRA_URL="https://cmext.ahrq.gov/jira" \
  -e JIRA_TOKEN="your-token" \
  -e PROJECT_KEY="CLOUD" \
  -e EVENT_NAME="pull_request" \
  -e PR_BRANCH="feature/CLOUD-1927" \
  -e PR_URL="https://github.com/rivasolutionsinc-corp/jira-sync/pull/1" \
  ghcr.io/rivasolutionsinc-corp/jira-sync-action:latest
```

## Testing

### Published Image Test

The repository includes automated tests for the published Docker image:

**Test Workflow:** `.github/workflows/test-published-image.yml`
- Pulls the published image from GHCR
- Authenticates with GHCR using GITHUB_TOKEN
- Tests Jira connectivity by listing issues
- Validates image execution

**Run Test Manually:**
```bash
gh workflow run test-published-image.yml
```

## Documentation

Comprehensive documentation is available in `.ai-memory/`:

- **00-DOCUMENTATION-SUMMARY.md** - Quick start guides by role
- **01-ARCHITECTURE-OVERVIEW.md** - System architecture and design
- **02-SETUP-AND-CONFIGURATION.md** - Detailed setup instructions
- **03-WORKFLOW-OPERATION-GUIDE.md** - How the workflow operates
- **04-TROUBLESHOOTING-GUIDE.md** - Common issues and solutions
- **05-FUTURE-ENHANCEMENTS.md** - Roadmap and planned features

## Phase 1: Generalized Python Toolset (CLOUD-1959)

### New CLI Arguments

Phase 1 introduces configurable event routing and transitions via CLI arguments:

#### Transition Arguments
- `--transition-opened` - Jira transition when PR is opened (e.g., "In Progress")
- `--transition-merged` - Jira transition when PR is merged (e.g., "Done")
- `--transition-tag` - Jira transition when pushed to target branch (e.g., "Released")

#### Event Routing Arguments
- `--target-branch` - Target branch for push event matching (e.g., "main")
- `--pr-action` - PR action type (opened, synchronize, closed)
- `--pr-merged` - Flag indicating PR was merged

#### Link Arguments
- `--link-title` - Custom title for GitHub PR links (default: "GitHub PR")

### Example Usage

```bash
# PR opened with transition
python jira_integration_script.py \
  --event-name pull_request \
  --jira-url https://jira.example.com \
  --jira-token YOUR_TOKEN \
  --project-key CLOUD \
  --pr-branch feature/CLOUD-1234-description \
  --pr-url https://github.com/org/repo/pull/1 \
  --pr-action opened \
  --transition-opened "In Progress"

# Push to main with release transition
python jira_integration_script.py \
  --event-name push \
  --jira-url https://jira.example.com \
  --jira-token YOUR_TOKEN \
  --project-key CLOUD \
  --push-branch main \
  --target-branch main \
  --transition-tag "Released"
```

### Backward Compatibility

All Phase 0 workflows continue to work without modification. New arguments are optional.

### Documentation

- **Implementation Guide:** [`.ai-memory/PHASE_1_IMPLEMENTATION_GUIDE.md`](.ai-memory/PHASE_1_IMPLEMENTATION_GUIDE.md)
- **Migration Guide:** [`.ai-memory/PHASE_0_TO_PHASE_1_MIGRATION_GUIDE.md`](.ai-memory/PHASE_0_TO_PHASE_1_MIGRATION_GUIDE.md)
- **Test Suite:** `test_phase1_generalization.py` (34 tests, 100% pass rate)

## Future Enhancements

### Phase 2: Enhanced Automation
- Custom field updates
- Subtask creation for PRs
- Advanced workflow automation

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
- Action includes retry logic with exponential backoff
- Monitors for rate limit errors

## Development

### Adding New Features

1. **Update `.github/workflows/jira-sync.yml`:**
   - Add new trigger event or step
   - Call appropriate Jira tool

2. **Test locally:**
   - Use Docker to test action startup
   - Test Jira operations
   - Verify integration

3. **Create feature branch:**
   ```bash
   git checkout -b feature/CLOUD-XXXX
   git commit -am "Add new feature"
   git push origin feature/CLOUD-XXXX
   ```

4. **Create pull request and merge after review**

### Publishing Updates

When updating the action:

1. Update action files in `.github/actions/jira-sync/`
2. Create a new version tag (e.g., `v1.1.0`)
3. Push tag to trigger publish workflow
4. Publish workflow automatically builds and pushes to GHCR

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Jira REST API v2 Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v2/)
- [GitHub Webhook Events](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review workflow logs in GitHub Actions
3. Review comprehensive documentation in `.ai-memory/`
4. Contact DevOps team

## License

This project is part of the AHRQ Drupal ecosystem and follows AHRQ licensing guidelines.
