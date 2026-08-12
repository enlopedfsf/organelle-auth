#!/usr/bin/env bash
set -euo pipefail

# Canonical project launcher. Run it from any directory; all paths are resolved from
# the repository root, not from the caller's current working directory.
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT_DIR="${PROJECT_ROOT}/runs/input"
INPUT_FILE="${ORG_AUTH_INPUT:-${INPUT_DIR}/samplesheet.csv}"
OUTPUT_DIR="${PROJECT_ROOT}/runs/output"
WORK_DIR="${ORG_AUTH_WORK:-${PROJECT_ROOT}/runs/work}"
M1_ANCHOR="${ORG_AUTH_M1_ANCHOR:-${INPUT_DIR}/corydalis/SRR38978846_M1_plastome.fasta}"

mkdir -p "${INPUT_DIR}" "${OUTPUT_DIR}" "${WORK_DIR}"

if [[ ! -s "${INPUT_FILE}" ]]; then
    printf 'ERROR: input samplesheet is missing or empty: %s\n' "${INPUT_FILE}" >&2
    printf 'Put the samplesheet in %s or set ORG_AUTH_INPUT to an existing file.\n' "${INPUT_DIR}" >&2
    exit 2
fi

EXTRA_ARGS=()
if [[ -s "${M1_ANCHOR}" ]]; then
    EXTRA_ARGS+=(--long_read_pilot_m1_anchor_fasta "${M1_ANCHOR}")
fi

cd "${PROJECT_ROOT}"
exec nextflow run "${PROJECT_ROOT}" \
    --input "${INPUT_FILE}" \
    --outdir "${OUTPUT_DIR}" \
    -work-dir "${WORK_DIR}" \
    "${EXTRA_ARGS[@]}" \
    "$@"
