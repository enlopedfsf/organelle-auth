process LR_SELECT_PAF {
    tag "${meta.id}:pass${pass_number}"
    label 'process_low_memory'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ? 'https://depot.galaxyproject.org/singularity/python:3.12' : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), path(paf)
    path policy
    val pass_number

    output:
    tuple val(meta), path("${meta.id}.pass${pass_number}.selected.ids"), emit: ids
    tuple val(meta), path("${meta.id}.pass${pass_number}.alignment-evidence.tsv"), emit: evidence
    tuple val(meta), path("${meta.id}.pass${pass_number}.recruitment-status.json"), emit: status
    tuple val("${task.process}"), val('organelle_lr_evidence'), val('0.1.0'), topic: versions, emit: versions

    script:
    """
    organelle_lr_evidence.py select-paf \
      --paf ${paf} --policy ${policy} --pass-number ${pass_number} \
      --out-ids ${meta.id}.pass${pass_number}.selected.ids \
      --out-evidence ${meta.id}.pass${pass_number}.alignment-evidence.tsv \
      --out-status ${meta.id}.pass${pass_number}.recruitment-status.json
    """

    stub:
    """
    : > ${meta.id}.pass${pass_number}.selected.ids
    printf 'query\teligible\treason\talignment_class\n' > ${meta.id}.pass${pass_number}.alignment-evidence.tsv
    printf '{"stage":"long_read_recruitment","pass":%s,"status":"STUB","decision":"NOT_APPLICABLE"}\n' '${pass_number}' > ${meta.id}.pass${pass_number}.recruitment-status.json
    """
}
