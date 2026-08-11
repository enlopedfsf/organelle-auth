process PMAT2_SUBSET_COMPARATOR {
    tag "${meta.id}"
    label 'process_high'
    container { params.pmat2_container }

    input:
    tuple val(meta), path(reads), path(gate_status)
    path policy
    val policy_data

    output:
    tuple val(meta), path("${meta.id}.pmat2-comparator.fasta"), path("${meta.id}.pmat2-comparator-status.json"), path("${meta.id}.pmat2-comparator-command.txt"), emit: assembly
    tuple val("${task.process}"), val('PMAT2'), val('2.1.5'), topic: versions, emit: versions

    script:
    def pmat = policy_data.pmat2_comparator ?: [:]
    if (pmat.correction_mode != 0) {
        error "PMAT2 comparator requires explicit -p 0"
    }
    def pmatArgs = "-t ${pmat.technology ?: 'ont'} -x ${pmat.taxon_code == null ? 0 : pmat.taxon_code} -p ${pmat.correction_mode}"
    """
    set -euo pipefail
    PREFIX='${meta.id}'
    INPUT_SHA256=\$(sha256sum ${reads} | cut -d' ' -f1)
    PMAT_VERSION=UNAVAILABLE
    if command -v PMAT >/dev/null 2>&1; then
        PMAT_VERSION=\$(PMAT --version 2>&1 | head -n 1 || true)
        [ -n "\$PMAT_VERSION" ] || PMAT_VERSION=AVAILABLE_VERSION_UNKNOWN
    fi
    printf '%s\n%s\n' 'PMAT autoMito -i ${reads} -o ${meta.id}.pmat2-comparator ${pmatArgs}' "version=\$PMAT_VERSION" > \${PREFIX}.pmat2-comparator-command.txt
    if [ '${pmat.enabled}' != 'true' ] || ! grep -q '"status": "ELIGIBLE_EXPERIMENTAL"' ${gate_status}; then
        : > \${PREFIX}.pmat2-comparator.fasta
        printf '{"stage":"long_read_subset_comparator","status":"INCONCLUSIVE","decision":"NOT_APPLICABLE","reason_codes":["TARGET_GATE_NOT_ELIGIBLE"],"role":"EXPERIMENTAL_COMPARATOR","correction_mode":0,"input_sha256":"%s","tool_version":"%s"}\n' "\$INPUT_SHA256" "\$PMAT_VERSION" > \${PREFIX}.pmat2-comparator-status.json
    else
        set +e
        PMAT autoMito -i ${reads} -o \${PREFIX}.pmat2-comparator ${pmatArgs}
        RC=\$?
        set -e
        CANDIDATE=\$(find \${PREFIX}.pmat2-comparator -type f -size +0c 2>/dev/null | grep -E '\.(fa|fasta|fna)\$' | head -n 1 || true)
        if [ \$RC -eq 0 ] && [ -n "\$CANDIDATE" ]; then
            cp "\$CANDIDATE" \${PREFIX}.pmat2-comparator.fasta
            printf '{"stage":"long_read_subset_comparator","status":"PASS","decision":"NOT_APPLICABLE","reason_codes":[],"role":"EXPERIMENTAL_COMPARATOR","correction_mode":0,"input_sha256":"%s","tool_version":"%s"}\n' "\$INPUT_SHA256" "\$PMAT_VERSION" > \${PREFIX}.pmat2-comparator-status.json
        else
            : > \${PREFIX}.pmat2-comparator.fasta
            printf '{"stage":"long_read_subset_comparator","status":"WARN","decision":"NOT_APPLICABLE","reason_codes":["COMPARATOR_ASSEMBLY_FAILED"],"role":"EXPERIMENTAL_COMPARATOR","correction_mode":0,"input_sha256":"%s","tool_version":"%s","exit_code":%s}\n' "\$INPUT_SHA256" "\$PMAT_VERSION" "\$RC" > \${PREFIX}.pmat2-comparator-status.json
        fi
    fi
    """

    stub:
    """
    printf '>pmat2_stub\nACGTACGT\n' > ${meta.id}.pmat2-comparator.fasta
    printf '{"stage":"long_read_subset_comparator","status":"STUB","decision":"NOT_APPLICABLE","role":"EXPERIMENTAL_COMPARATOR","correction_mode":0,"input_sha256":"STUB"}\n' > ${meta.id}.pmat2-comparator-status.json
    printf 'PMAT autoMito -p 0 STUB\n' > ${meta.id}.pmat2-comparator-command.txt
    """
}
