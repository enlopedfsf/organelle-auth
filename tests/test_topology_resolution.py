import json
from pathlib import Path


def test_mapq_recount_copy_aware_contract():
    p = Path("runs/output/topology-resolution-experiments/junction-recount.json")
    d = json.loads(p.read_text())
    assert d["prior_high_quality_count"] == 37
    assert d["mapq_ge_20_read_identity_count"] == 2
    assert d["raw_read_identity_count"] >= d["mapq_ge_20_read_identity_count"]
    assert d["copy_aware_weighted_support"] <= d["raw_read_identity_count"]
    assert d["decision"] == "NOT_APPLICABLE"


def test_grid_manifest_is_bounded_and_frozen():
    p = Path("runs/output/topology-resolution-experiments/grid/manifest.json")
    d = json.loads(p.read_text())
    assert len(d["combinations"]) <= 6
    assert d["input_sha256"] == "93f4fd3bc3969e5d4d3577870b32f4a63d99ddc57a325f84403d7f089531f3c8"
    assert d["status"] == "REDUCED_GRID_BLOCKED_RUNTIME_TERMINATION"
