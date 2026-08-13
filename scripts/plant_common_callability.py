#!/usr/bin/env python3
"""Freeze and compare M4 plant arms on a shared callable B0 denominator."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ARMS = ("B0", "R1", "P0", "C0", "R1P1", "R1C1")
CIGAR_TOKEN = re.compile(r"(\d+)([MIDNSHP=X])")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text())
    arms = config["inputs"]["arms"]
    if tuple(arms) != ARMS:
        raise ValueError(f"arms must be exactly {ARMS}, observed {tuple(arms)}")
    if config["comparison_row"] != "all_regions":
        raise ValueError("comparison_row must remain all_regions")
    return config


def iter_inputs(config: dict) -> Iterable[tuple[str, str, Path]]:
    yield "evaluation_policy", "ALL", Path(config["inputs"]["evaluation_policy"])
    yield "regions_bed", "ALL", Path(config["inputs"]["regions_bed"])
    for arm in ARMS:
        for role in ("projection_paf", "heldout_depth", "residual_ledger"):
            yield role, arm, Path(config["inputs"]["arms"][arm][role])


def freeze_manifest(config_path: Path, output: Path) -> None:
    config = load_config(config_path)
    rows = []
    for role, arm, path in iter_inputs(config):
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"required non-empty input missing: {path}")
        rows.append(
            {
                "role": role,
                "arm": arm,
                "path": str(path.resolve()),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    write_tsv(output, rows, ["role", "arm", "path", "size_bytes", "sha256"])


def verify_manifest(config: dict, manifest_path: Path) -> None:
    with manifest_path.open() as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    expected = {(role, arm, str(path.resolve())) for role, arm, path in iter_inputs(config)}
    observed = {(row["role"], row["arm"], row["path"]) for row in rows}
    if observed != expected:
        raise ValueError("input manifest paths/roles do not match preregistration")
    for row in rows:
        path = Path(row["path"])
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"frozen input missing or empty: {path}")
        if path.stat().st_size != int(row["size_bytes"]):
            raise ValueError(f"size mismatch: {path}")
        if sha256_file(path) != row["sha256"]:
            raise ValueError(f"SHA256 mismatch: {path}")


def parse_tags(fields: list[str]) -> dict[str, str]:
    tags = {}
    for field in fields:
        parts = field.split(":", 2)
        if len(parts) == 3:
            tags[parts[0]] = parts[2]
    return tags


def cigar_pairs(
    qname: str,
    qstart: int,
    qend: int,
    strand: str,
    tname: str,
    tstart: int,
    cigar: str,
) -> Iterable[tuple[tuple[str, int], tuple[str, int]]]:
    tokens = CIGAR_TOKEN.findall(cigar)
    if "".join(f"{length}{op}" for length, op in tokens) != cigar:
        raise ValueError(f"unsupported or malformed CIGAR: {cigar}")
    step = 1 if strand == "+" else -1
    qpos = qstart if strand == "+" else qend - 1
    tpos = tstart
    for length_text, op in tokens:
        length = int(length_text)
        if op in {"M", "=", "X"}:
            for _ in range(length):
                yield (qname, qpos), (tname, tpos)
                qpos += step
                tpos += 1
        elif op in {"I", "S"}:
            qpos += step * length
        elif op in {"D", "N"}:
            tpos += length
        elif op in {"H", "P"}:
            continue
        else:  # pragma: no cover - regex constrains this branch
            raise ValueError(f"unsupported CIGAR operation: {op}")
    expected_q = qend if strand == "+" else qstart - 1
    if qpos != expected_q:
        raise ValueError(
            f"CIGAR query consumption mismatch for {qname}: ended {qpos}, expected {expected_q}"
        )


def load_unique_projection(
    paf_path: Path, minimum_mapq: int
) -> tuple[dict[tuple[str, int], tuple[str, int]], set[tuple[str, int]], dict[str, int]]:
    query_targets: dict[tuple[str, int], set[tuple[str, int]]] = defaultdict(set)
    target_queries: dict[tuple[str, int], set[tuple[str, int]]] = defaultdict(set)
    stats = Counter()
    with paf_path.open() as handle:
        for raw in handle:
            if not raw.strip():
                continue
            fields = raw.rstrip().split("\t")
            if len(fields) < 12:
                raise ValueError(f"malformed PAF line in {paf_path}")
            tags = parse_tags(fields[12:])
            if tags.get("tp") != "P":
                stats["non_primary_alignments_skipped"] += 1
                continue
            if int(fields[11]) < minimum_mapq:
                stats["low_mapq_alignments_skipped"] += 1
                continue
            cigar = tags.get("cg")
            if not cigar:
                raise ValueError(f"primary PAF alignment lacks cg tag: {paf_path}")
            stats["primary_alignments_used"] += 1
            for query, target in cigar_pairs(
                fields[0],
                int(fields[2]),
                int(fields[3]),
                fields[4],
                fields[5],
                int(fields[7]),
                cigar,
            ):
                query_targets[query].add(target)
                target_queries[target].add(query)
    unique = {}
    for query, targets in query_targets.items():
        if len(targets) != 1:
            stats["ambiguous_query_bases"] += 1
            continue
        target = next(iter(targets))
        if len(target_queries[target]) != 1:
            stats["multiply_projected_b0_bases"] += 1
            continue
        unique[query] = target
    projected = set(unique.values())
    stats["unique_query_bases"] = len(unique)
    stats["unique_b0_bases"] = len(projected)
    return unique, projected, dict(sorted(stats.items()))


def load_depth(path: Path) -> dict[tuple[str, int], int]:
    depth = {}
    with path.open() as handle:
        for raw in handle:
            if not raw.strip():
                continue
            chrom, pos1, value, *_ = raw.rstrip().split("\t")
            key = (chrom, int(pos1) - 1)
            if key in depth:
                raise ValueError(f"duplicate depth position in {path}: {key}")
            depth[key] = int(value)
    return depth


def load_regions(path: Path) -> tuple[dict[str, list[tuple[int, int, str]]], list[str]]:
    intervals: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    labels = []
    with path.open() as handle:
        for raw in handle:
            if not raw.strip() or raw.startswith("#"):
                continue
            chrom, start, end, label, *_ = raw.rstrip().split("\t")
            intervals[chrom].append((int(start), int(end), label))
            if label not in labels:
                labels.append(label)
    if not labels:
        raise ValueError("region BED is empty")
    return intervals, labels


def region_at(intervals: dict[str, list[tuple[int, int, str]]], pos: tuple[str, int]) -> str:
    chrom, pos0 = pos
    labels = [label for start, end, label in intervals.get(chrom, []) if start <= pos0 < end]
    if len(set(labels)) > 1:
        raise ValueError(f"overlapping region labels at {chrom}:{pos0 + 1}: {labels}")
    return labels[0] if labels else "NOT_EVALUABLE"


def load_residuals(path: Path) -> list[dict[str, str]]:
    with path.open() as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    required = {"arm", "contig", "position_1based", "variant_type", "region", "evaluation_status"}
    if rows and not required.issubset(rows[0]):
        raise ValueError(f"residual ledger lacks required columns: {path}")
    return rows


def classify_r1p1(residual_counts: dict[str, int]) -> tuple[str, list[str]]:
    minimum = min(residual_counts.values())
    leaders = [arm for arm in ARMS if residual_counts[arm] == minimum]
    if leaders == ["R1P1"]:
        return "RETAINS_SOLE_LEAD", leaders
    if "R1P1" in leaders:
        return "TIED_LOWEST", leaders
    return "DOES_NOT_LEAD", leaders


def common_callable_intersection(callable_by_arm: dict[str, set[tuple[str, int]]]) -> set[tuple[str, int]]:
    if tuple(callable_by_arm) != ARMS:
        raise ValueError(f"callable sets must be ordered exactly as {ARMS}")
    common = set.intersection(*(callable_by_arm[arm] for arm in ARMS))
    if not common:
        raise ValueError("six-arm common-callable intersection is empty")
    return common


def denominator_metrics(projected_bases: int, callable_bases: int, residual_loci: int) -> dict[str, object]:
    return {
        "projected_bases": projected_bases,
        "callable_bases": callable_bases,
        "callable_fraction": f"{callable_bases / projected_bases:.6f}" if projected_bases else "",
        "residual_loci": residual_loci,
        "residual_rate_per_10kb": f"{residual_loci * 10000 / callable_bases:.6f}" if callable_bases else "",
    }


def merge_positions_by_region(
    positions: set[tuple[str, int]], intervals: dict[str, list[tuple[int, int, str]]]
) -> list[dict[str, object]]:
    ordered = sorted((chrom, pos, region_at(intervals, (chrom, pos))) for chrom, pos in positions)
    rows = []
    current = None
    for chrom, pos, label in ordered:
        if label == "NOT_EVALUABLE":
            continue
        if current and current[0] == chrom and current[2] == pos and current[3] == label:
            current[2] = pos + 1
        else:
            if current:
                rows.append(
                    {"contig": current[0], "start": current[1], "end": current[2], "region": current[3]}
                )
            current = [chrom, pos, pos + 1, label]
    if current:
        rows.append({"contig": current[0], "start": current[1], "end": current[2], "region": current[3]})
    return rows


def write_tsv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run_analysis(config_path: Path, manifest_path: Path, outdir: Path) -> None:
    started = datetime.now(timezone.utc)
    config = load_config(config_path)
    verify_manifest(config, manifest_path)
    policy = json.loads(Path(config["inputs"]["evaluation_policy"]).read_text())
    minimum_depth = int(policy["alignment_filters"]["minimum_callable_depth"])
    minimum_mapq = int(config["projection"]["minimum_mapq"])
    intervals, region_labels = load_regions(Path(config["inputs"]["regions_bed"]))

    arm_state = {}
    for arm in ARMS:
        inputs = config["inputs"]["arms"][arm]
        q_to_b0, projected, projection_stats = load_unique_projection(
            Path(inputs["projection_paf"]), minimum_mapq
        )
        depth = load_depth(Path(inputs["heldout_depth"]))
        callable_b0 = {
            b0 for query, b0 in q_to_b0.items() if depth.get(query, 0) >= minimum_depth and region_at(intervals, b0) != "NOT_EVALUABLE"
        }
        arm_state[arm] = {
            "q_to_b0": q_to_b0,
            "projected": {pos for pos in projected if region_at(intervals, pos) != "NOT_EVALUABLE"},
            "callable": callable_b0,
            "projection_stats": projection_stats,
            "depth_records": len(depth),
        }

    common_callable = common_callable_intersection(
        {arm: arm_state[arm]["callable"] for arm in ARMS}
    )

    residual_audit = []
    residual_positions: dict[str, dict[str, set[tuple[str, int]]]] = {
        arm: defaultdict(set) for arm in ARMS
    }
    exclusion_counts: dict[str, Counter] = {arm: Counter() for arm in ARMS}
    for arm in ARMS:
        q_to_b0 = arm_state[arm]["q_to_b0"]
        ledger = load_residuals(Path(config["inputs"]["arms"][arm]["residual_ledger"]))
        for row in ledger:
            source = (row["contig"], int(row["position_1based"]) - 1)
            b0 = q_to_b0.get(source)
            status = "INCLUDED"
            reason = "COMMON_CALLABLE_UNIQUE_ANCHOR"
            b0_region = ""
            if row["evaluation_status"] != "EVALUABLE":
                status, reason = "EXCLUDED", "SOURCE_NOT_EVALUABLE"
            elif b0 is None:
                status, reason = "EXCLUDED", "NO_UNIQUE_BASE_TO_BASE_PROJECTION"
            else:
                b0_region = region_at(intervals, b0)
                if b0_region == "NOT_EVALUABLE":
                    status, reason = "EXCLUDED", "B0_REGION_NOT_EVALUABLE"
                elif b0 not in common_callable:
                    status, reason = "EXCLUDED", "OUTSIDE_COMMON_CALLABLE"
            if status == "INCLUDED":
                residual_positions[arm][b0_region].add(b0)
                residual_positions[arm]["all_regions"].add(b0)
            else:
                exclusion_counts[arm][reason] += 1
            residual_audit.append(
                {
                    "arm": arm,
                    "source_contig": source[0],
                    "source_position_1based": source[1] + 1,
                    "variant_type": row["variant_type"],
                    "source_region": row["region"],
                    "b0_contig": b0[0] if b0 else "",
                    "b0_position_1based": b0[1] + 1 if b0 else "",
                    "b0_region": b0_region,
                    "status": status,
                    "reason": reason,
                }
            )

    denominator_rows = []
    ordered_regions = [*region_labels, "all_regions"]
    for arm in ARMS:
        for region in ordered_regions:
            if region == "all_regions":
                projected_bases = len(arm_state[arm]["projected"])
                callable_bases = len(common_callable)
            else:
                projected_bases = sum(
                    1 for pos in arm_state[arm]["projected"] if region_at(intervals, pos) == region
                )
                callable_bases = sum(1 for pos in common_callable if region_at(intervals, pos) == region)
            residual_loci = len(residual_positions[arm][region])
            denominator_rows.append(
                {
                    "arm": arm,
                    "region": region,
                    **denominator_metrics(projected_bases, callable_bases, residual_loci),
                }
            )

    combined_counts = {
        row["arm"]: int(row["residual_loci"])
        for row in denominator_rows
        if row["region"] == "all_regions"
    }
    conclusion, leaders = classify_r1p1(combined_counts)
    common_by_region = {
        region: sum(1 for pos in common_callable if region_at(intervals, pos) == region)
        for region in region_labels
    }

    outdir.mkdir(parents=True, exist_ok=True)
    write_tsv(
        outdir / "common-callable.bed",
        merge_positions_by_region(common_callable, intervals),
        ["contig", "start", "end", "region"],
    )
    write_tsv(
        outdir / "arm-region-denominators.tsv",
        denominator_rows,
        [
            "arm",
            "region",
            "projected_bases",
            "callable_bases",
            "callable_fraction",
            "residual_loci",
            "residual_rate_per_10kb",
        ],
    )
    write_tsv(
        outdir / "residual-projection-audit.tsv",
        residual_audit,
        [
            "arm",
            "source_contig",
            "source_position_1based",
            "variant_type",
            "source_region",
            "b0_contig",
            "b0_position_1based",
            "b0_region",
            "status",
            "reason",
        ],
    )
    summary = {
        "schema_version": "plant-common-callability-summary-v1",
        "execution_status": "PASS",
        "scientific_scope": "fair-denominator residual comparison only",
        "question": "Does R1P1 retain its residual lead on the six-arm common-callable denominator?",
        "answer": conclusion,
        "leaders": leaders,
        "common_callable_bases": len(common_callable),
        "common_callable_bases_by_region": common_by_region,
        "residual_loci_all_regions": combined_counts,
        "minimum_callable_depth": minimum_depth,
        "minimum_projection_mapq": minimum_mapq,
        "projection_stats": {arm: arm_state[arm]["projection_stats"] for arm in ARMS},
        "residual_exclusions": {arm: dict(sorted(exclusion_counts[arm].items())) for arm in ARMS},
        "parent_m4_result_modified": False,
        "topology_claim": "NOT_EVALUATED",
        "decision": "NOT_APPLICABLE",
        "cycloneseq": "PENDING_REAL_DATA",
        "pmat2_and_mitovgp": "UNCHANGED",
    }
    (outdir / "common-callability-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    ended = datetime.now(timezone.utc)
    provenance = {
        "schema_version": "plant-common-callability-execution-v1",
        "started_at_utc": started.isoformat(),
        "ended_at_utc": ended.isoformat(),
        "python": platform.python_version(),
        "argv": sys.argv,
        "script_sha256": sha256_file(Path(__file__)),
        "preregistration_sha256": sha256_file(config_path),
        "input_manifest_sha256": sha256_file(manifest_path),
    }
    (outdir / "execution-provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--config", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--outdir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "freeze":
        freeze_manifest(args.config, args.output)
    else:
        run_analysis(args.config, args.manifest, args.outdir)


if __name__ == "__main__":
    main()
