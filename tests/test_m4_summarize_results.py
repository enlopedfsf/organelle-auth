import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "m4_summarize_results.py"
SPEC = importlib.util.spec_from_file_location("m4_summarize_results", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def metric(arm, residuals, homopolymers, concordance, callable_bases=100):
    return {
        "taxon": "plant",
        "arm": arm,
        "residual_unsupported_loci": residuals,
        "evaluable_homopolymer_discordances": homopolymers,
        "heldout_core_concordance": concordance,
        "callable_core_bases": callable_bases,
    }


def test_dominance_uses_only_preregistered_counts_and_b0_nonregression():
    rows = [
        metric("B0", 10, 8, 0.99),
        metric("R1", 8, 7, 0.995),
        metric("P0", 6, 5, 0.996),
        metric("C0", 5, 4, 0.997),
        metric("R1P1", 1, 1, 0.999, callable_bases=70),
        metric("R1C1", 3, 2, 0.998),
    ]

    result = MODULE.dominance(rows, "plant")

    assert result["preregistered_numeric_winners"] == ["R1P1"]
    assert result["scientific_outcome"] == "NUMERIC_DOMINANT_UNDER_PREREGISTERED_RULE"
    assert result["callable_core_spread_bases"] == 30
    assert result["status"] == "INCONCLUSIVE"


def test_tied_minima_produce_conditional_not_posthoc_winner():
    rows = [
        metric("B0", 4, 4, 0.99),
        metric("R1", 2, 2, 0.995),
        metric("P0", 0, 0, 1.0),
        metric("C0", 0, 0, 1.0),
        metric("R1P1", 0, 0, 1.0),
        metric("R1C1", 0, 0, 1.0),
    ]

    result = MODULE.dominance(rows, "plant")

    assert result["preregistered_numeric_winners"] == []
    assert result["scientific_outcome"] == "CONDITIONAL"
