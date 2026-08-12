#!/usr/bin/env python3
"""Select animal ONT reads using one coherent PAF alignment per read.

The four rotated bait references are alternative views of the same molecule.
Intervals from different PAF records must therefore never be unioned to make a
read pass.  A single alignment record has to satisfy every configured rule.
"""

from __future__ import annotations

import argparse
import collections
import gzip
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paf", required=True, type=Path)
    parser.add_argument("--reads", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--min-aligned-bases", required=True, type=int)
    parser.add_argument("--min-query-aligned-fraction", required=True, type=float)
    parser.add_argument("--min-identity", required=True, type=float)
    parser.add_argument("--min-mapq", type=int, default=None)
    parser.add_argument("--max-read-length", type=int, default=None)
    return parser.parse_args()


def read_paf(path: Path) -> dict[str, list[dict[str, int | float | str]]]:
    records: dict[str, list[dict[str, int | float | str]]] = collections.defaultdict(list)
    with path.open() as handle:
        for line_number, line in enumerate(handle, 1):
            fields = line.rstrip().split("\t")
            if len(fields) < 12:
                raise ValueError(f"{path}:{line_number}: expected at least 12 PAF fields")
            query_length = int(fields[1])
            alignment_block_length = int(fields[10])
            if query_length <= 0 or alignment_block_length <= 0:
                continue
            query_start = int(fields[2])
            query_end = int(fields[3])
            records[fields[0]].append(
                {
                    "query_length": query_length,
                    "query_start": query_start,
                    "query_end": query_end,
                    "aligned_bases": query_end - query_start,
                    "aligned_fraction": (query_end - query_start) / query_length,
                    "identity": int(fields[9]) / alignment_block_length,
                    "target": fields[5],
                    "mapq": int(fields[11]),
                }
            )
    return records


def select_reads(
    records: dict[str, list[dict[str, int | float | str]]],
    *,
    min_aligned_bases: int,
    min_query_aligned_fraction: float,
    min_identity: float,
    min_mapq: int | None,
) -> dict[str, dict[str, int | float | str]]:
    selected: dict[str, dict[str, int | float | str]] = {}
    for read_id, read_records in records.items():
        passing = [
            record
            for record in read_records
            if record["aligned_bases"] >= min_aligned_bases
            and record["aligned_fraction"] >= min_query_aligned_fraction
            and record["identity"] >= min_identity
            and (min_mapq is None or record["mapq"] >= min_mapq)
        ]
        if passing:
            selected[read_id] = max(
                passing,
                key=lambda record: (
                    record["aligned_fraction"],
                    record["identity"],
                    record["aligned_bases"],
                ),
            )
    return selected


def write_selected_fastq(reads: Path, output: Path, selected_ids: set[str], max_read_length: int | None) -> int:
    opener = gzip.open if reads.suffix == ".gz" else open
    output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with opener(reads, "rt") as source, gzip.open(output, "wt") as destination:
        while True:
            header = source.readline()
            if not header:
                break
            sequence = source.readline()
            separator = source.readline()
            quality = source.readline()
            if not sequence or not separator or not quality:
                raise ValueError(f"{reads}: truncated FASTQ record after {header.rstrip()}")
            read_id = header[1:].split()[0]
            if read_id in selected_ids and (max_read_length is None or len(sequence.strip()) <= max_read_length):
                destination.write(header + sequence + separator + quality)
                written += 1
    return written


def main() -> None:
    args = parse_args()
    if args.min_aligned_bases <= 0:
        raise ValueError("--min-aligned-bases must be positive")
    for name, value in (
        ("--min-query-aligned-fraction", args.min_query_aligned_fraction),
        ("--min-identity", args.min_identity),
    ):
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be between 0 and 1")

    records = read_paf(args.paf)
    evidence = select_reads(
        records,
        min_aligned_bases=args.min_aligned_bases,
        min_query_aligned_fraction=args.min_query_aligned_fraction,
        min_identity=args.min_identity,
        min_mapq=args.min_mapq,
    )
    selected_ids = set(evidence)
    written = write_selected_fastq(args.reads, args.output, selected_ids, args.max_read_length)
    effective_ids = {read_id for read_id, record in evidence.items() if args.max_read_length is None or int(record["query_length"]) <= args.max_read_length}
    if written != len(effective_ids):
        raise ValueError(
            f"selected {len(selected_ids)} PAF read IDs but wrote {written} FASTQ records; "
            "the PAF and FASTQ inputs do not describe the same read set"
        )

    parameters = {
        "min_aligned_bases": args.min_aligned_bases,
        "min_query_aligned_fraction": args.min_query_aligned_fraction,
        "min_identity": args.min_identity,
        "mapq_filter": args.min_mapq,
        "max_read_length": args.max_read_length,
    }
    manifest = {
        "schema_version": "animal-lr-recruitment-v0.2.1",
        "selection_semantics": "one_coherent_alignment_must_satisfy_all_thresholds",
        "parameters": parameters,
        "input_reads": str(args.reads),
        "paf": str(args.paf),
        "selected_read_ids": sorted(effective_ids),
        "selected_read_count": len(effective_ids),
        "candidate_read_count": len(records),
        "selection_evidence": evidence,
        "output": str(args.output),
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                "parameters": parameters,
                "selected_read_count": len(effective_ids),
                "candidate_read_count": len(records),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
