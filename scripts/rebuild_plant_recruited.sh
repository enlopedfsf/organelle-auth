#!/usr/bin/env bash
set -euo pipefail
READS=${1:?uncompressed SRR38978847 FASTQ}
OUTDIR=${2:?output directory}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
REF="$ROOT/assets/reference_packs/corydalis-test-0.1/PZ405204_plastome.fasta"
POLICY="$ROOT/assets/policies/plant-long-read-reference-first/experimental-v0.1.json"
mkdir -p "$OUTDIR"
minimap2 -x map-ont -c --cs=long --secondary=yes -N 20 "$REF" "$READS" > "$OUTDIR/SRR38978847.recruitment.paf"
python "$ROOT/bin/organelle_lr_evidence.py" select-paf --paf "$OUTDIR/SRR38978847.recruitment.paf" --policy "$POLICY" --pass-number 1 --out-ids "$OUTDIR/SRR38978847.selected.ids" --out-evidence "$OUTDIR/SRR38978847.recruitment.evidence.tsv" --out-status "$OUTDIR/SRR38978847.recruitment.status.json"
python "$ROOT/bin/organelle_lr_evidence.py" extract-fastq --fastq "$READS" --ids "$OUTDIR/SRR38978847.selected.ids" --out-fastq "$OUTDIR/SRR38978847.final-recruited.fastq.gz" --out-manifest "$OUTDIR/SRR38978847.final-recruited.manifest.json"
EXPECTED=93f4fd3bc3969e5d4d3577870b32f4a63d99ddc57a325f84403d7f089531f3c8
ACTUAL=$(sha256sum "$OUTDIR/SRR38978847.final-recruited.fastq.gz" | awk '{print $1}')
printf '%s\t%s\n' "$EXPECTED" "$ACTUAL" > "$OUTDIR/recruitment.sha256.comparison.tsv"
[[ "$ACTUAL" == "$EXPECTED" ]]
