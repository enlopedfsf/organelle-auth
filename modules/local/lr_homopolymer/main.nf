process LR_HOMOPOLYMER {
    tag "${meta.id}"
    label 'process_low_memory'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ? 'https://depot.galaxyproject.org/singularity/python:3.12' : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), path(anchor), path(candidate), path(anchor_paf)
    val platform

    output:
    tuple val(meta), path("${meta.id}.homopolymer-spectrum.json"), path("${meta.id}.homopolymer-spectrum.tsv"), emit: spectrum
    tuple val("${task.process}"), val('organelle_lr_evidence'), val('0.1.0'), topic: versions, emit: versions

    script:
    """
    organelle_lr_evidence.py homopolymer \
      --anchor-fasta ${anchor} --candidate-fasta ${candidate} --paf ${anchor_paf} \
      --platform ${platform} --out-json ${meta.id}.homopolymer-spectrum.json \
      --out-tsv ${meta.id}.homopolymer-spectrum.tsv
    """

    stub:
    """
    printf '{"schema_version":"homopolymer-spectrum-0.1","state":"STUB","platform":"%s","records":[],"callable_run_bases":0,"unliftable_intervals":[]}\n' '${platform}' > ${meta.id}.homopolymer-spectrum.json
    printf 'anchor\tstart_1based\tend_1based\tbase\treference_run_length\tcandidate_run_length\trun_length_delta\tsubstitutions\tdeletions\tinsertions\tstate\n' > ${meta.id}.homopolymer-spectrum.tsv
    """
}
