#!/usr/bin/env python3
"""Summarize comparator assemblies against a frozen anchor without topology promotion."""

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fasta_lengths(path):
    lengths = []
    sequence = []
    for line in path.read_text().splitlines():
        if line.startswith(">"):
            if sequence:
                lengths.append(sum(map(len, sequence)))
            sequence = []
        else:
            sequence.append(line.strip())
    if sequence:
        lengths.append(sum(map(len, sequence)))
    return lengths


def union_length(intervals):
    total = 0
    end = -1
    for start, stop in sorted(intervals):
        if stop > end:
            total += stop - max(start, end)
            end = stop
    return total


def paf_summary(path):
    records = []
    for line in path.read_text().splitlines():
        fields = line.split("\t")
        if len(fields) < 12:
            continue
        tags = {tag[:2]: tag[5:] for tag in fields[12:] if len(tag) > 5 and tag[2:5] in {":i:", ":f:", ":A:"}}
        records.append(
            {
                "query": fields[0],
                "query_length": int(fields[1]),
                "query_start": int(fields[2]),
                "query_end": int(fields[3]),
                "target": fields[5],
                "target_length": int(fields[6]),
                "target_start": int(fields[7]),
                "target_end": int(fields[8]),
                "matches": int(fields[9]),
                "block_length": int(fields[10]),
                "mapq": int(fields[11]),
                "gap_compressed_divergence": float(tags["de"]) if "de" in tags else None,
            }
        )
    target_length = records[0]["target_length"] if records else 0
    block_total = sum(row["block_length"] for row in records)
    weighted_de_numerator = sum(
        (row["gap_compressed_divergence"] or 0.0) * (row["target_end"] - row["target_start"])
        for row in records
    )
    target_span_total = sum(row["target_end"] - row["target_start"] for row in records)
    return {
        "alignment_records": len(records),
        "target_length": target_length,
        "target_breadth_bases": union_length((row["target_start"], row["target_end"]) for row in records),
        "target_breadth_fraction": (
            union_length((row["target_start"], row["target_end"]) for row in records) / target_length
            if target_length
            else None
        ),
        "full_alignment_identity": sum(row["matches"] for row in records) / block_total if block_total else None,
        "gap_compressed_core_identity": (
            1.0 - weighted_de_numerator / target_span_total if target_span_total else None
        ),
        "query_inserted_bases_vs_target": sum(
            max(0, (row["query_end"] - row["query_start"]) - (row["target_end"] - row["target_start"]))
            for row in records
        ),
        "records": records,
    }


def circular_self_link(gfa):
    for line in gfa.read_text().splitlines():
        fields = line.split("\t")
        if len(fields) >= 6 and fields[0] == "L" and fields[1] == fields[3]:
            return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor", type=Path, required=True)
    parser.add_argument("--name", action="append", required=True)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--assembly", type=Path, action="append", required=True)
    parser.add_argument("--gfa", type=Path, action="append", required=True)
    parser.add_argument("--anchor-paf", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sizes = {len(args.name), len(args.input), len(args.assembly), len(args.gfa), len(args.anchor_paf)}
    if sizes != {len(args.name)}:
        raise SystemExit("name/input/assembly/gfa/anchor-paf counts must match")
    required = [args.anchor, *args.input, *args.assembly, *args.gfa, *args.anchor_paf]
    missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise SystemExit("missing or empty input: " + ", ".join(missing))
    rows = []
    for name, reads, assembly, gfa, paf in zip(args.name, args.input, args.assembly, args.gfa, args.anchor_paf):
        lengths = fasta_lengths(assembly)
        rows.append(
            {
                "name": name,
                "input": {"path": str(reads), "bytes": reads.stat().st_size, "sha256": sha256(reads)},
                "assembly": {
                    "path": str(assembly),
                    "sha256": sha256(assembly),
                    "contig_count": len(lengths),
                    "total_bases": sum(lengths),
                    "max_bases": max(lengths, default=0),
                    "gfa_self_loop": circular_self_link(gfa),
                },
                "anchor_alignment": paf_summary(paf),
            }
        )
    result = {
        "schema_version": "animal-lr-raven-comparator-0.1",
        "experimental_only": True,
        "decision": "NOT_APPLICABLE",
        "topology": "INCONCLUSIVE",
        "tool": {
            "name": "raven-assembler",
            "version": "1.8.3",
            "executable": "/home/iris-hp/miniconda3/envs/raven-assembler/bin/raven",
            "command_parameters": ["--disable-checkpoints", "-t", "4"],
        },
        "anchor": {"path": str(args.anchor), "bytes": args.anchor.stat().st_size, "sha256": sha256(args.anchor)},
        "runs": rows,
        "interpretation": (
            "Raven is an independent OLC-family comparator. GFA self-loops and core agreement are experimental "
            "structural evidence only and cannot promote animal topology without the full project evidence gate."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    tsv = args.output.with_suffix(".tsv")
    tsv.write_text(
        "name\tcontigs\ttotal_bases\tmax_bases\tgfa_self_loop\tanchor_breadth\tfull_alignment_identity\tgap_compressed_core_identity\tinserted_bases_vs_anchor\n"
        + "".join(
            f"{row['name']}\t{row['assembly']['contig_count']}\t{row['assembly']['total_bases']}\t{row['assembly']['max_bases']}\t"
            f"{str(row['assembly']['gfa_self_loop']).lower()}\t{row['anchor_alignment']['target_breadth_fraction']:.6f}\t"
            f"{row['anchor_alignment']['full_alignment_identity']:.6f}\t{row['anchor_alignment']['gap_compressed_core_identity']:.6f}\t"
            f"{row['anchor_alignment']['query_inserted_bases_vs_target']}\n"
            for row in rows
        )
    )


if __name__ == "__main__":
    main()
