//
// ANIMAL_SR_ASSEMBLY (M2-①): animal short-read mitogenome assembly.
// 方法学 §3.3 + §4.3 (short-read adaptation, design 决策 2/3/4/5):
//   multi-reference bait extraction (minimap2 -x sr) -> MitoFinder assembly + annotation
//   (genetic code etc. in conf/modules.config ext.args) -> animal_result_adapter grading.
// ①→② interface contract: *_mitogenome.fasta (CANDIDATE) | *_mitogenome.scaffold.fasta (DRAFT),
// annotation .gb, .infos; no forced circularization (§3.6). The multi-reference FASTA is a
// bundled tool-level resource (params.animal_bait_reference_fasta); the .gb annotation reference
// (params.animal_annotation_reference_gb) is the conspecific reference for MitoFinder annotation.
//
include { BAIT_MITO_READS } from '../../../modules/local/bait_mito_reads/main'
include { MITOFINDER } from '../../../modules/local/mitofinder/main'
include { ANIMAL_RESULT_ADAPTER } from '../../../modules/local/animal_result_adapter/main'

workflow ANIMAL_SR_ASSEMBLY {

    take:
    ch_clean_reads   // (meta, [clean_R1, clean_R2])
    bait_ref         // path: multi-reference mitogenome FASTA (bundled tool-level resource)
    ann_ref          // path: single GenBank reference for MitoFinder annotation

    main:

    // ---- multi-reference bait (design 决策 2/3; avoids D-loop dropout) ----
    bait = BAIT_MITO_READS(ch_clean_reads.map { meta, reads -> tuple(meta, reads, bait_ref) })
    // (meta, R1.fastq, R2.fastq)

    // ---- MitoFinder de novo assembly + annotation against a single GenBank reference ----
    mf = MITOFINDER(bait.reads.map { meta, r1, r2 -> tuple(meta, r1, r2, ann_ref) })
    // emits: (meta, mitogenome-glob), (meta, annotation-glob), (meta, infos-glob)

    // ---- grade + rename to ①→② contract paths ----
    adapter = ANIMAL_RESULT_ADAPTER(mf.mitogenome.join(mf.annotation).join(mf.infos))
    // (meta, mtfasta, annotation, infos)

    // Join adapter outputs: (meta, mito_file, annotation, infos, grade_file, produced_file)
    ch_assembly = adapter.mitogenome \
        .join(adapter.annotation) \
        .join(adapter.infos) \
        .join(adapter.grade_file) \
        .join(adapter.produced_file)

    emit:
    assembly = ch_assembly
    versions = bait.versions.mix(mf.versions).mix(adapter.versions)
}
