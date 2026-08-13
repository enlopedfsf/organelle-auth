process M4_SR_ALIGN {
    tag "${meta.taxon}:${meta.arm}:${meta.split}"
    label 'process_medium'
    conda "${moduleDir}/environment.yml"
    container 'community.wave.seqera.io/library/minimap2_samtools:b09096fc890429ce'

    input:
    tuple val(meta), path(candidate), path(reads_r1), path(reads_r2)

    output:
    tuple val(meta), path(candidate), path("${meta.taxon}.${meta.arm}.${meta.split}.primary.q20.bam"), path("${meta.taxon}.${meta.arm}.${meta.split}.primary.q20.bam.bai"), path("${meta.taxon}.${meta.arm}.${meta.split}.depth.tsv"), emit: alignment
    tuple val("${task.process}"), val('minimap2_samtools'), val('2.24_1.20'), topic: versions, emit: versions

    script:
    """
    set -euo pipefail
    ${params.m4_minimap2_bin} -ax sr --sam-hit-only -t ${task.cpus} ${candidate} ${reads_r1} ${reads_r2} \
      | ${params.m4_samtools_bin} view -b -F 0x904 -q 20 - \
      | ${params.m4_samtools_bin} sort -@ ${task.cpus} -o ${meta.taxon}.${meta.arm}.${meta.split}.primary.q20.bam
    ${params.m4_samtools_bin} index ${meta.taxon}.${meta.arm}.${meta.split}.primary.q20.bam
    ${params.m4_samtools_bin} depth -aa -q 20 -Q 20 ${meta.taxon}.${meta.arm}.${meta.split}.primary.q20.bam \
      > ${meta.taxon}.${meta.arm}.${meta.split}.depth.tsv
    """

    stub:
    """
    : > ${meta.taxon}.${meta.arm}.${meta.split}.primary.q20.bam
    : > ${meta.taxon}.${meta.arm}.${meta.split}.primary.q20.bam.bai
    printf 'stub\t1\t20\n' > ${meta.taxon}.${meta.arm}.${meta.split}.depth.tsv
    """
}
