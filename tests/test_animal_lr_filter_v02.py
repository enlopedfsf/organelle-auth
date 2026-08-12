import gzip
import json
import subprocess
import sys
from pathlib import Path


def paf_record(read_id, query_length, query_start, query_end, matches, block, target):
    return "\t".join(
        map(
            str,
            [
                read_id,
                query_length,
                query_start,
                query_end,
                "+",
                target,
                15000,
                0,
                block,
                matches,
                block,
                0,
            ],
        )
    )


def test_filter_requires_one_coherent_alignment(tmp_path):
    reads = tmp_path / "reads.fastq.gz"
    with gzip.open(reads, "wt") as handle:
        for read_id in ("fragmented", "coherent"):
            handle.write(f"@{read_id}\n" + "A" * 1000 + "\n+\n" + "I" * 1000 + "\n")

    paf = tmp_path / "rotations.paf"
    paf.write_text(
        "\n".join(
            [
                # The union covers 60%, but neither rotation covers 50% alone.
                paf_record("fragmented", 1000, 0, 300, 295, 300, "rotation_0"),
                paf_record("fragmented", 1000, 300, 600, 295, 300, "rotation_1"),
                paf_record("coherent", 1000, 100, 700, 570, 600, "rotation_0"),
            ]
        )
        + "\n"
    )
    output = tmp_path / "selected.fastq.gz"
    manifest = tmp_path / "manifest.json"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/animal_lr_filter_v02.py",
            "--paf",
            str(paf),
            "--reads",
            str(reads),
            "--output",
            str(output),
            "--manifest",
            str(manifest),
            "--min-aligned-bases",
            "500",
            "--min-query-aligned-fraction",
            "0.5",
            "--min-identity",
            "0.88",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    data = json.loads(manifest.read_text())
    assert data["selected_read_ids"] == ["coherent"]
    assert data["selection_semantics"] == "one_coherent_alignment_must_satisfy_all_thresholds"


def test_filter_applies_max_read_length_after_coherent_selection(tmp_path):
    reads = tmp_path / "reads.fastq.gz"
    with gzip.open(reads, "wt") as handle:
        for read_id, length in (("within", 900), ("too_long", 1200)):
            handle.write(f"@{read_id}\n" + "A" * length + "\n+\n" + "I" * length + "\n")

    paf = tmp_path / "rotations.paf"
    paf.write_text(
        "\n".join(
            [
                paf_record("within", 900, 0, 900, 891, 900, "rotation_0"),
                paf_record("too_long", 1200, 0, 1200, 1188, 1200, "rotation_0"),
            ]
        )
        + "\n"
    )
    output = tmp_path / "selected.fastq.gz"
    manifest = tmp_path / "manifest.json"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/animal_lr_filter_v02.py",
            "--paf",
            str(paf),
            "--reads",
            str(reads),
            "--output",
            str(output),
            "--manifest",
            str(manifest),
            "--min-aligned-bases",
            "500",
            "--min-query-aligned-fraction",
            "0.5",
            "--min-identity",
            "0.88",
            "--max-read-length",
            "1000",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    data = json.loads(manifest.read_text())
    assert data["selected_read_ids"] == ["within"]
    assert data["selected_read_count"] == 1
    assert data["parameters"]["max_read_length"] == 1000


def test_runtime_preflight_rejects_incomplete_path(tmp_path, monkeypatch):
    fake_flye = tmp_path / "flye"
    fake_flye.write_text("#!/bin/sh\necho 2.9.3\n")
    fake_flye.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    completed = subprocess.run(
        [sys.executable, "scripts/check_flye_runtime.py"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    result = json.loads(completed.stdout)
    assert result["status"] == "FAIL"
    assert result["missing_executables"] == ["flye-minimap2", "flye-samtools"]
