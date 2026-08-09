//
// Local module: emit animal assembly_qc status (M2-①, design ①→② interface contract §3).
//
// Mirrors the plant emitter (BUG #4 pattern: contract tree built INSIDE the work dir, mirrored
// to ${params.outdir} by publishDir) for the ANIMAL branch. Status is derived ONLY from
// structural signals (MitoFinder circularization grade) + the NUMT risk-screen signal — NOT
// from any hardcoded scientific threshold (SCI-005 / ENG-POL-002). NUMT signal -> WARN +
// NUMT_RISK_SUSPECTED. decision is always NOT_APPLICABLE (② fills it at stage=identify).

process EMIT_ANIMAL_ASSEMBLY_QC_STATUS {
    tag "${meta.id}"
    label 'process_low'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container
        ? 'https://depot.galaxyproject.org/singularity/python:3.12'
        : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), path(mitogenome), path(annotation), path(infos), val(grade), val(produced), path(bam), path(depth), path(flagstat), path(numt_signal)

    output:
    // Status JSON lives INSIDE the contract tree; publishDir (withName override) mirrors it to
    // ${params.outdir}/animal_sr_assembly/<sid>/<sid>.assembly_qc.status.json.
    tuple val(meta), path("animal_sr_assembly/${meta.id}/${meta.id}.assembly_qc.status.json"), emit: status_json
    tuple val(meta), val(grade), val(produced), emit: status_summary
    tuple val("${task.process}"), val('emit_animal_assembly_qc_status'), val('0.1.0'), topic: versions, emit: versions
    path "animal_sr_assembly/${meta.id}", emit: staged_tree

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    SAMPLE_ID="${meta.id}" \\
    POLICY_PACK_ID="${meta.policy_pack_id}" \\
    GRADE="${grade}" \\
    PRODUCED="${produced}" \\
    MITOGENOME="${mitogenome}" \\
    ANNOTATION="${annotation}" \\
    INFOS="${infos}" \\
    BAM="${bam}" \\
    DEPTH="${depth}" \\
    FLAGSTAT="${flagstat}" \\
    NUMT_SIGNAL="${numt_signal}" \\
    python3 - <<'PYEOF'
import os, json, shutil

sid   = os.environ["SAMPLE_ID"]
work  = os.getcwd()                       # task work dir — container-owned, always writable
tree  = os.path.join(work, "animal_sr_assembly", sid)
os.makedirs(os.path.join(tree, "readback"), exist_ok=True)

grade     = os.environ["GRADE"]
produced  = os.environ["PRODUCED"] == "true"
numt_sig  = False
if os.path.exists(os.environ["NUMT_SIGNAL"]):
    with open(os.environ["NUMT_SIGNAL"]) as fh:
        numt_sig = fh.read().strip().lower() == "true"

evidence_files = []

def stage(src, contract_rel):
    # Copy a real (non-marker, non-empty) file into the work-dir contract tree; record its
    # contract (outdir-relative) path. Files reach ${params.outdir} via publishDir, not here.
    if not src or not os.path.exists(src):
        return
    if src.endswith(".NONE") or os.path.getsize(src) == 0:
        return
    shutil.copy2(src, os.path.join(tree, contract_rel))
    evidence_files.append("animal_sr_assembly/" + sid + "/" + contract_rel)

mito = os.environ["MITOGENOME"]; ann = os.environ["ANNOTATION"]; infos = os.environ["INFOS"]
bam = os.environ["BAM"]; depth = os.environ["DEPTH"]; flagstat = os.environ["FLAGSTAT"]

# ① selected mitogenome (circularized *_mitogenome.fasta -> CANDIDATE, or *_mitogenome.scaffold.fasta -> DRAFT)
if produced:
    stage(mito, os.path.basename(mito))
# ② annotation (.gb)
stage(ann, sid + "_annotation.gb")
# ③ MitoFinder stats (.infos)
stage(infos, sid + ".infos")
# 4/5/6 read-back BAM / depth / flagstat (only when a mitogenome was produced)
if produced:
    stage(bam,      "readback/" + sid + ".sorted.bam")
    stage(depth,    "readback/" + sid + ".depth.tsv")
    stage(flagstat, "readback/" + sid + ".flagstat.txt")

# ---- status from STRUCTURAL signals only (no hardcoded scientific threshold) ----
if not produced:
    status, assembly_grade, reason = "FAIL", "NOT_APPLICABLE", ["ASSEMBLY_FAILED"]
    evidence_files = []
elif grade == "CANDIDATE":
    status, assembly_grade, reason = "PASS", "CANDIDATE", []
elif grade == "DRAFT":
    status, assembly_grade, reason = "WARN", "DRAFT", ["NO_CIRCULARIZATION"]
else:
    status, assembly_grade, reason = "FAIL", "NOT_APPLICABLE", ["ASSEMBLY_FAILED"]

# NUMT risk-screen signal -> WARN + NUMT_RISK_SUSPECTED (design 决策 6; screening, not confirmation).
if produced and numt_sig and "NUMT_RISK_SUSPECTED" not in reason:
    status = "WARN"
    reason.append("NUMT_RISK_SUSPECTED")

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

json_rel = "animal_sr_assembly/" + sid + "/" + sid + ".assembly_qc.status.json"
with open(os.path.join(work, json_rel), "w") as fh:
    json.dump(status_obj, fh, indent=2)
PYEOF
    """

    stub:
    """
    mkdir -p animal_sr_assembly/${meta.id}/readback
    printf '{"sample_id":"%s","stage":"assembly_qc","status":"PASS","assembly_grade":"CANDIDATE","decision":"NOT_APPLICABLE","reason_codes":[],"policy_pack_id":"%s","evidence_files":[]}' "${meta.id}" "${meta.policy_pack_id}" > animal_sr_assembly/${meta.id}/${meta.id}.assembly_qc.status.json
    """
}
