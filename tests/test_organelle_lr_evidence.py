#!/usr/bin/env python3
"""T1 tests for the M3 reference-first evidence helpers."""

from __future__ import annotations

import gzip
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "bin" / "organelle_lr_evidence.py"


def dump(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value, indent=2) + "\n")
    return path


def write_fastq(path: Path, records: list[tuple[str, str]]) -> Path:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "wt") as handle:
        for name, sequence in records:
            handle.write(f"@{name}\n{sequence}\n+\n{'F' * len(sequence)}\n")
    return path


def policy(target_bases=100) -> dict:
    return {
        "policy_id": "test-lr-experimental",
        "admission_status": "EXPERIMENTAL",
        "raw_input": {"target_bases": target_bases, "seed": 11, "purpose": "processing_budget_only"},
        "mapper": {"preset": "map-ont", "emit_cigar": True, "emit_cs": "long", "secondary": True, "max_secondary": 20, "secondary_score_ratio": 0.5},
        "recruitment": {
            "min_aligned_bases": 50,
            "min_query_aligned_fraction": 0.5,
            "max_divergence": 0.3,
            "mapq_is_sole_filter": False,
            "retain_alignment_classes": ["primary", "secondary", "supplementary"],
        },
        "target_gate": {
            "min_recruited_reads": 1,
            "min_recruited_bases": 100,
            "min_estimated_target_depth": 1.0,
            "min_reference_breadth": 0.5,
            "min_declared_junction_reads": 1,
            "max_recruited_to_aligned_ratio": 10.0,
        },
        "structural_evidence": {"min_junction_flank_bases": 5},
        "rescue": {"enabled": True, "max_passes": 2},
        "flye": {"read_type": "nano-hq", "genome_size": "100", "iterations": 1, "min_overlap": 20},
        "pmat2_comparator": {"enabled": True, "technology": "ont", "taxon_code": 0, "correction_mode": 0},
        "full_background_de_novo": {"enabled": False, "minimum_clean_depth": None},
    }


def metadata(status="ALLOWED_EXPERIMENTAL") -> dict:
    return {
        "schema_version": "test",
        "reference_pack_id": "test-pack",
        "reference_pack_version": "0.1",
        "reference_accession": "ref",
        "reference_status": status,
        "topology": "circular",
        "canonical_length": 100,
        "compatible_sample_ids": ["sample"],
        "rotation_offsets_0_based": [0, 25, 50, 75],
        "junctions": [
            {
                "id": "origin",
                "type": "circular_origin",
                "left_start_1based": 91,
                "left_end_1based": 100,
                "right_start_1based": 1,
                "right_end_1based": 10,
            }
        ],
        "m1_ir_gap": {"start_1based": 31, "end_1based": 50},
    }


class LongReadEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.work = Path(self.temp.name)
        self.ref = self.work / "ref.fasta"
        self.ref.write_text(">ref\n" + "A" * 100 + "\n")
        self.meta = dump(self.work / "metadata.json", metadata())
        self.policy = dump(self.work / "policy.json", policy())

    def tearDown(self):
        self.temp.cleanup()

    def run_tool(self, *arguments, success=True):
        result = subprocess.run([str(TOOL), *map(str, arguments)], text=True, capture_output=True)
        if success and result.returncode != 0:
            self.fail(f"command failed: {result.stderr}{result.stdout}")
        if not success:
            self.assertNotEqual(result.returncode, 0)
        return result

    def prepare(self):
        rotated = self.work / "rotated.fasta"
        coord = self.work / "coord.tsv"
        status = self.work / "reference-status.json"
        self.run_tool(
            "prepare-reference", "--sample-id", "sample", "--fasta", self.ref,
            "--metadata", self.meta, "--anchor-fasta", self.ref, "--out-fasta", rotated, "--out-map", coord,
            "--out-status", status,
        )
        return rotated, coord, status

    def test_reference_validation_and_rotations(self):
        rotated, coord, status = self.prepare()
        self.assertEqual(rotated.read_text().count(">"), 4)
        self.assertIn("ref|rot=75", coord.read_text())
        self.assertEqual(json.loads(status.read_text())["status"], "PASS")

        quarantined = dump(self.work / "quarantined.json", metadata("QUARANTINED"))
        result = self.run_tool(
            "prepare-reference", "--sample-id", "sample", "--fasta", self.ref,
            "--metadata", quarantined, "--anchor-fasta", self.ref, "--out-fasta", self.work / "bad.fa",
            "--out-map", self.work / "bad.tsv", "--out-status", self.work / "bad.json",
            success=False,
        )
        self.assertIn("REFERENCE_NOT_ALLOWED", result.stderr)

    def test_mapq_zero_secondary_whole_read_and_two_pass_union(self):
        paf = self.work / "reads.paf"
        paf.write_text(
            "read1\t100\t0\t100\t+\tref|rot=0\t100\t0\t100\t95\t100\t0\ttp:A:P\tcg:Z:100M\tcs:Z::100\n"
            "read1\t100\t0\t100\t+\tref|rot=50\t100\t0\t100\t95\t100\t0\ttp:A:S\tcg:Z:100M\tcs:Z::100\n"
            "read2\t100\t0\t60\t+\tref|rot=0\t100\t10\t70\t55\t60\t60\ttp:A:S\tcg:Z:60M\tcs:Z::60\n"
        )
        ids = self.work / "pass1.ids"
        evidence = self.work / "evidence.tsv"
        status = self.work / "selection.json"
        self.run_tool(
            "select-paf", "--paf", paf, "--policy", self.policy, "--pass-number", 1,
            "--out-ids", ids, "--out-evidence", evidence, "--out-status", status,
        )
        self.assertEqual(ids.read_text().splitlines(), ["read1", "read2"])
        self.assertIn("secondary", evidence.read_text())
        self.assertIn("\t0\t100M", evidence.read_text())

        fastq = write_fastq(self.work / "reads.fastq.gz", [("read1", "A" * 100), ("read2", "C" * 100), ("background", "G" * 100)])
        recruited = self.work / "recruited.fastq.gz"
        extract = self.work / "extract.json"
        self.run_tool("extract-fastq", "--fastq", fastq, "--ids", ids, "--out-fastq", recruited, "--out-manifest", extract)
        self.assertEqual(json.loads(extract.read_text())["extracted_complete_reads"], 2)
        with gzip.open(recruited, "rt") as handle:
            self.assertEqual(handle.read().count("@"), 2)

        pass2 = self.work / "pass2.ids"
        pass2.write_text("read2\nread3\n")
        union = self.work / "union.ids"
        union_status = self.work / "union.json"
        self.run_tool("union-ids", "--pass1", ids, "--pass2", pass2, "--policy", self.policy, "--out-ids", union, "--out-manifest", union_status)
        self.assertEqual(union.read_text().splitlines(), ["read1", "read2", "read3"])
        self.assertEqual(json.loads(union_status.read_text())["maximum_passes"], 2)

    def test_target_gate_and_production_null(self):
        _, coord, _ = self.prepare()
        evidence = self.work / "evidence.tsv"
        evidence.write_text(
            "query\teligible\treason\talignment_class\tquery_length\tquery_start\tquery_end\ttarget\ttarget_start\ttarget_end\tstrand\tmatches\talignment_length\tquery_aligned_fraction\tdivergence\tmapq\tcigar\tcs\n"
            "read1\t1\tPASS\tprimary\t100\t0\t100\tref|rot=0\t0\t100\t+\t100\t100\t1.0\t0.0\t0\t100M\t:100\n"
            "read2\t1\tPASS\tsecondary\t100\t0\t60\tref|rot=0\t10\t70\t+\t55\t60\t0.6\t0.0833\t0\t60M\t:60\n"
        )
        ids = self.work / "selected.ids"; ids.write_text("read1\nread2\n")
        reads = write_fastq(self.work / "recruited.fastq.gz", [("read1", "A" * 100), ("read2", "C" * 100)])
        metrics = self.work / "metrics.json"; status = self.work / "gate.json"
        self.run_tool(
            "target-gate", "--evidence", evidence, "--selected-ids", ids, "--reference-map", coord,
            "--reference-metadata", self.meta, "--policy", self.policy, "--recruited-fastq", reads,
            "--out-metrics", metrics, "--out-status", status,
        )
        self.assertEqual(json.loads(status.read_text())["status"], "ELIGIBLE_EXPERIMENTAL")
        self.assertGreaterEqual(json.loads(metrics.read_text())["reference_breadth"], 1.0)
        self.assertEqual(json.loads(metrics.read_text())["alignment_span_distribution"]["maximum"], 100)

        production = ROOT / "assets" / "policies" / "plant-long-read-reference-first" / "production-v0.1.json"
        null_status = self.work / "null-gate.json"
        self.run_tool(
            "target-gate", "--evidence", evidence, "--selected-ids", ids, "--reference-map", coord,
            "--reference-metadata", self.meta, "--policy", production, "--recruited-fastq", reads,
            "--out-metrics", self.work / "null-metrics.json", "--out-status", null_status,
        )
        self.assertEqual(json.loads(null_status.read_text())["reason_codes"], ["THRESHOLD_NOT_CONFIGURED"])

    def test_full_background_guard_is_closed(self):
        status = self.work / "route.json"
        self.run_tool(
            "route-guard", "--policy", self.policy, "--reference-state", "missing",
            "--strategy", "de_novo_fallback", "--observed-clean-depth", 100,
            "--out-status", status,
        )
        data = json.loads(status.read_text())
        self.assertFalse(data["full_background_pmat2_allowed"])
        self.assertEqual(data["reason_codes"], ["FULL_BACKGROUND_DE_NOVO_NOT_APPLICABLE"])

    def test_structural_gap_and_homopolymer_alignment(self):
        candidate = self.work / "candidate.fasta"; candidate.write_text(">candidate\n" + "A" * 100 + "\n")
        comparator = self.work / "comparator.fasta"; comparator.write_text(">comparator\n" + "A" * 100 + "\n")
        reference_paf = self.work / "candidate-ref.paf"
        reference_paf.write_text("candidate\t100\t0\t100\t+\tref\t100\t0\t100\t100\t100\t60\ttp:A:P\tcg:Z:100M\tcs:Z::100\n")
        comparator_paf = self.work / "comparator-ref.paf"
        comparator_paf.write_text("comparator\t100\t0\t100\t+\tref\t100\t0\t100\t100\t100\t60\ttp:A:P\tcg:Z:100M\tcs:Z::100\n")
        anchor_paf = self.work / "candidate-anchor.paf"; anchor_paf.write_text(reference_paf.read_text())
        read_paf = self.work / "read-candidate.paf"
        read_paf.write_text("read1\t100\t0\t100\t+\tcandidate\t100\t0\t100\t100\t100\t60\ttp:A:P\tcg:Z:100M\tcs:Z::100\n")
        structural = self.work / "structural.json"
        self.run_tool(
            "structural", "--candidate-fasta", candidate, "--comparator-fasta", comparator,
            "--reference-paf", reference_paf, "--comparator-reference-paf", comparator_paf,
            "--anchor-paf", anchor_paf, "--read-candidate-paf", read_paf,
            "--reference-metadata", self.meta, "--policy", self.policy, "--platform", "ONT",
            "--out-json", structural, "--out-tsv", self.work / "structural.tsv",
        )
        result = json.loads(structural.read_text())
        self.assertEqual(result["ir_gap_outcome"], "closed")
        self.assertEqual(result["independent_spanning_read_ids"], ["read1"])
        self.assertEqual(result["cycloneseq_transferability"], "PENDING_REAL_DATA")

        hp = self.work / "hp.json"
        self.run_tool(
            "homopolymer", "--anchor-fasta", self.ref, "--candidate-fasta", candidate,
            "--paf", anchor_paf, "--platform", "ONT", "--out-json", hp,
            "--out-tsv", self.work / "hp.tsv",
        )
        hp_result = json.loads(hp.read_text())
        self.assertEqual(hp_result["method"], "maximal_anchor_runs_lifted_through_minimap2_cigar")
        self.assertEqual(hp_result["records"][0]["run_length_delta"], 0)

    def test_budget_is_deterministic_and_streaming(self):
        reads = write_fastq(self.work / "input.fastq.gz", [(f"read{i}", "ACGT" * 25) for i in range(20)])
        budget_policy = dump(self.work / "budget-policy.json", policy(target_bases=1000))
        outputs = []
        for suffix in ("a", "b"):
            out = self.work / f"bounded-{suffix}.fastq.gz"
            manifest = self.work / f"bounded-{suffix}.json"
            self.run_tool("budget-fastq", "--fastq", reads, "--policy", budget_policy, "--out-fastq", out, "--out-manifest", manifest)
            outputs.append(json.loads(manifest.read_text()))
        self.assertEqual(outputs[0]["output_sha256"], outputs[1]["output_sha256"])
        self.assertEqual(outputs[0]["seed"], 11)
        self.assertEqual(outputs[0]["purpose"], "processing_budget_only")
        self.assertEqual(outputs[0]["input_sha256"], outputs[1]["input_sha256"])

    def test_corrupt_fastq_and_empty_candidate_fail_honestly(self):
        corrupt = self.work / "corrupt.fastq"
        corrupt.write_text("@truncated\nACGT\n+\n")
        result = self.run_tool(
            "budget-fastq", "--fastq", corrupt, "--policy", self.policy,
            "--out-fastq", self.work / "never.fastq", "--out-manifest", self.work / "never.json",
            success=False,
        )
        self.assertIn("FASTQ_TRUNCATED", result.stderr)

        empty = self.work / "empty.fasta"; empty.write_text("")
        empty_paf = self.work / "empty.paf"; empty_paf.write_text("")
        structural = self.work / "empty-structural.json"
        self.run_tool(
            "structural", "--candidate-fasta", empty, "--comparator-fasta", empty,
            "--reference-paf", empty_paf, "--comparator-reference-paf", empty_paf,
            "--anchor-paf", empty_paf, "--read-candidate-paf", empty_paf,
            "--reference-metadata", self.meta, "--policy", self.policy, "--platform", "ONT",
            "--out-json", structural, "--out-tsv", self.work / "empty-structural.tsv",
        )
        data = json.loads(structural.read_text())
        self.assertEqual(data["status"], "INCONCLUSIVE")
        self.assertEqual(data["ir_gap_outcome"], "not_assessable")
        self.assertEqual(data["reason_codes"], ["SUBSET_ASSEMBLY_FAILED"])

    def test_route_wiring_and_optional_comparator_failure_contracts(self):
        workflow = (ROOT / "workflows" / "organelleauth.nf").read_text()
        subworkflow = (ROOT / "subworkflows" / "local" / "plant_long_read_reference_first" / "main.nf").read_text()
        helper = (ROOT / "bin" / "organelle_lr_evidence.py").read_text()
        pmat = (ROOT / "modules" / "local" / "pmat2_subset_comparator" / "main.nf").read_text()
        flye = (ROOT / "modules" / "local" / "flye_subset" / "main.nf").read_text()

        identify_line = next(line for line in workflow.splitlines() if "identify = IDENTIFY(" in line)
        self.assertNotIn("lr_pilot", identify_line)
        self.assertIn("LR_ROUTE_GUARD", subworkflow)
        self.assertIn("LR_UNION_IDS", subworkflow)
        self.assertIn("rescue.max_passes must equal 2", helper)
        self.assertIn("pmat.correction_mode != 0", pmat)
        self.assertIn("COMPARATOR_ASSEMBLY_FAILED", pmat)
        self.assertIn("SUBSET_ASSEMBLY_FAILED", flye)


if __name__ == "__main__":
    unittest.main()
