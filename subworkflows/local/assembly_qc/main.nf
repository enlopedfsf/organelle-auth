//
// ASSEMBLY_QC (M1-①): read-back evidence.
// 方法学 §3.5 回贴验证 + §3.6 降级路径: clean reads remapped onto the assembled plastome
// with minimap2 -ax sr (modules.config), sorted BAM (built into minimap2/align when
// bam_format=true) → samtools depth/flagstat. Coverage-valley coefficient is policy-injected
// (null in experimental → annotate only; the coefficient itself is NOT computed here, so no
// scientific threshold is hardcoded — SCI-005/ENG-POL-002). Samples that produced no
// plastome get empty read-back markers (ASSEMBLY_FAILED handled by the emitter).
//
include { MINIMAP2_ALIGN    } from '../../../modules/nf-core/minimap2/align/main'
include { SAMTOOLS_INDEX    } from '../../../modules/nf-core/samtools/index/main'
include { SAMTOOLS_DEPTH    } from '../../../modules/nf-core/samtools/depth/main'
include { SAMTOOLS_FLAGSTAT } from '../../../modules/nf-core/samtools/flagstat/main'
include { TOUCH_READBACK_MARKERS } from '../../../modules/local/touch_readback_markers/main'

workflow ASSEMBLY_QC {

    take:
    ch_clean_reads   // (meta, [clean_R1, clean_R2])
    ch_assembly      // (meta, plastome_file, graph_file, grade_file, produced_pt_file, nrdna_file, produced_nr_file)

    main:

    // Read signal files into vals; keep the plastome as mapping target.
    // (meta, plastome, graph, grade_val, produced_pt_bool, nrdna, produced_nr_bool)
    ch_asm = ch_assembly.map { meta, plasto, graph, gf, pf, nrdna, pfn ->
        tuple(meta, plasto, graph, gf.text.trim(), pf.text.trim() == 'true', nrdna, pfn.text.trim() == 'true')
    }

    ch_ok   = ch_asm.filter { meta, plasto, graph, grade, prod_pt, nrdna, prod_nr -> prod_pt }
    ch_fail = ch_asm.filter { meta, plasto, graph, grade, prod_pt, nrdna, prod_nr -> !prod_pt }

    // ---- produced: remap clean reads onto the plastome (方法学 §3.5/§3.6) ----
    ch_map_in = ch_clean_reads.join(ch_ok)        // (meta, reads, plasto, graph, grade, prod_pt, nrdna, prod_nr)
    ch_reads  = ch_map_in.map { meta, reads, plasto, graph, grade, prod_pt, nrdna, prod_nr -> tuple(meta, reads) }
    ch_target = ch_map_in.map { meta, reads, plasto, graph, grade, prod_pt, nrdna, prod_nr -> tuple(meta, plasto) }

    // bam_format=true → module-internal `samtools sort` yields a sorted BAM directly.
    mm2       = MINIMAP2_ALIGN(ch_reads, ch_target, true, '', false, false)
    ch_bam    = mm2.bam                               // (meta, sorted.bam)
    idx       = SAMTOOLS_INDEX(ch_bam)                // (meta, bai)
    ch_bamidx = ch_bam.join(idx.index)                // (meta, bam, bai)

    // SAMTOOLS_DEPTH takes (meta, bam, index, intervals) as ONE tuple; intervals=[] → whole-genome depth.
    depth    = SAMTOOLS_DEPTH(ch_bamidx.map { mt, bb, bi -> tuple(mt, bb, bi, []) })
    flagstat = SAMTOOLS_FLAGSTAT(ch_bamidx)

    ch_readback_ok = ch_bam.join(depth.tsv).join(flagstat.flagstat)   // (meta, bam, depth, flagstat)

    // ---- failed: empty read-back markers (no target to map onto) ----
    ch_readback_fail = TOUCH_READBACK_MARKERS(ch_fail.map { meta, plasto, graph, grade, prod_pt, nrdna, prod_nr -> meta })

    ch_readback = ch_readback_ok.mix(ch_readback_fail)   // all samples carry read-back (real or markers)

    ch_out = ch_asm.join(ch_readback)   // assembly info + read-back

    emit:
    assembly_qc = ch_out   // (meta, plastome, graph, grade, prod_pt, nrdna, prod_nr, bam, depth, flagstat)
    versions    = mm2.versions_minimap2
}
