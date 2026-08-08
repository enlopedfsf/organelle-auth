//
// Local module: GetOrganelle result adapter (M1-①)
//
// Purpose: nf-core `getorganelle/fromreads` emits generic results/ outputs. This adapter
// implements the ①→② interface contract (design.md §1) by (a) detecting circularization,
// (b) producing contract-named FASTAs, and (c) emitting an assembly grade.
//
// Biology note (not just CLI): a plant plastome is NOT assumed circular (方法学 §3.6,
// SCI-005). GetOrganelle names a clean single-circular-contig result
// `*.complete.graph1.1.path_sequence*` (or `*.nearly-complete.*`); a fragmented/scaffolded
// result is `*.scaffolds.graph1.1.path_sequence*`. We never force-close a circle. nrDNA
// (embplant_nr) is a consensus repeat unit, not a circular molecule, so it carries no grade.
//
// Circularization detection = DUAL check (BUG #6 contract-semantics fix): CANDIDATE requires
// BOTH (a) the GetOrganelle completeness marker "circular" (complete/nearly-complete filename)
// AND (b) the result FASTA has exactly ONE contig. A `*.scaffolds.graph1.1.path_sequence*` file
// alone is NOT a CANDIDATE — GetOrganelle writes it even for a multi-scaffold fragmented result
// (observed: 6 scaffolds for Corydalis), which must be DRAFT (design §3: CANDIDATE=环化叶绿体,
// DRAFT=scaffold/部分). The nf-core module strips the marker from the .fasta.gz it copies, but
// emits the full results/* (this process's input), so the marker is recovered from the original
// path_sequence filename. nrDNA carries no circularization grade regardless.
//
// All FASTA/graph emits are ALWAYS present (a `.NONE` marker when nothing was assembled) so
// downstream channels can be joined cleanly on meta without optional-channel headaches.

