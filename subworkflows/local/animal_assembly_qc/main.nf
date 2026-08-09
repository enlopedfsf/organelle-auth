//
// ANIMAL_ASSEMBLY_QC (M2-①): read-back evidence for the animal mitogenome.
// Mirrors ASSEMBLY_QC (M1-①) but for the animal emit shape: clean reads remapped onto the
// mitogenome with minimap2 -ax sr (modules.config), sorted BAM -> samtools depth/flagstat.
// Coverage-valley coefficient is policy-injected (null in experimental -> annotate only).
// Samples that produced no mitogenome get empty read-back markers (ASSEMBLY_FAILED handled
// by the animal status emitter).
//
include { MINIMAP2_ALIGN    } from '../../../modules/nf-core/minimap2/align/main'
include { SAMTOOLS_INDEX    } from '../../../modules/nf-core/samtools/index/main'
include { SAMTOOLS_DEPTH    } from '../../../modules/nf-core/samtools/depth/main'
include { SAMTOOLS_FLAGSTAT } from '../../../modules/nf-core/samtools/flagstat/main'
include { TOUCH_READBACK_MARKERS } from '../../../modules/local/touch_readback_markers/main'

workflow ANIMAL_ASSEMBLY_QC {

    take:
    ch_clean_reads   // (meta, [clean_R1, clean_R2])
    ch_assembly      // (meta, mitogenome, annotation, infos, grade_file, produced_file)

    main:

    ch_asm = ch_assembly.map { meta, mito, ann, infos, gf, pf ->
        tuple(meta, mito, ann, infos, gf.text.trim(), pf.text.trim() == 'true')
    }
    // (meta, mito, ann, infos, grade_val, produced_bool)

    ch_ok   = ch_asm.filter { meta, mito, ann, infos, grade, prod -> prod }
    ch_fail = ch_asm.filter { meta, mito, ann, infos, grade, prod -> !prod }

    // ---- produced: remap clean reads onto the mitogenome (方法学 §3.5/§3.6) ----
    ch_map_in = ch_clean_reads.join(ch_ok)
    ch_reads  = ch_map_in.map { meta, reads, mito, ann, infos, grade, prod -> tuple(meta, reads) }
    ch_target = ch_map_in.map { meta, reads, mito, ann, infos, grade, prod -> tuple(meta, mito) }

    mm2       = MINIMAP2_ALIGN(ch_reads, ch_target, true, '', false, false)
    ch_bam    = mm2.bam                               // (meta, sorted.bam)
    idx       = SAMTOOLS_INDEX(ch_bam)                // (meta, bai)
    ch_bamidx = ch_bam.join(idx.index)                // (meta, bam, bai)

    depth    = SAMTOOLS_DEPTH(ch_bamidx.map { mt, bb, bi -> tuple(mt, bb, bi, []) })
    flagstat = SAMTOOLS_FLAGSTAT(ch_bamidx)

    ch_readback_ok = ch_bam.join(depth.tsv).join(flagstat.flagstat)   // (meta, bam, depth, flagstat)

    // ---- failed: empty read-back markers ----
    ch_readback_fail = TOUCH_READBACK_MARKERS(ch_fail.map { meta, mito, ann, infos, grade, prod -> meta })

    ch_readback = ch_readback_ok.mix(ch_readback_fail)

    ch_out = ch_asm.join(ch_readback)
    // (meta, mito, ann, infos, grade, prod, bam, depth, flagstat)

    emit:
    assembly_qc = ch_out
    versions    = mm2.versions_minimap2
}
