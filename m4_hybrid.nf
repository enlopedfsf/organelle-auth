#!/usr/bin/env nextflow

include { HYBRID_REFERENCE_BUILD } from './subworkflows/local/hybrid_reference_build'

def resolveM4Path(raw, root) {
    def value = raw.toString()
    file(value.startsWith('/') ? value : "${root}/${value}", checkIfExists: true)
}

/*
 * Standalone M4 evaluator.  It is deliberately separate from main.nf so public-data experimental
 * candidates cannot be routed into authentication stages.
 */
workflow {
    if (!params.m4_input_manifest) {
        error "--m4_input_manifest is required"
    }
    def manifest = new groovy.json.JsonSlurper().parse(file(params.m4_input_manifest, checkIfExists: true).toFile())
    if (manifest.schema_version != 'm4-execution-inputs-v1') {
        error "unsupported M4 input manifest schema: ${manifest.schema_version}"
    }
    def rows = manifest.taxa.collect { taxon, row ->
        tuple(
            [taxon: taxon, sample_id: row.sample_id],
            resolveM4Path(row.b0, projectDir),
            resolveM4Path(row.r1, projectDir),
            resolveM4Path(row.train_r1, projectDir),
            resolveM4Path(row.train_r2, projectDir),
            resolveM4Path(row.heldout_r1, projectDir),
            resolveM4Path(row.heldout_r2, projectDir),
            resolveM4Path(row.source_bed, projectDir)
        )
    }
    HYBRID_REFERENCE_BUILD(Channel.fromList(rows), resolveM4Path(manifest.evaluation_policy, projectDir))
}