process GETORGANELLE_RESULT_ADAPTER {
    tag "${meta.id}"
    label 'process_low'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container
        ? 'https://depot.galaxyproject.org/singularity/python:3.12'
        : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), path(results)   // getorganelle/fromreads `etc` emit (results/*), always present
    val   organelle_type             // 'embplant_pt' or 'embplant_nr'

    output:
    tuple val(meta), path("${meta.id}_plastome*"),          emit: plastome        // _plastome.fasta | _plastome.scaffold.fasta | _plastome.NONE
    tuple val(meta), path("${meta.id}_nrdna*"),             emit: nrdna           // _nrdna.fasta | _nrdna.NONE
    tuple val(meta), path("${meta.id}_assembly_graph*"),    emit: graph           // _assembly_graph.fastg | _assembly_graph.NONE
    tuple val(meta), path("*.grade.txt"),                                      emit: grade_file
    tuple val(meta), path("*.circularized.txt"),                               emit: circularized_file
    tuple val(meta), path("*.produced.txt"),                                   emit: produced_file
    tuple val("${task.process}"), val('getorganelle_result_adapter'), val('0.1.0'), topic: versions, emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    # always create markers so every emit is satisfied
    touch "${prefix}_plastome.NONE"
    touch "${prefix}_nrdna.NONE"
    touch "${prefix}_assembly_graph.NONE"

    # ---- result FASTA + marker-bearing path_sequence ----
    # Prefer the module-copied result FASTA (prefix + '.' + organelle_type + '.fasta.gz') as the
    # canonical result (deterministic contig count); a combined `find -o` returns matches in
    # directory order, NOT pattern order, so the contig count could be taken from the wrong file
    # (BUG #6 hardening, T4 unit case).
    CIRC_GZ="\$(find . -name "${prefix}.${organelle_type}.fasta.gz" 2>/dev/null | head -1 || true)"
    # ---- the marker-bearing path_sequence (carries GetOrganelle's own completeness verdict).
    # GetOrganelle (get_organelle_from_reads.py L3445-3471) names a clean single-circular-contig
    # result *.complete.graph1.1.* (or *.nearly-complete.*); a fragmented/scaffolded result is
    # *.scaffolds.graph1.1.*. The nf-core module strips the marker from the .fasta.gz it copies,
    # but emits the full results/* (this process's input), so we recover the marker here.
    PATHSEQ="\$(find . -name "*${organelle_type}*graph1.1*path_sequence*fasta" 2>/dev/null | head -1 || true)"
    CIRC=""
    if [ -n "\$CIRC_GZ" ] && [ -s "\$CIRC_GZ" ]; then CIRC="\$CIRC_GZ"; elif [ -n "\$PATHSEQ" ]; then CIRC="\$PATHSEQ"; fi
    # ---- scaffold (non-circularized assembly) ----
    # NB: every find|head / grep pipeline below is suffixed `|| true` — Nextflow runs this script
    # under `bash -e -u -o pipefail`, so a grep no-match (exit 1) or a find hit by SIGPIPE after
    # `head -1` closes the pipe (exit 141) would otherwise abort the whole process (observed:
    # ADAPTER_PT exit 1 when GetOrganelle produced no assembly). `|| true` lets the variable be
    # empty and the logic fall through to NOT_APPLICABLE/[ASSEMBLY_FAILED] instead of crashing.
    SCAFFOLD="\$(find . -name "*scaffold*fasta" 2>/dev/null | head -1 || true)"
    # ---- any other assembled organelle fasta (fallback, esp. nrDNA) ----
    ANYORG="\$(find . \\( -name "*${organelle_type}*.fasta" -o -name "*${organelle_type}*.fasta.gz" \\) 2>/dev/null | grep -v "scaffold" | head -1 || true)"
    # ---- assembly graph (Bandage / ② structural review; 方法学 §3.5 三件套之一) ----
    # GetOrganelle/SPAdes emits assembly_graph.fastg for the final k-mer. When found, copy it
    # AND remove the .NONE marker so the `graph` emit glob (${prefix}_assembly_graph*) matches
    # exactly ONE file (BUG #5: a leftover .NONE made the glob match two files, so the graph
    # channel carried a 2-file list that downstream staging could not resolve → graph dropped).
    GRAPH="\$(find . \\( -name "*assembly_graph*fastg" -o -name "*local_assembly_graph*fastg" -o -name "*.fastg" \\) 2>/dev/null | head -1 || true)"
    if [ -n "\$GRAPH" ]; then cp "\$GRAPH" "${prefix}_assembly_graph.fastg"; rm -f "${prefix}_assembly_graph.NONE"; fi

    # ---- completeness marker from the path_sequence filename ----
    MARKER="unknown"
    if [ -n "\$PATHSEQ" ]; then
        case "\$PATHSEQ" in
            *.complete.graph*|*.nearly-complete.graph*) MARKER="circular" ;;
            *.scaffolds.graph*)                          MARKER="scaffolds" ;;
        esac
    fi

    GRADE="NOT_APPLICABLE"; CIRC_FLAG="false"; PRODUCED="false"

    # ---- CANDIDATE requires a DUAL check (BUG #6 contract-semantics fix): the GetOrganelle
    # completeness marker is "circular" (complete/nearly-complete) AND the result FASTA has
    # exactly ONE contig. A graph1.1 path_sequence alone is NOT enough — GetOrganelle writes a
    # *.scaffolds.graph1.1.path_sequence.fasta even for a 6-scaffold fragmented result, which must
    # be DRAFT (design §3: CANDIDATE=环化叶绿体, DRAFT=scaffold/部分). nrDNA carries no grade. ----
    if [ -n "\$CIRC" ]; then
        # contig count: gunzip if gzipped. NB: use a case glob (no dollar sign) rather than a
        # grep on a dot-gz-end pattern — a literal dollar inside single quotes is mangled by the
        # Groovy string that renders this script, so the glob form is the only one safe through
        # both Groovy rendering and bash. (Dollar signs are not safe anywhere in this block —
        # not even in comments — unless escaped or a valid Groovy interpolation.)
        case "\$CIRC" in *.gz) NCONTIG=\$(zcat "\$CIRC" | grep -c '>' || true);; *) NCONTIG=\$(grep -c '>' "\$CIRC" || true);; esac
        if [ "${organelle_type}" = "embplant_pt" ]; then
            if [ "\$MARKER" = "circular" ] && [ "\$NCONTIG" -eq 1 ]; then
                rm -f "${prefix}_plastome.NONE"; gunzip -c "\$CIRC" > "${prefix}_plastome.fasta" 2>/dev/null || cp "\$CIRC" "${prefix}_plastome.fasta"
                GRADE="CANDIDATE"; CIRC_FLAG="true"; PRODUCED="true"
            else
                # incomplete (scaffolded / multi-contig / unknown marker) → DRAFT, contract names it *.scaffold.fasta
                rm -f "${prefix}_plastome.NONE"; gunzip -c "\$CIRC" > "${prefix}_plastome.scaffold.fasta" 2>/dev/null || cp "\$CIRC" "${prefix}_plastome.scaffold.fasta"
                GRADE="DRAFT"; PRODUCED="true"
            fi
        else
            rm -f "${prefix}_nrdna.NONE"; gunzip -c "\$CIRC" > "${prefix}_nrdna.fasta" 2>/dev/null || cp "\$CIRC" "${prefix}_nrdna.fasta"
            PRODUCED="true"
        fi
    elif [ -n "\$SCAFFOLD" ] && [ "${organelle_type}" = "embplant_pt" ]; then
        rm -f "${prefix}_plastome.NONE"; cp "\$SCAFFOLD" "${prefix}_plastome.scaffold.fasta"
        GRADE="DRAFT"; PRODUCED="true"
    elif [ -n "\$ANYORG" ]; then
        if [ "${organelle_type}" = "embplant_pt" ]; then
            rm -f "${prefix}_plastome.NONE"; gunzip -c "\$ANYORG" > "${prefix}_plastome.scaffold.fasta" 2>/dev/null || cp "\$ANYORG" "${prefix}_plastome.scaffold.fasta"
            GRADE="DRAFT"; PRODUCED="true"
        else
            rm -f "${prefix}_nrdna.NONE"; gunzip -c "\$ANYORG" > "${prefix}_nrdna.fasta" 2>/dev/null || cp "\$ANYORG" "${prefix}_nrdna.fasta"
            PRODUCED="true"
        fi
    fi

    printf '%s' "\$GRADE"      > "${prefix}.${organelle_type}.grade.txt"
    printf '%s' "\$CIRC_FLAG"  > "${prefix}.${organelle_type}.circularized.txt"
    printf '%s' "\$PRODUCED"   > "${prefix}.${organelle_type}.produced.txt"
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch "${prefix}_plastome.fasta"
    touch "${prefix}_nrdna.fasta"
    touch "${prefix}_assembly_graph.fastg"
    printf '%s' "CANDIDATE" > "${prefix}.${organelle_type}.grade.txt"
    printf '%s' "true"      > "${prefix}.${organelle_type}.circularized.txt"
    printf '%s' "true"      > "${prefix}.${organelle_type}.produced.txt"
    """
}
