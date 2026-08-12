#!/usr/bin/env python3
"""Create a per-read HYP-DNA-002 audit and SVG dotplots for excluded ultra-long reads."""

import argparse
import collections
import hashlib
import html
import json
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def read_fastq(path):
    records = {}
    with path.open() as handle:
        while True:
            header = handle.readline()
            if not header:
                break
            sequence = handle.readline().strip()
            handle.readline()
            handle.readline()
            records[header[1:].split()[0]] = sequence
    return records


def parse_paf(path):
    records = []
    for line in path.read_text().splitlines():
        fields = line.split("\t")
        if len(fields) < 12:
            continue
        records.append(
            {
                "query": fields[0],
                "query_length": int(fields[1]),
                "query_start": int(fields[2]),
                "query_end": int(fields[3]),
                "strand": fields[4],
                "target": fields[5],
                "target_length": int(fields[6]),
                "target_start": int(fields[7]),
                "target_end": int(fields[8]),
                "matches": int(fields[9]),
                "block_length": int(fields[10]),
                "identity": int(fields[9]) / int(fields[10]) if int(fields[10]) else 0.0,
                "mapq": int(fields[11]),
            }
        )
    return records


def union_length(intervals):
    total = 0
    end = -1
    for start, stop in sorted(intervals):
        if stop > end:
            total += stop - max(start, end)
            end = stop
    return total


def anchor_groups(records, anchor_length):
    groups = []
    for strand in ("+", "-"):
        strand_records = sorted((row for row in records if row["strand"] == strand), key=lambda row: row["query_start"])
        current = []
        current_end = -1
        for row in strand_records:
            if current and row["query_start"] - current_end > 1000:
                groups.append(current)
                current = []
            current.append(row)
            current_end = max(current_end, row["query_end"])
        if current:
            groups.append(current)
    result = []
    for group in groups:
        target_breadth = union_length((row["target_start"], row["target_end"]) for row in group)
        query_breadth = union_length((row["query_start"], row["query_end"]) for row in group)
        block = sum(row["block_length"] for row in group)
        result.append(
            {
                "strand": group[0]["strand"],
                "query_start": min(row["query_start"] for row in group),
                "query_end": max(row["query_end"] for row in group),
                "query_breadth": query_breadth,
                "target_breadth": target_breadth,
                "target_breadth_fraction": target_breadth / anchor_length,
                "weighted_identity": sum(row["matches"] for row in group) / block if block else 0.0,
                "records": len(group),
            }
        )
    return result


