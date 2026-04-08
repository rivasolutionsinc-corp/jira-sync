# Jira & GitHub Workflow Automation

Automated integration between GitHub and self-hosted Jira (cmext.ahrq.gov/jira) for the AHRQ Drupal ecosystem.

## Overview

This project automates the lifecycle between GitHub and Jira, enabling seamless synchronization of issues, pull requests, and code changes. It enforces a multi-agent architecture where planning, coding, and DevOps are strictly separated.

## Features

### Phase 0: Basic Integration (Existing)
- **GitHub Issue Opened** → Automatically creates a Jira Task
- **GitHub Push to Feature Branch** → Adds comment to linked Jira issue with commit details

### Phase 1: Advanced GitHub Actions CI/CD Automation (NEW)

#### Pull Request Lifecycle Automation
- **PR Opened** → Creates Jira subtask linked to parent issue
- **PR Synchronize** (new commits) → Updates Jira comment with latest commit SHA and author
- **PR Ready for Review** → Transitions Jira issue to "In Review" status
- **PR Closed (without merge)** → Adds comment indicating PR was closed without merging

#### Pull Request Merge Automation
- **PR Merged** → Transitions Jira issue to "Merged" status
- **PR Merged** → Adds comment with merge commit SHA, merge author, and timestamp

## Architecture

### Tech Stack
- **CMS:** Drupal (AHRQ Government instances)
- **Infrastructure:** Self-hosted Jira (Apache/Tomcat) + GitHub Actions
- **Automation:** Python-based Jira REST API v2 integrations (Bearer token authentication)
- **CI/CD:** GitHub Actions workflows

### Multi-Agent System
- **Orchestrator:** High-level planning and architecture
- **Documentation Writer:** Standardizes logs and ADRs in `./.ai-memory/`
- **Code (Drupal Builder):** Implements logic, hooks, and services
- **Git Ops:** Manages branching and commits

## Setup & Configuration

### Prerequisites
1. **GitHub Repository Secrets:**
   - `JIRA_TOKEN`: Personal Access Token for Jira API authentication (Bearer token format)
   - `JIRA_PROJECT_KEY` (optional): Jira project key for GitHub issue creation (defaults to `AQD` if not set)

2. **Jira Configuration:**
   - Project key (e.g., `AQD`)
   - Available transitions: `In Review`, `Merged`, `Start Progress`, etc.
   - Subtask issue type must be enabled

3. **GitHub Actions:**
   - Python 3.x available on runners
   - `requests` library installed (via `pip install requests`)

### Branch Naming Convention

All feature branches **must** follow this naming pattern:

```
feature/PROJECT-ID-ISSUE-NUMBER
```

**Examples:**
- `feature/AQD-1234` - Creates/links to Jira issue AQD-1234
- `feature/EHC-5678` - Creates/links to Jira issue EHC-5678

**Important:** Branches not matching this pattern will not trigger Jira automation.

### Multi-Project Support

The system supports multiple Jira projects:

**For GitHub Issues:**
- Set `JIRA_PROJECT_KEY` secret in GitHub repository settings
- If not set, defaults to `AQD`
- Example: Set `JIRA_PROJECT_KEY=EHC` to create issues in the EHC project

**For Pull Requests & Push Events:**
- Automatically extracts project key from branch name
- Example: `feature/EHC-5678` automatically uses the `EHC` project
- No configuration needed - fully dynamic

## Workflow Files

### `.github/workflows/jira-sync.yml`

Main workflow file that orchestrates all Jira integrations:

**Triggers:**
- `issues.opened` - GitHub issue created
- `push` to `feature/**` branches - Code pushed
- `pull_request` events:
  - `opened` - PR created
  - `synchronize` - New commits pushed to PR
  - `ready_for_review` - PR marked as ready for review
  - `closed` - PR closed (with or without merge)

**Jobs:**
1. `sync-to-jira` - Handles GitHub issues and push events
2. `pr-lifecycle` - Handles PR lifecycle and merge automation

## Python Integration Script

### `jira_integration_script.py`

Core API client for Jira REST v2 integration.

#### Existing Functions

- **`create_jira_issue(project_key, summary, description, issue_type="Task")`**
  - Creates a new Jira issue
  - Returns: Issue key (e.g., "AQD-1234") on success, None on failure

- **`add_comment(issue_key, comment_body)`**
  - Adds a comment to an existing Jira issue
  - Returns: None (prints status to stdout)

- **`get_issue_details(issue_key)`**
  - Retrieves details of a Jira issue
  - Returns: Dictionary with issue metadata (key, summary, status, assignee, etc.)

- **`change_issue_status(issue_key, transition_name)`**
  - Transitions a Jira issue to a new status
  - Returns: True on success, False on failure

#### New Functions (Phase 1)

- **`create_jira_subtask(parent_key, summary, description)`**
  - Creates a Jira subtask linked to a parent issue
  - Automatically extracts project key from parent_key
  - Returns: Subtask key (e.g., "AQD-1235") on success, None on failure
  - **Use Case:** Create PR subtask when PR is opened

- **`link_jira_issues(issue_key1, issue_key2, link_type="relates to")`**
  - Links two Jira issues together
  - Supported link types: "relates to", "blocks", "is blocked by", etc.
  - Returns: True on success, False on failure
  - **Use Case:** Link PR subtask to deployment issue

- **`retry_api_call(func, max_retries=3, backoff_factor=2)`**
  - Retry wrapper for Jira API calls with exponential backoff
  - Handles transient network/API failures gracefully
  - Backoff timing: 1s, 2s, 4s (exponential)
  - Returns: Result of func() on success, None on failure after max retries
  - **Use Case:** Resilience for all API calls

