//
// Local module: MitoFinder result adapter (M2-①, design 决策 5 / ①→② interface contract §1).
//
// Consumes the MitoFinder module's glob emits (explicit FILE inputs — Nextflow stages files as
// copies so this is container-safe) and (a) grades the assembly, (b) renames to the frozen ①→②
// contract paths. Grading mirrors the plant BUG #6 dual-check:
//   - CANDIDATE requires BOTH the MitoFinder stats file (`<seqid>.infos`) reports
//     "Circularization: Yes" AND the primary mitogenome FASTA has EXACTLY ONE contig.
//   - Otherwise DRAFT (`_mitogenome.scaffold.fasta`). No forced circularization (方法学 §3.6).
//   - No usable sequence at all (.NONE markers) -> NOT_APPLICABLE (downstream ASSEMBLY_FAILED).
//
// MitoFinder names the single-contig final as `<seqid>_mtDNA_contig.fasta` and multi-contig
// results as `<seqid>_mtDNA_contig_<N>.fasta`; the stats file is `<seqid>.infos`. All emits are
// ALWAYS present (a `.NONE` marker when nothing was assembled) so downstream joins stay clean.

process ANIMAL_RESULT_ADAPTER {
    tag "${meta.id}"
    label 'process_low'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container
        ? 'https://depot.galaxyproject.org/singularity/python:3.12'
        : 'quay.io/biocontainers/python:3.12' }"

    input:
    tuple val(meta), path(mtfasta), path(annotation_gb), path(infos)
    // mtfasta = 1+ files (*_mtDNA_contig*.fasta, real or .NONE marker); annotation_gb/infos = real or marker.

    output:
    tuple val(meta), path("${meta.id}_mitogenome*"),          emit: mitogenome      // _mitogenome.fasta | _mitogenome.scaffold.fasta | _mitogenome.NONE
    tuple val(meta), path("${meta.id}_annotation.gb"),        emit: annotation
    tuple val(meta), path("${meta.id}.infos"),                emit: infos
    tuple val(meta), path("*.grade.txt"),                     emit: grade_file
    tuple val(meta), path("*.circularized.txt"),              emit: circularized_file
    tuple val(meta), path("*.produced.txt"),                  emit: produced_file
    tuple val("${task.process}"), val('animal_result_adapter'), val('0.1.0'), topic: versions, emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    # always create markers so every emit is satisfied
    touch "${prefix}_mitogenome.NONE"
    touch "${prefix}_annotation.gb"
    touch "${prefix}.infos"

    # ---- primary mitogenome FASTA: prefer the single-contig final, else the first numbered ----
    PRIMARY=""
    for f in ${mtfasta}; do
        case "\$f" in
            *.NONE.fasta) continue ;;
            *_mtDNA_contig.fasta) PRIMARY="\$f"; break ;;
            *_mtDNA_contig_*.fasta) if [ -z "\$PRIMARY" ]; then PRIMARY="\$f"; fi ;;
        esac
    done

    # ---- stats (.infos) - non-marker file wins ----
    INFOS=""
    for f in ${infos}; do
        case "\$f" in *.NONE.infos) continue ;; *) INFOS="\$f"; break ;; esac
    done
    if [ -n "\$INFOS" ]; then cp "\$INFOS" "${prefix}.infos"; fi

    if [ -z "\$PRIMARY" ]; then
        # ---- no usable sequence: NOT_APPLICABLE ----
        echo "NOT_APPLICABLE" > "${prefix}.grade.txt"
        echo "false" > "${prefix}.produced.txt"
        echo "false" > "${prefix}.circularized.txt"
        touch "${prefix}_mitogenome.NONE"
    else
        # remove the no-result marker so the *_mitogenome* glob emits ONLY the real result
        rm -f "${prefix}_mitogenome.NONE"
        echo "true" > "${prefix}.produced.txt"
        NC="\$(grep -c '^>' "\$PRIMARY" 2>/dev/null || echo 0)"
        CIRC="false"
        if [ -n "\$INFOS" ] && grep -q 'Circularization: Yes' "\$INFOS"; then CIRC="true"; fi
        echo "\$CIRC" > "${prefix}.circularized.txt"
        if [ "\$NC" -eq 1 ] && [ "\$CIRC" = "true" ]; then
            # ---- CANDIDATE: single circular contig ----
            echo "CANDIDATE" > "${prefix}.grade.txt"
            cp "\$PRIMARY" "${prefix}_mitogenome.fasta"
        else
            # ---- DRAFT: multi-contig or circularization not found (no forced circularization) ----
            echo "DRAFT" > "${prefix}.grade.txt"
            cp "\$PRIMARY" "${prefix}_mitogenome.scaffold.fasta"
        fi
    fi
    # ---- annotation (.gb) - non-marker file wins ----
    for f in ${annotation_gb}; do
        case "\$f" in *.NONE.gb) continue ;; *) cp "\$f" "${prefix}_annotation.gb"; break ;; esac
    done
    """

    stub:
    """
    touch "${meta.id}_mitogenome.NONE"
    touch "${meta.id}_annotation.gb"
    touch "${meta.id}.infos"
    echo "DRAFT" > "${meta.id}.grade.txt"
    echo "true" > "${meta.id}.produced.txt"
    echo "false" > "${meta.id}.circularized.txt"
    printf '>contig_1\\nACGT\\n' > "${meta.id}_mitogenome.scaffold.fasta"
    """
}
