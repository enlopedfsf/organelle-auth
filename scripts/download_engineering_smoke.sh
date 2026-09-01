#!/usr/bin/env bash
set -euo pipefail

# Engineering fixture only. Large files stay outside Git.
OUTDIR=${1:?output directory}
mkdir -p "$OUTDIR"
export NCBI_SETTINGS=${NCBI_SETTINGS:-$OUTDIR/sra-settings}

# Resume-safe SRA acquisition for the NCBI fixture. The run accession is frozen
# in accession-manifest.json; checksum validation is mandatory before conversion.
prefetch --output-directory "$OUTDIR" --max-size 3G SRR31850014

if [[ -z "${CNP0006129_URL:-}" ]]; then
  printf '%s\n' 'CNP0006129 direct download URL is not configured; record INFRASTRUCTURE_BLOCKED and do not substitute data.' >&2
  exit 75
fi
aria2c --continue=true --max-tries=3 --retry-wait=5 --out="$OUTDIR/CNP0006129.reads" "$CNP0006129_URL"
[[ -n "${CNP0006129_SHA256:-}" ]]
echo "$CNP0006129_SHA256  $OUTDIR/CNP0006129.reads" | sha256sum -c -
