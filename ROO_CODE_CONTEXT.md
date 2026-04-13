# **ROO\_CODE\_CONTEXT**

**Cache-Optimized Context Bundle**

Static architecture rules and the repo map are placed first for optimal prompt caching.

Volatile project logs are summarized and placed at the bottom.

---

## **Table of Contents**

* [Repo Architecture: GOLDEN\_REPO\_MAP](#ref-golden-repo-map)
* [Architecture Decision Records: ADRs](#ref-adrs)
* [Project Milestones: SESSION\_LOG](#ref-session-log)

---

## **GOLDEN\_REPO\_MAP**

<a name="ref-golden-repo-map"></a>

```
jira-sync/
├── .github/
│   ├── actions/
│   │   └── jira-sync/              # Reusable Docker-based Action (self-contained)
│   │       ├── Dockerfile
│   │       ├── action.yml          # Action manifest — defines all inputs/outputs
│   │       ├── entrypoint.sh       # Maps action inputs → Python CLI args
│   │       ├── jira_integration_script.py  # BUNDLED copy (must stay in sync with root)
│   │       └── requirements.txt
│   └── workflows/
│       ├── jira-sync.yml           # Main integration workflow (public-release hardened)
│       ├── test-published-image.yml
│       └── verify-jira-access.yml
├── hooks/                          # Git hooks for AI memory management
│   ├── install-hooks.sh
│   ├── post-commit
│   └── README.md
├── tests/
│   ├── test_jira_lifecycle_automation.py
│   ├── test_phase1_generalization.py
│   ├── test_phase2_production_hardening.py
│   └── test_phase3_deployment_orchestration.py
├── config/
├── .env.example
├── .gitignore
├── docker-compose.yml              # Local testing/dev environment
├── jira_integration_script.py      # Core REST API Logic (ROOT reference copy)
├── README.md                       # Documentation & Quick Start
└── ROO_CODE_CONTEXT.md             # This file
```

---

## **ARCHITECTURE DECISION RECORDS**

<a name="ref-adrs"></a>

### **ADR-001: Pure REST API over MCP**
- **Decision:** Use direct Jira REST API calls via `requests` library
- **Rationale:** Upstream `sooperset/mcp-atlassian` had a silent failure bug in the comment tool
- **Status:** Accepted | Implemented

### **ADR-002: Docker Container Action over Composite**
- **Decision:** Use `runs.using: docker` with a local `Dockerfile`
- **Rationale:** 8–24x faster startup; stateless; self-contained; no dependency on runner environment
- **Status:** Accepted | Implemented

### **ADR-003: Bundled Script in Action Directory**
- **Decision:** `jira_integration_script.py` must exist in BOTH the root AND `.github/actions/jira-sync/`
- **Rationale:** Docker `COPY` instruction requires the file to be in the build context (action directory)
- **Constraint:** When updating the root script, always run `cp jira_integration_script.py .github/actions/jira-sync/`
- **Status:** Accepted | Implemented

### **ADR-004: Dynamic State Mapping via Workflow Inputs**
- **Decision:** Transition names are passed as workflow inputs, not hardcoded in the script
- **Rationale:** Enables multi-project, multi-organization reuse without forking
- **Pattern:**
  - `transition-on-open` → default `In Review`
  - `transition-on-merge` → `In QA` (stage) or `Done` (main) via expression
  - `transition-on-tag` → default `Deployed`
- **Status:** Accepted | Implemented

### **ADR-005: Public Release Hardening**
- **Decision:** Replace all hardcoded org-specific values with GitHub Secrets
- **Rationale:** Repository is being sanitized for public distribution
- **Changes:** `jira-url` → `secrets.JIRA_URL`; `project-key` → `secrets.JIRA_PROJECT_KEY`; `jira-token` → `secrets.JIRA_TOKEN`
- **Status:** Accepted | Implemented on `feature/public-release-workflow-hardening`

---

## **KEY FILE CONTRACTS**

### **`jira_integration_script.py` — CLI Interface**

**Required arguments:**
```
--event-name        {issues, pull_request, push, create}
--jira-url          Jira instance base URL
--jira-token        Bearer token for authentication
--project-key       Jira project key (e.g., PROJ)
```

**New arguments (Phase 3 / Public Release):**
```
--event-action      GitHub event action (opened, closed, synchronize, created)
--is-merged         Flag: PR was merged (store_true)
--transition-on-open    Jira transition when PR/Issue opened (default: "In Review")
--transition-on-merge   Jira transition when PR merged (default: "Done")
--transition-on-tag     Jira transition when tag created (default: "Deployed")
```

**Legacy arguments (preserved for backward compatibility):**
```
--pr-action         {opened, synchronize, closed}
--pr-merged         Flag: PR was merged (store_true, alias for --is-merged)
--transition-opened Alias for --transition-on-open
--transition-merged Alias for --transition-on-merge
--transition-tag    Alias for --transition-on-tag
--target-branch     Branch for push event matching
--push-branch       Branch name for push events
--tag-name          Tag name for create events
--tag-ref           Reference branch for tag
--link-title        Custom title for GitHub PR remote links
--issue-type        Jira issue type (default: Task)
```

### **`action.yml` — Input/Output Contract**

**Required inputs:** `jira-url`, `jira-token`, `project-key`, `event-name`

**Key optional inputs with defaults:**
```yaml
event-action:       default: 'created'
is-merged:          default: 'false'
transition-on-open: default: 'In Review'
transition-on-merge: default: 'Done'
transition-on-tag:  default: 'Deployed'
target-branch:      default: 'main'
link-title:         default: 'GitHub PR'
issue-type:         default: 'Task'
```

### **`entrypoint.sh` — Positional Argument Mapping**

```
$1  = JIRA_URL
$2  = JIRA_TOKEN
$3  = PROJECT_KEY
$4  = EVENT_NAME
$5  = EVENT_ACTION
$6  = ISSUE_TITLE
$7  = ISSUE_URL
$8  = PR_BRANCH
$9  = PR_URL
$10 = ISSUE_TYPE
$11 = IS_MERGED
$12 = TRANSITION_ON_OPEN
$13 = TRANSITION_ON_MERGE
$14 = TRANSITION_ON_TAG
$15 = LINK_TITLE
```

### **`jira-sync.yml` — Workflow Trigger Map**

| Event | Condition | Jira Action |
|-------|-----------|-------------|
| `issues: opened` | Always | Create Jira Task |
| `pull_request: opened` | Branch has Jira key | Comment + Remote Link + Transition `transition-on-open` |
| `pull_request: synchronize` | Branch has Jira key | Update Remote Link |
| `pull_request: closed` + merged | Branch has Jira key | Transition `transition-on-merge` |
| `create` + `ref_type == tag` | Tag has Jira key | Comment + Transition `transition-on-tag` |

---

## **SESSION\_LOG**

<a name="ref-session-log"></a>

### **Session: 2026-04-13 — Public Release Hardening**

**Branch:** `feature/public-release-workflow-hardening`
**Base:** `feature/sanitize-repo-for-public-use`

**Commits:**
- `035efc8` — feat: harden jira-sync workflow for public release
- `e321e03` — feat: update action manifest and entrypoint for new workflow inputs
- `d77086a` — chore: copy jira_integration_script.py to action directory
- `ddf3477` — feat: add new CLI arguments for public release workflow
- `684bc07` — chore: update jira_integration_script.py in action directory with new CLI arguments

**Changes Made:**
1. **`jira-sync.yml`** — Replaced hardcoded `jira-url` and `project-key` with secrets; added `workflow_dispatch` trigger; added Debug Event Context step
2. **`action.yml`** — Added `jira-token`, `event-action`, `is-merged`, `transition-on-open`, `transition-on-merge`, `transition-on-tag` inputs
3. **`entrypoint.sh`** — Simplified from 23 to 15 positional args; mapped new inputs
4. **`jira_integration_script.py`** — Added `--event-action`, `--is-merged`, `--transition-on-open`, `--transition-on-merge`, `--transition-on-tag` CLI arguments; updated event handlers to use new args with fallback to legacy args
5. **`README.md`** — Full rewrite to reflect public-release state, all phases, CLI reference, action inputs table

---

### **Session: 2026-04-10 — Phase 1-3 Implementation**

**Milestones Completed:**

| Milestone | Ticket | Status |
|-----------|--------|--------|
| MCP Migration & Stabilization | — | Completed/Reverted |
| Docker Container Action | CLOUD-1929 | ✅ Completed |
| Jenkins & GitFlow Alignment | CLOUD-1962 | ✅ Completed |
| Phase 1: Dynamic Multi-Project Support | CLOUD-1959 | ✅ Completed |
| Phase 2: Production Hardening | CLOUD-1961 | ✅ Completed |
| Phase 3: Deployment Orchestration | CLOUD-1962 | ✅ Completed |

**Key Outcomes:**
- Pure REST API with `requests` library (no MCP)
- 52 unit tests, 100% pass rate
- GitFlow/Jenkins lifecycle fully mapped
- `--transition-on-merge`, `--target-branch`, `--is-merged` flags implemented
- Remote Issue Linking via `/remotelink` API
- Transition discovery and validation logic

---

## **CRITICAL CONSTRAINTS**

1. **ALWAYS sync the script:** After editing `jira_integration_script.py`, run:
   ```bash
   cp jira_integration_script.py .github/actions/jira-sync/
   ```

2. **NEVER hardcode org values:** All Jira URLs, project keys, and tokens must come from GitHub Secrets.

3. **BACKWARD COMPATIBILITY:** New CLI arguments must have defaults. Legacy `--transition-opened`, `--transition-merged`, `--transition-tag` must continue to work.

4. **BRANCH GUARD:** The `create` event job condition `github.event_name != 'create' || github.event.ref_type == 'tag'` prevents spurious runs on branch creation. Do not remove it.

5. **JIRA KEY EXTRACTION:** The regex `([A-Z][A-Z0-9_]+-\d+)` extracts keys from branch/tag names. Branches not matching are skipped gracefully (not an error).

---

**Status:** Optimized | Public Release Ready
**Mode:** Knowledge Architect Verified
**Last Updated:** 2026-04-13
