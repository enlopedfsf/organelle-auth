//
// Local module: emit identify status (M1-② IDENTIFY, design 决策 5).
//
// Consumes the decision.json + ① read-only evidence, writes a schema_status.json-valid status
// object at stage=identify, and stages the identify evidence (decision record + ① evidence) under
// the taxon-specific identify tree (plant_sr_assembly/<sid>/ or animal_sr_identify/<sid>/).
// Mirrors ①'s
// EMIT_ASSEMBLY_QC_STATUS:
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
    // Stage similarly named evidence under distinct directories. Animal and plant inputs share
    // the generic channel contract, but animal annotation is not nrdna and is not an assembly
    // graph; the script below preserves those semantics in the published evidence tree.
    tuple val(meta), val(stage_root), path(decision_json), path(plastome, stageAs: 'assembly/*'), path(graph, stageAs: 'graph/*'), path(nrdna, stageAs: 'annotation/*'), path(bam, stageAs: 'readback/bam/*'), path(depth, stageAs: 'readback/depth/*'), path(flagstat, stageAs: 'readback/flagstat/*'), path(asm_status_json, stageAs: 'assembly_status/*')

    output:
    tuple val(meta), path("${stage_root}/${meta.id}/${meta.id}.identify.status.json"), emit: status_json
    path "${stage_root}/${meta.id}", emit: staged_tree
    tuple val("${task.process}"), val('emit_identify_status'), val('0.1.0'), topic: versions, emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    SAMPLE_ID="${meta.id}" \\
    STAGE_ROOT="${stage_root}" \\
    python3 - <<'PYEOF'
import os, json, shutil

sid  = os.environ["SAMPLE_ID"]
stage_root = os.environ["STAGE_ROOT"]
work = os.getcwd()
tree = os.path.join(work, stage_root, sid)
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
    evidence_files.append(stage_root + "/" + sid + "/" + contract_rel)

# ① evidence (read-only inputs; re-staged so the identify tree is self-contained)
plastome = "${plastome}"; graph = "${graph}"; nrdna = "${nrdna}"
bam = "${bam}"; depth = "${depth}"; flagstat = "${flagstat}"
stage(plastome, os.path.basename(plastome))
if stage_root == "animal_sr_identify":
    # The animal channel carries its GenBank annotation in the generic nrdna slot.
    # Keep the file, but label it as annotation and never emit fabricated nrdna evidence.
    stage(nrdna, "annotation/" + sid + "_annotation.gb")
else:
    stage(nrdna, sid + "_nrdna.fasta")
stage(bam,      "readback/" + sid + ".sorted.bam")
stage(depth,    "readback/" + sid + ".depth.tsv")
stage(flagstat, "readback/" + sid + ".flagstat.txt")
if stage_root != "animal_sr_identify":
    stage(graph, "getorganelle/" + sid + "_assembly_graph.fastg")
# identify decision record (provenance: thresholds used + metrics)
shutil.copy2("${decision_json}", os.path.join(tree, "identify", sid + ".decision.json"))
evidence_files.append(stage_root + "/" + sid + "/identify/" + sid + ".decision.json")

status_obj = {
    "sample_id": sid,
    "stage": "identify",
    "status": decision["status"],
    "assembly_grade": decision["assembly_grade"],
    "decision": decision["decision"],
    "reason_codes": decision["reason_codes"],
    "policy_pack_id": decision.get("policy_pack_id"),
    "nuclear_marker": decision.get("nuclear_marker"),
    "evidence_files": evidence_files,
}

json_rel = stage_root + "/" + sid + "/" + sid + ".identify.status.json"
with open(os.path.join(work, json_rel), "w") as fh:
    json.dump(status_obj, fh, indent=2)
PYEOF
    """

    stub:
    """
    mkdir -p ${stage_root}/${meta.id}/readback ${stage_root}/${meta.id}/getorganelle ${stage_root}/${meta.id}/identify
    printf '{"sample_id":"%s","stage":"identify","status":"WARN","assembly_grade":"DRAFT","decision":"AUTHENTIC","reason_codes":["INCOMPLETE_ASSEMBLY"],"policy_pack_id":"stub","evidence_files":[]}' "${meta.id}" > ${stage_root}/${meta.id}/${meta.id}.identify.status.json
    """
}
