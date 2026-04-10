#!/bin/bash
set -euo pipefail

echo "::group::Jira Sync Action"
echo "Event:   $EVENT_NAME"
echo "Project: $PROJECT_KEY"
echo "::endgroup::"

python /action/jira_integration_script.py \
   --event-name    "$EVENT_NAME" \
   --jira-url      "$JIRA_URL" \
   --jira-token    "${JIRA_PERSONAL_TOKEN:-$JIRA_TOKEN}" \
   --project-key   "$PROJECT_KEY" \
   --issue-title   "${ISSUE_TITLE:-}" \
   --issue-url     "${ISSUE_URL:-}" \
   --pr-branch     "${PR_BRANCH:-}" \
   --pr-url        "${PR_URL:-}" \
   --issue-type    "${ISSUE_TYPE:-Task}"
