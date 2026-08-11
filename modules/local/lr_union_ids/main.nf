process LR_UNION_IDS {
    tag "${meta.id}"
    label 'process_low_memory'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ? 'https://depot.galaxyproject.org/singularity/python:3.12' : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), path(pass1_ids), path(pass2_ids)
    path policy

    output:
    tuple val(meta), path("${meta.id}.final.selected.ids"), path("${meta.id}.recruitment-union.json"), emit: union
    tuple val("${task.process}"), val('organelle_lr_evidence'), val('0.1.0'), topic: versions, emit: versions

    script:
    """
    organelle_lr_evidence.py union-ids \
      --pass1 ${pass1_ids} --pass2 ${pass2_ids} --policy ${policy} \
      --out-ids ${meta.id}.final.selected.ids \
      --out-manifest ${meta.id}.recruitment-union.json
    """

    stub:
    """
    : > ${meta.id}.final.selected.ids
    printf '{"stage":"long_read_recruitment_union","status":"STUB","decision":"NOT_APPLICABLE","maximum_passes":2}\n' > ${meta.id}.recruitment-union.json
    """
}