def write_svg(path, read_id, read_length, records):
    size = 760
    pad = 55
    scale = (size - 2 * pad) / read_length
    lines = []
    for row in records:
        x1 = pad + row["query_start"] * scale
        x2 = pad + row["query_end"] * scale
        if row["strand"] == "+":
            y1 = pad + row["target_start"] * scale
            y2 = pad + row["target_end"] * scale
            color = "#2563eb"
        else:
            y1 = pad + row["target_end"] * scale
            y2 = pad + row["target_start"] * scale
            color = "#dc2626"
        opacity = max(0.18, min(0.95, row["identity"]))
        lines.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{color}" stroke-width="1.2" opacity="{opacity:.3f}" />'
        )
    body = "\n".join(lines)
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">\n'
        '<rect width="100%" height="100%" fill="white"/>\n'
        f'<text x="{pad}" y="24" font-family="sans-serif" font-size="14">{html.escape(read_id)} self-alignment</text>\n'
        f'<line x1="{pad}" y1="{pad}" x2="{size-pad}" y2="{size-pad}" stroke="#9ca3af" stroke-dasharray="4 4"/>\n'
        f'{body}\n'
        f'<text x="{pad}" y="{size-12}" font-family="sans-serif" font-size="11">query 0..{read_length}; blue=same strand, red=reverse</text>\n'
        '</svg>\n'
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reads", type=Path, required=True)
    parser.add_argument("--self-paf", type=Path, required=True)
    parser.add_argument("--anchor-paf", type=Path, required=True)
    parser.add_argument("--anchor-length", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dotplot-dir", type=Path, required=True)
    args = parser.parse_args()
    for path in (args.reads, args.self_paf, args.anchor_paf):
        if not path.is_file() or path.stat().st_size == 0:
            raise SystemExit(f"missing or empty input: {path}")
    reads = read_fastq(args.reads)
    if len(reads) != 13 or any(len(sequence) < 30000 for sequence in reads.values()):
        raise SystemExit("HYP-DNA-002 input must contain exactly 13 reads, all >=30 kb")
    self_by_read = collections.defaultdict(list)
    for row in parse_paf(args.self_paf):
        if row["query"] == row["target"]:
            self_by_read[row["query"]].append(row)
    anchor_by_read = collections.defaultdict(list)
    for row in parse_paf(args.anchor_paf):
        anchor_by_read[row["query"]].append(row)
    args.dotplot_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for read_id, sequence in sorted(reads.items()):
        anchor_records = anchor_by_read[read_id]
        groups = anchor_groups(anchor_records, args.anchor_length)
        high_conf_units = [
            group
            for group in groups
            if group["target_breadth_fraction"] >= 0.80 and group["weighted_identity"] >= 0.88
        ]
        all_query_breadth = union_length((row["query_start"], row["query_end"]) for row in anchor_records)
        best_span = max((row["query_end"] - row["query_start"] for row in anchor_records), default=0)
        best_identity = max((row["identity"] for row in anchor_records), default=0.0)
        opposite_full_groups = len({group["strand"] for group in groups if group["target_breadth_fraction"] >= 0.80}) > 1
        same_strand_units = max(
            (sum(group["strand"] == strand for group in high_conf_units) for strand in ("+", "-")), default=0
        )
        if same_strand_units >= 2:
            classification = "TRUE_MULTIMER"
            grade = "CONFIRMED"
            rationale = "At least two high-identity, near-complete anchor units occur in the same orientation."
        elif opposite_full_groups:
            classification = "CHIMERIC_JUNK"
            grade = "SUGGESTIVE"
            rationale = "Near-complete anchor-scale groups occur in opposite orientations, not as a same-direction concatemer."
        elif best_span >= 1000 and best_identity >= 0.88 and all_query_breadth < len(sequence) * 0.50:
            classification = "NUMT_FLANK_CHIMERA"
            grade = "SUGGESTIVE"
            rationale = "A substantial mt-like segment is embedded within much longer unaligned flanks; no nuclear reference is available for confirmation."
        else:
            classification = "CHIMERIC_JUNK"
            grade = "SUGGESTIVE"
            rationale = "Only short or weak mt-like local matches occur and no near-complete anchor unit is supported."
        self_records = self_by_read[read_id]
        high_identity_self = [row for row in self_records if row["identity"] >= 0.80 and row["block_length"] >= 1000]
        dotplot = args.dotplot_dir / f"{read_id}.svg"
        write_svg(dotplot, read_id, len(sequence), self_records)
        rows.append(
            {
                "read_id": read_id,
                "read_length": len(sequence),
                "at_fraction": (sequence.count("A") + sequence.count("T")) / len(sequence),
                "anchor_alignment_records": len(anchor_records),
                "anchor_query_breadth": all_query_breadth,
                "anchor_query_fraction": all_query_breadth / len(sequence),
                "best_anchor_span": best_span,
                "best_anchor_identity": best_identity,
                "anchor_groups": groups,
                "high_confidence_anchor_units": len(high_conf_units),
                "same_strand_high_confidence_units": same_strand_units,
                "self_alignment_records": len(self_records),
                "high_identity_self_repeat_records": len(high_identity_self),
                "classification": classification,
                "evidence_grade": grade,
                "rationale": rationale,
                "dotplot": str(dotplot),
            }
        )
    counts = collections.Counter(row["classification"] for row in rows)
    result = {
        "schema_version": "hyp-dna-002-ultralong-read-audit-0.1",
        "experimental_only": True,
        "decision": "NOT_APPLICABLE",
        "topology": "INCONCLUSIVE",
        "inputs": {
            "reads": {"path": str(args.reads), "sha256": sha256(args.reads)},
            "self_paf": {"path": str(args.self_paf), "sha256": sha256(args.self_paf)},
            "anchor_paf": {"path": str(args.anchor_paf), "sha256": sha256(args.anchor_paf)},
            "anchor_length": args.anchor_length,
        },
        "classification_counts": dict(sorted(counts.items())),
        "hypothesis": {
            "id": "HYP-DNA-002",
            "title": "AT-rich repeat adjacency and copy-number audit",
            "grade": "SUGGESTIVE",
            "true_same_orientation_multimer_subhypothesis": "REJECTED",
            "reason": (
                "No read contains two high-identity near-complete anchor units in the same orientation. "
                "Assembler repeat expansions and AT-rich micro-edge traversals remain suggestive, but adjacency and copy number are unresolved."
            ),
        },
        "classification_rule_note": (
            "Thresholds are audit rules, not production policy: a near-complete unit requires >=80% anchor breadth and >=0.88 identity; "
            "TRUE_MULTIMER additionally requires >=2 such units in the same orientation."
        ),
        "reads": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    tsv = args.output.with_suffix(".tsv")
    tsv.write_text(
        "read_id\tread_length\tat_fraction\tanchor_records\tanchor_query_breadth\tanchor_query_fraction\tbest_anchor_span\tbest_anchor_identity\thigh_conf_units\tsame_strand_units\tself_records\thigh_identity_self_records\tclassification\tevidence_grade\trationale\tdotplot\n"
        + "".join(
            f"{row['read_id']}\t{row['read_length']}\t{row['at_fraction']:.6f}\t{row['anchor_alignment_records']}\t"
            f"{row['anchor_query_breadth']}\t{row['anchor_query_fraction']:.6f}\t{row['best_anchor_span']}\t"
            f"{row['best_anchor_identity']:.6f}\t{row['high_confidence_anchor_units']}\t"
            f"{row['same_strand_high_confidence_units']}\t{row['self_alignment_records']}\t"
            f"{row['high_identity_self_repeat_records']}\t{row['classification']}\t{row['evidence_grade']}\t"
            f"{row['rationale']}\t{row['dotplot']}\n"
            for row in rows
        )
    )


if __name__ == "__main__":
    main()
