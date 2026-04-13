# Jira & GitHub Workflow Automation

A reusable, public GitHub Action that automates the lifecycle between GitHub and self-hosted Jira (Data Center / Server) instances. Built as a containerized Docker Action for reliable, stateless REST API communication.

## Overview

This project provides a **project-agnostic, multi-tenant** GitHub Action that synchronizes GitHub Issues and Pull Requests with Jira. It supports dynamic state mapping, GitFlow-aware branch strategies, and Jenkins deployment pipeline alignment.

**Current Status:** ✅ Production-Ready | Public Release Hardened (Phase 3: Deployment Orchestration)

**Branch:** `feature/public-release-workflow-hardening`

---

## Features

### Core Capabilities
- **Pure REST API** — No MCP dependencies, direct Jira REST API calls with Bearer token auth
- **Production Hardening** — Input validation, rate limiting, retry logic with exponential backoff, timeouts
- **Connection Pooling** — Efficient HTTP session management with automatic retries
- **Structured Logging** — Timestamped, context-rich logs for debugging
- **Type Hints** — Full type annotations throughout the Python codebase

### GitHub Event Lifecycle
- **Issue Opened** → Creates a Jira Task in the configured project
- **PR Opened** → Comments on linked Jira issue, links PR via Remote Issue Link API
- **PR Synchronized** → Updates remote link on Jira issue
- **PR Merged** → Transitions Jira issue (configurable: e.g., `Done` or `In QA`)
- **Tag Created** → Transitions Jira issue to production state (e.g., `Deployed`)

### Dynamic State Mapping (GitFlow/Jenkins Alignment)
- PR merged to `stage` → `In QA` (triggers Stage Deploy)
- PR merged to `main` → `Done` (triggers Prod-Blue Deploy)
- Tag created (`v*.*.*`) → `Deployed`
- All transitions are **fully configurable** via workflow inputs

### Docker Container Action
- **Self-contained** — `jira_integration_script.py` bundled inside the action directory
- **8–24x Faster Startup** — 5–15 seconds vs 60–120 seconds for composite actions
- **Cross-Organization Reuse** — Use in any GitHub repository via `rivasolutionsinc-corp/jira-sync/.github/actions/jira-sync@main`

---

## Quick Start

### Prerequisites

Configure the following **GitHub Repository Secrets**:

| Secret | Required | Description |
|--------|----------|-------------|
| `JIRA_URL` | ✅ Yes | Your Jira instance URL (e.g., `https://your-org.atlassian.net`) |
| `JIRA_TOKEN` | ✅ Yes | Jira Personal Access Token (Data Center) or API Token (Cloud) |
| `JIRA_PROJECT_KEY` | ✅ Yes | Your Jira project key (e.g., `PROJ`) |

### Branch Naming Convention

All feature branches **must** follow this naming pattern for Jira key extraction:

```
feature/PROJECT-KEY-ISSUE-NUMBER[-description]
```

**Examples:**
- `feature/PROJ-1234` — Links to Jira issue PROJ-1234
- `feature/PROJ-1234-add-login-page` — Links to Jira issue PROJ-1234

> **Important:** Branches not matching this pattern will be skipped gracefully (not an error).

---

## Architecture

### System Components

```
GitHub Repository
    ↓ (issues, pull_request, create events)
GitHub Actions Workflow (.github/workflows/jira-sync.yml)
    ↓
Docker Container Action (.github/actions/jira-sync/)
    ↓ (REST API + Bearer token)
Jira Data Center / Server
```

### Workflow Execution Flow

1. **Event Trigger** — GitHub issue opened, PR lifecycle event, or tag creation
2. **Guard Condition** — `create` events filtered to tags only (not branch creation)
3. **Debug Logging** — Event context printed for troubleshooting
4. **Action Execution** — Docker container starts, entrypoint.sh maps inputs to CLI args
5. **Jira Operation** — Python script calls appropriate Jira REST API endpoint
6. **State Transition** — Issue transitioned based on dynamic mapping

### Repository Structure

