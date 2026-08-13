import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin" / "m4_hybrid_evidence.py"
SPEC = importlib.util.spec_from_file_location("m4_hybrid_evidence", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_cs_parser_and_mask_liftover_exclude_query_insertions(tmp_path):
    fasta = tmp_path / "query.fa"
    fasta.write_text(">q\nAAAAACCGGGGG\n")
    bed = tmp_path / "source.bed"
    bed.write_text("t\t2\t8\tcore\n")
    paf = tmp_path / "alignment.paf"
    paf.write_text("q\t12\t0\t12\t+\tt\t10\t0\t10\t10\t12\t60\ttp:A:P\tcs:Z:=AAAAA+CC=GGGGG\n")

    lifted, metadata = MODULE.lift_mask(paf, bed, fasta)

    assert lifted == {"q": [(2, 5, "core"), (7, 10, "core")]}
    assert metadata["lifted_bases"] == 6
    assert metadata["topology_use"] == "PROHIBITED"


def test_heldout_metrics_are_core_only_and_preserve_nondecision_status(tmp_path):
    candidate = tmp_path / "candidate.fa"
    candidate.write_text(">ctg\nAAAACCCCGGGGTTTT\n")
    bed = tmp_path / "core.bed"
    bed.write_text("ctg\t0\t8\tunique\n")
    depth = tmp_path / "depth.tsv"
    depth.write_text("".join(f"ctg\t{i}\t20\n" for i in range(1, 17)))
    vcf = tmp_path / "heldout.vcf"
    vcf.write_text(
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsample\n"
        "ctg\t2\t.\tA\tG\t60\tPASS\t.\tGT:DP:AD\t1:20:1,19\n"
        "ctg\t12\t.\tG\tGA\t60\tPASS\t.\tGT:DP:AD\t1:20:0,20\n"
    )
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({
        "alignment_filters": {"minimum_callable_depth": 10},
        "homopolymer": {"minimum_candidate_run_length": 4},
    }))

    ledger, metrics = MODULE.evaluate_vcf(
        candidate, vcf, depth, bed, policy, "animal", "B0", "heldout",
    )

    assert metrics["residual_unsupported_loci"] == 1
    assert metrics["outside_core_residuals"] == 1
    assert metrics["heldout_core_concordance"] == 0.875
    assert metrics["status"] == "INCONCLUSIVE"
    assert metrics["decision"] == "NOT_APPLICABLE"
    assert [row["evaluation_status"] for row in ledger] == ["EVALUABLE", "NOT_EVALUABLE"]
