import json
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
RUN = ROOT / "runs/output/animal-lr-recruitment-diagnostics"


def test_raven_is_experimental_comparator_only():
    registry = yaml.safe_load((ROOT / "registries/tools.yaml").read_text())
    raven = next(item for item in registry["candidates"] if item["tool_id"] == "raven")
    assert raven["version"] == "1.8.3"
    assert raven["admission_status"] == "EXPERIMENTAL"
    assert "comparator" in raven["notes"].lower()
    assert "cannot enter identify or decision" in raven["notes"].lower()


def test_raven_comparison_records_order_sensitivity_without_topology_promotion():
    evidence = json.loads((RUN / "E/raven-comparison.json").read_text())
    assert evidence["decision"] == "NOT_APPLICABLE"
    assert evidence["topology"] == "INCONCLUSIVE"
    assert len(evidence["runs"]) == 2
    lengths = [run["assembly"]["total_bases"] for run in evidence["runs"]]
    assert lengths == [19421, 19271]
    assert all(run["assembly"]["gfa_self_loop"] for run in evidence["runs"])
    assert all(run["anchor_alignment"]["target_breadth_fraction"] == 1.0 for run in evidence["runs"])
    assert all(run["anchor_alignment"]["gap_compressed_core_identity"] > 0.999 for run in evidence["runs"])


def test_hyp_dna002_audits_all_13_reads_and_rejects_true_multimer_subhypothesis():
    evidence = json.loads((RUN / "F/hyp-dna-002.json").read_text())
    assert evidence["decision"] == "NOT_APPLICABLE"
    assert evidence["topology"] == "INCONCLUSIVE"
    assert len(evidence["reads"]) == 13
    assert evidence["classification_counts"] == {
        "CHIMERIC_JUNK": 12,
        "NUMT_FLANK_CHIMERA": 1,
    }
    assert evidence["hypothesis"]["grade"] == "SUGGESTIVE"
    assert evidence["hypothesis"]["true_same_orientation_multimer_subhypothesis"] == "REJECTED"
    assert all(Path(ROOT / row["dotplot"]).is_file() for row in evidence["reads"])


def test_validation_main_body_contains_five_link_closeout_and_hard_gates():
    report = (RUN / "VALIDATION-animal-lr.md").read_text()
    for phrase in (
        "Environment bug",
        "Recruitment logic bug",
        "Length-filter repair disproved",
        "Assembler run/order sensitivity",
        "AT-rich micro-edge remains unresolved",
        "Topology: `INCONCLUSIVE`",
        "Decision: `NOT_APPLICABLE`",
        "PMAT2 remains gated by Issue #10",
    ):
        assert phrase in report