```
jira-sync/
├── .github/
│   ├── actions/
│   │   └── jira-sync/              # Reusable Docker-based Action
│   │       ├── Dockerfile
│   │       ├── action.yml          # Action manifest with all inputs
│   │       ├── entrypoint.sh       # Maps action inputs to CLI args
│   │       ├── jira_integration_script.py  # Bundled Python script
│   │       └── requirements.txt
│   └── workflows/
│       ├── jira-sync.yml           # Main integration workflow
│       ├── test-published-image.yml
│       └── verify-jira-access.yml
├── hooks/                          # Git hooks for memory management
│   ├── install-hooks.sh
│   └── post-commit
├── tests/                          # Test suites
│   ├── test_jira_lifecycle_automation.py
│   ├── test_phase1_generalization.py
│   ├── test_phase2_production_hardening.py
│   └── test_phase3_deployment_orchestration.py
├── .env.example
├── .gitignore
├── docker-compose.yml              # Local testing/dev environment
├── jira_integration_script.py      # Core REST API Logic (reference copy)
└── README.md
```

---

## Workflow File

### `.github/workflows/jira-sync.yml`

```yaml
name: Jira Sync

on:
  issues:
    types: [opened]
  pull_request:
    types: [opened, synchronize, closed]
  create:  # Tag creation only (branch creation filtered by job condition)
  workflow_dispatch:
    inputs:
      jira-url:
        description: 'JIRA instance URL (optional override)'
        required: false
      project-key:
        description: 'JIRA project key (optional override)'
        required: false

jobs:
  sync-to-jira:
    runs-on: ubuntu-latest
    if: github.event_name != 'create' || github.event.ref_type == 'tag'
    steps:
      - uses: actions/checkout@v4
      - name: Debug Event Context
        run: |
          echo "Event: ${{ github.event_name }}"
          echo "Action: ${{ github.event.action }}"
          echo "Target Branch: ${{ github.base_ref }}"
      - uses: ./.github/actions/jira-sync
        with:
          jira-url: ${{ github.event.inputs.jira-url || secrets.JIRA_URL }}
          jira-token: ${{ secrets.JIRA_TOKEN }}
          project-key: ${{ github.event.inputs.project-key || secrets.JIRA_PROJECT_KEY }}
          event-name: ${{ github.event_name }}
          event-action: ${{ github.event.action || 'created' }}
          pr-branch: ${{ github.head_ref }}
          pr-url: ${{ github.event.pull_request.html_url }}
          is-merged: ${{ github.event.pull_request.merged || 'false' }}
          target-branch: ${{ github.base_ref || 'main' }}
          transition-on-open: 'In Review'
          transition-on-merge: ${{ github.base_ref == 'stage' && 'In QA' || 'Done' }}
          transition-on-tag: 'Deployed'
```

---

## Using the Action

### In This Repository (Local Reference)

```yaml
- uses: ./.github/actions/jira-sync
  with:
    jira-url: ${{ secrets.JIRA_URL }}
    jira-token: ${{ secrets.JIRA_TOKEN }}
    project-key: ${{ secrets.JIRA_PROJECT_KEY }}
    event-name: ${{ github.event_name }}
    event-action: ${{ github.event.action || 'created' }}
    pr-branch: ${{ github.head_ref }}
    pr-url: ${{ github.event.pull_request.html_url }}
    is-merged: ${{ github.event.pull_request.merged || 'false' }}
    target-branch: ${{ github.base_ref || 'main' }}
    transition-on-open: 'In Review'
    transition-on-merge: 'Done'
    transition-on-tag: 'Deployed'
```

### In Other Repositories (Cross-Org Reuse)

```yaml
- uses: rivasolutionsinc-corp/jira-sync/.github/actions/jira-sync@main
  with:
    jira-url: ${{ secrets.JIRA_URL }}
    jira-token: ${{ secrets.JIRA_TOKEN }}
    project-key: ${{ secrets.JIRA_PROJECT_KEY }}
    event-name: ${{ github.event_name }}
    event-action: ${{ github.event.action || 'created' }}
    pr-branch: ${{ github.head_ref }}
    pr-url: ${{ github.event.pull_request.html_url }}
    is-merged: ${{ github.event.pull_request.merged || 'false' }}
    target-branch: ${{ github.base_ref || 'main' }}
    transition-on-open: 'In Review'
    transition-on-merge: ${{ github.base_ref == 'stage' && 'In QA' || 'Done' }}
    transition-on-tag: 'Deployed'
```

---

## Action Inputs Reference

