/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    M1-①: plant short-read samples (taxon_group=plant, short reads available,
    targets ⊂ {plastome, nrdna}) are routed explicitly through QC_SHORT →
    PLANT_SR_ASSEMBLY → ASSEMBLY_QC → assembly_qc status emission (§3.3 routing, DATA-006;
    design 决策 on explicit routing). Other sample classes (animal, long-read, hybrid) are
    not handled by ① and remain future milestones.
----------------------------------------------------------------------------------------
*/

include { QC_SHORT               } from '../subworkflows/local/qc_short'
include { PLANT_SR_ASSEMBLY      } from '../subworkflows/local/plant_sr_assembly'
include { ASSEMBLY_QC            } from '../subworkflows/local/assembly_qc'
include { IDENTIFY               } from '../subworkflows/local/identify'
include { EMIT_ASSEMBLY_QC_STATUS } from '../modules/local/emit_assembly_qc_status/main'

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

    qc  = QC_SHORT(ch_plant_sr)
    asm = PLANT_SR_ASSEMBLY(qc.clean_reads)
    aqc = ASSEMBLY_QC(qc.clean_reads, asm.assembly)

    // Emit stage=assembly_qc status (decision=NOT_APPLICABLE; ① does not decide).
    // coverage_valley_coefficient is policy-injected (null in experimental).
    emit_asm = EMIT_ASSEMBLY_QC_STATUS(aqc.assembly_qc)

    // ② IDENTIFY (M1-②): route analysis_mode=identify plant samples → IDENTIFY after ① assembly_qc.
    // ① outputs feed ② unchanged (read-only); non-identify samples are filtered out, so when no
    // identify-mode sample is present IDENTIFY simply runs no tasks (empty input channel).
    ch_id_asm    = aqc.assembly_qc.filter { meta, pl, gr, grade, ppt, nr, pnr, bam, dp, fs -> meta.analysis_mode == 'identify' }
    ch_id_status = emit_asm.status_json.filter { meta, status_json -> meta.analysis_mode == 'identify' }
    identify = IDENTIFY(ch_id_asm, ch_id_status)

    log.info "[organelleauth] M1-①+②: plant short-read samples → assembly + read-back evidence; identify-mode samples → IDENTIFY."

    emit:
    multiqc_report = channel.empty().toList()   // MultiQC wiring is out of scope
    versions       = emit_asm.versions.mix(asm.versions).mix(identify.versions)
    status         = emit_asm.status_json.mix(identify.status)
}
