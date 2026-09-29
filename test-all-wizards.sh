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
    "debugwiz"
    "diffwiz"
    "jsonwiz"
    "todowiz"
    "writewiz"
    "tmuxwiz"
    "codeguardwiz"
)

# PLACEHOLDER tools (expect exit 2 or 3 = not implemented)
PLACEHOLDERS=(
)

echo "--- Phase 1: Implemented Tools (must respond with exit 0) ---"
for tool in "${IMPLEMENTED[@]}"; do
    TOTAL=$((TOTAL + 1))
    echo -n "[$tool] --help ... "
    wiz "$tool" --help > /dev/null 2>&1
    rc=$?
    if [ $rc -eq 0 ]; then
        echo "[PASS]"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "[FAIL] (exit $rc)"
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

# --- helper: check <label> <expected exit: N|nonzero> <command...> ---
check() {
    local label="$1" expect="$2"; shift 2
    TOTAL=$((TOTAL + 1))
    "$@" > /dev/null 2>&1
    local rc=$?
    local ok=1
    if [ "$expect" = "nonzero" ]; then
        [ $rc -ne 0 ] && ok=0
    else
        [ $rc -eq "$expect" ] && ok=0
    fi
    if [ $ok -eq 0 ]; then
        echo "$label ... [PASS]"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "$label ... [FAIL] (exit $rc, expected $expect)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

# --- fixtures (isolated; removed on exit) ---
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/good" "$T/bad"
echo '{"a": 1}' > "$T/good.json"
echo '{"a": '   > "$T/bad.json"
echo 'x = 1'    > "$T/good/ok.py"
echo 'def f(:'  > "$T/bad/broken.py"
echo 'same'     > "$T/a.txt"
echo 'same'     > "$T/b.txt"
echo 'different' > "$T/c.txt"

# --- helper: check <label> <expected exit: N|nonzero> <command...> ---
check() {
    local label="$1" expect="$2"; shift 2
    TOTAL=$((TOTAL + 1))
    "$@" > /dev/null 2>&1
    local rc=$?
    local ok=1
    if [ "$expect" = "nonzero" ]; then
        [ $rc -ne 0 ] && ok=0
    else
        [ $rc -eq "$expect" ] && ok=0
    fi
    if [ $ok -eq 0 ]; then
        echo "$label ... [PASS]"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "$label ... [FAIL] (exit $rc, expected $expect)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

# --- fixtures (isolated; removed on exit) ---
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/good" "$T/bad"
echo '{"a": 1}' > "$T/good.json"
echo '{"a": '   > "$T/bad.json"
echo 'x = 1'    > "$T/good/ok.py"
echo 'def f(:'  > "$T/bad/broken.py"
echo 'same'     > "$T/a.txt"
echo 'same'     > "$T/b.txt"
echo 'different' > "$T/c.txt"

# bannerwiz
check "[bannerwiz] render" 0 wiz bannerwiz TEST
check "[bannerwiz] fonts"  0 wiz bannerwiz --fonts

# readwiz
check "[readwiz] check ALLOW"  0 wiz readwiz check "ls -la"
check "[readwiz] check DENIED" 1 wiz readwiz check "rm -rf /"
check "[readwiz] law"          0 wiz readwiz law

# rustwiz
check "[rustwiz] help" 0 wiz rustwiz --help

# jsonwiz
check "[jsonwiz] validate good" 0       wiz jsonwiz validate "$T/good.json"
check "[jsonwiz] validate bad"  nonzero wiz jsonwiz validate "$T/bad.json"

# pythonwiz
check "[pythonwiz] check good" 0       wiz pythonwiz check "$T/good/ok.py"
check "[pythonwiz] check bad"  nonzero wiz pythonwiz check "$T/bad/broken.py"

# diffwiz
check "[diffwiz] same identical" 0 wiz diffwiz same "$T/a.txt" "$T/b.txt"
check "[diffwiz] same different" 1 wiz diffwiz same "$T/a.txt" "$T/c.txt"

# debugwiz
check "[debugwiz] law"          0       wiz debugwiz law
check "[debugwiz] audit good"   0       wiz debugwiz audit "$T/good"
check "[debugwiz] audit broken" nonzero wiz debugwiz audit "$T/bad"

# writewiz
check "[writewiz] law" 0 wiz writewiz law

# tmuxwiz (no tmux server needed: unknown subcommand must exit 2)
check "[tmuxwiz] unknown subcommand" 2 wiz tmuxwiz bogus-subcommand

# codeguardwiz (lang detection needs no Ollama; audit/fix do, so not tested here)
check "[codeguardwiz] lang" 0 wiz codeguardwiz lang "$T/good/ok.py"

# todowiz: intentionally not covered here; it writes to ~/.todo-wizard and
# needs an isolated bank directory before it can be tested safely.

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