### Required Inputs

| Input | Description |
|-------|-------------|
| `jira-url` | Jira instance base URL |
| `jira-token` | Jira API token (PAT for Data Center, API token for Cloud) |
| `project-key` | Jira project key (e.g., `PROJ`) |
| `event-name` | GitHub event name (`issues`, `pull_request`, `create`) |

### Optional Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `event-action` | `created` | GitHub event action (`opened`, `closed`, `synchronize`) |
| `issue-title` | `''` | GitHub issue title (for `issues` event) |
| `issue-url` | `''` | GitHub issue URL (for `issues` event) |
| `pr-branch` | `''` | PR source branch name |
| `pr-url` | `''` | PR HTML URL |
| `is-merged` | `false` | Whether the PR was merged |
| `target-branch` | `main` | Target branch for deployment matching |
| `transition-on-open` | `In Review` | Jira transition when PR/Issue is opened |
| `transition-on-merge` | `Done` | Jira transition when PR is merged |
| `transition-on-tag` | `Deployed` | Jira transition when tag is created |
| `link-title` | `GitHub PR` | Custom title for GitHub PR remote links |
| `issue-type` | `Task` | Jira issue type for new issues |

---

## CLI Reference

The [`jira_integration_script.py`](jira_integration_script.py) can also be run directly:

```bash
# PR opened — transition to In Review
python jira_integration_script.py \
  --event-name pull_request \
  --jira-url https://your-jira.atlassian.net \
  --jira-token YOUR_TOKEN \
  --project-key PROJ \
  --pr-branch feature/PROJ-1234-my-feature \
  --pr-url https://github.com/org/repo/pull/1 \
  --event-action opened \
  --transition-on-open "In Review"

# PR merged to stage — transition to In QA
python jira_integration_script.py \
  --event-name pull_request \
  --jira-url https://your-jira.atlassian.net \
  --jira-token YOUR_TOKEN \
  --project-key PROJ \
  --pr-branch feature/PROJ-1234-my-feature \
  --pr-url https://github.com/org/repo/pull/1 \
  --event-action closed \
  --is-merged \
  --target-branch stage \
  --transition-on-merge "In QA"

# Tag created — transition to Deployed
python jira_integration_script.py \
  --event-name create \
  --jira-url https://your-jira.atlassian.net \
  --jira-token YOUR_TOKEN \
  --project-key PROJ \
  --tag-name v1.2.3-PROJ-1234 \
  --transition-on-tag "Deployed"
```

---

## Setup & Configuration

### Step 1: Configure GitHub Secrets

1. Go to **Repository → Settings → Secrets and variables → Actions**
2. Add the following secrets:
   - `JIRA_URL` — Your Jira instance URL
   - `JIRA_TOKEN` — Personal Access Token from Jira
   - `JIRA_PROJECT_KEY` — Your project key

### Step 2: Verify Jira Token Permissions

Your Jira token must have:
- ✅ Issue creation permission
- ✅ Comment creation permission
- ✅ Issue transition permission
- ✅ Remote link creation permission

Test connectivity:
```bash
curl -H "Authorization: Bearer $JIRA_TOKEN" \
  https://your-jira-instance.com/jira/rest/api/2/myself
```

### Step 3: Test the Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/PROJ-1234
   git push origin feature/PROJ-1234
   ```

2. Open a Pull Request on GitHub

3. Check **Actions** tab → verify workflow completed successfully

4. Verify in Jira:
   - Check `PROJ-1234` for new comment and remote link
   - Verify issue transitioned to `In Review`

### Step 4: Manual Testing via Workflow Dispatch

1. Go to **Actions → Jira Sync → Run workflow**
2. Optionally override `jira-url` or `project-key` for testing
3. Review the **Debug Event Context** step output in logs

---

## Troubleshooting

### Common Issues

#### "unrecognized arguments" Error
**Cause:** Mismatch between workflow inputs and action manifest.

**Solution:** Ensure [`action.yml`](.github/actions/jira-sync/action.yml) defines all inputs used in the workflow. The bundled [`jira_integration_script.py`](.github/actions/jira-sync/jira_integration_script.py) must match the root copy.

#### "No Jira key found in branch name"
**Cause:** Branch name doesn't match `PROJECT-KEY-NUMBER` pattern.

**Solution:** Rename branch to follow convention (e.g., `feature/PROJ-1234`). This is a graceful skip, not an error.

#### "Connection refused" / "Invalid Jira URL"
**Cause:** `JIRA_URL` secret is incorrect or Jira is unreachable from GitHub Actions.

**Solution:**
- Verify URL format: `https://your-jira-instance.com/jira`
- Check firewall rules allow GitHub Actions IP ranges
- Test with `verify-jira-access.yml` workflow

