#!/bin/bash
# Script to check for uncommitted changes in the repository
# This can be used in CI/CD pipelines or as a pre-commit hook

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Checking for uncommitted changes..."

# Check if there are any uncommitted changes (modified/staged files or untracked files)
HAS_CHANGES=0

# Check for modified or staged files
if ! git diff --quiet || ! git diff --cached --quiet; then
    HAS_CHANGES=1
fi

# Check for untracked files (excluding those in .gitignore)
if [ -n "$(git ls-files --others --exclude-standard)" ]; then
    HAS_CHANGES=1
fi

if [ $HAS_CHANGES -eq 1 ]; then
    echo -e "${YELLOW}Warning: Uncommitted changes detected${NC}"
    
    # Show the status
    git status --short
    
    # Check if we should proceed anyway
    if [ "${ALLOW_UNCOMMITTED:-0}" = "1" ]; then
        echo -e "${GREEN}Proceeding anyway (ALLOW_UNCOMMITTED=1)${NC}"
        exit 0
    fi
    
    echo -e "${RED}Error: Please commit or stash your changes before proceeding${NC}"
    echo "To bypass this check, set ALLOW_UNCOMMITTED=1"
    exit 1
fi

echo -e "${GREEN}No uncommitted changes detected${NC}"
exit 0
