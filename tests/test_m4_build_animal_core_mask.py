import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "m4_build_animal_core_mask.py"
SPEC = importlib.util.spec_from_file_location("m4_build_animal_core_mask", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def paf(query: str, target: str, start: int, end: int, strand: str = "+", mapq: int = 60) -> str:
    length = end - start
    return "\t".join(
        [
            query,
            "1000",
            str(start),
            str(end),
            strand,
            target,
            "1000",
            str(start),
            str(end),
            str(length),
            str(length),
            str(mapq),
        ]
    )


class AnimalCoreMaskBuilderTests(unittest.TestCase):
    def test_multiply_projected_target_segment_is_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.paf"
            path.write_text(
                paf("query-a", "contig_1", 0, 100)
                + "\n"
                + paf("query-b", "contig_1", 50, 150)
                + "\n"
            )
            retained = MODULE.read_unique_paf(path, {"contig_1"})
        self.assertEqual(retained["contig_1"], [(0, 50, "+"), (100, 150, "+")])

    def test_non_mapq60_and_mixed_orientation_are_not_admitted(self):
        with tempfile.TemporaryDirectory() as directory:
            low_mapq = Path(directory) / "low.paf"
            low_mapq.write_text(paf("query", "contig_1", 0, 100, mapq=59) + "\n")
            self.assertEqual(MODULE.read_unique_paf(low_mapq, {"contig_1"}), {})

            mixed = Path(directory) / "mixed.paf"
            mixed.write_text(
                paf("query", "contig_1", 0, 100, "+")
                + "\n"
                + paf("query", "contig_1", 100, 200, "-")
                + "\n"
            )
            self.assertEqual(MODULE.read_unique_paf(mixed, {"contig_1"}), {})


if __name__ == "__main__":
    unittest.main()
