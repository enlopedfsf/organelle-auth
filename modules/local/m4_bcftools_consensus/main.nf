process M4_BCFTOOLS_CONSENSUS {
    tag "${meta.taxon}:${meta.output_arm}"
    label 'process_low_memory'
    conda "${moduleDir}/environment.yml"
    container 'quay.io/biocontainers/bcftools@sha256:969314d56b9131683917cc5801734891a9af130daf7a0fb902b7707060b06027'

    input:
    tuple val(meta), path(candidate), path(bam), path(bai), path(depth), path(vcf), path(csi)

    output:
    tuple val(meta), path("${meta.taxon}.${meta.output_arm}.fasta"), path(vcf), emit: candidate
    tuple val("${task.process}"), val('bcftools'), val('1.21'), topic: versions, emit: versions

    script:
    """
    set -euo pipefail
    ${params.m4_bcftools_bin} consensus -f ${candidate} ${vcf} > ${meta.taxon}.${meta.output_arm}.fasta
    test -s ${meta.taxon}.${meta.output_arm}.fasta
    """

    stub:
    """
    cp ${candidate} ${meta.taxon}.${meta.output_arm}.fasta
    """
}
