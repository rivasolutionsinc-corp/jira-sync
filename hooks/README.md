# Git Hooks

This directory contains Git hooks for the jira-sync project.

## Available Hooks

### post-commit
Automatically updates memory bank documentation after each commit:
- Updates `MEMORY_BANK_INDEX.md` with latest commit timestamp and branch
- Logs commit details to `SESSION_LOG.md`
- Migrates task-specific documentation to Roo Memory
- Triggers AI context bundler for instant memory updates

## Installation

Run the installation script from the project root:

```bash
bash hooks/install-hooks.sh
```

This will copy all hooks from this directory into `.git/hooks/` and make them executable.

## Manual Installation

If you prefer to install manually:

```bash
cp hooks/post-commit .git/hooks/post-commit
chmod +x .git/hooks/post-commit
```

## Hook Details

#### post-commit
- **Trigger:** After every successful commit
- **Dependencies:** 
  - `~/Documents/Roo_Memory/{PROJECT_NAME}/` directory must exist
  - Optional: `.roo/auto-sync-memory.sh` script
  - Optional: `docs/` directory with documentation files
- **Behavior:**
  - Silently exits if Roo Memory directory doesn't exist
  - Updates memory bank metadata (timestamp, branch)
  - Logs commit hash, message, and changed files
  - Migrates documentation matching specific patterns
  - Runs auto-sync script in background if available

## Troubleshooting

If hooks are not executing:

1. Verify they are executable: `ls -la .git/hooks/`
2. Check file permissions: `chmod +x .git/hooks/post-commit`
3. Verify the hook script has no syntax errors: `bash -n .git/hooks/post-commit`

## Notes

- Hooks are stored in version control in the `hooks/` directory
- The `.git/hooks/` directory is local and not tracked
- Always run `hooks/install-hooks.sh` after cloning or pulling updates to hooks
