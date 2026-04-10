#!/bin/bash
set -euo pipefail

echo "::group::Jira Sync Action"
echo "Event:   $EVENT_NAME"
echo "Project: $PROJECT_KEY"
echo "::endgroup::"

# Use JIRA_PERSONAL_TOKEN if available, otherwise fall back to JIRA_TOKEN
JIRA_TOKEN_VALUE="${JIRA_PERSONAL_TOKEN:-${JIRA_TOKEN:-}}"

python /action/jira_integration_script.py \
   --event-name    "$EVENT_NAME" \
   --jira-url      "$JIRA_URL" \
   --jira-token    "$JIRA_TOKEN_VALUE" \
   --project-key   "$PROJECT_KEY" \
   --issue-title   "${ISSUE_TITLE:-}" \
   --issue-url     "${ISSUE_URL:-}" \
   --pr-branch     "${PR_BRANCH:-}" \
   --pr-url        "${PR_URL:-}" \
   --issue-type    "${ISSUE_TYPE:-Task}"
