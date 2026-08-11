/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    M1-①: plant short-read samples (taxon_group=plant, short reads available,
    targets ⊂ {plastome, nrdna}) are routed explicitly through QC_SHORT →
    PLANT_SR_ASSEMBLY → ASSEMBLY_QC → assembly_qc status emission (§3.3 routing, DATA-006;
    design 决策 on explicit routing).
    M2-①: animal short-read samples (taxon_group=animal, short reads available,
    targets ⊇ {mitome}) are routed explicitly through the SAME QC_SHORT → ANIMAL_SR_ASSEMBLY
    (multi-ref bait → MitoFinder) → ANIMAL_ASSEMBLY_QC (read-back) → NUMT risk screen →
    animal assembly_qc status emission. Plant branch is untouched (regression lossless).
    Other sample classes (long-read, hybrid) remain future milestones.
----------------------------------------------------------------------------------------
*/

include { QC_SHORT               } from '../subworkflows/local/qc_short'
include { PLANT_SR_ASSEMBLY      } from '../subworkflows/local/plant_sr_assembly'
include { ASSEMBLY_QC            } from '../subworkflows/local/assembly_qc'
include { IDENTIFY               } from '../subworkflows/local/identify'
include { EMIT_ASSEMBLY_QC_STATUS } from '../modules/local/emit_assembly_qc_status/main'
include { ANIMAL_SR_ASSEMBLY     } from '../subworkflows/local/animal_sr_assembly'
include { ANIMAL_ASSEMBLY_QC     } from '../subworkflows/local/animal_assembly_qc'
include { NUMT_RISK_SCREEN       } from '../modules/local/numt_risk_screen/main'
include { EMIT_ANIMAL_ASSEMBLY_QC_STATUS } from '../modules/local/emit_animal_assembly_qc_status/main'
include { PLANT_LONG_READ_REFERENCE_FIRST } from '../subworkflows/local/plant_long_read_reference_first'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow ORGANELLEAUTH {

    take:
    ch_samplesheet // channel: (meta, [short_reads...], long_reads) from PIPELINE_INITIALISATION
    outdir

    main:

    //
    // Explicit routing (§3.3 / DATA-006): plant samples with short reads whose targets are a
    // subset of {plastome, nrdna} (must include plastome). Nothing is inferred from filenames.
    //
    ch_plant_sr = ch_samplesheet.filter { row ->
        def meta = row[0]
        meta.taxon_group == 'plant' &&
        meta.has_short_reads &&
        meta.targets.every { it in ['plastome', 'nrdna'] } &&
        meta.targets.contains('plastome')
    }

    // M2-① animal routing: taxon_group=animal + short reads + targets ⊇ {mitome}.
    ch_animal_sr = ch_samplesheet.filter { row ->
        def meta = row[0]
        meta.taxon_group == 'animal' &&
        meta.has_short_reads &&
        meta.targets.contains('mitome')
    }

    // M3 route is deliberately isolated from all short-read assembly/identify channels.
    // Its outputs are experimental evidence only and cannot reach IDENTIFY or DECISION_ENGINE.
    ch_plant_lr = ch_samplesheet.filter { row ->
        def meta = row[0]
        meta.analysis_mode == 'long_read_pilot' && meta.taxon_group == 'plant' && meta.has_long_reads
    }
    lr_policy_file = file(params.long_read_reference_first_policy_file)
    lr_policy_data = new groovy.json.JsonSlurper().parse(lr_policy_file.toFile())
    lr_manifest_file = file(params.long_read_pilot_manifest)
    lr_manifest_data = new groovy.json.JsonSlurper().parse(lr_manifest_file.toFile())
    // A missing M1 anchor is tolerated only when the LR channel is empty. Any actual pilot task
    // stages this explicit path and fails before alignment if it is missing/empty.
    lr_m1_anchor = file(params.long_read_pilot_m1_anchor_fasta ?: "${projectDir}/assets/long_read_pilot/M1_ANCHOR_NOT_CONFIGURED")
    lr_pilot = PLANT_LONG_READ_REFERENCE_FIRST(
        ch_plant_lr,
        file(params.long_read_pilot_reference_fasta),
        file(params.long_read_pilot_reference_metadata),
        lr_m1_anchor,
        lr_policy_file,
        lr_policy_data,
        lr_manifest_data.platform
    )

    // One QC_SHORT (fastp) invocation serves BOTH branches (Nextflow DSL2: a process cannot be
    // included twice in one workflow). Plant + animal clean reads are split after QC.
    ch_all_sr    = ch_plant_sr.mix(ch_animal_sr)
    qc           = QC_SHORT(ch_all_sr)
    ch_plant_clean = qc.clean_reads.filter { meta, reads -> meta.taxon_group == 'plant' }
    ch_animal_clean = qc.clean_reads.filter { meta, reads -> meta.taxon_group == 'animal' }

    asm = PLANT_SR_ASSEMBLY(ch_plant_clean)
    aqc = ASSEMBLY_QC(ch_plant_clean, asm.assembly)

    // Emit stage=assembly_qc status (decision=NOT_APPLICABLE; ① does not decide).
    // coverage_valley_coefficient is policy-injected (null in experimental).
    emit_asm = EMIT_ASSEMBLY_QC_STATUS(aqc.assembly_qc)

    // ② IDENTIFY (M1-②): route analysis_mode=identify plant samples → IDENTIFY after ① assembly_qc.
    // ① outputs feed ② unchanged (read-only); non-identify samples are filtered out, so when no
    // identify-mode sample is present IDENTIFY simply runs no tasks (empty input channel).
    ch_id_asm    = aqc.assembly_qc.filter { meta, pl, gr, grade, ppt, nr, pnr, bam, dp, fs -> meta.analysis_mode == 'identify' }
    ch_id_status = emit_asm.status_json.filter { meta, status_json -> meta.analysis_mode == 'identify' }

    //
    // M2-① animal branch: same QC_SHORT + read-back reuse; animal-specific assembly (MitoFinder),
    // NUMT risk screen, and a dedicated animal assembly_qc status emitter.
    //
    asm_a = ANIMAL_SR_ASSEMBLY(ch_animal_clean, params.animal_bait_reference_fasta, params.animal_annotation_reference_gb)
    aqc_a = ANIMAL_ASSEMBLY_QC(ch_animal_clean, asm_a.assembly)

    // NUMT risk screen on the mitogenome + read-back (coverage heterogeneity + multi-mapping).
    ch_numt_in = aqc_a.assembly_qc.map { meta, mito, ann, infos, grade, prod, bam, depth, flagstat ->
        tuple(meta, mito, bam, depth)
    }
    numt_a = NUMT_RISK_SCREEN(ch_numt_in)

    // Emit animal stage=assembly_qc status (decision=NOT_APPLICABLE). NUMT signal → WARN +
    // NUMT_RISK_SUSPECTED (design 决策 6; screening, not confirmation).
    ch_emit_a = aqc_a.assembly_qc.join(numt_a.signal).map { meta, mito, ann, infos, grade, prod, bam, depth, flagstat, ns ->
        tuple(meta, mito, ann, infos, grade, prod, bam, depth, flagstat, ns)
    }
    emit_a = EMIT_ANIMAL_ASSEMBLY_QC_STATUS(ch_emit_a)

    // M2-② animal identify reuses the frozen IDENTIFY skeleton. The adapter below only changes
    // tuple shape: animal mitogenome/annotation are read-only evidence, and no plant asset is
    // regenerated. The shared decision engine selects the animal pack from meta.reference_pack_id.
    ch_id_animal_asm = aqc_a.assembly_qc.filter { meta, mito, ann, infos, grade, prod, bam, dp, fs -> meta.analysis_mode == 'identify' }
        .map { meta, mito, ann, infos, grade, prod, bam, dp, fs ->
            tuple(meta, mito, ann, grade, prod, ann, prod, bam, dp, fs)
        }
    ch_id_animal_status = emit_a.status_json.filter { meta, status_json -> meta.analysis_mode == 'identify' }
    identify = IDENTIFY(ch_id_asm.mix(ch_id_animal_asm), ch_id_status.mix(ch_id_animal_status))

    log.info "[organelleauth] M1/M2 short-read routes remain unchanged. M3 uses isolated reference-first recruitment -> Flye subset primary -> PMAT2 -p 0 comparator evidence; it never feeds IDENTIFY/DECISION."

    emit:
    multiqc_report = channel.empty().toList()   // MultiQC wiring is out of scope
    versions       = emit_asm.versions.mix(asm.versions).mix(identify.versions).mix(lr_pilot.versions)
                        .mix(asm_a.versions).mix(aqc_a.versions).mix(numt_a.versions).mix(emit_a.versions)
    status         = emit_asm.status_json.mix(identify.status).mix(emit_a.status_json).mix(lr_pilot.status)
}
