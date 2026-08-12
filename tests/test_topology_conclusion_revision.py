import json
from pathlib import Path


def test_revision_ledger_requires_unique_global_placements():
    d = json.loads(Path("runs/output/topology-conclusion-revision/evidence-ledger.json").read_text())
    assert d["candidate_count"] == 587
    assert d["qualifying_count"] == 0
    assert d["formal_topology"] == "INCONCLUSIVE"
    assert d["classification_counts"]["MAPQ_ZERO_AMBIGUOUS"] == 517
    assert d["classification_counts"]["NON_UNIQUE_ANCHOR"] == 53


def test_no_ledger_record_claims_independent_support():
    d = json.loads(Path("runs/output/topology-conclusion-revision/evidence-ledger.json").read_text())
    assert not any(row["independent_alignment_support"] for row in d["ledger"])
