process M4_POLYPOLISH {
    tag "${meta.taxon}:${meta.arm}"
    label 'process_medium'
    conda "${moduleDir}/environment.yml"
    container 'quay.io/biocontainers/polypolish@sha256:729c4fc24b3e81969c06e8c9eeaf498feb17eeabdb91808615b1e177dd06aa5d'

    input:
    tuple val(meta), path(candidate), path(sam_r1), path(sam_r2)

    output:
    tuple val(meta), path("${meta.taxon}.${meta.output_arm}.fasta"), path("${meta.taxon}.${meta.output_arm}.polypolish-debug.tsv"), path("${meta.taxon}.${meta.output_arm}.polypolish-filter.log"), emit: candidate
    tuple val("${task.process}"), val('polypolish'), val('0.7.1'), topic: versions, emit: versions

    script:
    """
    set -euo pipefail
    ${params.m4_polypolish_bin} filter --orientation auto --low 0.1 --high 99.9 \
      --in1 ${sam_r1} --in2 ${sam_r2} \
      --out1 filtered.R1.sam --out2 filtered.R2.sam \
      > ${meta.taxon}.${meta.output_arm}.polypolish-filter.log 2>&1
    ${params.m4_polypolish_bin} polish --debug ${meta.taxon}.${meta.output_arm}.polypolish-debug.tsv \
      ${candidate} filtered.R1.sam filtered.R2.sam > ${meta.taxon}.${meta.output_arm}.fasta
    test -s ${meta.taxon}.${meta.output_arm}.fasta
    """

    stub:
    """
    cp ${candidate} ${meta.taxon}.${meta.output_arm}.fasta
    printf 'stub\n' > ${meta.taxon}.${meta.output_arm}.polypolish-debug.tsv
    printf 'stub\n' > ${meta.taxon}.${meta.output_arm}.polypolish-filter.log
    """
}
