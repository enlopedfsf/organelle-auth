process LR_TARGET_GATE {
    tag "${meta.id}:${gate_label}"
    label 'process_low_memory'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ? 'https://depot.galaxyproject.org/singularity/python:3.12' : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), path(evidence), path(selected_ids), path(reference_map), path(recruited_reads)
    path reference_metadata
    path policy
    val gate_label

    output:
    tuple val(meta), path("${meta.id}.${gate_label}.target-metrics.json"), emit: metrics
    tuple val(meta), path("${meta.id}.${gate_label}.gate-status.json"), emit: status
    tuple val("${task.process}"), val('organelle_lr_evidence'), val('0.1.0'), topic: versions, emit: versions

    script:
    def evidenceArgs = evidence instanceof List ? evidence.join(' ') : evidence
    """
    organelle_lr_evidence.py target-gate \
      --evidence ${evidenceArgs} --selected-ids ${selected_ids} \
      --reference-map ${reference_map} --reference-metadata ${reference_metadata} \
      --policy ${policy} --recruited-fastq ${recruited_reads} \
      --out-metrics ${meta.id}.${gate_label}.target-metrics.json \
      --out-status ${meta.id}.${gate_label}.gate-status.json
    """

    stub:
    """
    printf '{"stage":"long_read_target_gate","status":"STUB","decision":"NOT_APPLICABLE"}\n' > ${meta.id}.${gate_label}.target-metrics.json
    printf '{"stage":"long_read_target_gate","status":"STUB","decision":"NOT_APPLICABLE","reason_codes":["STUB"]}\n' > ${meta.id}.${gate_label}.gate-status.json
    """
}
