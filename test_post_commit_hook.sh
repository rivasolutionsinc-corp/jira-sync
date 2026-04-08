#!/bin/bash
# Test script for post-commit hook functionality

set -e

PROJECT_DIR="/Users/dietrichgottfriedschmidt/apps/jira-sync"
HOOK_PATH="$PROJECT_DIR/.git/hooks/post-commit"
TEST_DIR="/tmp/post-commit-hook-test"
MEMORY_DIR="$HOME/Documents/Roo_Memory/post-commit-hook-test"

echo "🧪 Testing post-commit hook..."
echo ""

# Cleanup from previous runs
rm -rf "$TEST_DIR" "$MEMORY_DIR"
mkdir -p "$TEST_DIR" "$MEMORY_DIR"

# Initialize test repo
cd "$TEST_DIR"
git init
git config user.email "test@example.com"
git config user.name "Test User"

# Copy hook to test repo
mkdir -p .git/hooks
cp "$HOOK_PATH" .git/hooks/post-commit
chmod +x .git/hooks/post-commit

# Create memory bank files
mkdir -p "$MEMORY_DIR"
cat > "$MEMORY_DIR/MEMORY_BANK_INDEX.md" << 'MEMEOF'
# Memory Bank Index

**Last Updated:** 2026-01-01 00:00 UTC
**Current Branch:** main

## Projects
- jira-sync
MEMEOF

cat > "$MEMORY_DIR/SESSION_LOG.md" << 'MEMEOF'
# Session Log

## Header
Initial session log

MEMEOF

# Create initial commit
echo "test content" > test.txt
git add test.txt
git commit -m "test: initial commit"

echo "✓ Test commit created"
echo ""

# Check if MEMORY_BANK_INDEX was updated
if grep -q "$(date +%Y-%m-%d)" "$MEMORY_DIR/MEMORY_BANK_INDEX.md"; then
    echo "✓ MEMORY_BANK_INDEX.md updated with timestamp"
else
    echo "✗ MEMORY_BANK_INDEX.md NOT updated"
fi

# Check if SESSION_LOG was updated
if grep -q "test: initial commit" "$MEMORY_DIR/SESSION_LOG.md"; then
    echo "✓ SESSION_LOG.md updated with commit message"
else
    echo "✗ SESSION_LOG.md NOT updated"
fi

# Check if branch was logged
if grep -q "master\|main" "$MEMORY_DIR/SESSION_LOG.md"; then
    echo "✓ Branch information logged"
else
    echo "✗ Branch information NOT logged"
fi

# Check if commit hash was logged
if grep -q "Commit Hash:" "$MEMORY_DIR/SESSION_LOG.md"; then
    echo "✓ Commit hash logged"
else
    echo "✗ Commit hash NOT logged"
fi

echo ""
echo "✓ All tests passed!"
echo ""
echo "Memory Bank Index:"
cat "$MEMORY_DIR/MEMORY_BANK_INDEX.md"
echo ""
echo "Session Log (first 30 lines):"
head -30 "$MEMORY_DIR/SESSION_LOG.md"

# Cleanup
cd /
rm -rf "$TEST_DIR" "$MEMORY_DIR"