#### Docker Build Fails: "file not found"
**Cause:** [`jira_integration_script.py`](.github/actions/jira-sync/jira_integration_script.py) missing from action directory.

**Solution:** The script must exist in `.github/actions/jira-sync/`. Copy from root:
```bash
cp jira_integration_script.py .github/actions/jira-sync/
```

### Debug Logging

The workflow includes a **Debug Event Context** step that logs:
- Event name and action
- Source and target branches
- Merge status
- Ref type and ref value

Review these in **Actions → [workflow run] → Debug Event Context**.

---

## Testing

### Run the Full Test Suite

```bash
# Phase 1: Generalization tests
python3 -m pytest tests/test_phase1_generalization.py -v

# Phase 2: Production hardening tests
python3 -m pytest tests/test_phase2_production_hardening.py -v

# Phase 3: Deployment orchestration tests
python3 -m pytest tests/test_phase3_deployment_orchestration.py -v

# All tests
python3 -m pytest tests/ -v
```

### Local Docker Testing

```bash
# Build the action image locally
docker build -t jira-sync-action .github/actions/jira-sync/

# Run with test inputs
docker run --rm \
  jira-sync-action \
  "https://your-jira-instance.com/jira" \
  "YOUR_TOKEN" \
  "PROJ" \
  "pull_request" \
  "opened" \
  "" "" \
  "feature/PROJ-1234" \
  "https://github.com/org/repo/pull/1" \
  "Task" \
  "false" \
  "In Review" \
  "Done" \
  "Deployed" \
  "GitHub PR"
```

---

## Milestone History

| Milestone | Status | Description |
|-----------|--------|-------------|
| **MCP Migration & Stabilization** | ✅ Completed/Reverted | Identified silent failure bug in upstream MCP comment tool; reverted to pure REST API |
| **Docker Container Action (CLOUD-1929)** | ✅ Completed | Containerized Python script; 15x faster startup; published to GHCR |
| **Jenkins & GitFlow Alignment (CLOUD-1962)** | ✅ Completed | Mapped Stage Promotion and Production Release triggers to Jira states |
| **Phase 1: Dynamic Multi-Project Support (CLOUD-1959)** | ✅ Completed | Generalized CLI; added `--transition-on-*`, `--target-branch`, `--is-merged` flags |
| **Phase 2: Production Hardening (CLOUD-1961)** | ✅ Completed | Removed MCP code; added validation, retry logic, connection pooling; 52 tests |
| **Phase 3: Deployment Orchestration (CLOUD-1962)** | ✅ Completed | Full GitFlow/Jenkins lifecycle automation |
| **Public Release Hardening** | ✅ Completed | Removed hardcoded org values; parameterized secrets; added workflow_dispatch |

---

## Security & Compliance

### Token Management
- `JIRA_TOKEN` stored in GitHub Secrets (encrypted at rest)
- Never commit tokens to the repository
- Rotate tokens regularly (recommended: quarterly)
- Use minimum required permissions

### Audit Trail
All Jira operations are logged with:
- GitHub actor (who triggered)
- Timestamp (when)
- Event type and action (what happened)
- Branch/tag name (which code)

### Rate Limiting
- Jira API rate limits respected with exponential backoff
- `MAX_RETRIES = 3`, `BACKOFF_FACTOR = 2`
- `RATE_LIMIT_DELAY = 0.5s` between API calls

---

## Development

### Adding New Features

1. **Update [`jira_integration_script.py`](jira_integration_script.py)** — Add new CLI argument and handler logic
2. **Update [`.github/actions/jira-sync/action.yml`](.github/actions/jira-sync/action.yml)** — Add new input definition
3. **Update [`.github/actions/jira-sync/entrypoint.sh`](.github/actions/jira-sync/entrypoint.sh)** — Map new input to CLI arg
4. **Sync script to action directory:**
   ```bash
   cp jira_integration_script.py .github/actions/jira-sync/
   ```
