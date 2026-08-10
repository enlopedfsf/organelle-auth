/* M3 plant long-read pilot. Experimental evidence only: no decision/status contract. */
include { PLANT_LONG_READ_PILOT_RUN } from '../../../modules/local/plant_long_read_pilot/main'

workflow PLANT_LONG_READ_PILOT {
    take:
    samples
    reference_fasta
    manifest

    main:
    PLANT_LONG_READ_PILOT_RUN(samples, reference_fasta, manifest)

    emit:
    report = PLANT_LONG_READ_PILOT_RUN.report
    status = PLANT_LONG_READ_PILOT_RUN.status
    versions = PLANT_LONG_READ_PILOT_RUN.versions
}
