import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
RESULTS = ROOT / "openspec/changes/m4-reference-grade-and-audit/evidence/results"


def test_candidate_ceiling_and_blockers():
    plant = json.loads((RESULTS / "plant-candidate-status.json").read_text())
    animal = json.loads((RESULTS / "animal-candidate-status.json").read_text())
    blockers = json.loads((RESULTS / "release-blockers.json").read_text())
    for record in (plant, animal):
        assert record["status"] == "INCONCLUSIVE"
        assert record["assembly_grade"] == "CANDIDATE"
        assert record["decision"] == "NOT_APPLICABLE"
        assert record["topology"] == "INCONCLUSIVE"
    assert plant["route"] == "R1P1"
    assert animal["route"] == "CONDITIONAL"
    assert blockers["assembly_grade_ceiling"] == "CANDIDATE"
    assert set(("TOPOLOGY_INCONCLUSIVE", "CYCLONESEQ_PENDING_REAL_DATA", "PRODUCTION_THRESHOLDS_NOT_CONFIGURED")) <= set(blockers["blockers"])
