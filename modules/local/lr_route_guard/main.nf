process LR_ROUTE_GUARD {
    tag "${meta.id}"
    label 'process_low_memory'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ? 'https://depot.galaxyproject.org/singularity/python:3.12' : 'quay.io/biocontainers/python:3.12' }"

    input:
    val meta
    path policy
    val reference_state
    val strategy
    val observed_clean_depth

    output:
    tuple val(meta), path("${meta.id}.full-background-route-status.json"), emit: status
    tuple val("${task.process}"), val('organelle_lr_evidence'), val('0.1.0'), topic: versions, emit: versions

    script:
    def depth = observed_clean_depth == null ? '' : "--observed-clean-depth ${observed_clean_depth}"
    """
    organelle_lr_evidence.py route-guard --policy ${policy} \
      --reference-state ${reference_state} --strategy ${strategy} ${depth} \
      --out-status ${meta.id}.full-background-route-status.json
    """

    stub:
    """
    printf '{"stage":"long_read_routing","status":"STUB","decision":"NOT_APPLICABLE","full_background_pmat2_allowed":false}\n' > ${meta.id}.full-background-route-status.json
    """
}
