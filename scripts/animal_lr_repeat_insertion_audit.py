#!/usr/bin/env python3
"""Audit large insertions supported by unique reference flanks in a BAM file."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


CIGAR_RE = re.compile(r"(\d+)([MIDNSHP=X])")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bam", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--locus-start", required=True, type=int)
    parser.add_argument("--locus-end", required=True, type=int)
    parser.add_argument("--flank-bases", required=True, type=int)
    parser.add_argument("--min-insertion-bases", required=True, type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.bam.is_file() or args.bam.stat().st_size == 0:
        raise FileNotFoundError(f"missing or empty BAM: {args.bam}")
    if args.locus_start < 0 or args.locus_end <= args.locus_start:
        raise ValueError("invalid locus interval")
    if args.flank_bases <= 0 or args.min_insertion_bases <= 0:
        raise ValueError("flank and insertion sizes must be positive")

    completed = subprocess.run(
        ["samtools", "view", str(args.bam)],
        text=True,
        capture_output=True,
        check=True,
    )
    spanning_records = []
    for line in completed.stdout.splitlines():
        fields = line.split("\t")
        flag = int(fields[1])
        if flag & (0x4 | 0x100 | 0x800):
            continue
        read_id = fields[0]
        reference_start = int(fields[3]) - 1
        reference_position = reference_start
        insertions = []
        for length_text, operation in CIGAR_RE.findall(fields[5]):
            length = int(length_text)
            if (
                operation == "I"
                and args.locus_start <= reference_position <= args.locus_end
                and length >= args.min_insertion_bases
            ):
                insertions.append(
                    {"reference_position": reference_position, "length": length}
                )
            if operation in "M=XDN":
                reference_position += length
        reference_end = reference_position
        if (
            reference_start <= args.locus_start - args.flank_bases
            and reference_end >= args.locus_end + args.flank_bases
        ):
            spanning_records.append(
                {
                    "read_id": read_id,
                    "mapq": int(fields[4]),
                    "orientation": "reverse" if flag & 0x10 else "forward",
                    "reference_start": reference_start,
                    "reference_end": reference_end,
                    "large_insertions": insertions,
                }
            )

    supported = [record for record in spanning_records if record["large_insertions"]]
    lengths = sorted(
        insertion["length"]
        for record in supported
        for insertion in record["large_insertions"]
    )
    result = {
        "schema_version": "animal-lr-repeat-insertion-audit-v0.1",
        "input_bam": str(args.bam),
        "parameters": {
            "locus_start": args.locus_start,
            "locus_end": args.locus_end,
            "flank_bases_each_side": args.flank_bases,
            "min_insertion_bases": args.min_insertion_bases,
            "alignment_semantics": "primary_non_supplementary",
        },
        "spanning_read_count": len(spanning_records),
        "spanning_reads_with_large_insertion": len(supported),
        "spanning_reads_without_large_insertion": len(spanning_records) - len(supported),
        "large_insertion_lengths": lengths,
        "supporting_records": supported,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
