import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "plant_common_callability.py"
SPEC = importlib.util.spec_from_file_location("plant_common_callability", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

ARMS = MODULE.ARMS
cigar_pairs = MODULE.cigar_pairs
classify_r1p1 = MODULE.classify_r1p1
common_callable_intersection = MODULE.common_callable_intersection
denominator_metrics = MODULE.denominator_metrics
load_unique_projection = MODULE.load_unique_projection
merge_positions_by_region = MODULE.merge_positions_by_region
write_bed = MODULE.write_bed


def test_preregistered_depth_source_matches_archived_policy():
    preregistration = json.loads(
        (
            ROOT
            / "openspec/changes/archive/2026-08-14-plant-common-callability/evidence/preregistration.json"
        ).read_text()
    )
    policy = json.loads(
        (ROOT / "openspec/changes/archive/2026-08-13-m4-hybrid-backbone-and-polish/evidence/evaluation-policy.json").read_text()
    )
    assert preregistration["callability"]["minimum_depth_source"] == (
        "evaluation_policy.alignment_filters.minimum_callable_depth"
    )
    assert policy["alignment_filters"]["minimum_callable_depth"] == 10


def test_cigar_projection_handles_indels_without_inventing_pairs():
    pairs = list(cigar_pairs("q", 0, 4, "+", "b0", 10, "1=1I1=1D1="))
    assert pairs == [
        (("q", 0), ("b0", 10)),
        (("q", 2), ("b0", 11)),
        (("q", 3), ("b0", 13)),
    ]


def test_cigar_projection_handles_reverse_query_coordinates():
    pairs = list(cigar_pairs("q", 2, 5, "-", "b0", 7, "3="))
    assert pairs == [
        (("q", 4), ("b0", 7)),
        (("q", 3), ("b0", 8)),
        (("q", 2), ("b0", 9)),
    ]


def test_projection_excludes_multiply_projected_b0_base(tmp_path: Path):
    paf = tmp_path / "ambiguous.paf"
    paf.write_text(
        "q1\t1\t0\t1\t+\tb0\t1\t0\t1\t1\t1\t60\ttp:A:P\tcg:Z:1=\n"
        "q2\t1\t0\t1\t+\tb0\t1\t0\t1\t1\t1\t60\ttp:A:P\tcg:Z:1=\n"
    )
    mapping, projected, stats = load_unique_projection(paf, 60)
    assert mapping == {}
    assert projected == set()
    assert stats["multiply_projected_b0_bases"] == 2


@pytest.mark.parametrize(
    ("counts", "expected", "leaders"),
    [
        ({"B0": 5, "R1": 3, "P0": 2, "C0": 4, "R1P1": 1, "R1C1": 2}, "RETAINS_SOLE_LEAD", ["R1P1"]),
        ({"B0": 5, "R1": 3, "P0": 1, "C0": 4, "R1P1": 1, "R1C1": 2}, "TIED_LOWEST", ["P0", "R1P1"]),
        ({"B0": 5, "R1": 3, "P0": 0, "C0": 4, "R1P1": 1, "R1C1": 2}, "DOES_NOT_LEAD", ["P0"]),
    ],
)
def test_preregistered_conclusion_states(counts, expected, leaders):
    assert tuple(counts) == ARMS
    assert classify_r1p1(counts) == (expected, leaders)


def test_common_bed_merge_respects_regions():
    intervals = {"b0": [(0, 3, "a"), (3, 6, "b")]}
    rows = merge_positions_by_region({("b0", 0), ("b0", 1), ("b0", 3), ("b0", 4)}, intervals)
    assert rows == [
        {"contig": "b0", "start": 0, "end": 2, "region": "a"},
        {"contig": "b0", "start": 3, "end": 5, "region": "b"},
    ]


def test_common_bed_is_headerless(tmp_path: Path):
    bed = tmp_path / "common.bed"
    write_bed(bed, [{"contig": "b0", "start": 1, "end": 3, "region": "core"}])
    assert bed.read_text() == "b0\t1\t3\tcore\n"


def test_common_intersection_uses_all_six_arms_and_fails_when_empty():
    shared = {("b0", 1), ("b0", 2)}
    callable_by_arm = {arm: shared | {("b0", index + 10)} for index, arm in enumerate(ARMS)}
    assert common_callable_intersection(callable_by_arm) == shared
    callable_by_arm["R1C1"] = {("b0", 99)}
    with pytest.raises(ValueError, match="intersection is empty"):
        common_callable_intersection(callable_by_arm)


def test_zero_denominators_are_explicitly_blank_not_division_errors():
    assert denominator_metrics(0, 0, 0) == {
        "projected_bases": 0,
        "callable_bases": 0,
        "callable_fraction": "",
        "residual_loci": 0,
        "residual_rate_per_10kb": "",
    }


def test_cigar_consumption_mismatch_fails_closed():
    with pytest.raises(ValueError, match="consumption mismatch"):
        list(cigar_pairs("q", 0, 3, "+", "b0", 0, "2="))
