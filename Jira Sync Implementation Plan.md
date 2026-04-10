# **Priority Implementation Plan: Jira & GitHub Sync**

**Target:** Local AI Orchestrator Agent

**Context:** This project synchronizes GitHub events to a self-hosted Jira Data Center instance (cmext.ahrq.gov). The primary router logic in jira\_integration\_script.py is complete. Please execute the following phases in order.

## **Phase 1: Security & Robustness (Immediate)**

**Goal:** Prevent sensitive internal AHRQ network data from leaking in GitHub Actions logs and ensure CI/CD fails appropriately on API errors.

**Tasks for AI:**

1. **Sanitize Error Logging:** Open jira\_integration\_script.py. Locate all instances where a failed REST API call logs the raw response (e.g., print(response.text) or print(f"Response: {response.text}")). Replace these with sanitized error messages that log the HTTP status code and a generic failure reason, without dumping the raw HTML/JSON response payload which could expose network topology.  
2. **Verify Exit States:** Confirm that all functions (create\_jira\_issue, add\_comment, etc.) consistently return False or None on failure, ensuring the sys.exit(1) in the \_\_main\_\_ block is reliably triggered.

## **Phase 2: Dynamic Issue Types (Short-Term)**

**Goal:** Hardcoding "Task" causes failures in Jira instances with custom schemas. We need to pass the issue type dynamically.

**Tasks for AI:**

1. **Update Action Definition:** Open .github/actions/jira-sync/action.yml. Add a new input named issue-type with a description "Jira Issue Type (e.g., Task, Story, Bug)" and a default value of 'Task'. Pass this to the environment as ISSUE\_TYPE: ${{ inputs.issue-type }}.  
2. **Update Entrypoint:** Open .github/actions/jira-sync/entrypoint.sh. Add \--issue-type "${ISSUE\_TYPE:-Task}" \\ to the python execution arguments.  
3. **Update Python Router:** Open jira\_integration\_script.py.  
   * Add parser.add\_argument("--issue-type", default="Task") to the argparse configuration.  
   * Update the create\_jira\_issue call in the issues event block to pass issue\_type=args.issue\_type.

## **Phase 3: Architectural Alignment (Medium-Term)**

**Goal:** The Python script attempts to import mcp\_client.atlassian\_mcp, but this dependency does not exist in requirements.txt or the Dockerfile. We must explicitly define our container strategy.

**Tasks for AI:**

*Evaluate the workspace and implement ONE of the following solutions (Ask the user for preference if unsure):*

**Option A (Fix Current Custom Python Action):**

1. Identify the correct pip package for mcp\_client (e.g., standard MCP SDK packages).  
2. Update .github/actions/jira-sync/requirements.txt to include the required MCP dependencies.  
3. Ensure the Dockerfile correctly installs them so MCP\_AVAILABLE evaluates to True.

**Option B (Adopt the Sooperset Image \- Recommended):**

1. Notice that docker-compose.yml already utilizes ghcr.io/sooperset/mcp-atlassian:latest.  
2. Refactor .github/actions/jira-sync/action.yml to use docker://ghcr.io/sooperset/mcp-atlassian:latest directly instead of building the custom Python Dockerfile.  
3. Map the inputs directly to the CLI commands expected by the sooperset MCP image, effectively deprecating the custom Python script entirely to reduce maintenance overhead.