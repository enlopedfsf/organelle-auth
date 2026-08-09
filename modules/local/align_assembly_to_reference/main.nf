//
// Local module: align ①'s selected plastome to the reference (M1-② IDENTIFY, design 决策 5).
//
// Re-maps the ① assembled plastome (single circular contig OR multi-scaffold DRAFT) onto the
// reference-pack reference with minimap2 `-x asm5` (assembly-to-reference, ≤5 % divergence;
// appropriate for intra-species/congeneric authentication). `-c --eqx` emits a PAF whose CIGAR
// uses = / X, so identity + reference-span coverage are derived from a plain-text PAF downstream
// (pure stdlib Python — no pysam, no BAM). This realizes 决策 5's "re-map ①'s selected plastome to
// the reference, reusing minimap2"; the site-level callability + identity computed from this PAF
// are the degenerate v0.1 global-alignment substitute (design Risks / 决策 1).
//
// ① outputs are read-only: this module only READS the plastome FASTA, it never regenerates ①.

process ALIGN_ASSEMBLY_TO_REFERENCE {
    tag "${meta.id}"
    label 'process_low'

    conda "${moduleDir}/environment.yml"
    // minimap2 binary-only image (no python needed — this is a pure shell wrapper). Reuses the
    // same minimap2_samtools image as nf-core minimap2/align so the tool version matches ①.
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container
        ? 'https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/37/37671219cfd244eb9b33db9345d3543ffd83037419a1c57f4648aace493ec2c2/data'
        : 'community.wave.seqera.io/library/minimap2_samtools:b09096fc890429ce' }"

    input:
    tuple val(meta), path(plastome), path(reference_fasta)

    output:
    tuple val(meta), path("${meta.id}.assembly_to_ref.paf"), emit: paf
    tuple val("${task.process}"), val('align_assembly_to_reference'), val('0.1.0'), topic: versions, emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    """
    minimap2 \\
        -x asm5 \\
        -c --eqx \\
        ${args} \\
        -t ${task.cpus} \\
        "${reference_fasta}" "${plastome}" \\
        > "${meta.id}.assembly_to_ref.paf"

    # minimap2 exits non-zero only on tool error; an empty PAF (no alignments) is a legitimate
    # scientific signal (assembly does not align to reference) handled downstream, not a crash.
    """

    stub:
    """
    # one synthetic spanning alignment over [1,4] with 4 matches (identity 1.0)
    printf '%s\t8\t0\t8\t+\tref_stub\t8\t1\t4\t4\t4\t60\tcg:Z:4=\\n' "${meta.id}" > "${meta.id}.assembly_to_ref.paf"
    """
}