### Logging

All functions include structured logging with timestamps:

```
[2026-04-08T20:33:10.123456] Creating Jira subtask for parent: AQD-1234
[2026-04-08T20:33:10.234567] Successfully created subtask: AQD-1235
```

## Testing

### Unit Tests

Run unit tests for all Jira integration functions:

```bash
python -m pytest test_jira_integration.py -v
```

**Test Coverage:**
- `TestCreateJiraSubtask` - Subtask creation success/failure scenarios
- `TestLinkJiraIssues` - Issue linking success/failure scenarios
- `TestRetryApiCall` - Retry logic and exponential backoff
- `TestExistingFunctions` - Backward compatibility for existing functions

### Integration Testing

1. **Create a test PR:**
   ```bash
   git checkout -b feature/TEST-9999
   git push origin feature/TEST-9999
   ```

2. **Open a PR on GitHub** from `feature/TEST-9999` to `main`

3. **Verify workflow execution:**
   - Check GitHub Actions workflow logs
   - Verify Jira subtask created for the PR
   - Verify Jira comment added with PR details

4. **Test PR lifecycle:**
   - Mark PR as ready for review → Verify Jira transitions to "In Review"
   - Merge PR → Verify Jira transitions to "Merged"
   - Close PR without merge → Verify Jira comment added

### Manual Testing Checklist

- [ ] Push commit to `feature/AQD-1234` branch
- [ ] Open PR and verify workflow triggers
- [ ] Verify Jira comment added with commit SHA
- [ ] Mark PR as ready for review and verify Jira transition
- [ ] Merge PR and verify Jira transition to "Merged"
- [ ] Check Jira audit trail for all transitions

## Troubleshooting

### Common Issues

#### 1. "No Jira key found in branch name"
**Cause:** Branch name doesn't match `feature/PROJECT-ID` pattern

**Solution:** Rename branch to follow naming convention:
```bash
git branch -m feature/AQD-1234
git push origin feature/AQD-1234
```

#### 2. "Failed to create subtask. Status code: 400"
**Cause:** Parent issue doesn't exist or project key is invalid

**Solution:**
- Verify Jira issue exists (e.g., AQD-1234)
- Verify project key is correct
- Check Jira API token has permissions

#### 3. "Could not transition to In Review (transition may not exist)"
**Cause:** Jira workflow doesn't have "In Review" transition

**Solution:**
- Check Jira project workflow configuration
- Update workflow step to use correct transition name
- Common transitions: "Start Progress", "In Progress", "In Review", "Done"

#### 4. "Failed after 3 attempts: Connection error"
**Cause:** Jira API is unreachable or network timeout

**Solution:**
- Verify Jira server is online: `https://cmext.ahrq.gov/jira`
- Check GitHub Actions runner network connectivity
- Verify `JIRA_TOKEN` secret is set correctly
- Check Jira API rate limits

#### 5. "401 Unauthorized"
**Cause:** Invalid or expired `JIRA_TOKEN`

**Solution:**
- Regenerate Personal Access Token in Jira
- Update `JIRA_TOKEN` secret in GitHub repository settings
- Verify token has API access permissions

### Debug Logging

Enable verbose logging by checking GitHub Actions workflow logs:

1. Go to repository → Actions tab
2. Click on workflow run
3. Expand job logs to see detailed output
4. Look for `[TIMESTAMP]` prefixed log messages

### API Response Codes

| Code | Meaning | Action |
|------|---------|--------|
| 201 | Created | Success - resource created |
| 204 | No Content | Success - resource updated |
| 400 | Bad Request | Check request payload format |
| 401 | Unauthorized | Check JIRA_TOKEN secret |
| 403 | Forbidden | Check token permissions |
| 404 | Not Found | Check issue key exists |
| 500 | Server Error | Jira server error - retry |

## Security & Compliance

### Token Management
- `JIRA_TOKEN` stored in GitHub Secrets (encrypted)
- Never commit tokens to repository
- Rotate tokens regularly (recommended: quarterly)

### Branch Validation
- Branch naming enforced: `feature/PROJECT-ID`
- Prevents accidental Jira key extraction from invalid branch names

### Audit Trail
- All Jira transitions logged with:
  - GitHub actor (who triggered the action)
  - Timestamp (when action occurred)
  - Commit SHA (what code was involved)
  - PR number (which PR triggered the action)

### Rate Limiting
- Jira API has rate limits (typically 10 requests/second)
- Retry logic with exponential backoff prevents rate limit violations
- Monitor workflow logs for rate limit errors

## Development

### Adding New Features

1. **Update `.github/workflows/jira-sync.yml`:**
   - Add new trigger event or job
   - Call appropriate Python function

2. **Update `jira_integration_script.py`:**
   - Add new function or enhance existing function
   - Include error handling and logging
   - Use `retry_api_call()` wrapper for resilience

3. **Add unit tests in `test_jira_integration.py`:**
   - Mock Jira API responses
   - Test success and failure scenarios
   - Test error handling

4. **Update `README.md`:**
   - Document new feature
   - Add troubleshooting section if needed
   - Update examples

5. **Create feature branch:**
   ```bash
   git checkout -b feature/JIRA-XXXX
   git commit -am "Add new feature"
   git push origin feature/JIRA-XXXX
   ```

6. **Create pull request and merge after review**

## References

- [Jira REST API v2 Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v2/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Webhook Events](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review workflow logs in GitHub Actions
3. Check Jira API response in workflow output
4. Contact DevOps team

## License

This project is part of the AHRQ Drupal ecosystem and follows AHRQ licensing guidelines.
