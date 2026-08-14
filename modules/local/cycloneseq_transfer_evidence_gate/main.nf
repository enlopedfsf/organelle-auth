process CYCLONESEQ_TRANSFER_EVIDENCE_GATE {
    tag "${meta.id}"
    label 'process_single'

    input:
    tuple val(meta), val(bundle)

    output:
    tuple val(meta), path("${meta.id}.cycloneseq-transfer.json"), emit: evidence

    script:
    def allowedStatus = ['PASS', 'WARN', 'FAIL', 'INCONCLUSIVE'] as Set
    def allowedOutcomes = [
        'PENDING_REAL_DATA',
        'ARRIVAL_BLOCKED',
        'INCONCLUSIVE_NOT_EVALUABLE',
        'NO_GO_CONTROL_FAILURE',
        'NO_GO_HARM_OR_FALSE_STRUCTURE',
        'NO_GO_NO_INDEPENDENT_GAIN',
        'CONDITIONAL_MIXED_EVIDENCE',
        'INSUFFICIENT_SCOPE_FOR_GO',
        'ELIGIBLE_FOR_GO_REVIEW'
    ] as Set
    def allowedRoutes = ['SHORT_READ_BASELINE', 'CYCLONESEQ_ONLY_RESEARCH', 'HYBRID'] as Set
    def allowedEvidenceTiers = ['ENGINEERING_FIXTURE', 'PROTOCOL_ONLY', 'SCIENTIFIC_TRANSFER'] as Set
    def channels = (bundle.channels ?: []) as Set
    def errors = []

    if (!allowedStatus.contains(bundle.status)) errors << 'invalid status vocabulary'
    if (!allowedOutcomes.contains(bundle.transfer_outcome)) errors << 'unregistered transfer outcome'
    if (!allowedRoutes.contains(bundle.route_role)) errors << 'unregistered route role'
    if (!allowedEvidenceTiers.contains(bundle.evidence_tier)) errors << 'unregistered evidence tier'
    if (bundle.decision != 'NOT_APPLICABLE') errors << 'authentication decision is prohibited'
    if (bundle.scientific_conclusion_allowed != false) errors << 'scientific self-authorization is prohibited'
    if (channels.intersect(['IDENTIFY', 'DECISION'] as Set)) errors << 'prohibited output channel'
    if (bundle.route_role == 'CYCLONESEQ_ONLY_RESEARCH' && channels != ['RESEARCH_EVIDENCE'] as Set) {
        errors << 'CycloneSEQ-only route must remain research evidence'
    }
    if (bundle.evidence_tier == 'ENGINEERING_FIXTURE') {
        if (bundle.branch_simulation != true) errors << 'engineering branch-simulation marker missing'
        if (bundle.cycloneseq != 'PENDING_REAL_DATA') errors << 'engineering fixture advanced scientific state'
        if (channels != ['RESEARCH_EVIDENCE'] as Set) errors << 'engineering fixture left research evidence'
    }
    if (bundle.evidence_tier == 'PROTOCOL_ONLY' && bundle.cycloneseq != 'PENDING_REAL_DATA') {
        errors << 'protocol-only evidence advanced scientific state'
    }
    if (bundle.governance?.pmat2 != 'GATED_ISSUE_10') errors << 'PMAT2 gate drift'
    if (bundle.governance?.mitovgp != 'OUT_OF_SCOPE_UNADMITTED') errors << 'mitoVGP scope drift'
    if (bundle.governance?.cycloneseq_only_terminal_decision != 'PROHIBITED') {
        errors << 'CycloneSEQ terminal-decision prohibition drift'
    }
    def requiredDenominators = [
        'eligible_samples',
        'attempted_routes',
        'declared_sequence_bases',
        'callable_sequence_bases',
        'declared_junctions'
    ] as Set
    if ((bundle.denominators?.keySet() ?: [] as Set) != requiredDenominators) {
        errors << 'explicit denominator contract incomplete'
    }
    if (errors) error "CycloneSEQ transfer evidence gate failed: ${errors.join('; ')}"

    def rendered = groovy.json.JsonOutput.prettyPrint(groovy.json.JsonOutput.toJson(bundle))
    """
    cat > ${meta.id}.cycloneseq-transfer.json <<'JSON'
    ${rendered}
    JSON
    """

    stub:
    """
    cat > ${meta.id}.cycloneseq-transfer.json <<'JSON'
    {"schema_version":"cycloneseq-transfer-evidence-v0.1","status":"INCONCLUSIVE","decision":"NOT_APPLICABLE","transfer_outcome":"PENDING_REAL_DATA","reason_codes":["STUB_ENGINEERING_ONLY"],"cycloneseq":"PENDING_REAL_DATA","evidence_tier":"ENGINEERING_FIXTURE","branch_simulation":true,"scientific_conclusion_allowed":false,"route_role":"CYCLONESEQ_ONLY_RESEARCH","channels":["RESEARCH_EVIDENCE"],"governance":{"pmat2":"GATED_ISSUE_10","mitovgp":"OUT_OF_SCOPE_UNADMITTED","cycloneseq_only_terminal_decision":"PROHIBITED"},"denominators":{"eligible_samples":0,"attempted_routes":0,"declared_sequence_bases":0,"callable_sequence_bases":0,"declared_junctions":0},"evidence":{"platform":{},"sequence":{},"structure":{},"blind_decision":{},"operations":{}}}
    JSON
    """
}
