process LR_BUDGET_FASTQ {
    tag "${meta.id}"
    label 'process_low_memory'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ? 'https://depot.galaxyproject.org/singularity/python:3.12' : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), path(reads)
    path policy

    output:
    tuple val(meta), path("${meta.id}.bounded.fastq"), path("${meta.id}.input-budget.json"), emit: bounded
    tuple val("${task.process}"), val('organelle_lr_evidence'), val('0.1.0'), topic: versions, emit: versions

    script:
    """
    organelle_lr_evidence.py budget-fastq \
      --fastq ${reads} \
      --policy ${policy} \
      --out-fastq ${meta.id}.bounded.fastq \
      --out-manifest ${meta.id}.input-budget.json
    """

    stub:
    """
    printf '@stub\nACGTACGT\n+\nFFFFFFFF\n' > ${meta.id}.bounded.fastq
    printf '{"stage":"long_read_input_budget","status":"STUB","decision":"NOT_APPLICABLE","selected_reads":1,"selected_bases":8}\n' > ${meta.id}.input-budget.json
    """
}
