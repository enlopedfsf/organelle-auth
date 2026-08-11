process LR_PREPARE_REFERENCE {
    tag "${meta.id}"
    label 'process_low_memory'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ? 'https://depot.galaxyproject.org/singularity/python:3.12' : 'quay.io/biocontainers/python:3.12' }"

    input:
    val meta
    path(reference, stageAs: 'reference/*')
    path(reference_metadata, stageAs: 'metadata/*')
    path(m1_anchor, stageAs: 'm1-anchor/*')

    output:
    tuple val(meta), path("${meta.id}.reference-rotations.fasta"), path("${meta.id}.reference-coordinate-map.tsv"), path("${meta.id}.reference-status.json"), emit: prepared
    tuple val("${task.process}"), val('organelle_lr_evidence'), val('0.1.0'), topic: versions, emit: versions

    script:
    """
    test -s ${reference}
    test -s ${reference_metadata}
    test -s ${m1_anchor}
    organelle_lr_evidence.py prepare-reference \
      --sample-id '${meta.id}' \
      --fasta ${reference} \
      --metadata ${reference_metadata} \
      --anchor-fasta ${m1_anchor} \
      --out-fasta ${meta.id}.reference-rotations.fasta \
      --out-map ${meta.id}.reference-coordinate-map.tsv \
      --out-status ${meta.id}.reference-status.json
    """

    stub:
    """
    printf '>ref|rot=0\nACGTACGT\n' > ${meta.id}.reference-rotations.fasta
    printf 'target_name\tcanonical_name\toffset_0based\tlength\nref|rot=0\tref\t0\t8\n' > ${meta.id}.reference-coordinate-map.tsv
    printf '{"stage":"long_read_reference_prepare","status":"STUB","decision":"NOT_APPLICABLE"}\n' > ${meta.id}.reference-status.json
    """
}
