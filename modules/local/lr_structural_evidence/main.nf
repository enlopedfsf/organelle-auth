process LR_STRUCTURAL_EVIDENCE {
    tag "${meta.id}"
    label 'process_low_memory'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ? 'https://depot.galaxyproject.org/singularity/python:3.12' : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), path(candidate), path(comparator), path(reference_paf), path(comparator_reference_paf), path(anchor_paf), path(read_candidate_paf)
    path reference_metadata
    path policy
    val platform

    output:
    tuple val(meta), path("${meta.id}.structural-evidence.json"), path("${meta.id}.structural-evidence.tsv"), emit: evidence
    tuple val("${task.process}"), val('organelle_lr_evidence'), val('0.1.0'), topic: versions, emit: versions

    script:
    """
    organelle_lr_evidence.py structural \
      --candidate-fasta ${candidate} --comparator-fasta ${comparator} \
      --reference-paf ${reference_paf} --comparator-reference-paf ${comparator_reference_paf} \
      --anchor-paf ${anchor_paf} --read-candidate-paf ${read_candidate_paf} \
      --reference-metadata ${reference_metadata} --policy ${policy} --platform ${platform} \
      --out-json ${meta.id}.structural-evidence.json --out-tsv ${meta.id}.structural-evidence.tsv
    """

    stub:
    """
    printf '{"stage":"long_read_structural_validation","status":"STUB","decision":"NOT_APPLICABLE","experimental_only":true,"platform":"%s","cycloneseq_transferability":"PENDING_REAL_DATA"}\n' '${platform}' > ${meta.id}.structural-evidence.json
    printf 'metric\tvalue\nir_gap_outcome\tnot_assessable\n' > ${meta.id}.structural-evidence.tsv
    """
}
