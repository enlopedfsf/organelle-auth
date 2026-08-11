/*
 * M3 EXPERIMENTAL plant long-read evidence route.
 * It is deliberately unreachable from IDENTIFY and DECISION_ENGINE.
 */
include { LR_BUDGET_FASTQ } from '../../../modules/local/lr_budget_fastq/main'
include { LR_PREPARE_REFERENCE } from '../../../modules/local/lr_prepare_reference/main'
include { LR_MAP_MINIMAP2 as LR_MAP_PASS1 } from '../../../modules/local/lr_map_minimap2/main'
include { LR_SELECT_PAF as LR_SELECT_PASS1 } from '../../../modules/local/lr_select_paf/main'
include { LR_EXTRACT_READS as LR_EXTRACT_PASS1 } from '../../../modules/local/lr_extract_reads/main'
include { LR_TARGET_GATE as LR_GATE_PASS1 } from '../../../modules/local/lr_target_gate/main'
include { FLYE_SUBSET as FLYE_PRELIMINARY } from '../../../modules/local/flye_subset/main'
include { LR_MAP_MINIMAP2 as LR_MAP_PASS2 } from '../../../modules/local/lr_map_minimap2/main'
include { LR_SELECT_PAF as LR_SELECT_PASS2 } from '../../../modules/local/lr_select_paf/main'
include { LR_UNION_IDS } from '../../../modules/local/lr_union_ids/main'
include { LR_EXTRACT_READS as LR_EXTRACT_FINAL } from '../../../modules/local/lr_extract_reads/main'
include { LR_TARGET_GATE as LR_GATE_FINAL } from '../../../modules/local/lr_target_gate/main'
include { FLYE_SUBSET as FLYE_FINAL } from '../../../modules/local/flye_subset/main'
include { PMAT2_SUBSET_COMPARATOR } from '../../../modules/local/pmat2_subset_comparator/main'
include { LR_ROUTE_GUARD } from '../../../modules/local/lr_route_guard/main'
include { LR_MAP_MINIMAP2 as LR_ALIGN_FLYE_REFERENCE } from '../../../modules/local/lr_map_minimap2/main'
include { LR_MAP_MINIMAP2 as LR_ALIGN_PMAT_REFERENCE } from '../../../modules/local/lr_map_minimap2/main'
include { LR_MAP_MINIMAP2 as LR_ALIGN_FLYE_ANCHOR } from '../../../modules/local/lr_map_minimap2/main'
include { LR_MAP_MINIMAP2 as LR_MAP_FINAL_READS_TO_FLYE } from '../../../modules/local/lr_map_minimap2/main'
include { LR_STRUCTURAL_EVIDENCE } from '../../../modules/local/lr_structural_evidence/main'
include { LR_HOMOPOLYMER } from '../../../modules/local/lr_homopolymer/main'

