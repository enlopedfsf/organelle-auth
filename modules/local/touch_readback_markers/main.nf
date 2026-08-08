//
// Local module: touch empty read-back markers for samples that produced no plastome.
//
// When GetOrganelle yields no usable plastome (ASSEMBLY_FAILED), ASSEMBLY_QC cannot map
// reads (no target). This process emits empty BAM/depth/flagstat markers so the read-back
// channel has an item for every sample, letting the status emitter uniformly produce a
// FAIL + ASSEMBLY_FAILED status (design ①→② contract §3; 方法学 §3.6 不强环化).

process TOUCH_READBACK_MARKERS {
    tag "${meta.id}"
    label 'process_low'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container
        ? 'https://depot.galaxyproject.org/singularity/python:3.12'
        : 'quay.io/biocontainers/python:3.12' }"

    input:
    val meta

    output:
    tuple val(meta), path("${meta.id}.sorted.bam"), path("${meta.id}.depth.tsv"), path("${meta.id}.flagstat.txt"), emit: readback
    tuple val("${task.process}"), val('touch_readback_markers'), val('0.1.0'), topic: versions, emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    touch "${meta.id}.sorted.bam" "${meta.id}.depth.tsv" "${meta.id}.flagstat.txt"
    """

    stub:
    """
    touch "${meta.id}.sorted.bam" "${meta.id}.depth.tsv" "${meta.id}.flagstat.txt"
    """
}
