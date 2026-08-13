#!/usr/bin/env python3
"""Build the frozen M4 animal evaluable-core BED from preregistered evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def provenance_path(path: Path) -> str:
    """Use a repository-relative path when possible, otherwise a fixed absolute path."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(resolved)


def read_assembly_info(path: Path) -> dict[str, dict]:
    rows = {}
    with path.open() as handle:
        header = handle.readline().lstrip("#").split()
        for line in handle:
            fields = line.split()
            row = dict(zip(header, fields))
            rows[row["seq_name"]] = row
    return rows


def read_unique_paf(path: Path, allowed: set[str]) -> dict[str, list[tuple[int, int, str]]]:
    raw: dict[str, list[tuple[int, int, int, int, str]]] = defaultdict(list)
    with path.open() as handle:
        for line in handle:
            fields = line.rstrip().split("\t")
            if len(fields) < 12:
                continue
            query_start, query_end = int(fields[2]), int(fields[3])
            strand = fields[4]
            target = fields[5]
            target_start, target_end = int(fields[7]), int(fields[8])
            mapq = int(fields[11])
            if target in allowed and mapq == 60:
                raw[target].append((target_start, target_end, query_start, query_end, strand))

    retained: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    for target, alignments in raw.items():
        strands = {item[4] for item in alignments}
        if len(strands) != 1:
            continue
        strand = next(iter(strands))
        boundaries = sorted({value for start, end, *_ in alignments for value in (start, end)})
        for start, end in zip(boundaries, boundaries[1:]):
            coverage = sum(
                alignment_start <= start and alignment_end >= end
                for alignment_start, alignment_end, *_ in alignments
            )
            if coverage == 1:
                retained[target].append((start, end, strand))
    return retained


def intersect(left: list[tuple[int, int]], right: list[tuple[int, int]]) -> list[tuple[int, int]]:
    result = []
    for a_start, a_end in left:
        for b_start, b_end in right:
            start, end = max(a_start, b_start), min(a_end, b_end)
            if start < end:
                result.append((start, end))
    return result


def callable_intervals(path: Path, minimum_depth: int) -> dict[str, list[tuple[int, int]]]:
    positions: dict[str, list[int]] = defaultdict(list)
    with path.open() as handle:
        for line in handle:
            contig, position, depth = line.split()[:3]
            if int(depth) >= minimum_depth:
                positions[contig].append(int(position) - 1)
    intervals = defaultdict(list)
    for contig, values in positions.items():
        if not values:
            continue
        start = previous = values[0]
        for value in values[1:]:
            if value != previous + 1:
                intervals[contig].append((start, previous + 1))
                start = value
            previous = value
        intervals[contig].append((start, previous + 1))
    return intervals


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembly-info", required=True, type=Path)
    parser.add_argument("--raven-paf", required=True, type=Path)
    parser.add_argument("--anchor-paf", required=True, type=Path)
    parser.add_argument("--depth", required=True, type=Path)
    parser.add_argument("--bed", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--boundary-trim", default=500, type=int)
    parser.add_argument("--minimum-depth", default=1, type=int)
    args = parser.parse_args()

    info = read_assembly_info(args.assembly_info)
    eligible = {
        name
        for name, row in info.items()
        if row["repeat"] == "N"
        and row["circ."] == "N"
        and row["graph_path"].count(",") == 2
    }
    raven = read_unique_paf(args.raven_paf, eligible)
    anchor = read_unique_paf(args.anchor_paf, eligible)
    depth = callable_intervals(args.depth, args.minimum_depth)

    final: dict[str, list[tuple[int, int]]] = defaultdict(list)
    pretrim: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for contig in sorted(eligible):
        raven_intervals = [(start, end) for start, end, _ in raven.get(contig, [])]
        anchor_intervals = [(start, end) for start, end, _ in anchor.get(contig, [])]
        projected = intersect(raven_intervals, anchor_intervals)
        projected = intersect(projected, depth.get(contig, []))
        for start, end in merge(projected):
            pretrim[contig].append((start, end))
            trimmed_start = start + args.boundary_trim
            trimmed_end = end - args.boundary_trim
            if trimmed_start < trimmed_end:
                final[contig].append((trimmed_start, trimmed_end))

    if not final:
        raise SystemExit("animal core mask is empty")
    args.bed.parent.mkdir(parents=True, exist_ok=True)
    with args.bed.open("w") as handle:
        for contig in sorted(final):
            for start, end in final[contig]:
                handle.write(f"{contig}\t{start}\t{end}\n")

    assembly_attributes = {
        name: {
            "length": int(row["length"]),
            "coverage": int(row["cov."]),
            "circular": row["circ."] == "Y",
            "repeat": row["repeat"] == "Y",
            "multiplicity": int(row["mult."]),
            "graph_path": row["graph_path"],
        }
        for name, row in sorted(info.items())
    }
    metadata = {
        "schema_version": "m4-animal-core-mask-v2",
        "status": "FROZEN_CANDIDATE_PENDING_REVIEW",
        "coordinate_frame": "animal Flye B0, 0-based half-open",
        "owner": "validation/evidence owner",
        "eligible_nonrepeat_single_edge_contigs": sorted(eligible),
        "excluded_repeat_or_ambiguous_contigs": sorted(set(info) - eligible),
        "assembly_attributes": assembly_attributes,
        "pretrim_intervals": pretrim,
        "final_intervals": final,
        "boundary_trim_bp": args.boundary_trim,
        "minimum_training_depth": args.minimum_depth,
        "rules": {
            "assembler_projection": "MAPQ 60, one orientation per B0 contig; retain only atomic target intervals covered by exactly one local alignment",
            "anchor_projection": "MAPQ 60, one orientation per B0 contig; retain only atomic target intervals covered by exactly one local alignment",
            "topology_use": "PROHIBITED: retained local blocks support sequence-core evaluation only; their global query order or adjacency is not interpreted",
            "callability": "training reads only; primary mapped MAPQ>=20, baseQ>=20, depth>=1",
            "repeat_exclusion": "Flye repeat=Y or non-single-edge contigs excluded",
            "junction_exclusion": "500 bp removed from both ends of every continuous projected block",
            "heldout_use": "PROHIBITED",
        },
        "inputs": {
            name: {"path": provenance_path(path), "sha256": sha256_file(path)}
            for name, path in {
                "assembly_info": args.assembly_info,
                "raven_paf": args.raven_paf,
                "anchor_paf": args.anchor_paf,
                "training_depth": args.depth,
            }.items()
        },
        "bed": {"path": provenance_path(args.bed), "sha256": sha256_file(args.bed)},
        "script": {"path": provenance_path(Path(__file__)), "sha256": sha256_file(Path(__file__))},
    }
    args.metadata.write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
