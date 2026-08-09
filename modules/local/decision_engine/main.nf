//
// Local module: decision engine (M1-② IDENTIFY, design 决策 1 + 决策 2).
//
// Applies the assembly_grade ↔ decision gating matrix (决策 1) using:
//   • ① stage=assembly_qc status (grade, status, reason_codes) — read-only passthrough/passthrough-reasons
//   • diagnostic-site metrics (callability + identity) — the SITE-LEVEL identity gate (决策 1)
//   • callable-region metrics (coverage + readback depth) — coverage adequacy
//   • conflict_rules.non_authentic_identity — read from the reference PACK (SCI-001, not hardcoded)
//   • callable_site / uncertainty_zone — read from the POLICY pack (ENG-POL, not hardcoded)
//
// 决策 2 (module-layer null defense): if any identify-referenced policy threshold is null →
// INCONCLUSIVE + [THRESHOLD_NOT_CONFIGURED], NO crash, NO forced call. This complements (does NOT
// replace) the ENG-POL-002 production startup gate. "无法判定" is a legitimate quality output.
//
// Precedence: ①-unusable passthrough → contamination → null-threshold → diagnostic-sites-not-callable
// → coverage-inadequate → identity-below-conflict → grey-zone → AUTHENTIC (CANDIDATE: PASS;
// DRAFT: WARN + [INCOMPLETE_ASSEMBLY]). See design.md 决策 1 matrix.

process DECISION_ENGINE {
    tag "${meta.id}"
    label 'process_low_memory'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container
        ? 'https://depot.galaxyproject.org/singularity/python:3.12'
        : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), val(grade), val(produced_pt), path(asm_status_json), path(callable_metrics), path(diagnostic_metrics), path(manifest)
    path  policy_file

    output:
    tuple val(meta), path("${meta.id}.decision.json"), emit: decision
    tuple val("${task.process}"), val('decision_engine'), val('0.1.0'), topic: versions, emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    SAMPLE_ID="${meta.id}" \\
    GRADE="${grade}" \\
    PRODUCED_PT="${produced_pt}" \\
    POLICY_PATH="${policy_file}" \\
    python3 - <<'PYEOF'
import os, json

sid         = os.environ["SAMPLE_ID"]
grade       = os.environ["GRADE"]
produced_pt = os.environ["PRODUCED_PT"] == "true"

asm      = json.load(open("${asm_status_json}"))
cm       = json.load(open("${callable_metrics}"))
dm       = json.load(open("${diagnostic_metrics}"))
manifest = json.load(open("${manifest}"))
# policy_file is a STAGED path (params.policy_pack_file, staged by Nextflow so it is visible inside
# the container — a host-path val is NOT mounted under docker). Missing/null/unreadable → empty
# policy → all thresholds null → INCONCLUSIVE + [THRESHOLD_NOT_CONFIGURED] (决策 2, no crash). This is
# the robust module-layer null defense: even a totally unset policy degrades to an honest INCONCLUSIVE.
ppath = os.environ.get("POLICY_PATH", "")
policy = {}
if ppath and ppath not in ("null", "None"):
    try:
        policy = json.load(open(ppath))
    except Exception:
        policy = {}

asm_status       = asm.get("status")
asm_reasons      = list(asm.get("reason_codes", []))
assembly_grade_1 = asm.get("assembly_grade")

thr       = policy.get("thresholds", {}) or {}
cs        = thr.get("callable_site")
uz        = thr.get("uncertainty_zone")
min_cf    = cs.get("min_callable_fraction") if isinstance(cs, dict) else None
min_md    = cs.get("min_mean_depth")       if isinstance(cs, dict) else None
uz_lo     = uz.get("lower") if isinstance(uz, dict) else None
uz_hi     = uz.get("upper") if isinstance(uz, dict) else None
non_auth  = (manifest.get("conflict_rules", {}) or {}).get("non_authentic_identity")

ident     = dm.get("diagnostic_identity")
call_cov  = cm.get("callable_coverage", 0.0)
mean_dep  = cm.get("mean_readback_depth", 0.0)

decision = status = "INCONCLUSIVE"
reason = []

