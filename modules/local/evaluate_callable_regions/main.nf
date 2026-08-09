//
// Local module: evaluate callable regions (M1-② IDENTIFY, design 决策 5).
//
// From the assembly→reference PAF: the union of alignment reference-spans, intersected with the
// pack's callable_regions, gives reference-coordinate callable coverage (fraction). This is the
// reference-coord coverage ② needs; ①'s read-back depth (assembly-coord) is used separately as a
// global coverage-ADEQUACY metric (mean depth over the assembled plastome). Both feed DECISION_ENGINE
// against policy.callable_site.{min_callable_fraction, min_mean_depth} (no hardcoded threshold).
//
// Degenerate v0.1 (design Risks): coverage from alignment spans is a global substitute for true
// per-base callability; a pack with adulterant controls must implement lifted per-base callability.
//

process EVALUATE_CALLABLE_REGIONS {
    tag "${meta.id}"
    label 'process_low'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container
        ? 'https://depot.galaxyproject.org/singularity/python:3.12'
        : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), path(paf), path(callable_regions_tsv), path(depth_tsv)

    output:
    tuple val(meta), path("${meta.id}.callable.metrics.json"), emit: metrics
    tuple val("${task.process}"), val('evaluate_callable_regions'), val('0.1.0'), topic: versions, emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    SAMPLE_ID="${meta.id}" \\
    python3 - <<'PYEOF'
import os, json

sid = os.environ["SAMPLE_ID"]

# ---- parse PAF reference spans (tname, tstart, tend) ----
spans = {}   # contig -> list of (start, end)
with open("${paf}") as fh:
    for line in fh:
        f = line.rstrip("\\n").split("\\t")
        if len(f) < 12:
            continue
        try:
            tname, ts, te = f[5], int(f[7]), int(f[8])
        except ValueError:
            continue
        if ts < te:
            spans.setdefault(tname, []).append((ts, te))

def union_len(intervals):
    if not intervals:
        return 0
    intervals = sorted(intervals)
    merged = [list(intervals[0])]
    for s, e in intervals[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return sum(e - s for s, e in merged)

def covered_in(contig, rs, re):
    # bp of [rs,re] covered by alignment spans on contig.
    clips = []
    for s, e in spans.get(contig, []):
        os_, oe = max(s, rs), min(e, re)
        if os_ < oe:
            clips.append((os_, oe))
    return union_len(clips)

# ---- callable coverage over pack callable_regions ----
covered_bp = 0
region_bp = 0
with open("${callable_regions_tsv}") as fh:
    for line in fh:
        if line.startswith("ref_contig") or line.startswith("#") or not line.strip():
            continue
        f = line.rstrip("\\n").split("\\t")
        if len(f) < 3:
            continue
        try:
            contig, rs, re = f[0], int(f[1]), int(f[2])
        except ValueError:
            continue
        region_bp += (re - rs)
        covered_bp += covered_in(contig, rs, re)

callable_coverage = (covered_bp / region_bp) if region_bp > 0 else 0.0

# ---- mean read-back depth (① depth.tsv: rname, pos, depth; assembly-coord adequacy metric) ----
depths = []
dpath = "${depth_tsv}"
if os.path.isfile(dpath) and os.path.getsize(dpath) > 0:
    with open(dpath) as fh:
        for line in fh:
            f = line.rstrip("\\n").split("\\t")
            if len(f) >= 3:
                try:
                    depths.append(float(f[2]))
                except ValueError:
                    continue
mean_depth = (sum(depths) / len(depths)) if depths else 0.0

metrics = {
    "sample_id": sid,
    "callable_coverage": round(callable_coverage, 6),
    "callable_regions_total_bp": region_bp,
    "covered_bp": covered_bp,
    "mean_readback_depth": round(mean_depth, 4),
    "n_depth_positions": len(depths),
}
with open(sid + ".callable.metrics.json", "w") as fh:
    json.dump(metrics, fh, indent=2)
PYEOF
    """

    stub:
    """
    printf '{"sample_id":"%s","callable_coverage":0.99,"callable_regions_total_bp":200540,"covered_bp":198533,"mean_readback_depth":500.0,"n_depth_positions":200000}' "${meta.id}" > "${meta.id}.callable.metrics.json"
    """
}
