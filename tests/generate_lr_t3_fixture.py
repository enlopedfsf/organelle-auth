#!/usr/bin/env python3
"""Generate a bounded circular-plastome T3 fixture from a verified reference."""

from __future__ import annotations

import argparse
import gzip
import sys
from pathlib import Path


def read_single_fasta(path: Path) -> tuple[str, str]:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"REFERENCE_FASTA_MISSING_OR_EMPTY: {path}")
    name = None
    sequence = []
    for line in path.read_text().splitlines():
        if line.startswith(">"):
            if name is not None:
                raise SystemExit("REFERENCE_FASTA_MULTIRECORD")
            name = line[1:].split()[0]
        elif line.strip():
            sequence.append(line.strip().upper())
    joined = "".join(sequence)
    if not name or not joined:
        raise SystemExit("REFERENCE_FASTA_INVALID")
    return name, joined


def circular_slice(sequence: str, start: int, length: int) -> str:
    start %= len(sequence)
    doubled = sequence + sequence
    return doubled[start : start + length]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--out-fastq", type=Path, required=True)
    parser.add_argument("--copies", type=int, default=10)
    parser.add_argument("--read-length", type=int, default=10000)
    parser.add_argument("--step", type=int, default=5000)
    args = parser.parse_args()
    _, sequence = read_single_fasta(args.reference)
    if args.read_length <= 0 or args.step <= 0 or args.copies <= 0:
        raise SystemExit("FIXTURE_ARGUMENT_INVALID")
    starts = list(range(0, len(sequence), args.step))
    # Explicitly include reads spanning the circular origin and both M1 gap boundaries.
    starts.extend([len(sequence) - args.read_length // 2, 96370 - args.read_length // 2, 134285 - args.read_length // 2])
    count = bases = 0
    with gzip.GzipFile(filename="", mode="wb", fileobj=open(args.out_fastq, "wb"), mtime=0) as compressed:
        for copy_index in range(args.copies):
            for start in starts:
                read = circular_slice(sequence, start, args.read_length)
                record = f"@plastome_c{copy_index}_s{start}\n{read}\n+\n{'I' * len(read)}\n"
                compressed.write(record.encode())
                count += 1
                bases += len(read)
        # A deterministic off-target read proves recruitment does not retain all background.
        background = ("ACGT" * (args.read_length // 4 + 1))[: args.read_length]
        compressed.write(f"@background_control\n{background}\n+\n{'I' * len(background)}\n".encode())
        count += 1
        bases += len(background)
    sys.stdout.write(f"reads={count} bases={bases} reference_bases={len(sequence)}\n")


if __name__ == "__main__":
    main()
