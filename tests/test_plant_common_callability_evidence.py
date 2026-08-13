import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHANGE = (
    ROOT
    / "openspec"
    / "changes"
    / "archive"
    / "2026-08-14-plant-common-callability"
)
RESULTS = CHANGE / "evidence" / "results"
ARMS = ("B0", "R1", "P0", "C0", "R1P1", "R1C1")


def rows(path: Path):
    with path.open() as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def test_denominator_table_has_exact_six_arm_region_matrix_and_fair_denominators():
    table = rows(RESULTS / "arm-region-denominators.tsv")
    assert {row["arm"] for row in table} == set(ARMS)
    regions = {row["region"] for row in table}
    assert len(table) == len(ARMS) * len(regions)
    by_region = defaultdict(set)
    for row in table:
        by_region[row["region"]].add(int(row["callable_bases"]))
        projected = int(row["projected_bases"])
        callable_bases = int(row["callable_bases"])
        residuals = int(row["residual_loci"])
        assert float(row["callable_fraction"]) == round(callable_bases / projected, 6)
        assert float(row["residual_rate_per_10kb"]) == round(residuals * 10000 / callable_bases, 6)
    assert all(len(values) == 1 for values in by_region.values())
    all_regions = [row for row in table if row["region"] == "all_regions"]
    assert all(int(row["callable_bases"]) > 0 for row in all_regions)


def test_summary_follows_preregistered_conclusion_rule():
    summary = json.loads((RESULTS / "common-callability-summary.json").read_text())
    counts = summary["residual_loci_all_regions"]
    minimum = min(counts.values())
    leaders = [arm for arm in ARMS if counts[arm] == minimum]
    expected = (
        "RETAINS_SOLE_LEAD"
        if leaders == ["R1P1"]
        else "TIED_LOWEST"
        if "R1P1" in leaders
        else "DOES_NOT_LEAD"
    )
    assert summary["answer"] == expected
    assert summary["leaders"] == leaders
    assert summary["decision"] == "NOT_APPLICABLE"
    assert summary["cycloneseq"] == "PENDING_REAL_DATA"
    assert summary["parent_m4_result_modified"] is False


def test_bed_and_audit_account_for_the_reported_evidence():
    summary = json.loads((RESULTS / "common-callability-summary.json").read_text())
    bed_counts = Counter()
    with (RESULTS / "common-callable.bed").open() as handle:
        for raw in handle:
            chrom, start, end, region = raw.rstrip().split("\t")
            assert chrom and int(end) > int(start)
            bed_counts[region] += int(end) - int(start)
    assert sum(bed_counts.values()) == summary["common_callable_bases"]
    assert dict(bed_counts) == summary["common_callable_bases_by_region"]

    audit = rows(RESULTS / "residual-projection-audit.tsv")
    prereg = json.loads((CHANGE / "evidence" / "preregistration.json").read_text())
    source_rows = 0
    for arm in ARMS:
        source_rows += len(rows(Path(prereg["inputs"]["arms"][arm]["residual_ledger"])))
    assert len(audit) == source_rows
    assert {row["status"] for row in audit} <= {"INCLUDED", "EXCLUDED"}
