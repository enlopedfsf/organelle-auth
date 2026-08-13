#!/usr/bin/env python3
"""Evidence helpers for the isolated M4 hybrid-reference comparison.

The commands in this file never make an authentication decision.  They only
translate frozen B0-coordinate masks, turn normalized VCF records into edit
ledgers, and calculate the pre-registered held-out metrics.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Iterator


CS_TOKEN = re.compile(r"(:[0-9]+|=[A-Za-z]+|\*[A-Za-z][A-Za-z]|[+-][A-Za-z]+|~[A-Za-z]{2}[0-9]+[A-Za-z]{2})")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def open_text(path: Path):
    return gzip.open(path, "rt") if path.suffix == ".gz" else path.open()


def read_fasta(path: Path) -> dict[str, str]:
    records: dict[str, list[str]] = {}
    name: str | None = None
    with path.open() as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                name = line[1:].split()[0]
                if not name or name in records:
                    raise ValueError(f"invalid or duplicate FASTA name in {path}: {name!r}")
                records[name] = []
            elif name is None:
                raise ValueError(f"sequence before FASTA header in {path}")
            else:
                records[name].append(line.upper())
    result = {key: "".join(parts) for key, parts in records.items()}
    if not result or any(not sequence for sequence in result.values()):
        raise ValueError(f"FASTA is empty or contains an empty record: {path}")
    return result


def read_bed(path: Path) -> dict[str, list[tuple[int, int, str]]]:
    intervals: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    with path.open() as handle:
        for line_no, raw in enumerate(handle, 1):
            if not raw.strip() or raw.startswith("#"):
                continue
            fields = raw.rstrip("\n").split("\t")
            if len(fields) < 3:
                raise ValueError(f"{path}:{line_no}: BED needs at least 3 columns")
            start, end = int(fields[1]), int(fields[2])
            if start < 0 or end <= start:
                raise ValueError(f"{path}:{line_no}: invalid interval {start}-{end}")
            intervals[fields[0]].append((start, end, fields[3] if len(fields) > 3 else "core"))
    if not intervals:
        raise ValueError(f"BED contains no intervals: {path}")
    return intervals


def merge_intervals(rows: Iterable[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    merged: list[list[object]] = []
    for start, end, label in sorted(rows, key=lambda row: (row[2], row[0], row[1])):
        if merged and merged[-1][2] == label and start <= int(merged[-1][1]):
            merged[-1][1] = max(int(merged[-1][1]), end)
        else:
            merged.append([start, end, label])
    return [(int(start), int(end), str(label)) for start, end, label in merged]


def paf_records(path: Path) -> Iterator[dict[str, object]]:
    with path.open() as handle:
        for line_no, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            fields = raw.rstrip("\n").split("\t")
            if len(fields) < 12:
                raise ValueError(f"{path}:{line_no}: truncated PAF record")
            tags = {field[:2]: field[5:] for field in fields[12:] if len(field) >= 6 and field[2:5] == ":Z:"}
            yield {
                "query": fields[0], "query_length": int(fields[1]), "query_start": int(fields[2]),
                "query_end": int(fields[3]), "strand": fields[4], "target": fields[5],
                "target_length": int(fields[6]), "target_start": int(fields[7]),
                "target_end": int(fields[8]), "mapq": int(fields[11]), "tags": tags,
            }


def cs_steps(cs: str) -> Iterator[tuple[str, str]]:
    tokens = CS_TOKEN.findall(cs)
    if "".join(tokens) != cs:
        raise ValueError(f"unsupported cs token sequence: {cs[:120]}")
    for token in tokens:
        yield token[0], token[1:]


def overlap_label(intervals: list[tuple[int, int, str]], pos0: int) -> str:
    labels = [label for start, end, label in intervals if start <= pos0 < end]
    return ",".join(sorted(set(labels))) if labels else "NOT_EVALUABLE"


def lift_mask(paf: Path, target_bed: Path, query_fasta: Path) -> tuple[dict[str, list[tuple[int, int, str]]], dict]:
    source = read_bed(target_bed)
    query_sequences = read_fasta(query_fasta)
    lifted: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    alignments = 0
    for record in paf_records(paf):
        target = str(record["target"])
        if target not in source:
            continue
        if record["strand"] != "+":
            raise ValueError(f"mask liftover requires same-orientation alignment: {target}->{record['query']}")
        cs = dict(record["tags"]).get("cs")
        if not cs:
            raise ValueError("PAF mask liftover requires a cs:Z tag")
        alignments += 1
        tpos, qpos = int(record["target_start"]), int(record["query_start"])
        query = str(record["query"])
        if query not in query_sequences:
            raise ValueError(f"PAF query absent from candidate FASTA: {query}")
        for op, payload in cs_steps(cs):
            if op in (":", "="):
                length = int(payload) if op == ":" else len(payload)
                for start, end, label in source[target]:
                    left, right = max(start, tpos), min(end, tpos + length)
                    if left < right:
                        qleft = qpos + (left - tpos)
                        lifted[query].append((qleft, qleft + (right - left), label))
                tpos += length
                qpos += length
            elif op == "*":
                for start, end, label in source[target]:
                    if start <= tpos < end:
                        lifted[query].append((qpos, qpos + 1, label))
                tpos += 1
                qpos += 1
            elif op == "+":
                qpos += len(payload)
            elif op == "-":
                tpos += len(payload)
            elif op == "~":
                intron = int(payload[2:-2])
                tpos += intron
            else:
                raise ValueError(f"unsupported cs operator: {op}")
    if alignments == 0 or not lifted:
        raise ValueError("no mask intervals could be lifted")
    result = {name: merge_intervals(rows) for name, rows in lifted.items()}
    total = sum(end - start for rows in result.values() for start, end, _ in rows)
    metadata = {
        "schema_version": "m4-mask-liftover-v1", "status": "PASS",
        "source_bed": str(target_bed), "source_bed_sha256": sha256_file(target_bed),
        "paf": str(paf), "paf_sha256": sha256_file(paf),
        "query_fasta": str(query_fasta), "query_fasta_sha256": sha256_file(query_fasta),
        "same_orientation_required": True, "alignment_records_used": alignments,
        "lifted_bases": total,
        "topology_use": "PROHIBITED",
    }
    return result, metadata


def write_bed(intervals: dict[str, list[tuple[int, int, str]]], path: Path) -> None:
    with path.open("w") as handle:
        for contig in sorted(intervals):
            for start, end, label in intervals[contig]:
                handle.write(f"{contig}\t{start}\t{end}\t{label}\n")


def parse_info(text: str) -> dict[str, str]:
    return {piece.split("=", 1)[0]: piece.split("=", 1)[1] for piece in text.split(";") if "=" in piece}


def vcf_rows(path: Path) -> Iterator[dict[str, object]]:
    samples: list[str] = []
    with open_text(path) as handle:
        for raw in handle:
            if raw.startswith("##"):
                continue
            if raw.startswith("#CHROM"):
                samples = raw.rstrip("\n").split("\t")[9:]
                continue
            if raw.startswith("#") or not raw.strip():
                continue
            fields = raw.rstrip("\n").split("\t")
            fmt = fields[8].split(":") if len(fields) > 8 else []
            sample_values = fields[9].split(":") if len(fields) > 9 else []
            sample = dict(zip(fmt, sample_values))
            alts = fields[4].split(",")
            yield {
                "chrom": fields[0], "pos1": int(fields[1]), "id": fields[2],
                "ref": fields[3], "alts": alts, "qual": None if fields[5] == "." else float(fields[5]),
                "filter": fields[6], "info": parse_info(fields[7]), "sample": sample,
                "sample_names": samples,
            }


def numeric_list(value: str | None) -> list[int]:
    if not value or value == ".":
        return []
    return [int(float(item)) if item not in (".", "") else 0 for item in value.split(",")]


def homopolymer_context(sequence: str, pos0: int, ref: str, alt: str, minimum_run: int) -> tuple[bool, int]:
    bases = set((ref + alt).upper()) - {"-", "."}
    max_run = 0
    for base in bases:
        left = max(0, pos0 - 1)
        right = min(len(sequence), pos0 + max(len(ref), 1) + 1)
        for pivot in range(left, right):
            if sequence[pivot] != base:
                continue
            a = pivot
            b = pivot + 1
            while a > 0 and sequence[a - 1] == base:
                a -= 1
            while b < len(sequence) and sequence[b] == base:
                b += 1
            max_run = max(max_run, b - a)
    return max_run >= minimum_run and len(ref) != len(alt), max_run


def load_depth(path: Path) -> dict[str, dict[int, int]]:
    depth: dict[str, dict[int, int]] = defaultdict(dict)
    with path.open() as handle:
        for line_no, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            fields = raw.rstrip("\n").split("\t")
            if len(fields) < 3:
                raise ValueError(f"{path}:{line_no}: truncated depth row")
            depth[fields[0]][int(fields[1]) - 1] = int(fields[2])
    return depth


LEDGER_FIELDS = [
    "taxon", "arm", "route", "contig", "position_1based", "ref", "alt", "variant_type",
    "region", "evaluation_status", "depth", "ref_count", "alt_count", "alt_fraction",
    "qual", "mapping_ambiguity", "filter_reason", "support_source",
]


def evaluate_vcf(
    candidate: Path, vcf: Path, depth_path: Path, bed_path: Path, policy_path: Path,
    taxon: str, arm: str, route: str,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    sequences = read_fasta(candidate)
    bed = read_bed(bed_path)
    depth = load_depth(depth_path)
    policy = json.loads(policy_path.read_text())
    min_depth = int(policy["alignment_filters"]["minimum_callable_depth"])
    min_run = int(policy["homopolymer"]["minimum_candidate_run_length"])
    total_core = sum(end - start for rows in bed.values() for start, end, _ in rows)
    callable_core = sum(
        1 for contig, rows in bed.items() for start, end, _ in rows
        for pos0 in range(start, end) if depth.get(contig, {}).get(pos0, 0) >= min_depth
    )
    ledger: list[dict[str, object]] = []
    by_region: dict[str, int] = defaultdict(int)
    snvs = indels = homopolymers = 0
    residual_span = 0
    for record in vcf_rows(vcf):
        chrom, pos1, ref = str(record["chrom"]), int(record["pos1"]), str(record["ref"])
        sample = dict(record["sample"])
        dp_values = numeric_list(sample.get("DP"))
        ad_values = numeric_list(sample.get("AD"))
        record_depth = dp_values[0] if dp_values else sum(ad_values)
        gt = sample.get("GT", "1").replace("|", "/").split("/")[0]
        try:
            alt_index = max(1, int(gt))
        except ValueError:
            alt_index = 1
        alts = list(record["alts"])
        alt = alts[min(alt_index - 1, len(alts) - 1)]
        ref_count = ad_values[0] if ad_values else None
        alt_count = ad_values[alt_index] if len(ad_values) > alt_index else None
        alt_fraction = (alt_count / record_depth) if alt_count is not None and record_depth else None
        region = overlap_label(bed.get(chrom, []), pos1 - 1)
        evaluable = region != "NOT_EVALUABLE"
        variant_type = "SNV" if len(ref) == len(alt) == 1 else "INDEL" if len(ref) != len(alt) else "MNV"
        hp, run_length = homopolymer_context(sequences[chrom], pos1 - 1, ref, alt, min_run)
        if evaluable:
            residual_span += max(len(ref), len(alt))
            by_region[region] += 1
            snvs += variant_type == "SNV"
            indels += variant_type == "INDEL"
            homopolymers += hp
        ledger.append({
            "taxon": taxon, "arm": arm, "route": route, "contig": chrom,
            "position_1based": pos1, "ref": ref, "alt": alt, "variant_type": variant_type,
            "region": region, "evaluation_status": "EVALUABLE" if evaluable else "NOT_EVALUABLE",
            "depth": record_depth, "ref_count": ref_count, "alt_count": alt_count,
            "alt_fraction": alt_fraction, "qual": record["qual"],
            "mapping_ambiguity": "PRIMARY_MAPQ20_FILTERED",
            "filter_reason": "PASS_PREREGISTERED_HELDOUT_FILTER",
            "support_source": f"heldout:{Path(vcf).name};homopolymer_run={run_length}",
        })
    residuals = sum(row["evaluation_status"] == "EVALUABLE" for row in ledger)
    concordance = None if callable_core == 0 else max(0.0, 1.0 - residual_span / callable_core)
    metrics: dict[str, object] = {
        "schema_version": "m4-heldout-metrics-v1", "taxon": taxon, "arm": arm,
        "status": "INCONCLUSIVE", "assembly_grade": "CANDIDATE", "decision": "NOT_APPLICABLE",
        "evidence_tier": "EXPERIMENTAL", "cycloneseq": "PENDING_REAL_DATA",
        "candidate_sha256": sha256_file(candidate), "core_bed_sha256": sha256_file(bed_path),
        "heldout_vcf_sha256": sha256_file(vcf), "core_bases": total_core,
        "callable_core_bases": callable_core, "residual_unsupported_loci": residuals,
        "residual_variant_span": residual_span, "heldout_core_concordance": concordance,
        "evaluable_homopolymer_discordances": homopolymers, "snvs": snvs, "indels": indels,
        "regional_residuals": dict(sorted(by_region.items())),
        "outside_core_residuals": sum(row["evaluation_status"] == "NOT_EVALUABLE" for row in ledger),
        "ranking_scope": "lifted frozen evaluable core", "topology_claim": "PROHIBITED",
    }
    return ledger, metrics


def write_ledger(rows: list[dict[str, object]], path: Path) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=LEDGER_FIELDS,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def command_lift(args: argparse.Namespace) -> None:
    intervals, metadata = lift_mask(args.paf, args.source_bed, args.query_fasta)
    write_bed(intervals, args.out_bed)
    metadata["output_bed_sha256"] = sha256_file(args.out_bed)
    args.out_json.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")


def command_evaluate(args: argparse.Namespace) -> None:
    ledger, metrics = evaluate_vcf(
        args.candidate, args.vcf, args.depth, args.core_bed, args.policy,
        args.taxon, args.arm, args.route,
    )
    write_ledger(ledger, args.out_ledger)
    metrics["ledger_sha256"] = sha256_file(args.out_ledger)
    args.out_metrics.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    lift = sub.add_parser("lift-mask")
    lift.add_argument("--paf", type=Path, required=True)
    lift.add_argument("--source-bed", type=Path, required=True)
    lift.add_argument("--query-fasta", type=Path, required=True)
    lift.add_argument("--out-bed", type=Path, required=True)
    lift.add_argument("--out-json", type=Path, required=True)
    lift.set_defaults(func=command_lift)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--candidate", type=Path, required=True)
    evaluate.add_argument("--vcf", type=Path, required=True)
    evaluate.add_argument("--depth", type=Path, required=True)
    evaluate.add_argument("--core-bed", type=Path, required=True)
    evaluate.add_argument("--policy", type=Path, required=True)
    evaluate.add_argument("--taxon", choices=("plant", "animal"), required=True)
    evaluate.add_argument("--arm", required=True)
    evaluate.add_argument("--route", required=True)
    evaluate.add_argument("--out-ledger", type=Path, required=True)
    evaluate.add_argument("--out-metrics", type=Path, required=True)
    evaluate.set_defaults(func=command_evaluate)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
