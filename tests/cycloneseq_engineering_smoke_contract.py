import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_engineering_smoke_is_not_scientific_evidence():
    manifest = json.loads((ROOT / "assets/engineering_smoke/accession-manifest.json").read_text())
    status = json.loads((ROOT / "assets/engineering_smoke/status.json").read_text())
    assert "工程冒烟，非科学结论" in manifest["title"]
    assert manifest["decision"] == "NOT_APPLICABLE"
    assert manifest["cycloneseq_state"] == "PENDING_REAL_DATA"
    assert manifest["rosa"]["status"] == "QUEUED"
    assert status["routes"]["IDENTIFY"] == "BLOCKED"
    assert status["routes"]["DECISION"] == "BLOCKED"
    assert manifest["q10_q11"]["calibrated"] is False
    assert manifest["q10_q11"]["gating"] is False
