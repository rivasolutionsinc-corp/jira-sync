# ROO_CODE_CONTEXT.md
**Project:** jira-sync  
**Last Updated:** 2026-04-08  
**Status:** Active Development (ADO-192 Complete)

---

## 1. Project Overview

**jira-sync** is a GitHub to Jira integration automation system designed to synchronize issues, pull requests, and status updates between GitHub repositories and Jira project management instances.

**Key Purpose:**
- Automate Jira issue creation and updates from GitHub events
- Synchronize PR status with Jira issue transitions
- Add automated comments linking GitHub PRs to Jira issues
- Enable seamless workflow between GitHub development and Jira project tracking

**Technology Stack:**
- **Language:** Python 3.x
- **HTTP Client:** `requests` library
- **Authentication:** Bearer token (Personal Access Token)
- **API:** Jira REST API v2 (not v3 - v3 requires OAuth2)

---

## 2. Git Workflow & Branch Strategy

**Current Branch:** `feature/ADO-192` (tracking `origin/feature/ADO-192`)

**Workflow Pattern:**
1. Create feature branch from `main` branch
2. Implement changes and commit to feature branch
3. Create Pull Request (PR) linking to Jira issue
4. Add Jira comment with PR link
5. Transition Jira issue status to reflect PR state
6. Merge PR after review

**ADO-192 Session Execution:**
- ✅ Feature branch created: `feature/ADO-192`
- ✅ Test commit pushed to feature branch
- ✅ PR #2 created linking to ADO-192
- ✅ Jira comment added with PR reference
- ✅ Jira issue transitioned to "Start Review"

---

## 3. Jira Integration Details

### Base Configuration
- **Jira Base URL:** `https://cmext.ahrq.gov/jira`
- **API Endpoint:** `{JIRA_URL}/rest/api/2/`
- **Authentication Method:** Bearer Token (PAT)
- **Token Storage:** `config/.env` file as `JIRA_TOKEN` environment variable

### API Version Constraints
- **Active Version:** REST API v2
- **Why Not v3:** REST API v3 requires OAuth2 authentication flow, which is more complex than Bearer token auth
- **Recommendation:** Continue using v2 for current implementation

### Authentication Headers
```python
headers = {
    "Authorization": f"Bearer {JIRA_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}
```

### Available Jira Transitions
**Discovered Transitions for Current Project:**
- `"Stop Progress"` - Pause work on issue
- `"On Hold"` - Place issue on hold
- `"Start Review"` - Move issue to review state (used in ADO-192)

**Note:** `"In Review"` is NOT available as a transition name; use `"Start Review"` instead.

