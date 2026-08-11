process LR_EXTRACT_READS {
    tag "${meta.id}:${label_name}"
    label 'process_low_memory'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ? 'https://depot.galaxyproject.org/singularity/python:3.12' : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), path(reads), path(ids)
    val label_name

    output:
    tuple val(meta), path("${meta.id}.${label_name}.fastq.gz"), path("${meta.id}.${label_name}.manifest.json"), emit: recruited
    tuple val("${task.process}"), val('organelle_lr_evidence'), val('0.1.0'), topic: versions, emit: versions

    script:
    """
    organelle_lr_evidence.py extract-fastq \
      --fastq ${reads} --ids ${ids} \
      --out-fastq ${meta.id}.${label_name}.fastq.gz \
      --out-manifest ${meta.id}.${label_name}.manifest.json
    """

    stub:
    """
    printf '@stub\nACGTACGT\n+\nFFFFFFFF\n' | gzip -c > ${meta.id}.${label_name}.fastq.gz
    printf '{"stage":"long_read_whole_read_extraction","status":"STUB","decision":"NOT_APPLICABLE","output_sha256":"STUB"}\n' > ${meta.id}.${label_name}.manifest.json
    """
}
