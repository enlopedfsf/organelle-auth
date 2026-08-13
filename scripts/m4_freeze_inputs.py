#!/usr/bin/env python3
"""Create the deterministic, pair-preserving M4 short-read split."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
from contextlib import ExitStack
from itertools import zip_longest
from pathlib import Path
from typing import BinaryIO, Iterator


SALT = "m4-hybrid-v1"
READ_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(READ_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_id(header: bytes) -> str:
    token = header.split(None, 1)[0].decode("utf-8")
    if token.startswith("@"):
        token = token[1:]
    if token.endswith(("/1", "/2")):
        token = token[:-2]
    if not token:
        raise ValueError("empty canonical FASTQ read identifier")
    return token


def fastq_records(path: Path) -> Iterator[tuple[bytes, bytes, bytes, bytes]]:
    with gzip.open(path, "rb") as handle:
        index = 0
        while True:
            header = handle.readline()
            if not header:
                return
            index += 1
            sequence = handle.readline()
            plus = handle.readline()
            quality = handle.readline()
            if not sequence or not plus or not quality:
                raise ValueError(f"truncated FASTQ record {index}: {path}")
            if not header.startswith(b"@") or not plus.startswith(b"+"):
                raise ValueError(f"malformed FASTQ record {index}: {path}")
            if len(sequence.rstrip(b"\r\n")) != len(quality.rstrip(b"\r\n")):
                raise ValueError(f"sequence/quality length mismatch at record {index}: {path}")
            yield header, sequence, plus, quality


def split_bucket(pair_id: str) -> str:
    value = int(
        hashlib.sha256(f"{SALT}\t{pair_id}".encode("utf-8")).hexdigest()[:8],
        16,
    )
    return "heldout" if value % 10 < 2 else "train"


def validate_input(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size == 0:
        raise ValueError(f"empty input: {path}")


def gzip_integrity(path: Path) -> None:
    with gzip.open(path, "rb") as handle:
        for _ in iter(lambda: handle.read(READ_SIZE), b""):
            pass


def pigz_version(pigz: str) -> str:
    result = subprocess.run(
        [pigz, "--version"], check=True, capture_output=True, text=True
    )
    return (result.stdout or result.stderr).strip().splitlines()[0]


def write_manifest_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    try:
        temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def split_pairs(
    r1: Path,
    r2: Path,
    out_dir: Path,
    label: str,
    sample_id: str,
    source_data_type: str,
    source_selection_seed: int,
    pigz: str,
    threads: int,
) -> dict:
    validate_input(r1)
    validate_input(r2)
    out_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "train_r1": out_dir / f"{label}.train.R1.fastq.gz",
        "train_r2": out_dir / f"{label}.train.R2.fastq.gz",
        "heldout_r1": out_dir / f"{label}.heldout.R1.fastq.gz",
        "heldout_r2": out_dir / f"{label}.heldout.R2.fastq.gz",
    }
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing:
        raise FileExistsError("refusing to overwrite frozen outputs: " + ", ".join(existing))

    temporary = {
        key: path.with_name(f".{path.name}.partial.{os.getpid()}")
        for key, path in outputs.items()
    }
    counts = {"train_pairs": 0, "heldout_pairs": 0, "total_pairs": 0}
    id_streams = {"train": hashlib.sha256(), "heldout": hashlib.sha256()}
    processes: dict[str, subprocess.Popen] = {}

    try:
        with ExitStack() as stack:
            output_handles: dict[str, BinaryIO] = {
                key: stack.enter_context(path.open("wb")) for key, path in temporary.items()
            }
            for key, handle in output_handles.items():
                processes[key] = subprocess.Popen(
                    [pigz, "-n", "-1", "-p", str(threads), "-c"],
                    stdin=subprocess.PIPE,
                    stdout=handle,
                )

            left = fastq_records(r1)
            right = fastq_records(r2)
            for index, records in enumerate(zip_longest(left, right), 1):
                rec1, rec2 = records
                if rec1 is None or rec2 is None:
                    raise ValueError("R1/R2 contain different numbers of records")
                id1 = canonical_id(rec1[0])
                id2 = canonical_id(rec2[0])
                if id1 != id2:
                    raise ValueError(f"mate mismatch at pair {index}: {id1} != {id2}")
                group = split_bucket(id1)
                for mate, record in (("r1", rec1), ("r2", rec2)):
                    pipe = processes[f"{group}_{mate}"].stdin
                    if pipe is None:
                        raise RuntimeError("pigz stdin unavailable")
                    pipe.write(b"".join(record))
                counts[f"{group}_pairs"] += 1
                counts["total_pairs"] += 1
                id_streams[group].update(id1.encode("utf-8") + b"\n")

            for process in processes.values():
                if process.stdin is not None:
                    process.stdin.close()
            failures = {}
            for key, process in processes.items():
                return_code = process.wait()
                if return_code != 0:
                    failures[key] = return_code
            if failures:
                raise RuntimeError(f"pigz compression failed: {failures}")

        for path in temporary.values():
            gzip_integrity(path)
        for key, path in temporary.items():
            os.replace(path, outputs[key])
    except BaseException:
        for process in processes.values():
            if process.stdin is not None and not process.stdin.closed:
                process.stdin.close()
            if process.poll() is None:
                process.terminate()
            process.wait()
        for path in temporary.values():
            path.unlink(missing_ok=True)
        raise

    return {
        "schema_version": "m4-freeze-inputs-v2",
        "label": label,
        "sample_id": sample_id,
        "source_data_type": source_data_type,
        "source_processing_budget": "approximately 2 Gb combined paired bases",
        "source_selection_seed": source_selection_seed,
        "inputs": {
            "r1": {"path": str(r1.resolve()), "bytes": r1.stat().st_size, "sha256": sha256_file(r1)},
            "r2": {"path": str(r2.resolve()), "bytes": r2.stat().st_size, "sha256": sha256_file(r2)},
        },
        "outputs": {
            key: {
                "path": str(path.resolve()),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "gzip_integrity": "PASS",
            }
            for key, path in outputs.items()
        },
        "pair_counts": counts,
        "assignment_audit": {
            "train_pair_id_stream_sha256": id_streams["train"].hexdigest(),
            "heldout_pair_id_stream_sha256": id_streams["heldout"].hexdigest(),
            "overlap_pairs": 0,
            "overlap_check": "PASS_BY_EXCLUSIVE_DETERMINISTIC_PARTITION",
            "count_balance": counts["train_pairs"] + counts["heldout_pairs"] == counts["total_pairs"],
        },
        "rule": {
            "salt": SALT,
            "canonical_id": "first whitespace-delimited token, strip leading @ and terminal /1 or /2",
            "hash": "SHA256(UTF-8(salt + tab + canonical_pair_id))",
            "bucket": "first 8 hex digits as unsigned integer modulo 10; 0-1 heldout, 2-9 train",
            "pair_preservation": True,
        },
        "runtime": {
            "pigz_path": str(Path(pigz).resolve()),
            "pigz_version": pigz_version(pigz),
            "pigz_parameters": ["-n", "-1", "-p", str(threads), "-c"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--r1", required=True, type=Path)
    parser.add_argument("--r2", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--sample-id", required=True)
    parser.add_argument(
        "--source-data-type",
        required=True,
        choices=("public_evaluation", "real_cycloneseq_transfer"),
    )
    parser.add_argument("--source-selection-seed", required=True, type=int)
    parser.add_argument("--pigz", default=shutil.which("pigz"))
    parser.add_argument("--threads", default=4, type=int)
    args = parser.parse_args()
    if not args.pigz:
        parser.error("pigz not found; provide --pigz")
    if args.threads < 1:
        parser.error("--threads must be positive")

    result = split_pairs(
        args.r1,
        args.r2,
        args.out_dir,
        args.label,
        args.sample_id,
        args.source_data_type,
        args.source_selection_seed,
        args.pigz,
        args.threads,
    )
    result["script"] = {
        "path": str(Path(__file__).resolve()),
        "sha256": sha256_file(Path(__file__)),
    }
    write_manifest_atomic(args.manifest, result)


if __name__ == "__main__":
    main()