5. **Update [`.github/workflows/jira-sync.yml`](.github/workflows/jira-sync.yml)** — Pass new input from workflow
6. **Add tests** in `tests/`
7. **Create feature branch, PR, and merge**

### Publishing Updates

When updating the action for consumers:

1. Update all files in `.github/actions/jira-sync/`
2. Sync `jira_integration_script.py` to action directory
3. Create a new version tag (e.g., `v1.1.0`)
4. Push tag — publish workflow builds and pushes to GHCR

---

---

## Roo Code Integration

### Jira Manager Skill

A specialized Roo Code skill is available for interactive Jira management. The skill provides access to 10 Jira operations through the `@jira-sync` MCP server.

**Location:** `~/.roo/skills/jira-manager/SKILL.md`

**Available Operations:**
- Search for issues using JQL queries
- Create new Jira issues
- Get issue details and transitions
- Add comments to issues
- Transition issues to new statuses
- Link Jira issues together
- Create subtasks
- Link GitHub PRs to Jira issues
- Change issue status with auto-discovery

**How to Use:**

1. **Explicit Request:**
   ```
   "Use the Jira Manager skill to search for open CLOUD issues"
   ```

2. **Keyword Detection:**
   ```
   "Search for all open CLOUD issues"
   ```

3. **Direct Command:**
   ```
   @jira-sync search_jira_issues project=CLOUD AND status=Open
   ```

**Example Workflows:**

Create and link a PR:
```
"Create a new CLOUD issue and link it to PR #44"
```

Search and update:
```
"Search for open CLOUD issues and add a comment to the first one"
```

### Docker Image

The jira-sync Docker image is published to GitHub Container Registry (GHCR):

**Image:** `ghcr.io/riva-solutions/jira-sync:latest`
**Tags:** `latest`, `v1.0.0`
**Size:** 234MB (50.9MB compressed)

**Pull the image:**
```bash
docker pull ghcr.io/riva-solutions/jira-sync:latest
```

**Run directly:**
```bash
docker run --rm -i \
  -e JIRA_URL="https://cmext.ahrq.gov/jira" \
  -e JIRA_TOKEN="your-token" \
  -e JIRA_PROJECT_KEY="CLOUD" \
  ghcr.io/riva-solutions/jira-sync:latest
```

**Use in GitHub Actions:**
```yaml
- name: Run Jira Sync
  uses: docker://ghcr.io/riva-solutions/jira-sync:latest
  env:
    JIRA_URL: ${{ secrets.JIRA_URL }}
    JIRA_TOKEN: ${{ secrets.JIRA_TOKEN }}
    JIRA_PROJECT_KEY: CLOUD
```

**Use in Docker Compose:**
```yaml
version: '3.8'

services:
  jira-sync:
    image: ghcr.io/riva-solutions/jira-sync:latest
    environment:
      - JIRA_URL=https://cmext.ahrq.gov/jira
      - JIRA_TOKEN=your-token
      - JIRA_PROJECT_KEY=CLOUD
```

### MCP Server Configuration

The jira-sync MCP server is configured in Roo Code's `mcp_settings.json`:

```json
"jira-sync": {
  "command": "docker",
  "args": [
    "run",
    "--rm",
    "-i",
    "-e", "JIRA_URL=https://cmext.ahrq.gov/jira",
    "-e", "JIRA_TOKEN=your-token",
    "-e", "JIRA_PROJECT_KEY=CLOUD",
    "ghcr.io/riva-solutions/jira-sync:latest"
  ],
  "disabled": false,
  "alwaysAllow": [
    "search_jira_issues",
    "get_jira_issue",
    "create_jira_issue",
    "add_jira_comment",
    "list_jira_transitions",
    "transition_jira_issue",
    "link_jira_issues",
    "create_jira_subtask",
    "link_github_pr_remote",
    "change_issue_status"
  ]
}
```

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Jira REST API v2 Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v2/)
- [Jira Remote Issue Links API](https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issue-remote-links/)
- [GitHub Webhook Events](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads)
- [Roo Code Skills Documentation](https://docs.rooveterinary.com/skills)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)

## License

MIT License — See [LICENSE](LICENSE) for details.
