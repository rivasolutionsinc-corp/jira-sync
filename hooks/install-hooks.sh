#!/bin/bash
# Install Git hooks into .git/hooks directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
GIT_HOOKS_DIR="$PROJECT_DIR/.git/hooks"

echo "Installing Git hooks..."

# Copy post-commit hook
if [ -f "$SCRIPT_DIR/post-commit" ]; then
    cp "$SCRIPT_DIR/post-commit" "$GIT_HOOKS_DIR/post-commit"
    chmod +x "$GIT_HOOKS_DIR/post-commit"
    echo "✓ post-commit hook installed"
else
    echo "✗ post-commit hook not found in $SCRIPT_DIR"
    exit 1
fi

echo "Git hooks installation complete!"
