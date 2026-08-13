process M4_BWA_ALIGN {
    tag "${meta.taxon}:${meta.arm}"
    label 'process_medium'
    conda "${moduleDir}/environment.yml"
    container 'quay.io/biocontainers/bwa@sha256:99a35e5ee4e9c329e8746c4689890b97a3ac5620cb36d374cba69ba52016e72a'

    input:
    tuple val(meta), path(candidate), path(reads_r1), path(reads_r2)

    output:
    tuple val(meta), path(candidate), path("${meta.taxon}.${meta.arm}.train.R1.sam"), path("${meta.taxon}.${meta.arm}.train.R2.sam"), emit: alignments
    tuple val("${task.process}"), val('bwa'), val('0.7.19-r1273'), topic: versions, emit: versions

    script:
    """
    set -euo pipefail
    test -s ${candidate}; test -s ${reads_r1}; test -s ${reads_r2}
    ${params.m4_bwa_bin} index ${candidate}
    ${params.m4_bwa_bin} mem -t ${task.cpus} -a ${candidate} ${reads_r1} > ${meta.taxon}.${meta.arm}.train.R1.sam
    ${params.m4_bwa_bin} mem -t ${task.cpus} -a ${candidate} ${reads_r2} > ${meta.taxon}.${meta.arm}.train.R2.sam
    """

    stub:
    """
    printf '@HD\tVN:1.6\n' > ${meta.taxon}.${meta.arm}.train.R1.sam
    printf '@HD\tVN:1.6\n' > ${meta.taxon}.${meta.arm}.train.R2.sam
    """
}