**Transition Discovery Method:**
The [`change_issue_status()`](#key-scripts) function queries available transitions dynamically:
```
GET /rest/api/2/issue/{issue_key}/transitions
```
This returns all valid transitions for the current issue state.

---

## 4. Key Scripts & Functions

### File: [`jira_integration_script.py`](jira_integration_script.py)

#### `add_comment(issue_key, comment_body)`
**Purpose:** Add a comment to an existing Jira issue

**Parameters:**
- `issue_key` (str): Jira issue identifier (e.g., "ADO-192")
- `comment_body` (str): Comment text to add

**Endpoint:** `POST /rest/api/2/issue/{issue_key}/comment`

**Success Response:** HTTP 201 Created

**Usage Example:**
```python
add_comment("ADO-192", "PR #2 created: https://github.com/repo/pull/2")
```

---

#### `change_issue_status(issue_key, transition_name)`
**Purpose:** Transition a Jira issue to a new status

**Parameters:**
- `issue_key` (str): Jira issue identifier (e.g., "ADO-192")
- `transition_name` (str): Name of the transition (case-insensitive)

**Process:**
1. Query available transitions: `GET /rest/api/2/issue/{issue_key}/transitions`
2. Match transition name to transition ID
3. Execute transition: `POST /rest/api/2/issue/{issue_key}/transitions`

**Success Response:** HTTP 204 No Content

**Error Handling:** If transition not found, prints available transitions and returns `False`

**Usage Example:**
```python
change_issue_status("ADO-192", "Start Review")
```

---

#### `get_issue_details(issue_key)`
**Purpose:** Retrieve full details of a Jira issue

**Returns Dictionary:**
- `key`: Issue identifier
- `summary`: Issue title
- `description`: Issue description
- `status`: Current status name
- `assignee`: Assigned user display name
- `created`: Creation timestamp
- `updated`: Last update timestamp
- `issue_type`: Type (Task, Bug, Story, etc.)
- `priority`: Priority level

**Endpoint:** `GET /rest/api/2/issue/{issue_key}`

---

#### `create_jira_issue(project_key, summary, description, issue_type="Task")`
**Purpose:** Create a new Jira issue

**Parameters:**
- `project_key` (str): Project key (e.g., "AQD")
- `summary` (str): Issue title
- `description` (str): Issue description
- `issue_type` (str): Type of issue (default: "Task")

**Success Response:** HTTP 201 Created, returns issue key

---

## 5. Session Log: ADO-192 Task Execution

**Date:** 2026-04-08  
**Branch:** `feature/ADO-192`  
**Status:** ✅ Complete

### Execution Steps

1. **Feature Branch Creation**
   - Created `feature/ADO-192` from `main` branch
   - Branch tracking: `origin/feature/ADO-192`

2. **Test Commit**
   - Committed test changes to feature branch
   - Verified branch is ahead of main

3. **Pull Request Creation**
   - Created PR #2 linking to ADO-192 Jira issue
   - PR title includes Jira issue reference

4. **Jira Comment Addition**
   - Called `add_comment("ADO-192", "PR #2 created...")`
   - Successfully added GitHub PR link to Jira issue
   - Response: HTTP 201 Created

5. **Status Transition**
   - Called `change_issue_status("ADO-192", "Start Review")`
   - Successfully transitioned issue from previous state to "Start Review"
   - Response: HTTP 204 No Content

### Learnings & Constraints Discovered

- ✅ Bearer token authentication works correctly with REST API v2
- ✅ Transition names are case-insensitive in the matching logic
- ⚠️ Transition name `"In Review"` does NOT exist; use `"Start Review"` instead
- ✅ Comments can include markdown and external links (GitHub URLs)
- ✅ Dynamic transition discovery prevents hardcoding invalid transitions

---

## 6. Architecture Notes

### Authentication Flow
```
Environment Variable (JIRA_TOKEN)
    ↓
Bearer Token Header
    ↓
Jira REST API v2 Endpoint
    ↓
Response (JSON)
```

### Error Handling Pattern
All functions follow consistent error handling:
1. Check HTTP status code
2. Print error message with status code
3. Print response body for debugging
4. Return `None` or `False` on failure

### API Response Patterns

**Success Responses:**
- `201 Created` - Issue/comment created
- `204 No Content` - Transition successful
- `200 OK` - GET requests successful

**Error Responses:**
- `400 Bad Request` - Invalid payload
- `401 Unauthorized` - Invalid/expired token
- `404 Not Found` - Issue/transition not found
- `500 Server Error` - Jira server error

### Security Considerations
- ✅ Token stored in environment variable (not hardcoded)
- ✅ `.env` file should be in `.gitignore`
- ✅ Bearer token provides API-level authentication
- ⚠️ No rate limiting implemented (consider adding for production)

---

## 7. Configuration Files

### `config/.env`
```
JIRA_TOKEN=<your_personal_access_token>
```

**Security:** This file is git-ignored and should never be committed.

---

## 8. Next Steps & Recommendations

1. **Implement GitHub Webhook Integration**
   - Listen for PR events from GitHub
   - Automatically trigger Jira updates

2. **Add Rate Limiting**
   - Implement exponential backoff for API calls
   - Respect Jira API rate limits

3. **Enhance Error Logging**
   - Add structured logging (JSON format)
   - Log all API calls for audit trail

4. **Create Integration Tests**
   - Test against staging Jira instance
   - Validate all transition paths

5. **Document Jira Project Configuration**
   - Map all available transitions per issue type
   - Document custom fields if used

---

## 9. Related Files

- [`jira_integration_script.py`](jira_integration_script.py) - Main integration script
- [`test_jira_issue.py`](test_jira_issue.py) - Test suite
- [`config/.env`](config/.env) - Environment configuration
- [`ADO-192-test.md`](ADO-192-test.md) - ADO-192 test documentation

---

**Document Version:** 1.0  
**Last Reviewed:** 2026-04-08  
**Maintainer:** Documentation Writer Mode
