#!/usr/bin/env python3
"""T0 static check: JSON/YAML validity + Requirement traceability matrix integrity.

Run by .github/workflows/spec-and-schema.yml on every PR/push (M0).

Checks:
  1. All JSON files (nextflow_schema.json + assets/*.json) parse.
  2. Key YAML files (openspec/config.yaml, openspec/traceability.yaml, .nf-core.yml) parse.
  3. Traceability matrix: no duplicate IDs; every ID maps to a declared spec_domain.
  4. Bidirectional: every Requirement ID cited in a spec (change delta or main spec)
     must appear in the matrix.
"""
import glob
import json
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")


def main() -> None:
    # 1. JSON
    json_files = ["nextflow_schema.json"] + glob.glob("assets/*.json")
    for f in json_files:
        with open(f) as fh:
            json.load(fh)
    print(f"JSON ok ({len(json_files)} files)")

    # 2. YAML
    yaml_files = ["openspec/config.yaml", "openspec/traceability.yaml", ".nf-core.yml"]
    for f in yaml_files:
        with open(f) as fh:
            yaml.safe_load(fh)
    print(f"YAML ok ({len(yaml_files)} files)")

    # 3. Traceability matrix integrity
    with open("openspec/traceability.yaml") as fh:
        m = yaml.safe_load(fh)
    reqs = m["requirements"]
    ids = [r["id"] for r in reqs]
    assert len(ids) == len(set(ids)), "duplicate Requirement IDs in matrix"
    domains = set(m["spec_domains"])
    for r in reqs:
        assert r["spec_domain"] in domains, (
            f"{r['id']} maps to unknown spec_domain {r['spec_domain']!r}"
        )

    # 4. Bidirectional: every ReqID cited in a spec must be in the matrix
    reqid_re = re.compile(
        r"\b(?:SCI|DATA|TEST|REL)-\d{3}\b|\bENG-POL-\d{3}\b|\bHYP-DNA-\d{3}\b"
    )
    id_set = set(ids)
    spec_files = glob.glob("openspec/changes/**/specs/**/*.md", recursive=True) + glob.glob(
        "openspec/specs/**/*.md", recursive=True
    )
    cited = set()
    for f in spec_files:
        cited.update(reqid_re.findall(open(f).read()))
    missing = cited - id_set
    assert not missing, f"ReqIDs cited in specs but absent from matrix: {sorted(missing)}"

    print(
        f"traceability ok: {len(ids)} ids across {len(domains)} domains; "
        f"{len(cited)} cited in specs, all present in matrix"
    )


if __name__ == "__main__":
    main()
