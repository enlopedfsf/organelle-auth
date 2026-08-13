include { M4_BWA_ALIGN } from '../../../modules/local/m4_bwa_align/main'
include { M4_POLYPOLISH } from '../../../modules/local/m4_polypolish/main'
include { M4_SR_ALIGN as M4_SR_ALIGN_TRAIN } from '../../../modules/local/m4_sr_align/main'
include { M4_BCFTOOLS_CALL as M4_BCFTOOLS_CALL_TRAIN } from '../../../modules/local/m4_bcftools_call/main'
include { M4_BCFTOOLS_CONSENSUS } from '../../../modules/local/m4_bcftools_consensus/main'
include { M4_CANDIDATE_TO_B0 } from '../../../modules/local/m4_candidate_to_b0/main'
include { M4_LIFT_MASK } from '../../../modules/local/m4_lift_mask/main'
include { M4_SR_ALIGN as M4_SR_ALIGN_HELDOUT } from '../../../modules/local/m4_sr_align/main'
include { M4_BCFTOOLS_CALL as M4_BCFTOOLS_CALL_HELDOUT } from '../../../modules/local/m4_bcftools_call/main'
include { M4_HELDOUT_EVALUATE } from '../../../modules/local/m4_heldout_evaluate/main'

/*
 * M4 EXPERIMENTAL hybrid-reference evidence route.
 *
 * Input tuple:
 *   meta, B0, R1, train_R1, train_R2, heldout_R1, heldout_R2, B0_core_BED
 *
 * This subworkflow is intentionally not imported by workflows/organelleauth.nf.  Its candidates
 * cannot reach IDENTIFY or DECISION, and all emitted metric JSONs retain INCONCLUSIVE/CANDIDATE/
 * NOT_APPLICABLE.
 */
workflow HYBRID_REFERENCE_BUILD {
    take:
    samples
    evaluation_policy

    main:
    ch_base = samples.flatMap { meta, b0, r1, train_r1, train_r2, heldout_r1, heldout_r2, source_bed ->
        def common = [
            taxon: meta.taxon,
            sample_id: meta.sample_id,
            b0_ref: b0,
            heldout_r1: heldout_r1,
            heldout_r2: heldout_r2,
            source_bed: source_bed,
            status: 'INCONCLUSIVE',
            assembly_grade: 'CANDIDATE',
            decision: 'NOT_APPLICABLE'
        ]
        [
            tuple(common + [arm: 'B0', p_output_arm: 'P0', c_output_arm: 'C0', split: 'train'], b0, train_r1, train_r2),
            tuple(common + [arm: 'R1', p_output_arm: 'R1P1', c_output_arm: 'R1C1', split: 'train'], r1, train_r1, train_r2)
        ]
    }

    // Polypolish and bcftools are parallel routes from each frozen backbone stratum.
    ch_p_base = ch_base.map { meta, candidate, train_r1, train_r2 ->
        tuple(meta + [output_arm: meta.p_output_arm], candidate, train_r1, train_r2)
    }
    M4_BWA_ALIGN(ch_p_base)
    M4_POLYPOLISH(M4_BWA_ALIGN.out.alignments)

    ch_c_base = ch_base.map { meta, candidate, train_r1, train_r2 ->
        tuple(meta + [output_arm: meta.c_output_arm], candidate, train_r1, train_r2)
    }
    M4_SR_ALIGN_TRAIN(ch_c_base)
    M4_BCFTOOLS_CALL_TRAIN(M4_SR_ALIGN_TRAIN.out.alignment)
    M4_BCFTOOLS_CONSENSUS(M4_BCFTOOLS_CALL_TRAIN.out.calls)

    ch_static = ch_base.map { meta, candidate, train_r1, train_r2 ->
        tuple(meta + [output_arm: meta.arm], candidate, meta.b0_ref, meta.source_bed, meta.heldout_r1, meta.heldout_r2)
    }
    ch_polypolish = M4_POLYPOLISH.out.candidate.map { meta, candidate, debug, filter_log ->
        tuple(meta + [arm: meta.output_arm], candidate, meta.b0_ref, meta.source_bed, meta.heldout_r1, meta.heldout_r2)
    }
    ch_bcftools = M4_BCFTOOLS_CONSENSUS.out.candidate.map { meta, candidate, training_vcf ->
        tuple(meta + [arm: meta.output_arm], candidate, meta.b0_ref, meta.source_bed, meta.heldout_r1, meta.heldout_r2)
    }
    ch_candidates = ch_static.mix(ch_polypolish).mix(ch_bcftools)

    // Translate only the frozen B0 core coordinates; this operation cannot support topology.
    M4_CANDIDATE_TO_B0(ch_candidates)
    M4_LIFT_MASK(M4_CANDIDATE_TO_B0.out.alignment)

    // Every final arm receives a fresh independent held-out alignment in its own coordinate frame.
    ch_heldout = M4_LIFT_MASK.out.lifted.map { meta, candidate, heldout_r1, heldout_r2, core_bed, liftover_json ->
        tuple(meta + [split: 'heldout', core_bed: core_bed, liftover_json: liftover_json], candidate, heldout_r1, heldout_r2)
    }
    M4_SR_ALIGN_HELDOUT(ch_heldout)
    M4_BCFTOOLS_CALL_HELDOUT(M4_SR_ALIGN_HELDOUT.out.alignment)
    ch_evaluate = M4_BCFTOOLS_CALL_HELDOUT.out.calls.map { meta, candidate, bam, bai, depth, vcf, csi ->
        tuple(meta, candidate, bam, bai, depth, vcf, csi, meta.core_bed, meta.liftover_json)
    }
    M4_HELDOUT_EVALUATE(ch_evaluate, evaluation_policy)

    emit:
    candidates = ch_candidates
    evidence = M4_HELDOUT_EVALUATE.out.evidence
    versions = M4_BWA_ALIGN.out.versions
        .mix(M4_POLYPOLISH.out.versions)
        .mix(M4_SR_ALIGN_TRAIN.out.versions)
        .mix(M4_BCFTOOLS_CALL_TRAIN.out.versions)
        .mix(M4_BCFTOOLS_CONSENSUS.out.versions)
        .mix(M4_CANDIDATE_TO_B0.out.versions)
        .mix(M4_LIFT_MASK.out.versions)
        .mix(M4_SR_ALIGN_HELDOUT.out.versions)
        .mix(M4_BCFTOOLS_CALL_HELDOUT.out.versions)
        .mix(M4_HELDOUT_EVALUATE.out.versions)
}
