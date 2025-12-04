#!/bin/bash
# Test script for check-uncommitted.sh functionality

set -e

echo "=== Testing check-uncommitted.sh ==="
echo ""

# Test 1: Clean working tree
echo "Test 1: Testing with clean working tree..."
if ./check-uncommitted.sh; then
    echo "✓ Test 1 passed: Script correctly detected no uncommitted changes"
else
    echo "✗ Test 1 failed: Script incorrectly reported uncommitted changes"
    exit 1
fi
echo ""

# Test 2: Modified file detection
echo "Test 2: Testing detection of modified files..."
echo "# test comment" >> README.md
if ! ./check-uncommitted.sh; then
    echo "✓ Test 2 passed: Script correctly detected modified files"
else
    echo "✗ Test 2 failed: Script did not detect modified files"
    git checkout README.md
    exit 1
fi
git checkout README.md
echo ""

# Test 3: Untracked file detection
echo "Test 3: Testing detection of untracked files..."
echo "test" > test-file.txt
if ! ./check-uncommitted.sh; then
    echo "✓ Test 3 passed: Script correctly detected untracked files"
else
    echo "✗ Test 3 failed: Script did not detect untracked files"
    rm -f test-file.txt
    exit 1
fi
rm -f test-file.txt
echo ""

# Test 4: Bypass with ALLOW_UNCOMMITTED
echo "Test 4: Testing bypass with ALLOW_UNCOMMITTED=1..."
echo "test" > test-file.txt
if ALLOW_UNCOMMITTED=1 ./check-uncommitted.sh; then
    echo "✓ Test 4 passed: Script correctly bypassed check"
else
    echo "✗ Test 4 failed: Script did not respect ALLOW_UNCOMMITTED flag"
    rm -f test-file.txt
    exit 1
fi
rm -f test-file.txt
echo ""

echo "=== All tests passed! ==="
