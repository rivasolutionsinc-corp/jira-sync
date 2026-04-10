#!/bin/bash
set -eo pipefail

# GitHub Actions passes inputs as positional arguments to the Docker container
JIRA_URL="$1"
JIRA_USERNAME="$2"
JIRA_PERSONAL_TOKEN="$3"
PROJECT_KEY="$4"
EVENT_NAME="$5"
ISSUE_TITLE="${6:-}"
ISSUE_URL="${7:-}"
PR_BRANCH="${8:-}"
PR_URL="${9:-}"
ISSUE_TYPE="${10:-Task}"

echo "::group::Jira Sync Action"
echo "Event:   $EVENT_NAME"
echo "Project: $PROJECT_KEY"
echo "::endgroup::"

python /action/jira_integration_script.py \
   --event-name    "$EVENT_NAME" \
   --jira-url      "$JIRA_URL" \
   --jira-token    "$JIRA_PERSONAL_TOKEN" \
   --project-key   "$PROJECT_KEY" \
   --issue-title   "$ISSUE_TITLE" \
   --issue-url     "$ISSUE_URL" \
   --pr-branch     "$PR_BRANCH" \
   --pr-url        "$PR_URL" \
   --issue-type    "$ISSUE_TYPE"
