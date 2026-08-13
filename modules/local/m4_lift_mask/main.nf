process M4_LIFT_MASK {
    tag "${meta.taxon}:${meta.arm}"
    label 'process_low_memory'
    conda "${moduleDir}/environment.yml"
    container 'quay.io/biocontainers/python:3.12'

    input:
    tuple val(meta), path(candidate, stageAs: 'candidate/*'), path(b0, stageAs: 'b0/*'), path(source_bed), path(heldout_r1), path(heldout_r2), path(paf)

    output:
    tuple val(meta), path(candidate), path(heldout_r1), path(heldout_r2), path("${meta.taxon}.${meta.arm}.core.bed"), path("${meta.taxon}.${meta.arm}.core-liftover.json"), emit: lifted
    tuple val("${task.process}"), val('m4_hybrid_evidence'), val('0.1.0'), topic: versions, emit: versions

    script:
    """
    set -euo pipefail
    m4_hybrid_evidence.py lift-mask --paf ${paf} --source-bed ${source_bed} \
      --query-fasta ${candidate} --out-bed ${meta.taxon}.${meta.arm}.core.bed \
      --out-json ${meta.taxon}.${meta.arm}.core-liftover.json
    """

    stub:
    """
    printf 'stub\t0\t8\tcore\n' > ${meta.taxon}.${meta.arm}.core.bed
    printf '{"status":"STUB","topology_use":"PROHIBITED"}\n' > ${meta.taxon}.${meta.arm}.core-liftover.json
    """
}
