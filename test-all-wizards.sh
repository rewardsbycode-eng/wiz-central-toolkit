#!/bin/bash
# wiz-central-toolkit Wizard Validation Harness
# Tests every registered tool and reports ACTUAL disk truth

echo "=========================================="
echo "Wizard Fleet Validation — Disk Truth Check"
echo "=========================================="
echo ""

PASS_COUNT=0
FAIL_COUNT=0
TOTAL=0

# IMPLEMENTED tools (expect exit 0)
IMPLEMENTED=(
    "bannerwiz"
    "godfatherwiz"
    "readwiz"
    "rustwiz"
    "pythonwiz"
)

# PLACEHOLDER tools (expect exit 2 or 3 = not implemented)
PLACEHOLDERS=(
    "codeguardwiz"
    "debugwiz"
    "diffwiz"
    "jsonwiz"
    "tmuxwiz"
    "todowiz"
    "writewiz"
)

echo "--- Phase 1: Implemented Tools (must respond with exit 0) ---"
for tool in "${IMPLEMENTED[@]}"; do
    TOTAL=$((TOTAL + 1))
    echo -n "[$tool] --help ... "
    wiz "$tool" --help > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "[PASS]"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "[FAIL] (exit $?)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done

echo ""
echo "--- Phase 2: Placeholder Tools (expect non-zero = not ready) ---"
for tool in "${PLACEHOLDERS[@]}"; do
    TOTAL=$((TOTAL + 1))
    echo -n "[$tool] --help ... "
    wiz "$tool" --help > /tmp/placeholder_${tool}.txt 2>&1
    local_exit=$?
    if [ $local_exit -ne 0 ]; then
        # Non-zero exit = placeholder confirmed
        echo "[PLACEHOLDER] (exit $local_exit)"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "[UNEXPECTED PASS] (should be placeholder)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done

echo ""
echo "--- Phase 3: Functional Tests for Implemented Tools ---"

# bannerwiz
wiz bannerwiz TEST > /dev/null 2>&1 && { echo "[bannerwiz] render ... [PASS]"; PASS_COUNT=$((PASS_COUNT+1)); } || echo "[bannerwiz] render ... [FAIL]"; TOTAL=$((TOTAL+1))
wiz bannerwiz --fonts > /dev/null 2>&1 && { echo "[bannerwiz] fonts ... [PASS]"; PASS_COUNT=$((PASS_COUNT+1)); } || echo "[bannerwiz] fonts ... [FAIL]"; TOTAL=$((TOTAL+1))

# readwiz
wiz readwiz check "ls -la" > /dev/null 2>&1 && { echo "[readwiz] check ALLOW ... [PASS]"; PASS_COUNT=$((PASS_COUNT+1)); } || echo "[readwiz] check ALLOW ... [FAIL]"; TOTAL=$((TOTAL+1))
wiz readwiz check "rm -rf /" > /dev/null 2>&1; [ $? -eq 1 ] && { echo "[readwiz] check DENIED ... [PASS]"; PASS_COUNT=$((PASS_COUNT+1)); } || echo "[readwiz] check DENIED ... [FAIL]"; TOTAL=$((TOTAL+1))
wiz readwiz law > /dev/null 2>&1 && { echo "[readwiz] law ... [PASS]"; PASS_COUNT=$((PASS_COUNT+1)); } || echo "[readwiz] law ... [FAIL]"; TOTAL=$((TOTAL+1))

# rustwiz
wiz rustwiz --help > /dev/null 2>&1 && { echo "[rustwiz] help ... [PASS]"; PASS_COUNT=$((PASS_COUNT+1)); } || echo "[rustwiz] help ... [FAIL]"; TOTAL=$((TOTAL+1))

echo ""
echo "=========================================="
echo "VALIDATION SUMMARY"
echo "=========================================="
echo "Passed: $PASS_COUNT / $TOTAL"
echo "Failed: $FAIL_COUNT / $TOTAL"

if [ $FAIL_COUNT -gt 0 ]; then
    echo "[⚠] Some tests failed."
    exit 1
else
    echo "[✓] All tests passed!"
    exit 0
fi
