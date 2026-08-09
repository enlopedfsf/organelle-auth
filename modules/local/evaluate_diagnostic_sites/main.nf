//
// Local module: evaluate diagnostic sites (M1-② IDENTIFY, design 决策 1 / 决策 5).
//
// The core of the site-level identity gate. For each reference-pack diagnostic_site window, check
// whether an assembly→reference alignment SPANS the whole window (callable) and read its identity
// from the =/X CIGAR (--eqx). A site that falls in an assembly gap / uncallable region is NOT
// callable → DECISION_ENGINE emits INCONCLUSIVE + [DIAGNOSTIC_SITES_NOT_CALLABLE], even if global
// identity is high (决策 1: identity must be site-level, not a single global number — SCI-001).
//
// Degenerate v0.1 (design Risks): no adulterant controls, so identity here is alignment identity
// (global substitute). A pack WITH adulterant controls must implement true site-level conflict
// discrimination, not this global-alignment substitute.
//

process EVALUATE_DIAGNOSTIC_SITES {
    tag "${meta.id}"
    label 'process_low_memory'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container
        ? 'https://depot.galaxyproject.org/singularity/python:3.12'
        : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), path(paf), path(diagnostic_sites_tsv), path(reference_fasta)

    output:
    tuple val(meta), path("${meta.id}.diagnostic.metrics.json"), emit: metrics
    tuple val("${task.process}"), val('evaluate_diagnostic_sites'), val('0.1.0'), topic: versions, emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    SAMPLE_ID="${meta.id}" \\
    python3 - <<'PYEOF'
import os, re, json

sid = os.environ["SAMPLE_ID"]
cigar_re = re.compile(r"(\\d+)([=XIDMSHPN])")

def aln_identity(cigar, nmatch, blen):
    # BLAST-like identity from an =/X CIGAR: matches / (matches+subs+ins+dels).
    # Falls back to nmatch/blen if the CIGAR has no =/X (e.g. -c without --eqx).
    m = s = ins = dl = 0
    has_eqx = False
    for n, op in cigar_re.findall(cigar or ""):
        n = int(n)
        if op == "=": m += n; has_eqx = True
        elif op == "X": s += n; has_eqx = True
        elif op == "I": ins += n
        elif op == "D": dl += n
    if has_eqx:
        denom = m + s + ins + dl
        return (m / denom) if denom > 0 else None
    try:
        return (int(nmatch) / int(blen)) if int(blen) > 0 else None
    except Exception:
        return None

# ---- parse PAF alignments ----
alignments = {}   # contig -> list of dict(tstart,tend,identity)
with open("${paf}") as fh:
    for line in fh:
        f = line.rstrip("\\n").split("\\t")
        if len(f) < 12:
            continue
        try:
            tname, ts, te = f[5], int(f[7]), int(f[8])
        except ValueError:
            continue
        if ts >= te:
            continue
        cigar = ""
        nmatch, blen = f[9], f[10]
        for tag in f[12:]:
            if tag.startswith("cg:Z:"):
                cigar = tag[5:]
                break
        ident = aln_identity(cigar, nmatch, blen)
        alignments.setdefault(tname, []).append({"tstart": ts, "tend": te, "identity": ident})

# ---- per diagnostic site: callable if a single alignment spans the whole window ----
per_site = []
with open("${diagnostic_sites_tsv}") as fh:
    for line in fh:
        if line.startswith("name") or line.startswith("#") or not line.strip():
            continue
        f = line.rstrip("\\n").split("\\t")
        if len(f) < 4:
            continue
        try:
            name, contig, s, e = f[0], f[1], int(f[2]), int(f[3])
        except ValueError:
            continue
        candidates = [a for a in alignments.get(contig, []) if a["tstart"] <= s and a["tend"] >= e]
        if candidates:
            # identity of the best (max-identity) spanning alignment
            idents = [a["identity"] for a in candidates if a["identity"] is not None]
            site_ident = max(idents) if idents else None
            per_site.append({"name": name, "callable": True, "identity": site_ident})
        else:
            per_site.append({"name": name, "callable": False, "identity": None})

n_total = len(per_site)
callable_sites = [p for p in per_site if p["callable"]]
n_callable = len(callable_sites)
idents = [p["identity"] for p in callable_sites if p["identity"] is not None]
diagnostic_identity = (sum(idents) / len(idents)) if idents else None
uncallable = [p["name"] for p in per_site if not p["callable"]]

metrics = {
    "sample_id": sid,
    "n_diagnostic_total": n_total,
    "n_diagnostic_callable": n_callable,
    "diagnostic_identity": round(diagnostic_identity, 6) if diagnostic_identity is not None else None,
    "uncallable_sites": uncallable,
    "per_site": per_site,
}
with open(sid + ".diagnostic.metrics.json", "w") as fh:
    json.dump(metrics, fh, indent=2)
PYEOF
    """

    stub:
    """
    printf '{"sample_id":"%s","n_diagnostic_total":5,"n_diagnostic_callable":5,"diagnostic_identity":0.9995,"uncallable_sites":[],"per_site":[{"name":"ds1","callable":true,"identity":0.9995}]}' "${meta.id}" > "${meta.id}.diagnostic.metrics.json"
    """
}
