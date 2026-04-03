#!/usr/bin/env bash
# Smoke test: generate FCPXML from sample media and validate it.
#
# Usage:
#   ./scripts/smoke_test_import.sh [input_dir]
#
# Requires: roughcut-fcpx installed, ffmpeg available.
set -euo pipefail

INPUT_DIR="${1:-./input}"
OUTPUT_DIR="./output"

echo "=== roughcut-fcpx smoke test ==="
echo "Input:  $INPUT_DIR"
echo "Output: $OUTPUT_DIR"

# Run the pipeline
roughcut-fcpx run --input "$INPUT_DIR" --output "$OUTPUT_DIR" --style "poetic observational montage" --duration 30

# Check outputs exist
for f in project.fcpxml edit_decisions.json report.md; do
    if [ ! -f "$OUTPUT_DIR/$f" ]; then
        echo "FAIL: $OUTPUT_DIR/$f not found"
        exit 1
    fi
    echo "OK: $OUTPUT_DIR/$f exists"
done

# Validate the FCPXML
roughcut-fcpx validate "$OUTPUT_DIR/project.fcpxml"

echo ""
echo "=== Smoke test passed ==="
echo "You can now import $OUTPUT_DIR/project.fcpxml into Final Cut Pro."
