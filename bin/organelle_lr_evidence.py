#!/usr/bin/env python3
"""Deterministic evidence helpers for the EXPERIMENTAL plant long-read route.

The commands calculate evidence and enforce policy separation. They never emit an
authentication class. Scientific thresholds are read from versioned JSON policy.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
import re
import shutil
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def fail(code: str, detail: str = "") -> None:
    message = code if not detail else f"{code}: {detail}"
    raise SystemExit(message)


def load_json(path: str) -> dict:
    p = Path(path)
    if not p.is_file() or p.stat().st_size == 0:
        fail("INPUT_JSON_MISSING_OR_EMPTY", str(p))
    try:
        value = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail("INPUT_JSON_INVALID", f"{p}: {exc}")
    if not isinstance(value, dict):
        fail("INPUT_JSON_INVALID", f"{p}: root must be an object")
    return value


def write_json(path: str, value: dict) -> None:
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def open_text(path: str, mode: str = "rt"):
    return gzip.open(path, mode) if str(path).endswith(".gz") else open(path, mode)


def open_deterministic_gzip_text(path: str):
    """Return a deterministic FASTQ writer.

    Uncompressed output is supported for large ephemeral bounded FASTQ files so
    a near-100% processing budget does not waste CPU on decompress/recompress.
    Gzip output uses level 1 with a stable header for small archival subsets.
    """
    if not str(path).endswith(".gz"):
        return open(path, "w")
    raw = open(path, "wb")
    compressed = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=1)
    return io.TextIOWrapper(compressed, encoding="utf-8")


def read_fasta(path: str) -> list[tuple[str, str]]:
    p = Path(path)
    if not p.is_file() or p.stat().st_size == 0:
        fail("FASTA_MISSING_OR_EMPTY", str(p))
    records: list[tuple[str, str]] = []
    name = None
    chunks: list[str] = []
    with open_text(path) as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                if name is not None:
                    records.append((name, "".join(chunks).upper()))
                name = line[1:].split()[0]
                chunks = []
            else:
                if name is None:
                    fail("FASTA_INVALID", "sequence before header")
                chunks.append(line)
    if name is not None:
        records.append((name, "".join(chunks).upper()))
    if not records or any(not sequence for _, sequence in records):
        fail("FASTA_INVALID", "no non-empty sequence record")
    if any(re.search(r"[^ACGTRYSWKMBDHVN]", sequence) for _, sequence in records):
        fail("FASTA_INVALID", "unsupported sequence characters")
    return records


def write_fasta(path: str, records: list[tuple[str, str]]) -> None:
    with open(path, "w") as handle:
        for name, sequence in records:
            handle.write(f">{name}\n")
            for start in range(0, len(sequence), 80):
                handle.write(sequence[start : start + 80] + "\n")


def iter_fastq(path: str):
    with open_text(path) as handle:
        index = 0
        while True:
            header = handle.readline()
            if not header:
                break
            sequence = handle.readline()
            plus = handle.readline()
            quality = handle.readline()
            index += 1
            if not sequence or not plus or not quality:
                fail("FASTQ_TRUNCATED", f"record {index}")
            if not header.startswith("@") or not plus.startswith("+"):
                fail("FASTQ_INVALID", f"record {index}")
            sequence = sequence.rstrip("\r\n")
            quality = quality.rstrip("\r\n")
            if not sequence or len(sequence) != len(quality):
                fail("FASTQ_INVALID", f"record {index}: sequence/quality length")
            read_id = header[1:].split()[0]
            yield read_id, header, sequence, plus, quality


def fastq_census(path: str) -> tuple[int, int]:
    reads = bases = 0
    for _, _, sequence, _, _ in iter_fastq(path):
        reads += 1
        bases += len(sequence)
    return reads, bases


def command_budget_fastq(args) -> None:
    policy = load_json(args.policy)
    raw = policy.get("raw_input", {})
    target = raw.get("target_bases")
    seed = raw.get("seed")
    if target is None or seed is None:
        status = {
            "stage": "long_read_input_budget",
            "status": "INCONCLUSIVE",
            "decision": "NOT_APPLICABLE",
            "reason_codes": ["THRESHOLD_NOT_CONFIGURED"],
        }
        write_json(args.out_manifest, status)
        fail("THRESHOLD_NOT_CONFIGURED", "raw_input.target_bases/seed")
    target = int(target)
    if target <= 0:
        fail("POLICY_INVALID", "raw_input.target_bases must be positive")
    input_reads, input_bases = fastq_census(args.fastq)
    if input_reads == 0:
        fail("FASTQ_EMPTY", args.fastq)
    probability = min(1.0, target / input_bases)
    selected_reads = selected_bases = 0
    with open_deterministic_gzip_text(args.out_fastq) as output:
        for read_id, header, sequence, plus, quality in iter_fastq(args.fastq):
            score = int.from_bytes(
                hashlib.sha256(f"{seed}\0{read_id}".encode()).digest()[:8], "big"
            ) / float(2**64)
            if probability == 1.0 or score < probability:
                output.write(header)
                output.write(sequence + "\n")
                output.write(plus)
                output.write(quality + "\n")
                selected_reads += 1
                selected_bases += len(sequence)
    if selected_reads == 0:
        fail("SUBSAMPLE_EMPTY", "deterministic selection emitted no reads")
    write_json(
        args.out_manifest,
        {
            "schema_version": "long-read-budget-0.1",
            "stage": "long_read_input_budget",
            "status": "PASS",
            "decision": "NOT_APPLICABLE",
            "purpose": "processing_budget_only",
            "seed": seed,
            "requested_bases": target,
            "input_reads": input_reads,
            "input_bases": input_bases,
            "input_sha256": sha256_file(args.fastq),
            "selection_probability": probability,
            "selected_reads": selected_reads,
            "selected_bases": selected_bases,
            "output_sha256": sha256_file(args.out_fastq),
        },
    )


def command_prepare_reference(args) -> None:
    metadata = load_json(args.metadata)
    records = read_fasta(args.fasta)
    anchor_records = read_fasta(args.anchor_fasta)
    if len(records) != 1:
        fail("REFERENCE_FASTA_INVALID", "exactly one canonical sequence is required")
    name, sequence = records[0]
    status = metadata.get("reference_status")
    if status != "ALLOWED_EXPERIMENTAL":
        fail("REFERENCE_NOT_ALLOWED", str(status))
    if metadata.get("reference_accession") != name:
        fail("REFERENCE_ACCESSION_MISMATCH", f"{name}")
    if metadata.get("canonical_length") != len(sequence):
        fail("REFERENCE_LENGTH_MISMATCH", f"{len(sequence)}")
    compatible = metadata.get("compatible_sample_ids") or []
    if compatible and args.sample_id not in compatible:
        fail("REFERENCE_SAMPLE_INCOMPATIBLE", args.sample_id)
    offsets = metadata.get("rotation_offsets_0_based")
    if metadata.get("topology") != "circular" or not isinstance(offsets, list):
        fail("REFERENCE_METADATA_INVALID", "circular topology/rotation offsets required")
    clean_offsets = []
    for offset in offsets:
        if not isinstance(offset, int) or offset < 0 or offset >= len(sequence):
            fail("REFERENCE_ROTATION_INVALID", str(offset))
        if offset not in clean_offsets:
            clean_offsets.append(offset)
    if 0 not in clean_offsets:
        fail("REFERENCE_ROTATION_INVALID", "offset 0 is required")
    rotated = []
    rows = ["target_name\tcanonical_name\toffset_0based\tlength"]
    for offset in clean_offsets:
        target = f"{name}|rot={offset}"
        rotated.append((target, sequence[offset:] + sequence[:offset]))
        rows.append(f"{target}\t{name}\t{offset}\t{len(sequence)}")
    write_fasta(args.out_fasta, rotated)
    Path(args.out_map).write_text("\n".join(rows) + "\n")
    write_json(
        args.out_status,
        {
            "schema_version": "long-read-reference-validation-0.1",
            "stage": "long_read_reference_prepare",
            "status": "PASS",
            "decision": "NOT_APPLICABLE",
            "sample_id": args.sample_id,
            "reference_accession": name,
            "reference_pack_id": metadata.get("reference_pack_id"),
            "reference_pack_version": metadata.get("reference_pack_version"),
            "canonical_length": len(sequence),
            "rotation_offsets_0based": clean_offsets,
            "input_sha256": sha256_file(args.fasta),
            "rotated_sha256": sha256_file(args.out_fasta),
            "m1_anchor_sha256": sha256_file(args.anchor_fasta),
            "m1_anchor_contigs": len(anchor_records),
            "m1_anchor_bases": sum(len(sequence) for _, sequence in anchor_records),
        },
    )


def parse_paf_line(line: str) -> dict:
    fields = line.rstrip("\n").split("\t")
    if len(fields) < 12:
        fail("PAF_INVALID", line[:120])
    tags = {}
    for token in fields[12:]:
        parts = token.split(":", 2)
        if len(parts) == 3:
            tags[parts[0]] = parts[2]
    try:
        result = {
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
            "alignment_length": int(fields[10]),
            "mapq": int(fields[11]),
            "tags": tags,
            "raw": line.rstrip("\n"),
        }
    except ValueError as exc:
        fail("PAF_INVALID", str(exc))
    tp = tags.get("tp", "P")
    result["alignment_class"] = "primary" if tp == "P" else "secondary" if tp == "S" else "supplementary"
    result["query_aligned_fraction"] = (
        (result["query_end"] - result["query_start"]) / result["query_length"]
        if result["query_length"]
        else 0.0
    )
    result["divergence"] = 1.0 - (result["matches"] / result["alignment_length"]) if result["alignment_length"] else 1.0
    return result


def command_select_paf(args) -> None:
    policy = load_json(args.policy)
    selection = policy.get("recruitment", {})
    required = ["min_aligned_bases", "min_query_aligned_fraction", "max_divergence"]
    if any(selection.get(key) is None for key in required):
        write_json(
            args.out_status,
            {"stage": "long_read_recruitment", "status": "INCONCLUSIVE", "decision": "NOT_APPLICABLE", "reason_codes": ["THRESHOLD_NOT_CONFIGURED"]},
        )
        Path(args.out_ids).write_text("")
        Path(args.out_evidence).write_text("query\teligible\treason\talignment_class\tquery_length\tquery_start\tquery_end\ttarget\ttarget_start\ttarget_end\tstrand\tmatches\talignment_length\tquery_aligned_fraction\tdivergence\tmapq\tcigar\tcs\n")
        return
    if selection.get("mapq_is_sole_filter") is not False:
        fail("POLICY_INVALID", "mapq_is_sole_filter must be false")
    allowed_classes = set(selection.get("retain_alignment_classes") or [])
    selected = set()
    total = eligible_count = 0
    header = "query\teligible\treason\talignment_class\tquery_length\tquery_start\tquery_end\ttarget\ttarget_start\ttarget_end\tstrand\tmatches\talignment_length\tquery_aligned_fraction\tdivergence\tmapq\tcigar\tcs"
    rows = [header]
    with open(args.paf) as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = parse_paf_line(line)
            total += 1
            reasons = []
            if rec["alignment_class"] not in allowed_classes:
                reasons.append("ALIGNMENT_CLASS_EXCLUDED")
            if rec["alignment_length"] < int(selection["min_aligned_bases"]):
                reasons.append("ALIGNED_BASES_LOW")
            if rec["query_aligned_fraction"] < float(selection["min_query_aligned_fraction"]):
                reasons.append("QUERY_FRACTION_LOW")
            if rec["divergence"] > float(selection["max_divergence"]):
                reasons.append("DIVERGENCE_HIGH")
            eligible = not reasons
            if eligible:
                selected.add(rec["query"])
                eligible_count += 1
            rows.append(
                "\t".join(
                    map(
                        str,
                        [
                            rec["query"], int(eligible), "PASS" if eligible else ";".join(reasons), rec["alignment_class"],
                            rec["query_length"], rec["query_start"], rec["query_end"], rec["target"], rec["target_start"],
                            rec["target_end"], rec["strand"], rec["matches"], rec["alignment_length"],
                            f"{rec['query_aligned_fraction']:.8f}", f"{rec['divergence']:.8f}", rec["mapq"],
                            rec["tags"].get("cg", ""), rec["tags"].get("cs", ""),
                        ],
                    )
                )
            )
    Path(args.out_ids).write_text("".join(f"{read_id}\n" for read_id in sorted(selected)))
    Path(args.out_evidence).write_text("\n".join(rows) + "\n")
    write_json(
        args.out_status,
        {
            "schema_version": "long-read-recruitment-0.1",
            "stage": "long_read_recruitment",
            "pass": args.pass_number,
            "status": "PASS" if selected else "INCONCLUSIVE",
            "decision": "NOT_APPLICABLE",
            "reason_codes": ["RECRUITMENT_COMPLETE"] if selected else ["LOW_TARGET_READ_YIELD"],
            "alignment_records": total,
            "eligible_alignment_records": eligible_count,
            "selected_complete_read_ids": len(selected),
            "mapq_used_as_sole_filter": False,
        },
    )


def command_extract_fastq(args) -> None:
    selected = {line.strip() for line in Path(args.ids).read_text().splitlines() if line.strip()}
    found = set()
    reads = bases = 0
    with open_deterministic_gzip_text(args.out_fastq) as output:
        for read_id, header, sequence, plus, quality in iter_fastq(args.fastq):
            if read_id in selected:
                output.write(header)
                output.write(sequence + "\n")
                output.write(plus)
                output.write(quality + "\n")
                found.add(read_id)
                reads += 1
                bases += len(sequence)
    missing = sorted(selected - found)
    if missing:
        fail("SELECTED_READ_ID_MISSING", ",".join(missing[:5]))
    write_json(
        args.out_manifest,
        {
            "schema_version": "whole-read-extraction-0.1",
            "stage": "long_read_whole_read_extraction",
            "status": "PASS" if reads else "INCONCLUSIVE",
            "decision": "NOT_APPLICABLE",
            "selected_ids": len(selected),
            "extracted_complete_reads": reads,
            "extracted_bases": bases,
            "output_sha256": sha256_file(args.out_fastq),
        },
    )


def command_union_ids(args) -> None:
    policy = load_json(args.policy)
    rescue = policy.get("rescue", {})
    if rescue.get("max_passes") != 2:
        fail("POLICY_INVALID", "rescue.max_passes must equal 2")
    first = {line.strip() for line in Path(args.pass1).read_text().splitlines() if line.strip()}
    second = {line.strip() for line in Path(args.pass2).read_text().splitlines() if line.strip()}
    if not rescue.get("enabled", False):
        second = set()
    union = first | second
    Path(args.out_ids).write_text("".join(f"{read_id}\n" for read_id in sorted(union)))
    write_json(
        args.out_manifest,
        {
            "schema_version": "recruitment-union-0.1",
            "stage": "long_read_recruitment_union",
            "status": "PASS" if union else "INCONCLUSIVE",
            "decision": "NOT_APPLICABLE",
            "maximum_passes": 2,
            "rescue_enabled": bool(rescue.get("enabled", False)),
            "pass1_ids": len(first),
            "pass2_new_ids": len(second - first),
            "union_ids": len(union),
        },
    )


def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged = []
    for start, end in sorted((max(0, s), max(0, e)) for s, e in intervals if e > s):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def interval_bases(intervals: list[tuple[int, int]]) -> int:
    return sum(end - start for start, end in merge_intervals(intervals))


def load_rotation_map(path: str) -> dict[str, tuple[int, int]]:
    mapping = {}
    lines = Path(path).read_text().splitlines()
    if not lines or lines[0].split("\t")[:3] != ["target_name", "canonical_name", "offset_0based"]:
        fail("REFERENCE_MAP_INVALID", path)
    for line in lines[1:]:
        target, _, offset, length = line.split("\t")[:4]
        mapping[target] = (int(offset), int(length))
    return mapping


def lift_rotated_interval(start: int, end: int, offset: int, length: int) -> list[tuple[int, int]]:
    canonical_start = (start + offset) % length
    span = end - start
    canonical_end = canonical_start + span
    if canonical_end <= length:
        return [(canonical_start, canonical_end)]
    return [(canonical_start, length), (0, canonical_end - length)]


def read_evidence(path: str) -> list[dict]:
    lines = Path(path).read_text().splitlines()
    if not lines:
        return []
    header = lines[0].split("\t")
    records = []
    for line in lines[1:]:
        fields = line.split("\t")
        if len(fields) < len(header):
            fields += [""] * (len(header) - len(fields))
        records.append(dict(zip(header, fields)))
    return records


def command_target_gate(args) -> None:
    policy = load_json(args.policy)
    metadata = load_json(args.reference_metadata)
    gate = policy.get("target_gate", {})
    required = [
        "min_recruited_reads", "min_recruited_bases", "min_estimated_target_depth",
        "min_reference_breadth", "min_declared_junction_reads", "max_recruited_to_aligned_ratio",
    ]
    rotation_map = load_rotation_map(args.reference_map)
    selected = {line.strip() for line in Path(args.selected_ids).read_text().splitlines() if line.strip()}
    evidence_paths = args.evidence if isinstance(args.evidence, list) else [args.evidence]
    eligible = [
        row
        for evidence_path in evidence_paths
        for row in read_evidence(evidence_path)
        if row.get("eligible") == "1" and row.get("query") in selected
    ]
    query_intervals = defaultdict(list)
    canonical_by_read = defaultdict(list)
    divergences = []
    for row in eligible:
        query_intervals[row["query"]].append((int(row["query_start"]), int(row["query_end"])))
        if row["target"] not in rotation_map:
            continue
        offset, length = rotation_map[row["target"]]
        canonical_by_read[row["query"]].extend(lift_rotated_interval(int(row["target_start"]), int(row["target_end"]), offset, length))
        divergences.append(float(row["divergence"]))
    canonical_length = int(metadata["canonical_length"])
    aligned_target_bases = sum(interval_bases(intervals) for intervals in query_intervals.values())
    per_read_alignment_spans = sorted(interval_bases(query_intervals[read_id]) for read_id in selected if query_intervals[read_id])
    breadth_intervals = [interval for intervals in canonical_by_read.values() for interval in intervals]
    breadth = interval_bases(breadth_intervals) / canonical_length if canonical_length else 0.0
    estimated_depth = aligned_target_bases / canonical_length if canonical_length else 0.0
    recruited_reads, recruited_bases = fastq_census(args.recruited_fastq)
    ratio = recruited_bases / aligned_target_bases if aligned_target_bases else math.inf
    junction_support = {}
    for junction in metadata.get("junctions", []):
        left = (int(junction["left_start_1based"]) - 1, int(junction["left_end_1based"]))
        right = (int(junction["right_start_1based"]) - 1, int(junction["right_end_1based"]))
        supporting = []
        for read_id, intervals in canonical_by_read.items():
            left_hit = any(start < left[1] and end > left[0] for start, end in intervals)
            right_hit = any(start < right[1] and end > right[0] for start, end in intervals)
            if left_hit and right_hit:
                supporting.append(read_id)
        junction_support[junction["id"]] = sorted(supporting)
    metrics = {
        "schema_version": "long-read-target-evidence-0.1",
        "stage": "long_read_target_gate",
        "decision": "NOT_APPLICABLE",
        "canonical_reference_length": canonical_length,
        "selected_read_ids": len(selected),
        "recruited_reads": recruited_reads,
        "recruited_bases": recruited_bases,
        "aligned_target_bases": aligned_target_bases,
        "alignment_span_distribution": {
            "count": len(per_read_alignment_spans),
            "minimum": min(per_read_alignment_spans) if per_read_alignment_spans else None,
            "median": statistics.median(per_read_alignment_spans) if per_read_alignment_spans else None,
            "maximum": max(per_read_alignment_spans) if per_read_alignment_spans else None,
        },
        "estimated_target_depth": estimated_depth,
        "reference_breadth": breadth,
        "median_eligible_divergence": statistics.median(divergences) if divergences else None,
        "recruited_to_aligned_ratio": ratio if math.isfinite(ratio) else None,
        "declared_junction_support": junction_support,
        "recruited_fastq_sha256": sha256_file(args.recruited_fastq),
    }
    write_json(args.out_metrics, metrics)
    if any(gate.get(key) is None for key in required):
        status = "INCONCLUSIVE"
        reasons = ["THRESHOLD_NOT_CONFIGURED"]
    else:
        reasons = []
        if recruited_reads < int(gate["min_recruited_reads"]) or recruited_bases < int(gate["min_recruited_bases"]):
            reasons.append("LOW_TARGET_READ_YIELD")
        if estimated_depth < float(gate["min_estimated_target_depth"]):
            reasons.append("LOW_TARGET_COVERAGE")
        if breadth < float(gate["min_reference_breadth"]):
            reasons.append("LOW_REFERENCE_BREADTH")
        minimum_junction = int(gate["min_declared_junction_reads"])
        if minimum_junction and any(len(reads) < minimum_junction for reads in junction_support.values()):
            reasons.append("JUNCTION_SUPPORT_INSUFFICIENT")
        if not math.isfinite(ratio) or ratio > float(gate["max_recruited_to_aligned_ratio"]):
            reasons.append("OFFTARGET_RECRUITMENT_SUSPECTED")
        status = "ELIGIBLE_EXPERIMENTAL" if not reasons else "INCONCLUSIVE"
    write_json(
        args.out_status,
        {
            "schema_version": "long-read-target-gate-status-0.1",
            "stage": "long_read_target_gate",
            "status": status,
            "decision": "NOT_APPLICABLE",
            "reason_codes": reasons,
            "policy_id": policy.get("policy_id"),
            "evidence_file": str(args.out_metrics),
        },
    )


def command_route_guard(args) -> None:
    policy = load_json(args.policy)
    fallback = policy.get("full_background_de_novo", {})
    enabled = bool(fallback.get("enabled"))
    threshold = fallback.get("minimum_clean_depth")
    allowed = (
        args.reference_state != "usable"
        and args.strategy == "de_novo_fallback"
        and enabled
        and threshold is not None
        and args.observed_clean_depth is not None
        and args.observed_clean_depth >= float(threshold)
    )
    write_json(
        args.out_status,
        {
            "schema_version": "long-read-route-guard-0.1",
            "stage": "long_read_routing",
            "status": "ELIGIBLE_EXPERIMENTAL" if allowed else "INCONCLUSIVE",
            "decision": "NOT_APPLICABLE",
            "full_background_pmat2_allowed": allowed,
            "reason_codes": [] if allowed else ["FULL_BACKGROUND_DE_NOVO_NOT_APPLICABLE"],
            "reference_state": args.reference_state,
            "strategy": args.strategy,
            "minimum_clean_depth": threshold,
            "observed_clean_depth": args.observed_clean_depth,
        },
    )


def summarize_paf(path: str) -> dict:
    records = []
    with open(path) as handle:
        for line in handle:
            if line.strip():
                records.append(parse_paf_line(line))
    if not records:
        return {"alignment_records": 0, "aligned_span": 0, "identity": None, "gaps_conflicts": None}
    best = max(records, key=lambda rec: (rec["matches"], rec["alignment_length"]))
    target_intervals = defaultdict(list)
    orientation_counts = defaultdict(int)
    gap_bases = 0
    conflict_bases = 0
    for rec in records:
        target_intervals[rec["target"]].append((rec["target_start"], rec["target_end"]))
        orientation_counts[rec["strand"]] += 1
        cigar_gap_bases = sum(
            int(length)
            for length, operation in re.findall(r"(\d+)([MIDNSHP=X])", rec["tags"].get("cg", ""))
            if operation in {"I", "D", "N"}
        )
        gap_bases += cigar_gap_bases
        try:
            edit_distance = int(rec["tags"].get("NM", "0"))
        except ValueError:
            edit_distance = 0
        conflict_bases += max(0, edit_distance - cigar_gap_bases)
    union_span = max((interval_bases(intervals) for intervals in target_intervals.values()), default=0)
    return {
        "alignment_records": len(records),
        "aligned_span": union_span,
        "best_alignment_span": best["alignment_length"],
        "identity": best["matches"] / best["alignment_length"] if best["alignment_length"] else None,
        "gaps_conflicts": {
            "gap_bases_across_records": gap_bases,
            "conflict_bases_across_records": conflict_bases,
            "mapq_zero_records": sum(rec["mapq"] == 0 for rec in records),
        },
        "orientation_counts": dict(sorted(orientation_counts.items())),
        "query": best["query"],
        "target": best["target"],
        "query_start": best["query_start"],
        "query_end": best["query_end"],
        "target_start": best["target_start"],
        "target_end": best["target_end"],
        "strand": best["strand"],
        "mapq": best["mapq"],
        "cigar": best["tags"].get("cg"),
    }


def projected_query_position(alignment: dict, target_position: int) -> int | None:
    if target_position < alignment["target_start"] or target_position >= alignment["target_end"]:
        return None
    span_t = alignment["target_end"] - alignment["target_start"]
    span_q = alignment["query_end"] - alignment["query_start"]
    fraction = (target_position - alignment["target_start"]) / span_t if span_t else 0
    if alignment["strand"] == "+":
        return int(alignment["query_start"] + fraction * span_q)
    return int(alignment["query_end"] - fraction * span_q)


def command_structural(args) -> None:
    metadata = load_json(args.reference_metadata)
    policy = load_json(args.policy)
    if not Path(args.candidate_fasta).is_file() or Path(args.candidate_fasta).stat().st_size == 0:
        result = {
            "schema_version": "plant-long-read-structural-evidence-0.1",
            "stage": "long_read_structural_validation",
            "status": "INCONCLUSIVE",
            "decision": "NOT_APPLICABLE",
            "experimental_only": True,
            "platform": args.platform,
            "cycloneseq_transferability": "PENDING_REAL_DATA",
            "candidate_contigs": 0,
            "candidate_bases": 0,
            "ir_gap_outcome": "not_assessable",
            "independent_spanning_read_ids": [],
            "reason_codes": ["SUBSET_ASSEMBLY_FAILED"],
        }
        write_json(args.out_json, result)
        Path(args.out_tsv).write_text("metric\tvalue\ncandidate_contigs\t0\nir_gap_outcome\tnot_assessable\n")
        return
    candidates = read_fasta(args.candidate_fasta)
    comparator_candidates = read_fasta(args.comparator_fasta) if Path(args.comparator_fasta).stat().st_size else []
    ref_summary = summarize_paf(args.reference_paf)
    anchor_summary = summarize_paf(args.anchor_paf)
    comparator_ref_summary = summarize_paf(args.comparator_reference_paf)
    read_alignments = []
    with open(args.read_candidate_paf) as handle:
        for line in handle:
            if line.strip():
                read_alignments.append(parse_paf_line(line))
    gap = metadata.get("m1_ir_gap") or {}
    gap_start = int(gap.get("start_1based", 0)) - 1
    gap_end = int(gap.get("end_1based", 0))
    assembly_alignments = []
    with open(args.reference_paf) as handle:
        for line in handle:
            if line.strip():
                assembly_alignments.append(parse_paf_line(line))
    spanning_candidate = None
    projected = None
    for rec in assembly_alignments:
        if rec["target_start"] <= gap_start and rec["target_end"] >= gap_end:
            q_left = projected_query_position(rec, gap_start)
            q_right = projected_query_position(rec, gap_end - 1)
            if q_left is not None and q_right is not None:
                spanning_candidate = rec["query"]
                projected = sorted((q_left, q_right))
                break
    spanning_reads = []
    flank = policy.get("structural_evidence", {}).get("min_junction_flank_bases")
    if spanning_candidate and projected and flank is not None:
        flank = int(flank)
        for rec in read_alignments:
            if rec["target"] == spanning_candidate and rec["target_start"] <= max(0, projected[0] - flank) and rec["target_end"] >= projected[1] + flank:
                spanning_reads.append(rec["query"])
    minimum = policy.get("target_gate", {}).get("min_declared_junction_reads")
    if spanning_candidate is None:
        outcome = "not_closed"
    elif minimum is None or flank is None:
        outcome = "not_assessable"
    elif len(set(spanning_reads)) >= int(minimum):
        outcome = "closed"
    else:
        outcome = "not_assessable"
    result = {
        "schema_version": "plant-long-read-structural-evidence-0.1",
        "stage": "long_read_structural_validation",
        "status": "PASS" if outcome == "closed" else "INCONCLUSIVE",
        "decision": "NOT_APPLICABLE",
        "experimental_only": True,
        "platform": args.platform,
        "cycloneseq_transferability": "PENDING_REAL_DATA",
        "candidate_contigs": len(candidates),
        "candidate_bases": sum(len(sequence) for _, sequence in candidates),
        "comparator_candidate_contigs": len(comparator_candidates),
        "comparator_candidate_bases": sum(len(sequence) for _, sequence in comparator_candidates),
        "reference_alignment": ref_summary,
        "comparator_reference_alignment": comparator_ref_summary,
        "m1_anchor_alignment": anchor_summary,
        "m1_ir_gap": gap,
        "ir_gap_outcome": outcome,
        "candidate_spanning_gap": spanning_candidate,
        "projected_candidate_gap_coordinates_0based": projected,
        "independent_spanning_read_ids": sorted(set(spanning_reads)),
        "reason_codes": [] if outcome == "closed" else ["JUNCTION_SUPPORT_INSUFFICIENT"],
    }
    result["flye_vs_pmat2"] = {
        "state": "measured" if comparator_candidates and comparator_ref_summary.get("alignment_records") else "comparator_not_assessable",
        "candidate_base_delta": result["candidate_bases"] - result["comparator_candidate_bases"] if comparator_candidates else None,
        "reference_identity_delta": (
            ref_summary.get("identity") - comparator_ref_summary.get("identity")
            if ref_summary.get("identity") is not None and comparator_ref_summary.get("identity") is not None
            else None
        ),
    }
    write_json(args.out_json, result)
    Path(args.out_tsv).write_text(
        "metric\tvalue\n"
        + f"candidate_contigs\t{result['candidate_contigs']}\n"
        + f"candidate_bases\t{result['candidate_bases']}\n"
        + f"comparator_candidate_bases\t{result['comparator_candidate_bases']}\n"
        + f"reference_identity\t{ref_summary.get('identity')}\n"
        + f"reference_aligned_span\t{ref_summary.get('aligned_span')}\n"
        + f"ir_gap_outcome\t{outcome}\n"
        + f"independent_spanning_reads\t{len(set(spanning_reads))}\n"
    )


def reverse_complement(sequence: str) -> str:
    return sequence.translate(str.maketrans("ACGTRYMKBDHVN", "TGCAYRKMVHDBN"))[::-1]


def parse_cigar(cigar: str) -> list[tuple[int, str]]:
    if not cigar:
        return []
    parts = [(int(length), operation) for length, operation in re.findall(r"(\d+)([MIDNSHP=X])", cigar)]
    if sum(len(str(length)) + 1 for length, _ in parts) != len(cigar):
        fail("CIGAR_INVALID", cigar)
    return parts


def command_homopolymer(args) -> None:
    if not Path(args.candidate_fasta).is_file() or Path(args.candidate_fasta).stat().st_size == 0:
        write_json(args.out_json, {"schema_version": "homopolymer-spectrum-0.1", "state": "not_assessable", "platform": args.platform, "records": [], "callable_run_bases": 0, "unliftable_intervals": [], "reason_codes": ["SUBSET_ASSEMBLY_FAILED"]})
        Path(args.out_tsv).write_text("anchor\tstart_1based\tend_1based\tbase\treference_run_length\tcandidate_run_length\trun_length_delta\tsubstitutions\tdeletions\tinsertions\tstate\n")
        return
    anchor_records = read_fasta(args.anchor_fasta)
    candidate_records = dict(read_fasta(args.candidate_fasta))
    anchor_name, anchor = anchor_records[0]
    alignments = []
    with open(args.paf) as handle:
        for line in handle:
            if line.strip():
                alignments.append(parse_paf_line(line))
    usable = [rec for rec in alignments if rec["target"] == anchor_name and rec["query"] in candidate_records and rec["tags"].get("cg")]
    if not usable:
        write_json(args.out_json, {"schema_version": "homopolymer-spectrum-0.1", "state": "not_assessable", "records": [], "callable_run_bases": 0, "unliftable_intervals": []})
        Path(args.out_tsv).write_text("anchor\tstart_1based\tend_1based\tbase\treference_run_length\tcandidate_run_length\trun_length_delta\tsubstitutions\tdeletions\tinsertions\tstate\n")
        return
    rec = max(usable, key=lambda item: item["matches"])
    candidate_forward = candidate_records[rec["query"]][rec["query_start"] : rec["query_end"]]
    candidate = candidate_forward if rec["strand"] == "+" else reverse_complement(candidate_forward)
    target_position = rec["target_start"]
    query_position = 0
    target_to_query: dict[int, str | None] = {}
    insertions_after = defaultdict(str)
    for length, operation in parse_cigar(rec["tags"]["cg"]):
        if operation in ("M", "=", "X"):
            for offset in range(length):
                if target_position + offset < len(anchor) and query_position + offset < len(candidate):
                    target_to_query[target_position + offset] = candidate[query_position + offset]
            target_position += length
            query_position += length
        elif operation in ("D", "N"):
            for offset in range(length):
                target_to_query[target_position + offset] = None
            target_position += length
        elif operation == "I":
            insertions_after[target_position - 1] += candidate[query_position : query_position + length]
            query_position += length
        elif operation == "S":
            query_position += length
    records = []
    unliftable = []
    start = 0
    for index in range(1, len(anchor) + 1):
        if index < len(anchor) and anchor[index] == anchor[start]:
            continue
        run_length = index - start
        if run_length >= args.min_run:
            lifted = [target_to_query.get(pos, "UNLIFTABLE") for pos in range(start, index)]
            if "UNLIFTABLE" in lifted:
                state = "unliftable"
                unliftable.append([start + 1, index])
                candidate_run_length = substitutions = deletions = insertions = None
            else:
                state = "callable"
                deletions = sum(base is None for base in lifted)
                substitutions = sum(base is not None and base != anchor[start] for base in lifted)
                insertions = sum(len(insertions_after.get(pos, "")) for pos in range(start, index))
                candidate_run_length = sum(base == anchor[start] for base in lifted if base is not None)
                candidate_run_length += sum(base == anchor[start] for pos in range(start, index) for base in insertions_after.get(pos, ""))
            records.append(
                {
                    "anchor": anchor_name,
                    "start_1based": start + 1,
                    "end_1based": index,
                    "base": anchor[start],
                    "reference_run_length": run_length,
                    "candidate_run_length": candidate_run_length,
                    "run_length_delta": None if candidate_run_length is None else candidate_run_length - run_length,
                    "substitutions": substitutions,
                    "deletions": deletions,
                    "insertions": insertions,
                    "state": state,
                }
            )
        start = index
    output = {
        "schema_version": "homopolymer-spectrum-0.1",
        "state": "measured",
        "method": "maximal_anchor_runs_lifted_through_minimap2_cigar",
        "platform": args.platform,
        "records": records,
        "callable_run_bases": sum(rec["reference_run_length"] for rec in records if rec["state"] == "callable"),
        "unliftable_intervals": unliftable,
    }
    write_json(args.out_json, output)
    columns = ["anchor", "start_1based", "end_1based", "base", "reference_run_length", "candidate_run_length", "run_length_delta", "substitutions", "deletions", "insertions", "state"]
    with open(args.out_tsv, "w") as handle:
        handle.write("\t".join(columns) + "\n")
        for item in records:
            handle.write("\t".join("" if item[column] is None else str(item[column]) for column in columns) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("budget-fastq")
    p.add_argument("--fastq", required=True); p.add_argument("--policy", required=True)
    p.add_argument("--out-fastq", required=True); p.add_argument("--out-manifest", required=True)
    p.set_defaults(func=command_budget_fastq)

    p = sub.add_parser("prepare-reference")
    p.add_argument("--sample-id", required=True); p.add_argument("--fasta", required=True); p.add_argument("--metadata", required=True); p.add_argument("--anchor-fasta", required=True)
    p.add_argument("--out-fasta", required=True); p.add_argument("--out-map", required=True); p.add_argument("--out-status", required=True)
    p.set_defaults(func=command_prepare_reference)

    p = sub.add_parser("select-paf")
    p.add_argument("--paf", required=True); p.add_argument("--policy", required=True); p.add_argument("--pass-number", type=int, choices=(1, 2), required=True)
    p.add_argument("--out-ids", required=True); p.add_argument("--out-evidence", required=True); p.add_argument("--out-status", required=True)
    p.set_defaults(func=command_select_paf)

    p = sub.add_parser("extract-fastq")
    p.add_argument("--fastq", required=True); p.add_argument("--ids", required=True); p.add_argument("--out-fastq", required=True); p.add_argument("--out-manifest", required=True)
    p.set_defaults(func=command_extract_fastq)

    p = sub.add_parser("union-ids")
    p.add_argument("--pass1", required=True); p.add_argument("--pass2", required=True); p.add_argument("--policy", required=True)
    p.add_argument("--out-ids", required=True); p.add_argument("--out-manifest", required=True)
    p.set_defaults(func=command_union_ids)

    p = sub.add_parser("target-gate")
    p.add_argument("--evidence", required=True, nargs="+"); p.add_argument("--selected-ids", required=True); p.add_argument("--reference-map", required=True)
    p.add_argument("--reference-metadata", required=True); p.add_argument("--policy", required=True); p.add_argument("--recruited-fastq", required=True)
    p.add_argument("--out-metrics", required=True); p.add_argument("--out-status", required=True)
    p.set_defaults(func=command_target_gate)

    p = sub.add_parser("route-guard")
    p.add_argument("--policy", required=True); p.add_argument("--reference-state", choices=("usable", "missing", "inadequate"), required=True)
    p.add_argument("--strategy", choices=("reference_first", "de_novo_fallback"), required=True); p.add_argument("--observed-clean-depth", type=float)
    p.add_argument("--out-status", required=True); p.set_defaults(func=command_route_guard)

    p = sub.add_parser("structural")
    p.add_argument("--candidate-fasta", required=True); p.add_argument("--comparator-fasta", required=True); p.add_argument("--reference-paf", required=True); p.add_argument("--comparator-reference-paf", required=True); p.add_argument("--anchor-paf", required=True)
    p.add_argument("--read-candidate-paf", required=True); p.add_argument("--reference-metadata", required=True); p.add_argument("--policy", required=True)
    p.add_argument("--platform", required=True); p.add_argument("--out-json", required=True); p.add_argument("--out-tsv", required=True)
    p.set_defaults(func=command_structural)

    p = sub.add_parser("homopolymer")
    p.add_argument("--anchor-fasta", required=True); p.add_argument("--candidate-fasta", required=True); p.add_argument("--paf", required=True)
    p.add_argument("--platform", required=True); p.add_argument("--min-run", type=int, default=3); p.add_argument("--out-json", required=True); p.add_argument("--out-tsv", required=True)
    p.set_defaults(func=command_homopolymer)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
