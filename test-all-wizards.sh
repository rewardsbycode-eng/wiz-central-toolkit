#!/bin/bash
echo "=========================================="
echo "Wizard Fleet Validation — Disk Truth Check"
echo "=========================================="
echo ""

PASS_COUNT=0
FAIL_COUNT=0
TOTAL=0

# ALL TOOLS NOW IMPLEMENTED
TOOLS=(
    "bannerwiz"
    "codeguardwiz"
    "diffwiz"
    "godfatherwiz"
    "jsonwiz"
    "pythonwiz"
    "readwiz"
    "rustwiz"
    "tmuxwiz"
    "todowiz"
    "writewiz"
)

for tool in "${TOOLS[@]}"; do
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

# Functional tests
echo ""
echo "--- Functional Tests ---"

readwiz check "ls -la" > /dev/null 2>&1 && { echo "[readwiz] check ALLOW ... [PASS]"; PASS_COUNT=$((PASS_COUNT+1)); } || echo "[readwiz] check ALLOW ... [FAIL]"; TOTAL=$((TOTAL+1))
readwiz check "rm -rf /" > /dev/null 2>&1; [ $? -eq 1 ] && { echo "[readwiz] check DENIED ... [PASS]"; PASS_COUNT=$((PASS_COUNT+1)); } || echo "[readwiz] check DENIED ... [FAIL]"; TOTAL=$((TOTAL+1))

echo ""
echo "=========================================="
echo "VALIDATION SUMMARY"
echo "=========================================="
echo "Passed: $PASS_COUNT / $TOTAL"
echo "Failed: $FAIL_COUNT / $TOTAL"

[ $FAIL_COUNT -eq 0 ] && echo "[✓] All tests passed!" && exit 0 || echo "[⚠] Some tests failed." && exit 1
