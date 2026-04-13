#!/bin/bash
set -eo pipefail

# GitHub Actions passes inputs as positional arguments to the Docker container
JIRA_URL="$1"
JIRA_TOKEN="$2"
PROJECT_KEY="$3"
EVENT_NAME="$4"
EVENT_ACTION="${5:-created}"
ISSUE_TITLE="${6:-}"
ISSUE_URL="${7:-}"
PR_BRANCH="${8:-}"
PR_URL="${9:-}"
ISSUE_TYPE="${10:-Task}"
IS_MERGED="${11:-false}"
TRANSITION_ON_OPEN="${12:-In Review}"
TRANSITION_ON_MERGE="${13:-Done}"
TRANSITION_ON_TAG="${14:-Deployed}"
LINK_TITLE="${15:-GitHub PR}"

echo "::group::Jira Sync Action"
echo "Event:   $EVENT_NAME"
echo "Action:  $EVENT_ACTION"
echo "Project: $PROJECT_KEY"
echo "::endgroup::"

# Build command with optional arguments
CMD="python /action/jira_integration_script.py"
CMD="$CMD --event-name '$EVENT_NAME'"
CMD="$CMD --jira-url '$JIRA_URL'"
CMD="$CMD --jira-token '$JIRA_TOKEN'"
CMD="$CMD --project-key '$PROJECT_KEY'"

# Add optional arguments only if they have values
[ -n "$EVENT_ACTION" ] && CMD="$CMD --event-action '$EVENT_ACTION'"
[ -n "$ISSUE_TITLE" ] && CMD="$CMD --issue-title '$ISSUE_TITLE'"
[ -n "$ISSUE_URL" ] && CMD="$CMD --issue-url '$ISSUE_URL'"
[ -n "$PR_BRANCH" ] && CMD="$CMD --pr-branch '$PR_BRANCH'"
[ -n "$PR_URL" ] && CMD="$CMD --pr-url '$PR_URL'"
[ -n "$ISSUE_TYPE" ] && CMD="$CMD --issue-type '$ISSUE_TYPE'"
[ "$IS_MERGED" = "true" ] && CMD="$CMD --is-merged"
[ -n "$TRANSITION_ON_OPEN" ] && CMD="$CMD --transition-on-open '$TRANSITION_ON_OPEN'"
[ -n "$TRANSITION_ON_MERGE" ] && CMD="$CMD --transition-on-merge '$TRANSITION_ON_MERGE'"
[ -n "$TRANSITION_ON_TAG" ] && CMD="$CMD --transition-on-tag '$TRANSITION_ON_TAG'"
[ -n "$LINK_TITLE" ] && CMD="$CMD --link-title '$LINK_TITLE'"

eval "$CMD"
