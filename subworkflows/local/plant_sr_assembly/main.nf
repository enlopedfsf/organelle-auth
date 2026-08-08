//
// PLANT_SR_ASSEMBLY (M1-①): plant short-read organelle assembly.
// 方法学 §3.1/§3.2 Scenario A via nf-core getorganelle (config + fromreads) + a local
// result adapter. -F/-R/-k are GetOrganelle ALGORITHM params (§9.3), verbatim Scenario A
// (set in conf/modules.config per aliased process), identical in all profiles.
// ①→② interface contract: plastome.fasta (CANDIDATE) | plastome.scaffold.fasta (DRAFT),
// nrdna.fasta, assembly_graph.fastg; no forced circularization (§3.6).
//
include { GETORGANELLE_CONFIG as GETORGANELLE_CONFIG_PT } from '../../../modules/nf-core/getorganelle/config/main'
include { GETORGANELLE_CONFIG as GETORGANELLE_CONFIG_NR } from '../../../modules/nf-core/getorganelle/config/main'
include { GETORGANELLE_FROMREADS as GETORGANELLE_FROMREADS_PT } from '../../../modules/nf-core/getorganelle/fromreads/main'
include { GETORGANELLE_FROMREADS as GETORGANELLE_FROMREADS_NR } from '../../../modules/nf-core/getorganelle/fromreads/main'
include { GETORGANELLE_RESULT_ADAPTER as GETORGANELLE_RESULT_ADAPTER_PT } from '../../../modules/local/getorganelle_result_adapter/main'
include { GETORGANELLE_RESULT_ADAPTER as GETORGANELLE_RESULT_ADAPTER_NR } from '../../../modules/local/getorganelle_result_adapter/main'

workflow PLANT_SR_ASSEMBLY {

    take:
    ch_clean_reads   // (meta, [clean_R1, clean_R2])

    main:

    // ---- plastome (embplant_pt): 方法学 §3.1 (-R 15 -k 21,45,65,85,105 in modules.config) ----
    // REAL-DATA FINDING (task 7.1): GetOrganelle `-F embplant_pt` UNCONDITIONALLY requires BOTH
    // the embplant_pt AND embplant_mt reference DBs (get_organelle_from_reads.py ~L549-551 checks
    // both, to disentangle MTPT/PTMT). The nf-core config module fetches only the requested type,
    // so we fetch pt+mt together here. from_reads still assembles the PLASTOME only (-F embplant_pt);
    // the mt DB is present purely to satisfy the cross-check / MTPT filtering.
    db_pt_full = GETORGANELLE_CONFIG_PT(channel.of('embplant_pt,embplant_mt'))
    db_pt      = db_pt_full.db.map { organelle_type, db -> tuple('embplant_pt', db) }
    asm_pt     = GETORGANELLE_FROMREADS_PT(ch_clean_reads, db_pt)
    adapter_pt = GETORGANELLE_RESULT_ADAPTER_PT(asm_pt.etc, channel.value('embplant_pt'))

    // ---- nrDNA (embplant_nr): 方法学 §3.2 (-k 35,85,115 in modules.config) ----
    db_nr      = GETORGANELLE_CONFIG_NR(channel.of('embplant_nr'))
    asm_nr     = GETORGANELLE_FROMREADS_NR(ch_clean_reads, db_nr.db)
    adapter_nr = GETORGANELLE_RESULT_ADAPTER_NR(asm_nr.etc, channel.value('embplant_nr'))

    // Join pt + nr results on meta (always both run; 方法学 §2.3 default plastome + nrDNA).
    // From pt: plastome file, plastome assembly graph, plastome grade, produced flag.
    // From nr: nrdna file, produced flag.
    ch_pt = adapter_pt.plastome \
        .join(adapter_pt.graph) \
        .join(adapter_pt.grade_file) \
        .join(adapter_pt.produced_file)
    // (meta, plastome_file, graph_file, grade_file, produced_file)

    ch_nr = adapter_nr.nrdna.join(adapter_nr.produced_file)
    // (meta, nrdna_file, produced_file)

    ch_assembly = ch_pt.join(ch_nr)
    // (meta, plastome_file, graph_file, grade_file, produced_pt, nrdna_file, produced_nr)

    emit:
    assembly = ch_assembly
    versions = adapter_pt.versions.mix(adapter_nr.versions)
}
