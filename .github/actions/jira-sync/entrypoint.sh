#!/bin/bash
set -euo pipefail

echo "::group::Jira Sync Action"
echo "Event:   ${INPUT_EVENT_NAME:-}"
echo "Project: ${INPUT_PROJECT_KEY:-}"
echo "::endgroup::"

# GitHub Actions converts input names with hyphens to environment variables with underscores
# e.g., jira-url becomes INPUT_JIRA_URL
JIRA_TOKEN_VALUE="${INPUT_JIRA_PERSONAL_TOKEN:-${INPUT_JIRA_TOKEN:-}}"

python /action/jira_integration_script.py \
   --event-name    "${INPUT_EVENT_NAME}" \
   --jira-url      "${INPUT_JIRA_URL}" \
   --jira-token    "${JIRA_TOKEN_VALUE}" \
   --project-key   "${INPUT_PROJECT_KEY}" \
   --issue-title   "${INPUT_ISSUE_TITLE:-}" \
   --issue-url     "${INPUT_ISSUE_URL:-}" \
   --pr-branch     "${INPUT_PR_BRANCH:-}" \
   --pr-url        "${INPUT_PR_URL:-}" \
   --issue-type    "${INPUT_ISSUE_TYPE:-Task}"
