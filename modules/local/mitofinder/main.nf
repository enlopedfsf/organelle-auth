//
// Local module: MitoFinder assembly + annotation (M2-①, design 决策 4).
//
// 方法学 §3.3: MitoFinder assembles the mito-enriched baited reads de novo (--megahit default,
// --metaspades recommended for PE) and annotates them against a GenBank reference. Core is
// Python 2.7 (official image built from GitHub source — see containers/mitofinder/Dockerfile).
//
// Target biological parameters (genetic code via -o, assembler choice, tRNA tool) are tool
// algorithm parameters set in conf/modules.config via ext.args (GetOrganelle precedent: 总方案
// §9.3 tool params, NOT acceptance thresholds). The ② reference pack will carry genetic_code
// per taxon (M2-②); here it is the M2 invertebrate default (NCBI code 5).
//
// MitoFinder writes everything into CWD/<seqid>/ (pathtowork = cwd + '/' + processName). The
// whole result dir is emitted for animal_result_adapter to grade + rename to the ①→② contract
// paths. `--override` forces a clean re-assembly when the process re-runs in place.
//
// Container built 2026-08-09 from RemiAllio/MitoFinder master (v1.4.2) — ghcr.io/enlopedfsf.
process MITOFINDER {
    tag "${meta.id}"
    label 'process_medium'

    container 'ghcr.io/enlopedfsf/mitofinder:1.4.2-fix'

    input:
    tuple val(meta), path(r1), path(r2), path(reference)   // reference = single GenBank (.gb) for annotation

    output:
    // Glob emits ALWAYS match ≥1 file: mitofinder's real outputs OR the `.NONE` markers created
    // below when MitoFinder produced no usable result (keeps downstream joins clean).
    // MitoFinder writes the FINAL results into `<sid>/<sid>_MitoFinder_*_Final_Results/` (a subdir);
    // the script copies the exact final files to the CONTRACT ROOT so the root globs match
    // (Nextflow `**` globs do not match root-level files). The adapter resolves the real (non-.NONE) file.
    tuple val(meta), path("${meta.id}/*_mtDNA_contig*.fasta"), emit: mitogenome   // single (final) or numbered (multi-contig)
    tuple val(meta), path("${meta.id}/*_mtDNA_contig*.gb"),     emit: annotation  // real .gb or .NONE.gb marker
    tuple val(meta), path("${meta.id}/*.infos"),                emit: infos       // real .infos or .NONE.infos marker
    tuple val("${task.process}"), val('mitofinder'), val('1.4.2'), topic: versions, emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    """
    # MitoFinder exits non-zero when it assembles but finds NO mitochondrial contig (a normal
    # no-result outcome, distinct from a crash). `|| true` lets the marker-guarantee below run so
    # the process emits the .NONE markers -> adapter grades NOT_APPLICABLE -> ASSEMBLY_FAILED.
    # (reason_codes.yaml: ASSEMBLY_FAILED covers both "no contig" and "tool error"; a genuine
    # crash is visible in the MitoFinder log.)
    mitofinder -j ${meta.id} -1 ${r1} -2 ${r2} -r ${reference} -p ${task.cpus} --override ${args} || true
    # ---- copy the exact final files from <sid>/<sid>_*_Final_Results/ to the CONTRACT ROOT so the
    # root-level emit globs match (Nextflow `**` globs do not match root-level files).
    # NOTE: bash does NOT glob-expand a `VAR=value` assignment RHS, so the globs must be INLINE
    # in the for/cp commands (unquoted `*` expands there); a non-matching glob stays literal and
    # is skipped by `[ -f ]`. ----
    for f in ${meta.id}/*_Final_Results/${meta.id}_mtDNA_contig.fasta ${meta.id}/*_Final_Results/${meta.id}_mtDNA_contig_[0-9]*.fasta; do
        if [ -f "\$f" ]; then cp "\$f" "${meta.id}/"; fi
    done
    cp ${meta.id}/*_Final_Results/${meta.id}_mtDNA_contig.gb "${meta.id}/" 2>/dev/null || true
    cp ${meta.id}/*_Final_Results/${meta.id}.infos "${meta.id}/" 2>/dev/null || true
    # ---- guarantee every glob emit matches ≥1 file when MitoFinder produced no usable output ----
    if ! ls "${meta.id}"/"${meta.id}"_mtDNA_contig*.fasta >/dev/null 2>&1; then touch "${meta.id}/${meta.id}_mtDNA_contig.NONE.fasta"; fi
    if ! ls "${meta.id}"/"${meta.id}"_mtDNA_contig.gb >/dev/null 2>&1; then touch "${meta.id}/${meta.id}_mtDNA_contig.NONE.gb"; fi
    if ! ls "${meta.id}"/"${meta.id}".infos >/dev/null 2>&1; then touch "${meta.id}/${meta.id}.NONE.infos"; fi
    """

    stub:
    """
    mkdir -p ${meta.id}
    printf '>contig_1\\nACGTACGTACGTACGT\\n' > ${meta.id}/${meta.id}_mtDNA_contig.fasta
    printf 'LOCUS       demo 16 bp\\n' > ${meta.id}/${meta.id}_mtDNA_contig.gb
    printf 'Initial contig name: contig_1\\nStatistics for final sequence:\\nLength: 16\\nGC content: 50.00%%\\nCircularization: Yes\\n' > ${meta.id}/${meta.id}.infos
    """
}
