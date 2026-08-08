#!/usr/bin/env python3
"""T0 static check for organelle-auth — schema + registry + contract integrity.

Run by .github/workflows/spec-and-schema.yml on every PR/push (M0+).
Requires: pyyaml, jsonschema.

Checks:
  1. JSON / YAML files parse.
  2. assets/schema_input.json is a valid JSON Schema; the valid samplesheet fixture
     passes and the truth-field fixture is rejected (DATA-003).
  3. assets/schema_status.json is valid; the 3 §5.5 enum sets are closed.
  4. Requirement traceability matrix integrity (bidirectional vs specs).
  5. registries/tools.yaml: 13 §8.3 candidates + 7 PROHIBITED, each PROHIBITED with
     reason + re_evaluation_trigger; spot-check no tier inflated.
  6. PROHIBITED tools do not appear in modules/ or conf/ (cheap T0 grep).
  7. registries/hypotheses.yaml: state machine + full HYP-DNA-001 (two-metric).
  8. policies/tcm-plant-experimental.yaml thresholds all null; compatibility manifest
     framework present (§10.3).
"""
import csv
import glob
import json
import os
import re
import sys

import yaml

try:
    import jsonschema
except ImportError:
    sys.exit("jsonschema + pyyaml required: pip install jsonschema pyyaml")


def load_yaml(path):
    with open(path) as fh:
        return yaml.safe_load(fh)


def load_json(path):
    with open(path) as fh:
        return json.load(fh)


def _rows(path):
    """Parse a samplesheet CSV into row dicts; empty cells -> None (absence); split comma-list `targets`."""
    out = []
    with open(path) as fh:
        for raw in csv.DictReader(fh):
            row = {k: (None if v is None or v == "" else v) for k, v in raw.items()}
            if isinstance(row.get("targets"), str):
                row["targets"] = [t.strip() for t in row["targets"].split(",") if t.strip()]
            out.append(row)
    return out


def check_parse():
    json_files = sorted(
        set(["nextflow_schema.json", "assets/schema_input.json", "assets/schema_status.json"] + glob.glob("assets/*.json"))
    )
    for f in json_files:
        if os.path.exists(f):
            load_json(f)
    yaml_files = [
        "openspec/config.yaml", "openspec/traceability.yaml", ".nf-core.yml",
        "assets/reason_codes.yaml", "registries/tools.yaml", "registries/hypotheses.yaml",
        "policies/tcm-plant-experimental.yaml", "assets/compatibility_manifest.yaml",
    ]
    for f in yaml_files:
        if os.path.exists(f):
            load_yaml(f)
    print("JSON/YAML parse ok")


def check_schema_input_fixtures():
    schema = load_json("assets/schema_input.json")
    jsonschema.Draft202012Validator.check_schema(schema)
    item = schema["items"]
    # valid fixture: every row must pass
    for row in _rows("tests/fixtures/samplesheet_valid.csv"):
        jsonschema.validate(row, item)
    # truth-field fixture: at least one row must be rejected (DATA-003)
    any_fail = False
    for row in _rows("tests/fixtures/samplesheet_with_truth.csv"):
        try:
            jsonschema.validate(row, item)
        except jsonschema.ValidationError:
            any_fail = True
    assert any_fail, "samplesheet_with_truth.csv should be rejected (DATA-003 truth column)"
    print("schema_input.json + fixtures ok (DATA-003 enforced)")


def check_status_schema():
    schema = load_json("assets/schema_status.json")
    jsonschema.Draft202012Validator.check_schema(schema)
    props = schema["properties"]
    assert set(props["status"]["enum"]) == {"PASS", "WARN", "FAIL", "INCONCLUSIVE"}
    assert {"REFERENCE", "DRAFT", "CANDIDATE", "NOT_APPLICABLE"} <= set(props["assembly_grade"]["enum"])
    assert {"AUTHENTIC", "NON_AUTHENTIC", "INCONCLUSIVE", "NOT_APPLICABLE"} <= set(props["decision"]["enum"])
    print("schema_status.json ok (3 enum sets)")


def check_traceability():
    m = load_yaml("openspec/traceability.yaml")
    ids = [r["id"] for r in m["requirements"]]
    assert len(ids) == len(set(ids)), "duplicate Requirement IDs in matrix"
    domains = set(m["spec_domains"])
    for r in m["requirements"]:
        assert r["spec_domain"] in domains, f"{r['id']} unknown spec_domain"
    reqid = re.compile(r"\b(?:SCI|DATA|TEST|REL)-\d{3}\b|\bENG-POL-\d{3}\b|\bHYP-DNA-\d{3}\b")
    id_set = set(ids)
    cited = set()
    for f in glob.glob("openspec/changes/**/specs/**/*.md", recursive=True) + glob.glob("openspec/specs/**/*.md", recursive=True):
        cited.update(reqid.findall(open(f).read()))
    missing = cited - id_set
    assert not missing, f"ReqIDs cited in specs but absent from matrix: {sorted(missing)}"
    print(f"traceability ok: {len(ids)} ids, {len(cited)} cited")


