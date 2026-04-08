# **Project Context: Jira & Drupal Workflow Automation**

## **🎯 Purpose**

This project automates the lifecycle between GitHub and a self-hosted Jira instance (cmext.ahrq.gov/jira) for the AHRQ Drupal ecosystem. It enforces a multi-agent architecture where planning, coding, and DevOps are strictly separated.

## **🛠️ Architecture & Tech Stack**

* **Primary CMS:** Drupal (AHRQ Government instances)  
* **Infrastructure:** Self-hosted Jira (Apache/Tomcat) \+ GitHub Actions  
* **Automation:** Python-based Jira REST API integrations (using PAT)  
* **AI Strategy:** Roo Code Multi-Agent System (Orchestrator, Documentation, Code, Git Ops)

## **🤖 Multi-Agent Boundaries**

* **Orchestrator:** High-level planning and architecture only. **Forbidden** from writing files.  
* **Documentation Writer:** Standardizes logs and ADRs in ./.ai-memory/.  
* **Code (Drupal Builder):** Implements logic, hooks, and services. **Forbidden** from Git operations.  
* **Git Ops:** Manages branching and commits via structured MCP tools. **Forbidden** from committing to main/master/develop.

## **📡 Jira Integration Protocol**

* **Base URL:** https://cmext.ahrq.gov/jira  
* **Authentication:** Personal Access Token (PAT) via Bearer Header.  
* **GitHub Secrets:** JIRA\_TOKEN (The PAT).  
* **Branch Naming:** feature/PROJECT-ID (e.g., feature/AQD-1234).  
* **Automation Flow:**  
  1. GitHub Issue Opened \-\> jira\_automation.yml \-\> create\_ticket.py \-\> New Jira Task.  
  2. GitHub Push \-\> Extract Key from Branch \-\> Add comment to Jira ticket.

## **📜 Key Files**

* create\_ticket.py: Core API client for Jira REST v2.  
* jira\_automation.yml: CI/CD pipeline orchestration.  
* ./.ai-memory/: Ephemeral session memory for agent handoffs.

## **🚦 Operational Constraints (DSI)**

* **Authentication:** Always read mcp\_settings.json to initialize the AnythingLLM brain. No hallucinations allowed.  
* **Git Safety:** Always check the current branch during Pre-Flight. If on a default branch, switch to Git Ops to branch out immediately.  
* **Drupal Standards:** \- PSR-4 namespacing.  
  * Business logic in Services, not .module files.  
  * Dependency Injection is mandatory.

## **📋 Session Log Template**

All agents must log their progress in ./.ai-memory/session\_log.md using:

1. **Context:** What ticket are we on?  
2. **Action:** What is being done right now?  
3. **Next Step:** What is required from the next agent in the chain?