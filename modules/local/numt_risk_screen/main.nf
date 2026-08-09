//
// Local module: NUMT risk screening (minimal) (M2-①, design 决策 6).
//
// 方法学 §3.3 NUMT 排检 first step: re-map reads onto the mitogenome assembly and check
//   (a) coverage heterogeneity — depth-valley regions below median × coefficient,
//   (b) multi-mapping signals (secondary-alignment fraction).
//
// This is explicitly a RISK SCREEN, NOT NUMT confirmation: nuclear-flank / premature-stop-codon /
// frameshift checks + long-read evidence are documented in design.md known limitations (future
// change). Thresholds are policy-injected and null in experimental -> the screen ALWAYS writes a
// metrics report, but only emits signal=true when a configured threshold is exceeded. The status
// emitter translates signal -> WARN reason code NUMT_RISK_SUSPECTED.
//
// Bash + awk implementation (the minimap2_samtools wave container has no python3).

process NUMT_RISK_SCREEN {
    tag "${meta.id}"
    label 'process_low'

    container 'community.wave.seqera.io/library/minimap2_samtools:b09096fc890429ce'

    input:
    tuple val(meta), path(mitogenome), path(bam), path(depth)
    // thresholds read from params.numt_coverage_coefficient / params.numt_multimap_fraction
    // (policy-injected; null -> that dimension does not fire)

    output:
    tuple val(meta), path("${meta.id}.numt_report.tsv"),  emit: report
    tuple val(meta), path("${meta.id}.numt_signal.txt"),  emit: signal
    tuple val("${task.process}"), val('numt_risk_screen'), val('0.1.0'), topic: versions, emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    DEPTH="${depth}"
    BAM="${bam}"
    COEFF="${params.numt_coverage_coefficient}"
    MMT="${params.numt_multimap_fraction}"

    # ---- coverage metrics (samtools depth col 3) ----
    MEDIAN=0; VALLEY_BP=0
    if [ -s "\$DEPTH" ]; then
        MEDIAN=\$(sort -k3,3n "\$DEPTH" | awk '{a[NR]=\$3} END {if (NR%2) print a[(NR+1)/2]; else print (a[NR/2]+a[NR/2+1])/2}')
        if [ -n "\$COEFF" ] && [ "\$MEDIAN" != "0" ]; then
            VALLEY_BP=\$(awk -v m="\$MEDIAN" -v c="\$COEFF" '\$3 < m*c {n++} END {print n+0}' "\$DEPTH")
        fi
    fi

    # ---- multi-mapping metrics (secondary alignments, flag 0x100) ----
    TOTAL=0; SECONDARY=0
    if [ -s "\$BAM" ]; then
        TOTAL=\$(samtools view -c -F 0x904 "\$BAM" 2>/dev/null || echo 0)
        SECONDARY=\$(samtools view -c -f 0x100 "\$BAM" 2>/dev/null || echo 0)
    fi
    MMFRAC=0
    if [ "\$TOTAL" != "0" ]; then
        MMFRAC=\$(awk -v s="\$SECONDARY" -v t="\$TOTAL" 'BEGIN {printf "%.6f", s/t}')
    fi

    # ---- per-dimension signals (only when the policy threshold is configured) ----
    VALLEY_SIGNAL=false; MM_SIGNAL=false; SIGNAL=false
    if [ -n "\$COEFF" ] && [ "\$VALLEY_BP" -gt 0 ]; then VALLEY_SIGNAL=true; fi
    if [ -n "\$MMT" ] && awk -v mf="\$MMFRAC" -v mt="\$MMT" 'BEGIN {exit !(mf > mt)}'; then MM_SIGNAL=true; fi
    if [ "\$VALLEY_SIGNAL" = "true" ] || [ "\$MM_SIGNAL" = "true" ]; then SIGNAL=true; fi

    printf 'median_depth\\t%s\\n' "\$MEDIAN" > ${meta.id}.numt_report.tsv
    printf 'valley_bp\\t%s\\n' "\$VALLEY_BP" >> ${meta.id}.numt_report.tsv
    printf 'numt_coverage_coefficient\\t%s\\n' "\$COEFF" >> ${meta.id}.numt_report.tsv
    printf 'secondary_alignments\\t%s\\n' "\$SECONDARY" >> ${meta.id}.numt_report.tsv
    printf 'total_mapped\\t%s\\n' "\$TOTAL" >> ${meta.id}.numt_report.tsv
    printf 'multimap_fraction\\t%s\\n' "\$MMFRAC" >> ${meta.id}.numt_report.tsv
    printf 'numt_multimap_fraction_threshold\\t%s\\n' "\$MMT" >> ${meta.id}.numt_report.tsv
    printf 'valley_signal\\t%s\\n' "\$VALLEY_SIGNAL" >> ${meta.id}.numt_report.tsv
    printf 'multimap_signal\\t%s\\n' "\$MM_SIGNAL" >> ${meta.id}.numt_report.tsv
    printf 'signal\\t%s\\n' "\$SIGNAL" >> ${meta.id}.numt_report.tsv

    printf '%s\\n' "\$SIGNAL" > ${meta.id}.numt_signal.txt
    """

    stub:
    """
    printf 'median_depth\\t0\\nvalley_bp\\t0\\nnumt_coverage_coefficient\\tnull\\nsecondary_alignments\\t0\\ntotal_mapped\\t0\\nmultimap_fraction\\t0.0\\nnumt_multimap_fraction_threshold\\tnull\\nvalley_signal\\tfalse\\nmultimap_signal\\tfalse\\nsignal\\tfalse\\n' > ${meta.id}.numt_report.tsv
    echo false > ${meta.id}.numt_signal.txt
    """
}
