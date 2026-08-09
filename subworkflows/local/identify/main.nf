//
// IDENTIFY (M1-②): reference-first identification consuming ①'s frozen outputs (design 决策 5).
//
// LOAD_REFERENCE_PACK (DATA-005) → ALIGN_ASSEMBLY_TO_REFERENCE (minimap2 asm→ref PAF) →
// EVALUATE_CALLABLE_REGIONS (coverage) ‖ EVALUATE_DIAGNOSTIC_SITES (site-level callability+identity)
// → DECISION_ENGINE (决策 1 matrix + 决策 2 null defense) → EMIT_IDENTIFY_STATUS (stage=identify).
//
// ① outputs are read-only inputs; nothing in ① is regenerated. The frozen ①→② interface contract
// lives at openspec/changes/archive/2026-08-09-plant-short-read-assembly-evidence/design.md §1-4.
//

include { LOAD_REFERENCE_PACK         } from '../../../modules/local/load_reference_pack/main'
include { ALIGN_ASSEMBLY_TO_REFERENCE } from '../../../modules/local/align_assembly_to_reference/main'
include { EVALUATE_CALLABLE_REGIONS   } from '../../../modules/local/evaluate_callable_regions/main'
include { EVALUATE_DIAGNOSTIC_SITES   } from '../../../modules/local/evaluate_diagnostic_sites/main'
include { DECISION_ENGINE             } from '../../../modules/local/decision_engine/main'
include { EMIT_IDENTIFY_STATUS        } from '../../../modules/local/emit_identify_status/main'

workflow IDENTIFY {

    take:
    ch_assembly_qc   // (meta, plastome, graph, grade, prod_pt, nrdna, prod_nr, bam, depth, flagstat)
    ch_asm_status    // (meta, status_json)  — ① stage=assembly_qc status JSON

    main:

    // ① evidence + ① status, joined on meta (read-only).
    ch = ch_assembly_qc.join(ch_asm_status)
    // (meta, plastome, graph, grade, prod_pt, nrdna, prod_nr, bam, depth, flagstat, status_json)

    // ---- LOAD_REFERENCE_PACK: resolve reference_pack_id (in meta) → pack; DATA-005 fail-fast ----
    // reference_pack_dir is staged as a path (not a host-path val) so it is visible inside the container.
    ch_meta = ch.map { meta, pl, gr, grade, ppt, nr, pnr, bam, dp, fs, st -> meta }
    pack = LOAD_REFERENCE_PACK(ch_meta, channel.value(file(params.reference_pack_dir)))
    // pack.pack = (meta, manifest, reference_fasta, diagnostic_sites_tsv, callable_regions_tsv)

    ch_packed = ch.join(pack.pack)
    // (meta, plastome, graph, grade, prod_pt, nrdna, prod_nr, bam, depth, flagstat, status_json,
    //  manifest, reference_fasta, diag_tsv, callable_tsv)

    // ---- ALIGN ① selected plastome → reference (决策 5 re-map; asm5 -c --eqx → PAF) ----
    align_in = ch_packed.map { meta, pl, gr, grade, ppt, nr, pnr, bam, dp, fs, st, man, ref, dtv, ctv ->
        tuple(meta, pl, ref) }
    aln = ALIGN_ASSEMBLY_TO_REFERENCE(align_in)
    // aln.paf = (meta, paf)

    ch_aligned = ch_packed.join(aln.paf)
    // (... 15 above ..., paf)

    // ---- EVALUATE_CALLABLE_REGIONS: (meta, paf, callable_tsv, ① depth) ----
    // Closure params are suffixed _f to avoid clashing with the workflow-scoped channel names.
    call_in = ch_aligned.map { meta, pl, gr, grade, ppt, nr, pnr, bam, dp, fs, st, man, ref, dtv, ctv, paf_f ->
        tuple(meta, paf_f, ctv, dp) }
    callr = EVALUATE_CALLABLE_REGIONS(call_in)
    // callr.metrics = (meta, callable.metrics.json)

    // ---- EVALUATE_DIAGNOSTIC_SITES: (meta, paf, diag_tsv, reference_fasta) ----
    diag_in = ch_aligned.map { meta, pl, gr, grade, ppt, nr, pnr, bam, dp, fs, st, man, ref, dtv, ctv, paf_f ->
        tuple(meta, paf_f, dtv, ref) }
    diag = EVALUATE_DIAGNOSTIC_SITES(diag_in)
    // diag.metrics = (meta, diagnostic.metrics.json)

    // ---- join metrics, then DECISION_ENGINE ----
    ch_metrics = ch_aligned.join(callr.metrics).join(diag.metrics)
    // (... 16 ..., callable_metrics, diagnostic_metrics)

    dec_in = ch_metrics.map { meta, pl, gr, grade, ppt, nr, pnr, bam, dp, fs, st, man, ref, dtv, ctv, paf_f, cm_f, dm_f ->
        tuple(meta, grade, ppt, st, cm_f, dm_f, man) }
    // policy_pack_file is staged as a path (file(...)) so DECISION_ENGINE can read it inside the
    // container — a host-path val is NOT mounted under docker (BUG surfaced by the scenario-1 real
    // run; same val→path fix as LOAD_REFERENCE_PACK). null/production → /dev/null stages an empty
    // file → DECISION_ENGINE policy={} → THRESHOLD_NOT_CONFIGURED (决策 2 null defense, unchanged).
    dec = DECISION_ENGINE(dec_in, channel.value(file(params.policy_pack_file ?: '/dev/null')))
    // dec.decision = (meta, decision.json)

    // ---- EMIT_IDENTIFY_STATUS: stage=identify status JSON + staged evidence ----
    ch_decided = ch_metrics.join(dec.decision)
    emit_in = ch_decided.map { meta, pl, gr, grade, ppt, nr, pnr, bam, dp, fs, st, man, ref, dtv, ctv, paf_f, cm_f, dm_f, dec_f ->
        tuple(meta, dec_f, pl, gr, nr, bam, dp, fs, st) }
    emitted = EMIT_IDENTIFY_STATUS(emit_in)

    emit:
    status   = emitted.status_json
    versions = pack.versions.mix(aln.versions).mix(callr.versions).mix(diag.versions).mix(dec.versions).mix(emitted.versions)
}
