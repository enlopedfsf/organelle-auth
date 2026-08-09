//
// Local module: load reference pack (M1-② IDENTIFY, design 决策 3 / DATA-005).
//
// Resolves samplesheet.reference_pack_id → a reference pack directory under
// params.reference_pack_dir. A pack = manifest.json + reference FASTA + diagnostic_sites.tsv +
// callable_regions.tsv (stdlib JSON/TSV → no pyyaml dependency). On missing / unreadable /
// id-mismatched / empty-reference it FAILS FAST (DATA-005) — there is NO fallback to any public
// database. Decision rules live in the pack, never hardcoded in pipeline code (SCI-001).
//
// manifest.json is the unit resolved by reference_pack_id; a formal on-disk pack schema is a
// separate change (决策 3 — this change treats the pack as the resolved unit).
//

process LOAD_REFERENCE_PACK {
    tag "${meta.id}"
    label 'process_low_memory'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container
        ? 'https://depot.galaxyproject.org/singularity/python:3.12'
        : 'quay.io/biocontainers/python:3.12' }"

    input:
    val meta
    path reference_pack_dir

    output:
    tuple val(meta), path("pack.manifest.json"), path("pack.reference.fasta"), path("pack.diagnostic_sites.tsv"), path("pack.callable_regions.tsv"), emit: pack
    tuple val("${task.process}"), val('load_reference_pack'), val('0.1.0'), topic: versions, emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    REFERENCE_PACK_ID="${meta.reference_pack_id}" \\
    REFERENCE_PACK_DIR="${reference_pack_dir}" \\
    python3 - <<'PYEOF'
import os, sys, json, shutil

pid   = os.environ["REFERENCE_PACK_ID"]
pdir  = os.environ["REFERENCE_PACK_DIR"]
pack  = os.path.join(pdir, pid)
manifest_path = os.path.join(pack, "manifest.json")

# ---- DATA-005: fail-fast on missing / incompatible reference pack. NO public-DB fallback. ----
if not os.path.isfile(manifest_path):
    sys.stderr.write("[LOAD_REFERENCE_PACK] DATA-005: reference pack not found: %s\\n" % manifest_path)
    sys.exit(1)
try:
    manifest = json.load(open(manifest_path))
except Exception as e:
    sys.stderr.write("[LOAD_REFERENCE_PACK] DATA-005: unreadable pack manifest: %s (%s)\\n" % (manifest_path, e))
    sys.exit(1)
if manifest.get("reference_pack_id") != pid:
    sys.stderr.write("[LOAD_REFERENCE_PACK] DATA-005: pack id mismatch (manifest=%s != requested=%s)\\n" % (manifest.get("reference_pack_id"), pid))
    sys.exit(1)

# CLAUDE.md hard rule: verify reference FASTA exists and is non-empty before use.
ref_name = manifest.get("reference_fasta")
ref_path = os.path.join(pack, ref_name)
if not ref_name or not os.path.isfile(ref_path) or os.path.getsize(ref_path) == 0:
    sys.stderr.write("[LOAD_REFERENCE_PACK] DATA-005: reference fasta missing/empty: %s\\n" % ref_path)
    sys.exit(1)
for aux in ("diagnostic_sites.tsv", "callable_regions.tsv"):
    if not os.path.isfile(os.path.join(pack, aux)):
        sys.stderr.write("[LOAD_REFERENCE_PACK] DATA-005: pack missing required file: %s\\n" % aux)
        sys.exit(1)

# Stage to deterministic work-dir names so downstream modules can reference them.
shutil.copy2(manifest_path, "pack.manifest.json")
shutil.copy2(ref_path, "pack.reference.fasta")
shutil.copy2(os.path.join(pack, "diagnostic_sites.tsv"), "pack.diagnostic_sites.tsv")
shutil.copy2(os.path.join(pack, "callable_regions.tsv"), "pack.callable_regions.tsv")
PYEOF
    """

    stub:
    """
    printf '{"reference_pack_id":"%s","version":"0.1.0","status":"test","reference_fasta":"ref.fasta","conflict_rules":{"non_authentic_identity":0.90}}' "${meta.reference_pack_id}" > pack.manifest.json
    printf '>ref_stub\\nACGTACGT\\n' > pack.reference.fasta
    printf 'name\\tref_contig\\tstart\\tend\\nds1\\tref_stub\\t1\\t4\\n' > pack.diagnostic_sites.tsv
    printf 'ref_contig\\tstart\\tend\\nref_stub\\t1\\t8\\n' > pack.callable_regions.tsv
    """
}
