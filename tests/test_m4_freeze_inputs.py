import gzip
import importlib.util
import json
import shutil
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "m4_freeze_inputs.py"
SPEC = importlib.util.spec_from_file_location("m4_freeze_inputs", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
PIGZ = shutil.which("pigz")
assert PIGZ is not None, "pigz is required for M4 splitter tests"


def write_fastq(path: Path, ids: list[str], mate: int) -> None:
    with gzip.open(path, "wt") as handle:
        for read_id in ids:
            handle.write(f"@{read_id}/{mate}\nACGT\n+\nIIII\n")


def run_split(tmp_path: Path, ids: list[str], suffix: str = "") -> dict:
    r1 = tmp_path / f"r1{suffix}.fastq.gz"
    r2 = tmp_path / f"r2{suffix}.fastq.gz"
    write_fastq(r1, ids, 1)
    write_fastq(r2, ids, 2)
    return MODULE.split_pairs(
        r1,
        r2,
        tmp_path / f"out{suffix}",
        f"sample{suffix}",
        "SAMPLE",
        "public_evaluation",
        11,
        PIGZ,
        1,
    )


def test_split_is_pair_preserving_and_deterministic(tmp_path):
    ids = [f"read-{index}" for index in range(100)]
    first = run_split(tmp_path, ids, "-a")
    second = run_split(tmp_path, ids, "-b")

    assert first["pair_counts"] == second["pair_counts"]
    assert first["assignment_audit"]["overlap_pairs"] == 0
    assert first["assignment_audit"]["count_balance"] is True
    for key in first["outputs"]:
        assert first["outputs"][key]["sha256"] == second["outputs"][key]["sha256"]


def test_mate_id_mismatch_removes_partial_outputs(tmp_path):
    r1 = tmp_path / "r1.fastq.gz"
    r2 = tmp_path / "r2.fastq.gz"
    write_fastq(r1, ["same", "left"], 1)
    write_fastq(r2, ["same", "right"], 2)
    output = tmp_path / "out"

    with pytest.raises(ValueError, match="mate mismatch"):
        MODULE.split_pairs(
            r1,
            r2,
            output,
            "sample",
            "SAMPLE",
            "public_evaluation",
            11,
            PIGZ,
            1,
        )
    assert not list(output.glob("*.fastq.gz"))
    assert not list(output.glob("*.partial.*"))


def test_unequal_mate_counts_fail(tmp_path):
    r1 = tmp_path / "r1.fastq.gz"
    r2 = tmp_path / "r2.fastq.gz"
    write_fastq(r1, ["one", "two"], 1)
    write_fastq(r2, ["one"], 2)

    with pytest.raises(ValueError, match="different numbers"):
        MODULE.split_pairs(
            r1,
            r2,
            tmp_path / "out",
            "sample",
            "SAMPLE",
            "public_evaluation",
            11,
            PIGZ,
            1,
        )


def test_manifest_is_valid_json(tmp_path):
    manifest = tmp_path / "manifest.json"
    MODULE.write_manifest_atomic(manifest, {"state": "PASS"})
    assert json.loads(manifest.read_text()) == {"state": "PASS"}
