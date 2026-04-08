# GitHub Secret Setup Instructions

## Creating JIRA_PROJECT_KEY Secret

### Method 1: GitHub Web UI (Recommended)

1. **Navigate to Repository Settings:**
   - Go to: https://github.com/rivasolutionsinc-corp/jira-sync
   - Click on **Settings** tab
   - Click on **Secrets and variables** → **Actions** (left sidebar)

2. **Create New Secret:**
   - Click **New repository secret** button
   - **Name:** `JIRA_PROJECT_KEY`
   - **Value:** `CLOUD` (or your desired Jira project key)
   - Click **Add secret**

3. **Verify:**
   - You should see `JIRA_PROJECT_KEY` listed under "Repository secrets"
   - The value is encrypted and hidden

### Method 2: GitHub CLI

```bash
# Install GitHub CLI if not already installed
# https://cli.github.com/

# Authenticate with GitHub
gh auth login

# Create the secret
gh secret set JIRA_PROJECT_KEY --body "CLOUD" --repo rivasolutionsinc-corp/jira-sync

# Verify the secret was created
gh secret list --repo rivasolutionsinc-corp/jira-sync
```

### Method 3: Using curl (Advanced)

```bash
# Requires: GitHub Personal Access Token with 'repo' scope
# Set your token as environment variable
export GITHUB_TOKEN="your_personal_access_token"

# Create the secret
curl -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+raw" \
  -d '{"encrypted_value":"CLOUD"}' \
  https://api.github.com/repos/rivasolutionsinc-corp/jira-sync/actions/secrets/JIRA_PROJECT_KEY
```

---

## Secret Configuration Options

### Option A: Single Project (CLOUD)
```
JIRA_PROJECT_KEY = CLOUD
```
- All GitHub issues created in CLOUD project
- PRs and pushes still extract project from branch name

### Option B: Default to AQD (Backward Compatible)
```
JIRA_PROJECT_KEY = AQD
```
- All GitHub issues created in AQD project (default behavior)
- PRs and pushes still extract project from branch name

### Option C: Leave Unset (Use Default)
- Do not create the secret
- System automatically defaults to AQD
- PRs and pushes still extract project from branch name

---

## Verification

After creating the secret, verify it works by:

1. **Create a test PR from `feature/CLOUD-9999` branch:**
   ```bash
   git checkout -b feature/CLOUD-9999
   git push origin feature/CLOUD-9999
   ```

2. **Open a Pull Request on GitHub**
   - The workflow should trigger
   - Check workflow logs to verify JIRA_PROJECT_KEY is being used

3. **Check Jira:**
   - Verify subtask was created in CLOUD project
   - Verify issue key starts with CLOUD (e.g., CLOUD-9999-1)

---

## Troubleshooting

### Secret Not Found Error
- Verify secret name is exactly: `JIRA_PROJECT_KEY`
- Check that you're in the correct repository
- Secrets are case-sensitive

### Workflow Still Uses AQD
- Verify the secret was created successfully
- Check workflow logs for the actual value being used
- Secrets may take a few seconds to propagate

### Permission Denied
- Ensure you have admin access to the repository
- For GitHub CLI, verify authentication with `gh auth status`

---

## Security Notes

- Secrets are encrypted at rest and in transit
- Secrets are never logged in workflow output
- Only repository admins can view/manage secrets
- Secrets are not available to pull requests from forks (by default)

---

## Next Steps

1. Create the `JIRA_PROJECT_KEY` secret with value `CLOUD`
2. Create a test PR from `feature/CLOUD-9999` branch
3. Verify workflow triggers and creates Jira subtask in CLOUD project
4. Merge `feature/advanced-jira-ci` to `main` after testing
