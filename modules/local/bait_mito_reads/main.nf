//
// Local module: multi-reference mitochondrial bait extraction (M2-①, design 决策 2/3).
//
// 方法学 §4.3 adapted to short reads: minimap2 -x sr maps clean reads against a MULTI-reference
// mitogenome set — a single reference can drop the hypervariable control region / D-loop, which is
// exactly the high-discrimination region for animal authentication. Proper-pair reads whose mates
// both map to the reference set are extracted as the mito-enriched bait for MitoFinder.
//
// The multi-reference FASTA is a BUNDLED tool-level resource (design 决策 3) — it enriches, it does
// NOT decide. The ② decision reference pack (diagnostic sites, conflict rules) is a separate asset.
// minimap2 maps each read independently; samtools collate + fixmate recompute proper-pair (0x2)
// flags before filtering, so both mates of a mito-mapped pair are kept (unpaired singletons dropped).

process BAIT_MITO_READS {
    tag "${meta.id}"
    label 'process_low'

    container 'community.wave.seqera.io/library/minimap2_samtools:b09096fc890429ce'

    input:
    tuple val(meta), path(reads), path(reference)   // reads = [R1, R2]; reference = multi-ref FASTA

    output:
    tuple val(meta), path("${meta.id}.R1.fastq"), path("${meta.id}.R2.fastq"), emit: reads
    tuple val("${task.process}"), val('bait_mito_reads'), val('0.1.0'), topic: versions, emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    """
    minimap2 -a -x sr -t ${task.cpus} ${args} ${reference} ${reads} \\
      | samtools view -b -F 0x904 - \\
      | samtools collate -O -u - \\
      | samtools fixmate -m -u - - \\
      | samtools view -b -f 0x2 -F 0x904 - \\
      | samtools fastq -1 ${meta.id}.R1.fastq -2 ${meta.id}.R2.fastq -
    """

    stub:
    """
    echo ">A" > ${meta.id}.R1.fastq
    echo "ACGT" >> ${meta.id}.R1.fastq
    echo ">A" > ${meta.id}.R2.fastq
    echo "TGCA" >> ${meta.id}.R2.fastq
    """
}
