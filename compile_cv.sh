#!/bin/bash
exec "$(cd "$(dirname "$0")" && pwd)/scripts/compile_cv.sh" "$@"
