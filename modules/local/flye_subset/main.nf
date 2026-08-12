process FLYE_SUBSET {
    tag "${meta.id}:${assembly_label}"
    label 'process_high'
    container { params.flye_container }

    input:
    tuple val(meta), path(reads), path(gate_status)
    path policy
    val policy_data
    val assembly_label

    output:
    tuple val(meta), path("${meta.id}.${assembly_label}.flye.fasta"), path("${meta.id}.${assembly_label}.flye-status.json"), path("${meta.id}.${assembly_label}.flye-command.txt"), emit: assembly
    tuple val("${task.process}"), val('flye'), val('2.9.5-container-policy'), topic: versions, emit: versions

    script:
    def flye = policy_data.flye ?: [:]
    def readFlag = flye.read_type == 'nano-hq' ? '--nano-hq' : flye.read_type == 'nano-raw' ? '--nano-raw' : flye.read_type == 'pacbio-hifi' ? '--pacbio-hifi' : null
    def policyComplete = readFlag && flye.genome_size && flye.iterations != null && flye.min_overlap != null
    def assemblyCoverageArg = flye.asm_coverage == null ? '' : " --asm-coverage ${flye.asm_coverage}"
    def deterministicArg = flye.deterministic == true ? ' --deterministic' : ''
    def flyeArgs = policyComplete ? "${readFlag} ${reads} --genome-size ${flye.genome_size}${assemblyCoverageArg} --iterations ${flye.iterations} --min-overlap ${flye.min_overlap}${deterministicArg}" : ''
    """
    set -euo pipefail
    FLYE_POLICY_REVISION=6
    for REQUIRED_EXE in flye flye-minimap2 flye-samtools; do
        command -v "\$REQUIRED_EXE" >/dev/null || {
            printf 'required Flye runtime executable missing: %s\n' "\$REQUIRED_EXE" >&2
            exit 127
        }
    done
    INPUT_SHA256=\$(sha256sum ${reads} | cut -d' ' -f1)
    FLYE_VERSION=\$(flye --version 2>&1 | head -n 1 || true)
    [ -n "\$FLYE_VERSION" ] || FLYE_VERSION=UNAVAILABLE
    printf '%s\n%s\n%s\n%s\n%s\n' 'flye ${flyeArgs} --threads ${task.cpus} --out-dir ${meta.id}.${assembly_label}.flye' "version=\$FLYE_VERSION" "flye_path=\$(command -v flye)" "flye_minimap2_path=\$(command -v flye-minimap2)" "flye_samtools_path=\$(command -v flye-samtools)" > ${meta.id}.${assembly_label}.flye-command.txt
    if ! grep -q '"status": "ELIGIBLE_EXPERIMENTAL"' ${gate_status}; then
        : > ${meta.id}.${assembly_label}.flye.fasta
        printf '{"stage":"long_read_subset_assembly","status":"INCONCLUSIVE","decision":"NOT_APPLICABLE","reason_codes":["TARGET_GATE_NOT_ELIGIBLE"],"role":"PRIMARY","input_sha256":"%s","tool_version":"%s"}\n' "\$INPUT_SHA256" "\$FLYE_VERSION" > ${meta.id}.${assembly_label}.flye-status.json
    elif [ '${policyComplete}' != 'true' ]; then
        : > ${meta.id}.${assembly_label}.flye.fasta
        printf '{"stage":"long_read_subset_assembly","status":"INCONCLUSIVE","decision":"NOT_APPLICABLE","reason_codes":["THRESHOLD_NOT_CONFIGURED"],"role":"PRIMARY","input_sha256":"%s","tool_version":"%s"}\n' "\$INPUT_SHA256" "\$FLYE_VERSION" > ${meta.id}.${assembly_label}.flye-status.json
    else
        set +e
        flye ${flyeArgs} --threads ${task.cpus} --out-dir ${meta.id}.${assembly_label}.flye
        RC=\$?
        set -e
        if [ \$RC -eq 0 ] && [ -s ${meta.id}.${assembly_label}.flye/assembly.fasta ]; then
            cp ${meta.id}.${assembly_label}.flye/assembly.fasta ${meta.id}.${assembly_label}.flye.fasta
            printf '{"stage":"long_read_subset_assembly","status":"PASS","decision":"NOT_APPLICABLE","reason_codes":[],"role":"PRIMARY","input_sha256":"%s","tool_version":"%s"}\n' "\$INPUT_SHA256" "\$FLYE_VERSION" > ${meta.id}.${assembly_label}.flye-status.json
        else
            : > ${meta.id}.${assembly_label}.flye.fasta
            printf '{"stage":"long_read_subset_assembly","status":"FAIL","decision":"NOT_APPLICABLE","reason_codes":["SUBSET_ASSEMBLY_FAILED"],"role":"PRIMARY","input_sha256":"%s","tool_version":"%s","exit_code":%s}\n' "\$INPUT_SHA256" "\$FLYE_VERSION" "\$RC" > ${meta.id}.${assembly_label}.flye-status.json
        fi
    fi
    """

    stub:
    """
    printf '>flye_stub\nACGTACGT\n' > ${meta.id}.${assembly_label}.flye.fasta
    printf '{"stage":"long_read_subset_assembly","status":"STUB","decision":"NOT_APPLICABLE","role":"PRIMARY","input_sha256":"STUB"}\n' > ${meta.id}.${assembly_label}.flye-status.json
    printf 'flye STUB\n' > ${meta.id}.${assembly_label}.flye-command.txt
    """
}
