#!/usr/bin/env bash
# Wrapper redirecting to update_local.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/update_local.sh" "$@"
