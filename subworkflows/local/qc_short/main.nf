//
// QC_SHORT (M1-①): short-read QC via fastp.
// 方法学 §2.1; fastp Q/length thresholds live ONLY in the experimental profile
// (conf/experimental.config, ENG-POL-001). --detect_adapter_for_pe is built into the
// nf-core fastp PE branch.
//
include { FASTP } from '../../../modules/nf-core/fastp/main'

workflow QC_SHORT {

    take:
    ch_reads   // (meta, [short_reads...]) — paired short reads; meta.single_end expected

    main:

    // FASTP input is (meta, reads, adapter_fasta); no adapter FASTA supplied ([]).
    // The incoming channel is (meta, reads, lr) — take meta+reads, ignore long reads.
    FASTP(
        ch_reads.map { row -> tuple(row[0], row[1], []) },
        false,   // discard_trimmed_pass
        false,   // save_trimmed_fail
        false    // save_merged
    )

    emit:
    clean_reads = FASTP.out.reads          // (meta, [trimmed_R1, trimmed_R2])
    json        = FASTP.out.json           // fastp JSON report (archived per 方法学 §2.1)
    html        = FASTP.out.html           // fastp HTML report
    fastp_log   = FASTP.out.log
    versions    = FASTP.out.versions_fastp
}
