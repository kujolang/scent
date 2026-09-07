#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
KUJO_BIN="$(command -v "${KUJO_BIN:-kujo}")"
KUJO_BIN="$(cd "$(dirname "$KUJO_BIN")" && pwd)/$(basename "$KUJO_BIN")"
export KUJO_BIN
export SCENT_SCRIPT="$PWD/scent.kujo"
# Each run owns its evidence directory, including concurrent local runs.
mkdir -p out/verification
receipt_dir="$(mktemp -d "$PWD/out/verification/run.XXXXXX")"
run_check() {
    local name="$1"
    shift
    if "$@" >"$receipt_dir/$name.log" 2>&1; then
        echo "PASS $name"
    else
        echo "FAIL $name: $receipt_dir/$name.log" >&2
        return 1
    fi
}
run_check check "$KUJO_BIN" check scent.kujo
run_check inline env SCENT_TEST_ROOT="$receipt_dir/fixtures" "$KUJO_BIN" test-run scent.kujo
run_check hardening python3 tests/hardening.py
run_check artifacts bash .github/scripts/check-kujo-tool-artifacts.sh
printf 'Evidence: %s\n' "$receipt_dir"
