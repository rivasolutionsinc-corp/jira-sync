#!/bin/bash
set -euo pipefail

echo "::group::Jira Sync Action"
echo "Event:   $EVENT_NAME"
echo "Project: $PROJECT_KEY"
echo "::endgroup::"

cd /action
python -m jira_integration_script \
  --event-name    "$EVENT_NAME" \
  --jira-url      "$JIRA_URL" \
  --jira-token    "$JIRA_TOKEN" \
  --project-key   "$PROJECT_KEY" \
  --issue-title   "${ISSUE_TITLE:-}" \
  --issue-url     "${ISSUE_URL:-}" \
  --pr-branch     "${PR_BRANCH:-}" \
  --pr-url        "${PR_URL:-}"
