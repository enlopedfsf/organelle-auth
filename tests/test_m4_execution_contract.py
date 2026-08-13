import csv
import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHANGE = (
    ROOT
    / "openspec"
    / "changes"
    / "archive"
    / "2026-08-13-m4-hybrid-backbone-and-polish"
)
RESULTS = CHANGE / "evidence" / "results"


class M4ExecutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads((RESULTS / "execution-audit.json").read_text())
        cls.dominance = {
            row["taxon"]: row for row in json.loads((RESULTS / "dominance.json").read_text())
        }
        with (RESULTS / "six-arm-comparison.tsv").open() as handle:
            cls.comparison = list(csv.DictReader(handle, delimiter="\t"))

    def test_exact_six_by_two_matrix_and_all_tasks_completed(self):
        expected = {
            (taxon, arm)
            for taxon in ("plant", "animal")
            for arm in ("B0", "R1", "P0", "C0", "R1P1", "R1C1")
        }
        self.assertEqual({(row["taxon"], row["arm"]) for row in self.comparison}, expected)
        self.assertEqual(self.audit["metric_records"], 12)
        self.assertEqual(self.audit["nextflow_tasks"], 80)
        self.assertEqual(self.audit["task_status_counts"], {"COMPLETED": 80})
        self.assertTrue(self.audit["all_tasks_exit_zero"])

    def test_route_isolation_and_machine_status(self):
        self.assertFalse(self.audit["pmat2_invoked"])
        self.assertFalse(self.audit["identify_or_decision_invoked"])
        for row in self.comparison:
            self.assertEqual(row["status"], "INCONCLUSIVE")
            self.assertEqual(row["assembly_grade"], "CANDIDATE")
            self.assertEqual(row["decision"], "NOT_APPLICABLE")

    def test_preregistered_result_is_plant_numeric_winner_and_animal_conditional(self):
        self.assertEqual(
            self.dominance["plant"]["preregistered_numeric_winners"], ["R1P1"]
        )
        self.assertEqual(
            self.dominance["animal"]["scientific_outcome"], "CONDITIONAL"
        )
        self.assertEqual(self.dominance["animal"]["preregistered_numeric_winners"], [])
        self.assertGreater(self.dominance["plant"]["callable_core_spread_bases"], 0)

    def test_result_manifest_is_complete_and_valid(self):
        pattern = re.compile(r"^([0-9a-f]{64})  (.+)$")
        listed = set()
        for line in (RESULTS / "RESULT-MANIFEST.sha256").read_text().splitlines():
            match = pattern.fullmatch(line)
            self.assertIsNotNone(match, line)
            digest, filename = match.groups()
            path = RESULTS / filename
            self.assertTrue(path.is_file(), filename)
            self.assertNotIn(filename, listed)
            listed.add(filename)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        expected = {path.name for path in RESULTS.iterdir() if path.is_file()}
        expected.remove("RESULT-MANIFEST.sha256")
        self.assertEqual(listed, expected)

    def test_ledgers_have_required_fields_and_animal_outside_core_is_not_evaluable(self):
        required = {
            "taxon", "arm", "route", "contig", "position_1based", "ref", "alt",
            "depth", "mapping_ambiguity", "filter_reason", "support_source",
        }
        for path in RESULTS.glob("*.introduced-edit-ledger.tsv"):
            with path.open() as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                self.assertTrue(required.issubset(reader.fieldnames), path.name)
        with (RESULTS / "animal.P0.introduced-edit-ledger.tsv").open() as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        self.assertTrue(any(row["evaluation_status"] == "NOT_EVALUABLE" for row in rows))

    def test_local_reproduction_executables_are_hidden_schema_metadata(self):
        schema = json.loads((ROOT / "nextflow_schema.json").read_text())
        options = schema["$defs"]["hybrid_reference_build_options"]
        expected = {
            "m4_bwa_bin": "bwa",
            "m4_polypolish_bin": "polypolish",
            "m4_minimap2_bin": "minimap2",
            "m4_samtools_bin": "samtools",
            "m4_bcftools_bin": "bcftools",
        }
        self.assertIn(
            {"$ref": "#/$defs/hybrid_reference_build_options"}, schema["allOf"]
        )
        self.assertEqual(set(options["properties"]), set(expected))
        for name, default in expected.items():
            self.assertEqual(options["properties"][name]["type"], "string")
            self.assertEqual(options["properties"][name]["default"], default)
            self.assertTrue(options["properties"][name]["hidden"])


if __name__ == "__main__":
    unittest.main()