# 1. ① unusable → passthrough INCONCLUSIVE (透传 ① reason)
if (not produced_pt) or asm_status == "FAIL" or grade == "NOT_APPLICABLE" or assembly_grade_1 == "NOT_APPLICABLE":
    decision, status = "INCONCLUSIVE", "INCONCLUSIVE"
    reason = list(asm_reasons) if asm_reasons else []
# 2. contamination signal from ① (COVERAGE_ANOMALY) → INCONCLUSIVE, never AUTHENTIC
elif "COVERAGE_ANOMALY" in asm_reasons:
    decision, status, reason = "INCONCLUSIVE", "INCONCLUSIVE", ["CONTAMINATION_SUSPECTED"]
# 3. 决策 2: null policy threshold → INCONCLUSIVE + THRESHOLD_NOT_CONFIGURED (no crash)
elif cs is None or uz is None or min_cf is None or min_md is None or uz_lo is None or uz_hi is None:
    decision, status, reason = "INCONCLUSIVE", "INCONCLUSIVE", ["THRESHOLD_NOT_CONFIGURED"]
# 4. diagnostic sites not all callable → INCONCLUSIVE (site-level gate, even if global identity high)
elif dm.get("n_diagnostic_callable", 0) < dm.get("n_diagnostic_total", 0):
    decision, status, reason = "INCONCLUSIVE", "INCONCLUSIVE", ["DIAGNOSTIC_SITES_NOT_CALLABLE"]
# 5. coverage inadequate → INCONCLUSIVE + LOW_COVERAGE
elif (min_cf is not None and call_cov < min_cf) or (min_md is not None and mean_dep < min_md):
    decision, status, reason = "INCONCLUSIVE", "INCONCLUSIVE", ["LOW_COVERAGE"]
else:
    # identity ladders
    if ident is None:
        decision, status, reason = "INCONCLUSIVE", "INCONCLUSIVE", []   # identity unmeasurable → grey
    elif non_auth is not None and ident < non_auth:
        decision, status = "NON_AUTHENTIC", ("WARN" if grade == "DRAFT" else "PASS")
        reason = ["IDENTITY_BELOW_THRESHOLD"]
    elif uz_hi is not None and ident < uz_hi:
        decision, status, reason = "INCONCLUSIVE", "INCONCLUSIVE", []   # grey zone
    else:
        # authentic-track: identity ≥ uncertainty_zone.upper
        if grade == "CANDIDATE":
            decision, status, reason = "AUTHENTIC", "PASS", []
        elif grade == "DRAFT":
            decision, status, reason = "AUTHENTIC", "WARN", ["INCOMPLETE_ASSEMBLY"]
        else:
            decision, status, reason = "INCONCLUSIVE", "INCONCLUSIVE", []  # unexpected grade → no forced call

out = {
    "sample_id": sid,
    "decision": decision,
    "status": status,
    "assembly_grade": grade,
    "reason_codes": reason,
    "policy_pack_id": policy.get("policy_id"),
    "policy_status": policy.get("status"),
    "diagnostic_identity": ident,
    "n_diagnostic_callable": dm.get("n_diagnostic_callable"),
    "n_diagnostic_total": dm.get("n_diagnostic_total"),
    "uncallable_sites": dm.get("uncallable_sites", []),
    "callable_coverage": call_cov,
    "mean_readback_depth": mean_dep,
    "thresholds_used": {
        "min_callable_fraction": min_cf,
        "min_mean_depth": min_md,
        "uncertainty_zone": [uz_lo, uz_hi],
        "non_authentic_identity": non_auth,
    },
}
with open(sid + ".decision.json", "w") as fh:
    json.dump(out, fh, indent=2)
PYEOF
    """

    stub:
    """
    printf '{"sample_id":"%s","decision":"AUTHENTIC","status":"WARN","assembly_grade":"DRAFT","reason_codes":["INCOMPLETE_ASSEMBLY"],"policy_pack_id":"stub","diagnostic_identity":0.9995,"n_diagnostic_callable":5,"n_diagnostic_total":5,"callable_coverage":0.99,"mean_readback_depth":500.0,"thresholds_used":{}}' "${meta.id}" > "${meta.id}.decision.json"
    """
}
