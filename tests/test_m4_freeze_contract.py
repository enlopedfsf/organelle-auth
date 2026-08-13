import hashlib
import json
import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CHANGE = ROOT / "openspec" / "changes" / "m4-hybrid-backbone-and-polish"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class M4FreezeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checklist = json.loads((CHANGE / "freeze-checklist.json").read_text())
        cls.mask = json.loads(
            (CHANGE / "evidence" / "animal-core-mask" / "animal-core.metadata.json").read_text()
        )
        cls.mask_approval = json.loads(
            (CHANGE / "evidence" / "animal-core-mask" / "animal-core.approval.json").read_text()
        )
        cls.compatibility = json.loads(
            (CHANGE / "evidence" / "input-compatibility.json").read_text()
        )
        cls.arm_protocols = json.loads(
            (CHANGE / "evidence" / "arm-protocols.json").read_text()
        )
        cls.tools = yaml.safe_load((ROOT / "registries" / "tools.yaml").read_text())

    def test_execution_completed_without_crossing_nondecision_boundary(self):
        execution = self.checklist["execution"]
        self.assertEqual(execution["twelve_arms"], "COMPLETE_12_OF_12")
        self.assertEqual(execution["task_result"], "80_OF_80_COMPLETED_EXIT_0")
        self.assertEqual(execution["animal_scientific_outcome"], "CONDITIONAL")
        self.assertEqual(execution["status"], "INCONCLUSIVE")
        self.assertEqual(execution["assembly_grade"], "CANDIDATE")
        self.assertEqual(execution["decision"], "NOT_APPLICABLE")
        self.assertEqual(execution["cycloneseq"], "PENDING_REAL_DATA")
        self.assertEqual(execution["pmat2"], "GATED_ISSUE_10")

    def test_public_short_reads_are_illumina_and_not_marked_project_validated(self):
        for taxon in ("plant", "animal"):
            self.assertEqual(
                self.compatibility["taxa"][taxon]["short_read_platform"], "ILLUMINA"
            )

        required = {"bwa_mem", "polypolish", "bcftools_consensus"}
        entries = {
            row["tool_id"]: row
            for row in self.tools["candidates"]
            if row["tool_id"] in required
        }
        self.assertEqual(set(entries), required)
        for entry in entries.values():
            self.assertIn("illumina", entry["supported_platforms"])
            self.assertEqual(entry["project_validated_platforms"], [])
            self.assertEqual(entry["admission_status"], "EXPERIMENTAL")
            self.assertRegex(entry["container_digest"], r"@sha256:[0-9a-f]{64}$")

    def test_split_counts_are_pair_preserving_and_near_eighty_twenty(self):
        for taxon in ("plant", "animal"):
            split = self.checklist["heldout_split"][taxon]
            self.assertEqual(
                split["source_pairs"], split["training_pairs"] + split["heldout_pairs"]
            )
            heldout_fraction = split["heldout_pairs"] / split["source_pairs"]
            self.assertGreater(heldout_fraction, 0.19)
            self.assertLess(heldout_fraction, 0.21)
            self.assertEqual(split["gzip_test"], "PASS")

    def test_arm_protocols_prevent_hidden_depth_truncation_and_heldout_leakage(self):
        polypolish = self.arm_protocols["polypolish"]
        bcftools = self.arm_protocols["bcftools_consensus"]
        self.assertIn("polypolish filter", polypolish["insert_filter"])
        self.assertIn("-a", polypolish["align_r1"].split())
        self.assertEqual(polypolish["polish_defaults"]["rounds"], 1)
        self.assertEqual(bcftools["maximum_depth"], 20_000_000)
        self.assertEqual(bcftools["maximum_indel_depth"], 20_000_000)
        self.assertIn("FORMAT/AD[0:1]/FORMAT/DP[0]>=0.8", bcftools["filter"])
        self.assertEqual(
            self.arm_protocols["heldout_use"],
            "PROHIBITED_FOR_POLISHING_OR_PARAMETER_SELECTION",
        )

    def test_animal_mask_is_local_nonrepeat_sequence_evidence_only(self):
        expected = {
            "contig_1": [[500, 2441]],
            "contig_3": [[515, 3800], [4839, 10305]],
        }
        self.assertEqual(self.mask["final_intervals"], expected)
        self.assertEqual(self.mask["excluded_repeat_or_ambiguous_contigs"], ["contig_2"])
        self.assertTrue(self.mask["assembly_attributes"]["contig_2"]["repeat"])
        self.assertFalse(self.mask["assembly_attributes"]["contig_1"]["circular"])
        self.assertFalse(self.mask["assembly_attributes"]["contig_3"]["circular"])
        self.assertEqual(self.mask["rules"]["heldout_use"], "PROHIBITED")
        self.assertTrue(self.mask["rules"]["topology_use"].startswith("PROHIBITED"))
        self.assertEqual(
            sum(end - start for blocks in expected.values() for start, end in blocks),
            self.checklist["animal_core_mask"]["total_bases"],
        )
        self.assertEqual(
            sha256_file(CHANGE / "evidence" / "animal-core-mask" / "animal-core.bed"),
            self.checklist["animal_core_mask"]["sha256"],
        )

    def test_freeze_requires_separate_owner_approval_with_topology_prohibited(self):
        approval_path = CHANGE / self.checklist["animal_core_mask"]["approval_record"]
        self.assertEqual(self.checklist["state"], "FROZEN")
        self.assertEqual(self.checklist["blocking_items"], [])
        self.assertEqual(self.checklist["animal_core_mask"]["status"], "FROZEN")
        self.assertEqual(self.mask["status"], "FROZEN")
        self.assertEqual(self.arm_protocols["state"], "FROZEN")
        self.assertEqual(sha256_file(approval_path), self.checklist["animal_core_mask"]["approval_record_sha256"])
        self.assertEqual(self.mask_approval["artifact_sha256"], self.checklist["animal_core_mask"]["sha256"])
        self.assertEqual(self.mask_approval["total_bases"], 10_692)
        self.assertEqual(
            self.mask_approval["approved_scope"],
            "animal six-arm local sequence-ranking metrics only",
        )
        self.assertIn("circularity", self.mask_approval["prohibited_claims"])
        self.assertIn("complete mitochondrial topology", self.mask_approval["prohibited_claims"])

    def test_manifest_is_sha256sum_compatible_and_repo_entries_match(self):
        seen = set()
        pattern = re.compile(r"^([0-9a-f]{64})  (.+)$")
        for line in (CHANGE / "MANIFEST.sha256").read_text().splitlines():
            if not line or line.startswith("#"):
                continue
            match = pattern.fullmatch(line)
            self.assertIsNotNone(match, line)
            digest, name = match.groups()
            self.assertNotIn(name, seen)
            seen.add(name)
            path = Path(name)
            if not path.is_absolute():
                local = ROOT / path
                self.assertTrue(local.is_file(), name)
                self.assertEqual(sha256_file(local), digest, name)


if __name__ == "__main__":
    unittest.main()
