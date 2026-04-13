# **ROO\_CODE\_CONTEXT**

**Cache-Optimized Context Bundle**

Static architecture rules and the repo map are placed first for optimal prompt caching.

Volatile project logs are summarized and placed at the bottom.

## **Table of Contents**

* [Repo Architecture: GOLDEN\_REPO\_MAP.md](https://www.google.com/search?q=%23ref-golden_repo_map-md)  
* [Project Milestones: SESSION\_LOG.md](https://www.google.com/search?q=%23ref-session-log)

## **GOLDEN\_REPO\_MAP.md**

\<a name="ref-golden\_repo\_map-md"\>\</a\>

# **GOLDEN\_REPO\_MAP.md**

## **Automated Directory Map**

jira-sync/  
├── .github/  
│   ├── actions/  
│   │   └── jira-sync/              \# Reusable Docker-based Action  
│   │       ├── Dockerfile  
│   │       ├── action.yml  
│   │       ├── entrypoint.sh  
│   │       ├── jira\_integration\_script.py  
│   │       └── requirements.txt  
│   └── workflows/  
│       ├── jira-sync.yml           \# Main integration workflow  
│       ├── test-published-image.yml  
│       └── verify-jira-access.yml  
├── hooks/                          \# Git hooks for memory management  
│   ├── install-hooks.sh  
│   └── post-commit  
├── .env.example  
├── .gitignore  
├── JENKINS\_DEPLOYMENT\_WORKFLOW\_ANALYSIS.md  \# Critical legacy DevOps context  
├── README.md                       \# Documentation & Quick Start  
├── docker-compose.yml              \# Local testing/dev environment  
└── jira\_integration\_script.py      \# Core REST API Logic (Reference Copy)

## **SESSION\_LOG.md**

\<a name="ref-session-log"\>\</a\>

# **Session Log: Jira Sync Stabilization & Generalization**

**Date:** 2026-04-10

## **Executive Summary: Milestone History**

### **Milestone 1: MCP Migration & Stabilization**

* **Status:** Completed/Aborted  
* **Description:** Attempted to use sooperset/mcp-atlassian MCP server. Identified a critical "silent failure" bug in the upstream comment tool.  
* **Outcome:** Reverted to a pure REST API approach for production stability.

### **Milestone 2: Docker Container Action (CLOUD-1929)**

* **Status:** Completed  
* **Description:** Containerized the Python REST script into a standalone GitHub Action. Published to GHCR for organization-wide reuse.  
* **Outcome:** Reduced startup time by 15x and simplified workflow YAMLs.

### **Milestone 3: Jenkins & GitFlow Alignment**

* **Status:** Completed  
* **Description:** Analyzed your-organization legacy Jenkins pipelines. Mapped "Stage Promotion" (develop/stage branches) and "Production Release" (tags) triggers.  
* **Outcome:** Documented in JENKINS\_DEPLOYMENT\_WORKFLOW\_ANALYSIS.md.

## **Current Focus: Phase 1 \- Dynamic Multi-Project Support**

**Date:** 2026-04-10

**Goal:** Refactor the action to be project-agnostic.

### **Recent Activity**

* **REST Stability Check:** Verified jira\_integration\_script.py is stripped of MCP code.  
* **Primitive Expansion:** Added link\_github\_pr (formal Remote Issue Linking) and transition discovery logic.  
* **Logic Routing:** Refactoring CLI to accept \--transition-on-merge and \--target-branch flags to support different Jenkins-driven flows (your-organizationGOV vs Search-Appliance).

**Status:** Optimized | Lean Context Enabled

**Mode:** Solutions Architect Verified