workflow PLANT_LONG_READ_REFERENCE_FIRST {
    take:
    samples
    reference_fasta
    reference_metadata
    m1_anchor_fasta
    policy_file
    policy_data
    platform

    main:
    ch_meta = samples.map { meta, short_reads, long_reads -> meta }
    ch_long_reads = samples.map { meta, short_reads, long_reads -> tuple(meta, long_reads) }

    LR_BUDGET_FASTQ(ch_long_reads, policy_file)
    LR_PREPARE_REFERENCE(ch_meta, reference_fasta, reference_metadata, m1_anchor_fasta)

    ch_map1 = LR_BUDGET_FASTQ.out.bounded
        .join(LR_PREPARE_REFERENCE.out.prepared)
        .map { meta, bounded, budget_manifest, rotations, coordinate_map, reference_status ->
            tuple(meta, bounded, rotations)
        }
    LR_MAP_PASS1(ch_map1, policy_data, 'mapper', 'recruitment_pass1')

    ch_select1 = LR_MAP_PASS1.out.alignment.map { meta, paf, command -> tuple(meta, paf) }
    LR_SELECT_PASS1(ch_select1, policy_file, 1)

    ch_extract1 = LR_BUDGET_FASTQ.out.bounded
        .join(LR_SELECT_PASS1.out.ids)
        .map { meta, bounded, budget_manifest, ids -> tuple(meta, bounded, ids) }
    LR_EXTRACT_PASS1(ch_extract1, 'pass1-recruited')

    ch_gate1 = LR_SELECT_PASS1.out.evidence
        .join(LR_SELECT_PASS1.out.ids)
        .join(LR_PREPARE_REFERENCE.out.prepared)
        .join(LR_EXTRACT_PASS1.out.recruited)
        .map { meta, evidence, ids, rotations, coordinate_map, reference_status, recruited, extraction_manifest ->
            tuple(meta, evidence, ids, coordinate_map, recruited)
        }
    LR_GATE_PASS1(ch_gate1, reference_metadata, policy_file, 'pass1')

    ch_preliminary = LR_EXTRACT_PASS1.out.recruited
        .join(LR_GATE_PASS1.out.status)
        .map { meta, recruited, extraction_manifest, gate_status -> tuple(meta, recruited, gate_status) }
    FLYE_PRELIMINARY(ch_preliminary, policy_file, policy_data, 'preliminary')

    // Candidate-guided rescue is invoked at most once. With rescue disabled or an ineligible
    // preliminary gate, downstream union deterministically retains pass-one identifiers only.
    ch_map2 = LR_BUDGET_FASTQ.out.bounded
        .join(FLYE_PRELIMINARY.out.assembly)
        .map { meta, bounded, budget_manifest, candidate, assembly_status, command -> tuple(meta, bounded, candidate) }
    LR_MAP_PASS2(ch_map2, policy_data, 'mapper', 'recruitment_pass2')
    ch_select2 = LR_MAP_PASS2.out.alignment.map { meta, paf, command -> tuple(meta, paf) }
    LR_SELECT_PASS2(ch_select2, policy_file, 2)

    ch_union = LR_SELECT_PASS1.out.ids
        .join(LR_SELECT_PASS2.out.ids)
        .map { meta, pass1_ids, pass2_ids -> tuple(meta, pass1_ids, pass2_ids) }
    LR_UNION_IDS(ch_union, policy_file)

    ch_extract_final = LR_BUDGET_FASTQ.out.bounded
        .join(LR_UNION_IDS.out.union)
        .map { meta, bounded, budget_manifest, ids, union_manifest -> tuple(meta, bounded, ids) }
    LR_EXTRACT_FINAL(ch_extract_final, 'final-recruited')

    ch_gate_final = LR_SELECT_PASS1.out.evidence
        .join(LR_SELECT_PASS2.out.evidence)
        .join(LR_UNION_IDS.out.union)
        .join(LR_PREPARE_REFERENCE.out.prepared)
        .join(LR_EXTRACT_FINAL.out.recruited)
        .map { meta, evidence1, evidence2, ids, union_manifest, rotations, coordinate_map, reference_status, recruited, extraction_manifest ->
            tuple(meta, [evidence1, evidence2], ids, coordinate_map, recruited)
        }
    LR_GATE_FINAL(ch_gate_final, reference_metadata, policy_file, 'final')

    ch_final_assembly = LR_EXTRACT_FINAL.out.recruited
        .join(LR_GATE_FINAL.out.status)
        .map { meta, recruited, extraction_manifest, gate_status -> tuple(meta, recruited, gate_status) }
    FLYE_FINAL(ch_final_assembly, policy_file, policy_data, 'final')
    PMAT2_SUBSET_COMPARATOR(ch_final_assembly, policy_file, policy_data)

    // The guard is evidence even though this corrected route has a usable reference. Its output
    // proves full-background PMAT2 is not a silent fallback for shallow data.
    LR_ROUTE_GUARD(ch_meta, policy_file, 'usable', 'reference_first', -1.0)

    ch_flye_ref = FLYE_FINAL.out.assembly
        .map { meta, candidate, status, command -> tuple(meta, candidate, reference_fasta) }
    LR_ALIGN_FLYE_REFERENCE(ch_flye_ref, policy_data, 'structural_alignment', 'flye_to_reference')

    ch_pmat_ref = PMAT2_SUBSET_COMPARATOR.out.assembly
        .map { meta, candidate, status, command -> tuple(meta, candidate, reference_fasta) }
    LR_ALIGN_PMAT_REFERENCE(ch_pmat_ref, policy_data, 'structural_alignment', 'pmat2_to_reference')

    ch_flye_anchor = FLYE_FINAL.out.assembly
        .map { meta, candidate, status, command -> tuple(meta, candidate, m1_anchor_fasta) }
    LR_ALIGN_FLYE_ANCHOR(ch_flye_anchor, policy_data, 'structural_alignment', 'flye_to_m1_anchor')

    ch_reads_to_flye = LR_EXTRACT_FINAL.out.recruited
        .join(FLYE_FINAL.out.assembly)
        .map { meta, recruited, extraction_manifest, candidate, status, command -> tuple(meta, recruited, candidate) }
    LR_MAP_FINAL_READS_TO_FLYE(ch_reads_to_flye, policy_data, 'mapper', 'reads_to_flye')

    ch_structural = FLYE_FINAL.out.assembly
        .join(PMAT2_SUBSET_COMPARATOR.out.assembly)
        .join(LR_ALIGN_FLYE_REFERENCE.out.alignment)
        .join(LR_ALIGN_PMAT_REFERENCE.out.alignment)
        .join(LR_ALIGN_FLYE_ANCHOR.out.alignment)
        .join(LR_MAP_FINAL_READS_TO_FLYE.out.alignment)
        .map { meta, flye, flye_status, flye_command, pmat, pmat_status, pmat_command,
               flye_ref_paf, flye_ref_command, pmat_ref_paf, pmat_ref_command,
               anchor_paf, anchor_command, read_paf, read_command ->
            tuple(meta, flye, pmat, flye_ref_paf, pmat_ref_paf, anchor_paf, read_paf)
        }
    LR_STRUCTURAL_EVIDENCE(ch_structural, reference_metadata, policy_file, platform)

    ch_homopolymer = FLYE_FINAL.out.assembly
        .join(LR_ALIGN_FLYE_ANCHOR.out.alignment)
        .map { meta, candidate, status, command, anchor_paf, anchor_command ->
            tuple(meta, m1_anchor_fasta, candidate, anchor_paf)
        }
    LR_HOMOPOLYMER(ch_homopolymer, platform)

    emit:
    report = LR_STRUCTURAL_EVIDENCE.out.evidence
    status = LR_GATE_FINAL.out.status
    primary_assembly = FLYE_FINAL.out.assembly
    comparator_assembly = PMAT2_SUBSET_COMPARATOR.out.assembly
    recruitment = LR_UNION_IDS.out.union
    target_metrics = LR_GATE_FINAL.out.metrics
    homopolymer = LR_HOMOPOLYMER.out.spectrum
    route_guard = LR_ROUTE_GUARD.out.status
    versions = LR_BUDGET_FASTQ.out.versions
        .mix(LR_PREPARE_REFERENCE.out.versions)
        .mix(LR_MAP_PASS1.out.versions)
        .mix(LR_SELECT_PASS1.out.versions)
        .mix(LR_EXTRACT_PASS1.out.versions)
        .mix(LR_GATE_PASS1.out.versions)
        .mix(FLYE_PRELIMINARY.out.versions)
        .mix(LR_MAP_PASS2.out.versions)
        .mix(LR_SELECT_PASS2.out.versions)
        .mix(LR_UNION_IDS.out.versions)
        .mix(LR_EXTRACT_FINAL.out.versions)
        .mix(LR_GATE_FINAL.out.versions)
        .mix(FLYE_FINAL.out.versions)
        .mix(PMAT2_SUBSET_COMPARATOR.out.versions)
        .mix(LR_ROUTE_GUARD.out.versions)
        .mix(LR_ALIGN_FLYE_REFERENCE.out.versions)
        .mix(LR_ALIGN_PMAT_REFERENCE.out.versions)
        .mix(LR_ALIGN_FLYE_ANCHOR.out.versions)
        .mix(LR_MAP_FINAL_READS_TO_FLYE.out.versions)
        .mix(LR_STRUCTURAL_EVIDENCE.out.versions)
        .mix(LR_HOMOPOLYMER.out.versions)
}
