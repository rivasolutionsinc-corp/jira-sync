#!/bin/bash
set -euo pipefail

echo "::group::Jira Sync Action"
echo "Event:   $EVENT_NAME"
echo "Project: $PROJECT_KEY"
echo "::endgroup::"

# Find jira_integration_script.py in action directory or parent directories
SCRIPT_PATH="/action/jira_integration_script.py"
if [ ! -f "$SCRIPT_PATH" ]; then
  # Try parent directory (for GitHub Actions context)
  SCRIPT_PATH="/jira_integration_script.py"
fi

if [ ! -f "$SCRIPT_PATH" ]; then
  echo "ERROR: jira_integration_script.py not found"
  exit 1
fi

python "$SCRIPT_PATH" \
  --event-name    "$EVENT_NAME" \
  --jira-url      "$JIRA_URL" \
  --jira-token    "$JIRA_TOKEN" \
  --project-key   "$PROJECT_KEY" \
  --issue-title   "${ISSUE_TITLE:-}" \
  --issue-url     "${ISSUE_URL:-}" \
  --pr-branch     "${PR_BRANCH:-}" \
  --pr-url        "${PR_URL:-}"
