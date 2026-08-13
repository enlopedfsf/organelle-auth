#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CHANGE_DIR="$PROJECT_DIR/openspec/changes/m4-hybrid-backbone-and-polish"
MANIFEST="$CHANGE_DIR/MANIFEST.sha256"
INPUT_MANIFEST="$CHANGE_DIR/evidence/execution-inputs.json"
RUN_ROOT=/home/iris-hp/Project/organelle-auth-ci-fix/runs
OUTDIR="$RUN_ROOT/output/m4-hybrid-backbone-and-polish/matrix-v1"
WORKDIR="$RUN_ROOT/work/m4-hybrid-backbone-and-polish/matrix-v1"
METADIR="$OUTDIR/run-metadata"

for required in "$MANIFEST" "$INPUT_MANIFEST" \
  /home/iris-hp/miniconda3/envs/CAT/bin/bwa \
  /home/iris-hp/miniconda3/envs/polypolish/bin/polypolish \
  /home/iris-hp/miniconda3/envs/flye/bin/flye-minimap2 \
  /home/iris-hp/miniconda3/envs/agrvate/bin/samtools \
  /home/iris-hp/miniconda3/envs/agrvate/bin/bcftools; do
    test -s "$required" || { printf 'missing or empty required M4 input/runtime: %s\n' "$required" >&2; exit 2; }
done

# Verify every frozen reference/read/tool object before launch.  No file is modified.
(cd "$PROJECT_DIR" && sha256sum -c "$MANIFEST")

mkdir -p "$METADIR" "$WORKDIR"

export NXF_OFFLINE=true
exec nextflow run "$PROJECT_DIR/m4_hybrid.nf" \
  -profile m4_local_reproduction \
  --m4_input_manifest "$INPUT_MANIFEST" \
  --outdir "$OUTDIR" \
  --work_dir "$WORKDIR" \
  -with-trace "$METADIR/trace.tsv" \
  -with-report "$METADIR/report.html" \
  -with-timeline "$METADIR/timeline.html" \
  -ansi-log false \
  "$@"
