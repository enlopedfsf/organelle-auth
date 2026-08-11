process LR_MAP_MINIMAP2 {
    tag "${meta.id}:${mapping_label}"
    label 'process_medium'
    container { params.minimap2_container }

    input:
    tuple val(meta), path(query), path(target)
    val policy_data
    val policy_section
    val mapping_label

    output:
    tuple val(meta), path("${meta.id}.${mapping_label}.paf"), path("${meta.id}.${mapping_label}.command.txt"), emit: alignment
    tuple val("${task.process}"), val('minimap2'), val('2.28-container-policy'), topic: versions, emit: versions

    script:
    def mapper = policy_data[policy_section] ?: [:]
    def preset = mapper.preset ?: 'map-ont'
    def mapperArgs = []
    if (mapper.emit_cigar) mapperArgs << '-c'
    if (mapper.emit_cs) mapperArgs << "--cs=${mapper.emit_cs}"
    if (mapper.secondary != null) mapperArgs << "--secondary=${mapper.secondary ? 'yes' : 'no'}"
    if (mapper.max_secondary != null) mapperArgs << "-N ${mapper.max_secondary}"
    if (mapper.secondary_score_ratio != null) mapperArgs << "-p ${mapper.secondary_score_ratio}"
    def args = mapperArgs.join(' ')
    """
    set -euo pipefail
    MINIMAP2_VERSION=\$(minimap2 --version 2>&1 | head -n 1 || true)
    [ -n "\$MINIMAP2_VERSION" ] || MINIMAP2_VERSION=UNAVAILABLE
    printf '%s\n%s\n' 'minimap2 -x ${preset} -t ${task.cpus} ${args} ${target} ${query}' "version=\$MINIMAP2_VERSION" > ${meta.id}.${mapping_label}.command.txt
    if [ ! -s ${query} ] || [ ! -s ${target} ]; then
        : > ${meta.id}.${mapping_label}.paf
    else
        minimap2 -x ${preset} -t ${task.cpus} ${args} ${target} ${query} > ${meta.id}.${mapping_label}.paf
    fi
    """

    stub:
    """
    : > ${meta.id}.${mapping_label}.paf
    printf '%s\n' 'minimap2 STUB ${mapping_label}' > ${meta.id}.${mapping_label}.command.txt
    """
}