EXPECTED_CANDIDATES = {
    "fastp", "nanoplot", "kraken2", "getorganelle", "novoplasty", "mitofinder_mitoz",
    "flye", "pmat2", "racon", "polypolish", "bcftools_consensus", "nextpolish2", "geseq_plastidhub",
}
EXPECTED_PROHIBITED = {"medaka", "nanopolish", "clair3_ont", "oatk", "tippo", "mitohifi", "hifiasm"}


def check_tools_registry():
    t = load_yaml("registries/tools.yaml")
    cands = t.get("candidates", [])
    proh = t.get("prohibited", [])
    assert len(cands) == 13, f"expected 13 candidates, got {len(cands)}"
    cand_ids = {c["tool_id"] for c in cands}
    assert cand_ids == EXPECTED_CANDIDATES, f"candidate mismatch: {cand_ids ^ EXPECTED_CANDIDATES}"
    tier = {c["tool_id"]: c["admission_status"] for c in cands}
    # spot-check the 3 the audit emphasised (no inflation vs §8.3)
    assert tier["getorganelle"] == "CONDITIONAL", "GetOrganelle must be CONDITIONAL"
    assert tier["pmat2"] == "EXPERIMENTAL", "PMAT2 must be EXPERIMENTAL"
    assert tier["nextpolish2"] == "DEFERRED", "NextPolish2 must be DEFERRED"
    assert len(proh) == 7, f"expected 7 prohibited, got {len(proh)}"
    proh_ids = {p["tool_id"] for p in proh}
    assert proh_ids == EXPECTED_PROHIBITED, f"prohibited mismatch: {proh_ids ^ EXPECTED_PROHIBITED}"
    for p in proh:
        assert p.get("reason") and p.get("re_evaluation_trigger"), f"{p['tool_id']} missing reason/re_evaluation_trigger"
    print(f"tools.yaml ok: {len(cands)} candidates + {len(proh)} prohibited (reason+trigger each)")


def check_prohibited_absent():
    t = load_yaml("registries/tools.yaml")
    tokens = set()
    for tid in [p["tool_id"] for p in t["prohibited"]]:
        tokens.add(tid.replace("_", "-"))
        tokens.add(tid.replace("_", ""))
    hits = []
    for root_dir in ("modules", "conf"):
        for f in glob.glob(f"{root_dir}/**/*", recursive=True):
            if not os.path.isfile(f):
                continue
            try:
                txt = open(f, encoding="utf-8", errors="ignore").read().lower()
            except OSError:
                continue
            for tok in tokens:
                if tok in txt:
                    hits.append((f, tok))
    assert not hits, f"PROHIBITED tools found in modules/conf: {hits}"
    print("PROHIBITED grep ok: none in modules/ + conf/")


def check_hypotheses():
    h = load_yaml("registries/hypotheses.yaml")
    sm = h.get("state_machine", {})
    for s in ("proposed", "under_validation", "validated", "rejected", "superseded"):
        assert s in sm, f"state_machine missing {s}"
    hyps = {x["hypothesis_id"]: x for x in h.get("hypotheses", [])}
    assert "HYP-DNA-001" in hyps, "HYP-DNA-001 missing"
    hd = hyps["HYP-DNA-001"]
    for k in ("statement", "basis", "scope_notes", "metric_definitions", "derived_fields", "status", "validation_protocol"):
        assert k in hd, f"HYP-DNA-001 missing {k}"
    assert hd["status"] == "proposed"
    assert hd["validation_protocol"] is None
    md = str(hd["metric_definitions"])
    assert "片段分布" in md or "fragment" in md.lower(), "metric_definitions missing fragment-distribution metric"
    assert "n50" in md.lower(), "metric_definitions missing read N50 metric"
    print("hypotheses.yaml ok: state machine + HYP-DNA-001 (two-metric)")


def check_policy_and_compat():
    pol = load_yaml("policies/tcm-plant-experimental.yaml")
    assert pol["status"] == "experimental"
    for k, v in pol["thresholds"].items():
        assert v is None, f"experimental policy threshold {k} must be null, got {v!r}"
    cm = load_yaml("assets/compatibility_manifest.yaml")
    for k in ("compatibility_id", "pipeline", "method_spec", "reference_pack", "kraken_db", "policy_pack", "validation_dataset"):
        assert k in cm, f"compatibility manifest missing {k}"
    print("policy example (all-null) + compatibility manifest ok")


def main():
    check_parse()
    check_schema_input_fixtures()
    check_status_schema()
    check_traceability()
    check_tools_registry()
    check_prohibited_absent()
    check_hypotheses()
    check_policy_and_compat()
    print("ALL T0 CONTRACT CHECKS PASSED")


if __name__ == "__main__":
    main()
