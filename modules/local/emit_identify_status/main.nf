//
// Local module: emit identify status (M1-② IDENTIFY, design 决策 5).
//
// Consumes the decision.json + ① read-only evidence, writes a schema_status.json-valid status
// object at stage=identify, and stages the identify evidence (decision record + ① evidence) under
// the frozen contract tree plant_sr_assembly/<sid>/. Mirrors ①'s EMIT_ASSEMBLY_QC_STATUS:
// everything is written inside the task WORK dir (container-owned) and mirrored to
// ${params.outdir} by the withName publishDir override in conf/modules.config (BUG #4 pattern).
//
// decision/reason_codes come from DECISION_ENGINE; assembly_grade is ①'s (passthrough).
// ① outputs are NOT modified — this module only reads them and adds the identify status.

process EMIT_IDENTIFY_STATUS {
    tag "${meta.id}"
    label 'process_low_memory'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container
        ? 'https://depot.galaxyproject.org/singularity/python:3.12'
        : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), path(decision_json), path(plastome), path(graph), path(nrdna), path(bam), path(depth), path(flagstat), path(asm_status_json)

    output:
    tuple val(meta), path("plant_sr_assembly/${meta.id}/${meta.id}.identify.status.json"), emit: status_json
    path "plant_sr_assembly/${meta.id}", emit: staged_tree
    tuple val("${task.process}"), val('emit_identify_status'), val('0.1.0'), topic: versions, emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    SAMPLE_ID="${meta.id}" \\
    python3 - <<'PYEOF'
import os, json, shutil

sid  = os.environ["SAMPLE_ID"]
work = os.getcwd()
tree = os.path.join(work, "plant_sr_assembly", sid)
os.makedirs(os.path.join(tree, "readback"), exist_ok=True)
os.makedirs(os.path.join(tree, "getorganelle"), exist_ok=True)
os.makedirs(os.path.join(tree, "identify"), exist_ok=True)

decision = json.load(open("${decision_json}"))

evidence_files = []

def stage(src, contract_rel):
    # Copy a real (non-empty) file into the work-dir contract tree; record its contract path.
    if not src or not os.path.exists(src):
        return
    if src.endswith(".NONE") or os.path.getsize(src) == 0:
        return
    dst = os.path.join(tree, contract_rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    evidence_files.append("plant_sr_assembly/" + sid + "/" + contract_rel)

# ① evidence (read-only inputs; re-staged so the identify tree is self-contained)
plastome = "${plastome}"; graph = "${graph}"; nrdna = "${nrdna}"
bam = "${bam}"; depth = "${depth}"; flagstat = "${flagstat}"
stage(plastome, os.path.basename(plastome))
stage(nrdna, sid + "_nrdna.fasta")
stage(bam,      "readback/" + sid + ".sorted.bam")
stage(depth,    "readback/" + sid + ".depth.tsv")
stage(flagstat, "readback/" + sid + ".flagstat.txt")
stage(graph,    "getorganelle/" + sid + "_assembly_graph.fastg")
# identify decision record (provenance: thresholds used + metrics)
shutil.copy2("${decision_json}", os.path.join(tree, "identify", sid + ".decision.json"))
evidence_files.append("plant_sr_assembly/" + sid + "/identify/" + sid + ".decision.json")

status_obj = {
    "sample_id": sid,
    "stage": "identify",
    "status": decision["status"],
    "assembly_grade": decision["assembly_grade"],
    "decision": decision["decision"],
    "reason_codes": decision["reason_codes"],
    "policy_pack_id": decision.get("policy_pack_id"),
    "evidence_files": evidence_files,
}

json_rel = "plant_sr_assembly/" + sid + "/" + sid + ".identify.status.json"
with open(os.path.join(work, json_rel), "w") as fh:
    json.dump(status_obj, fh, indent=2)
PYEOF
    """

    stub:
    """
    mkdir -p plant_sr_assembly/${meta.id}/readback plant_sr_assembly/${meta.id}/getorganelle plant_sr_assembly/${meta.id}/identify
    printf '{"sample_id":"%s","stage":"identify","status":"WARN","assembly_grade":"DRAFT","decision":"AUTHENTIC","reason_codes":["INCOMPLETE_ASSEMBLY"],"policy_pack_id":"stub","evidence_files":[]}' "${meta.id}" > plant_sr_assembly/${meta.id}/${meta.id}.identify.status.json
    """
}
