process M4_CANDIDATE_TO_B0 {
    tag "${meta.taxon}:${meta.arm}"
    label 'process_low'
    conda "${moduleDir}/environment.yml"
    container 'community.wave.seqera.io/library/minimap2_samtools:b09096fc890429ce'

    input:
    tuple val(meta), path(candidate, stageAs: 'candidate/*'), path(b0, stageAs: 'b0/*'), path(source_bed), path(heldout_r1), path(heldout_r2)

    output:
    tuple val(meta), path(candidate), path(b0), path(source_bed), path(heldout_r1), path(heldout_r2), path("${meta.taxon}.${meta.arm}.candidate-to-b0.paf"), emit: alignment
    tuple val("${task.process}"), val('minimap2'), val('2.24'), topic: versions, emit: versions

    script:
    """
    set -euo pipefail
    ${params.m4_minimap2_bin} -x asm5 -c --cs=long --eqx --secondary=no -t ${task.cpus} \
      ${b0} ${candidate} > ${meta.taxon}.${meta.arm}.candidate-to-b0.paf
    test -s ${meta.taxon}.${meta.arm}.candidate-to-b0.paf
    """

    stub:
    """
    printf 'stub\t8\t0\t8\t+\tstub\t8\t0\t8\t8\t8\t60\tcs:Z:=ACGTACGT\n' > ${meta.taxon}.${meta.arm}.candidate-to-b0.paf
    """
}
