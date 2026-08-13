process M4_HELDOUT_EVALUATE {
    tag "${meta.taxon}:${meta.arm}"
    label 'process_low_memory'
    conda "${moduleDir}/environment.yml"
    container 'quay.io/biocontainers/python:3.12'

    input:
    tuple val(meta), path(candidate), path(bam), path(bai), path(depth), path(vcf), path(csi), path(core_bed), path(liftover_json)
    path evaluation_policy

    output:
    tuple val(meta), path(candidate), path("${meta.taxon}.${meta.arm}.heldout-edit-ledger.tsv"), path("${meta.taxon}.${meta.arm}.metrics.json"), path(core_bed), emit: evidence
    tuple val("${task.process}"), val('m4_hybrid_evidence'), val('0.1.0'), topic: versions, emit: versions

    script:
    """
    set -euo pipefail
    m4_hybrid_evidence.py evaluate --candidate ${candidate} --vcf ${vcf} --depth ${depth} \
      --core-bed ${core_bed} --policy ${evaluation_policy} --taxon ${meta.taxon} \
      --arm ${meta.arm} --route heldout --out-ledger ${meta.taxon}.${meta.arm}.heldout-edit-ledger.tsv \
      --out-metrics ${meta.taxon}.${meta.arm}.metrics.json
    """

    stub:
    """
    printf 'taxon\tarm\troute\tcontig\tposition_1based\tref\talt\tvariant_type\tregion\tevaluation_status\tdepth\tref_count\talt_count\talt_fraction\tqual\tmapping_ambiguity\tfilter_reason\tsupport_source\n' > ${meta.taxon}.${meta.arm}.heldout-edit-ledger.tsv
    printf '{"taxon":"%s","arm":"%s","status":"INCONCLUSIVE","assembly_grade":"CANDIDATE","decision":"NOT_APPLICABLE","residual_unsupported_loci":0,"evaluable_homopolymer_discordances":0}\n' '${meta.taxon}' '${meta.arm}' > ${meta.taxon}.${meta.arm}.metrics.json
    """
}
