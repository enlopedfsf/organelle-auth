//
// Local module: emit assembly_qc status (M1-①, design ①→② interface contract §3).
//
// Stages evidence to the frozen contract paths and writes a schema_status.json-valid status
// object at stage=assembly_qc. Status is derived ONLY from structural signals (circularization
// success / assembly failure) — NOT from any hardcoded scientific threshold. The coverage-valley
// coefficient is policy-injected; null in experimental → no valley call, no COVERAGE_ANOMALY.
//
// decision is always NOT_APPLICABLE in ① (decision logic lives in ②, stage=identify).

process EMIT_ASSEMBLY_QC_STATUS {
    tag "${meta.id}"
    label 'process_low'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container
        ? 'https://depot.galaxyproject.org/singularity/python:3.12'
        : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), path(plastome), path(graph), val(grade), val(produced_pt), path(nrdna), val(produced_nr), path(bam), path(depth), path(flagstat)
    // coverage_valley_coefficient is read directly from params.coverage_valley_coefficient
    // (policy-injected; null in experimental). policy_pack_id is read from meta.

    output:
    // Status JSON lives INSIDE the contract tree; its relative work-dir path IS its contract
    // path, so publishDir (withName override in conf/modules.config → path:${params.outdir})
    // mirrors it to ${params.outdir}/plant_sr_assembly/<sid>/<sid>.assembly_qc.status.json.
    tuple val(meta), path("plant_sr_assembly/${meta.id}/${meta.id}.assembly_qc.status.json"), emit: status_json
    tuple val(meta), val(grade), val(produced_pt), emit: status_summary
    tuple val("${task.process}"), val('emit_assembly_qc_status'), val('0.1.0'), topic: versions, emit: versions
    // The whole staged contract tree (evidence + status JSON) — published by the withName
    // publishDir override. Captures the conditional evidence set without per-file outputs.
    path "plant_sr_assembly/${meta.id}", emit: staged_tree

    when:
    task.ext.when == null || task.ext.when

    script:
    // All inputs passed as env vars so the Python body contains no Groovy interpolation.
    // The Python body builds the contract tree under the task WORK dir only (container-owned,
    // always writable) and NEVER writes to params.outdir directly — publishDir (host-side, as
    // the run user) mirrors work/plant_sr_assembly/<sid>/ → ${params.outdir}/plant_sr_assembly/<sid>/.
    // This fixes the container/host UID PermissionError when staging evidence from inside the
    // container (BUG #4). No OUTDIR env var is needed.
    """
    SAMPLE_ID="${meta.id}" \\
    POLICY_PACK_ID="${meta.policy_pack_id}" \\
    GRADE="${grade}" \\
    PRODUCED_PT="${produced_pt}" \\
    PRODUCED_NR="${produced_nr}" \\
    COVERAGE_COEFF="${params.coverage_valley_coefficient}" \\
    PLASTOME="${plastome}" \\
    GRAPH="${graph}" \\
    NRDNA="${nrdna}" \\
    BAM="${bam}" \\
    DEPTH="${depth}" \\
    FLAGSTAT="${flagstat}" \\
    python3 - <<'PYEOF'
import os, json, shutil

sid   = os.environ["SAMPLE_ID"]
work  = os.getcwd()                       # task work dir — container-owned, always writable
tree  = os.path.join(work, "plant_sr_assembly", sid)
os.makedirs(os.path.join(tree, "readback"), exist_ok=True)
os.makedirs(os.path.join(tree, "getorganelle"), exist_ok=True)

grade        = os.environ["GRADE"]
produced_pt  = os.environ["PRODUCED_PT"] == "true"
produced_nr  = os.environ["PRODUCED_NR"] == "true"
raw_coeff    = os.environ.get("COVERAGE_COEFF", "")
coverage_coeff = None if raw_coeff in ("", "null", "None") else float(raw_coeff)

evidence_files = []

def stage(src, contract_rel):
    # Copy a real (non-marker, non-empty) file into the work-dir contract tree; record its
    # contract (outdir-relative) path. Files reach ${params.outdir} via publishDir, not here.
    if not src or not os.path.exists(src):
        return
    if src.endswith(".NONE") or os.path.getsize(src) == 0:
        return
    shutil.copy2(src, os.path.join(tree, contract_rel))
    evidence_files.append("plant_sr_assembly/" + sid + "/" + contract_rel)

plastome = os.environ["PLASTOME"]; graph = os.environ["GRAPH"]; nrdna = os.environ["NRDNA"]
bam = os.environ["BAM"]; depth = os.environ["DEPTH"]; flagstat = os.environ["FLAGSTAT"]

# ① selected plastome (circularized *_plastome.fasta → CANDIDATE, or *_plastome.scaffold.fasta → DRAFT)
if produced_pt:
    stage(plastome, os.path.basename(plastome))
# ② nrDNA
if produced_nr:
    stage(nrdna, sid + "_nrdna.fasta")
# 3/4/5 read-back BAM / depth / flagstat (only when a plastome was produced)
if produced_pt:
    stage(bam,      "readback/" + sid + ".sorted.bam")
    stage(depth,    "readback/" + sid + ".depth.tsv")
    stage(flagstat, "readback/" + sid + ".flagstat.txt")
# ⑥ assembly graph
stage(graph, "getorganelle/" + sid + "_assembly_graph.fastg")

# ---- status from STRUCTURAL signals only (no hardcoded scientific threshold) ----
if not produced_pt:
    status, assembly_grade, reason = "FAIL", "NOT_APPLICABLE", ["ASSEMBLY_FAILED"]
    evidence_files = []
elif grade == "CANDIDATE":
    status, assembly_grade, reason = "PASS", "CANDIDATE", []
elif grade == "DRAFT":
    status, assembly_grade, reason = "WARN", "DRAFT", ["NO_CIRCULARIZATION"]
else:
    status, assembly_grade, reason = "FAIL", "NOT_APPLICABLE", ["ASSEMBLY_FAILED"]

# Coverage-valley coefficient: policy-injected. null (experimental) → no valley call, no
# COVERAGE_ANOMALY. M1-① deliberately does NOT use coverage_coeff to alter status (SCI-005 /
# ENG-POL-002); the variable is bound only to make the policy-injection point explicit.
_ = coverage_coeff

status_obj = {
    "sample_id": sid,
    "stage": "assembly_qc",
    "status": status,
    "assembly_grade": assembly_grade,
    "decision": "NOT_APPLICABLE",
    "reason_codes": reason,
    "policy_pack_id": os.environ["POLICY_PACK_ID"],
    "evidence_files": evidence_files,
}

# Single status JSON, written at its contract path inside the work-dir tree.
json_rel = "plant_sr_assembly/" + sid + "/" + sid + ".assembly_qc.status.json"
with open(os.path.join(work, json_rel), "w") as fh:
    json.dump(status_obj, fh, indent=2)
PYEOF
    """

    stub:
    """
    mkdir -p plant_sr_assembly/${meta.id}/readback plant_sr_assembly/${meta.id}/getorganelle
    printf '{"sample_id":"%s","stage":"assembly_qc","status":"PASS","assembly_grade":"CANDIDATE","decision":"NOT_APPLICABLE","reason_codes":[],"policy_pack_id":"%s","evidence_files":[]}' "${meta.id}" "${meta.policy_pack_id}" > plant_sr_assembly/${meta.id}/${meta.id}.assembly_qc.status.json
    """
}
