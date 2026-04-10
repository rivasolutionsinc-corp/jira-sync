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
PR_ACTION="${11:-}"
PR_MERGED="${12:-}"
TRANSITION_OPENED="${13:-}"
TRANSITION_MERGED="${14:-}"
LINK_TITLE="${15:-}"
PUSH_BRANCH="${16:-}"
TARGET_BRANCH="${17:-}"
TRANSITION_TAG="${18:-}"
DEPLOYMENT_STAGE="${19:-}"
DEPLOYMENT_BRANCH="${20:-}"
TAG_NAME="${21:-}"
TAG_REF="${22:-}"
DEPLOYMENT_TAG="${23:-}"

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
   --issue-type    "$ISSUE_TYPE" \
   --pr-action     "$PR_ACTION" \
   --pr-merged     "$PR_MERGED" \
   --transition-opened "$TRANSITION_OPENED" \
   --transition-merged "$TRANSITION_MERGED" \
   --link-title    "$LINK_TITLE" \
   --push-branch   "$PUSH_BRANCH" \
   --target-branch "$TARGET_BRANCH" \
   --transition-tag "$TRANSITION_TAG" \
   --deployment-stage "$DEPLOYMENT_STAGE" \
   --deployment-branch "$DEPLOYMENT_BRANCH" \
   --tag-name      "$TAG_NAME" \
   --tag-ref       "$TAG_REF" \
   --deployment-tag "$DEPLOYMENT_TAG"
