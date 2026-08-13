#!/usr/bin/env python3
"""Create the lightweight M4 comparison, edit-ledger, and audit bundle."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ARMS = ("B0", "R1", "P0", "C0", "R1P1", "R1C1")
CS_TOKEN = re.compile(r"(:[0-9]+|=[A-Za-z]+|\*[A-Za-z][A-Za-z]|[+-][A-Za-z]+|~[A-Za-z]{2}[0-9]+[A-Za-z]{2})")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_bed(path: Path) -> dict[str, list[tuple[int, int, str]]]:
    result: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    with path.open() as handle:
        for raw in handle:
            if not raw.strip() or raw.startswith("#"):
                continue
            chrom, start, end, *rest = raw.rstrip().split("\t")
            result[chrom].append((int(start), int(end), rest[0] if rest else "core"))
    return result


def region_at(bed: dict[str, list[tuple[int, int, str]]], chrom: str, pos0: int) -> str:
    labels = [label for start, end, label in bed.get(chrom, []) if start <= pos0 < end]
    return ",".join(sorted(set(labels))) if labels else "NOT_EVALUABLE"


def parse_vcf(path: Path):
    with gzip.open(path, "rt") as handle:
        for raw in handle:
            if raw.startswith("#"):
                continue
            fields = raw.rstrip().split("\t")
            fmt = fields[8].split(":")
            sample = dict(zip(fmt, fields[9].split(":")))
            yield fields, sample


def c_ledger(taxon: str, arm: str, vcf: Path, bed: Path) -> list[dict[str, object]]:
    intervals = read_bed(bed)
    rows = []
    for fields, sample in parse_vcf(vcf):
        chrom, pos1, ref, alt = fields[0], int(fields[1]), fields[3], fields[4].split(",")[0]
        dp = int(sample.get("DP", "0").split(",")[0])
        ad = [int(value) for value in sample.get("AD", "0,0").split(",")]
        alt_count = ad[1] if len(ad) > 1 else 0
        rows.append({
            "taxon": taxon, "arm": arm, "route": "bcftools_consensus",
            "contig": chrom, "position_1based": pos1, "ref": ref, "alt": alt,
            "variant_type": "SNV" if len(ref) == len(alt) == 1 else "INDEL" if len(ref) != len(alt) else "MNV",
            "region": region_at(intervals, chrom, pos1 - 1),
            "evaluation_status": "EVALUABLE" if region_at(intervals, chrom, pos1 - 1) != "NOT_EVALUABLE" else "NOT_EVALUABLE",
            "depth": dp, "ref_count": ad[0] if ad else 0, "alt_count": alt_count,
            "alt_fraction": alt_count / dp if dp else None, "qual": fields[5],
            "mapping_ambiguity": "PRIMARY_MAPQ20_FILTERED",
            "filter_reason": "PASS_TRAINING_QUAL30_DP10_AF0.8",
            "allele_evidence": sample.get("AD", "."), "support_source": vcf.name,
        })
    return rows


def pileup_count(pileup: str, allele: str) -> int | None:
    result = None
    for token in pileup.split(",") if pileup else []:
        match = re.fullmatch(r"(.+)x([0-9]+)", token)
        if match and match.group(1) == allele:
            result = int(match.group(2))
    return result


def p_ledger(taxon: str, arm: str, debug: Path, bed: Path) -> list[dict[str, object]]:
    intervals = read_bed(bed)
    rows = []
    with debug.open() as handle:
        for item in csv.DictReader(handle, delimiter="\t"):
            if item["status"] != "changed":
                continue
            pos0, ref, alt = int(item["pos"]), item["base"], item["new_base"]
            region = region_at(intervals, item["name"], pos0)
            rows.append({
                "taxon": taxon, "arm": arm, "route": "polypolish",
                "contig": item["name"], "position_1based": pos0 + 1, "ref": ref, "alt": alt,
                "variant_type": "SNV" if len(ref) == len(alt) == 1 else "INDEL" if len(ref) != len(alt) or alt == "-" else "MNV",
                "region": region, "evaluation_status": "EVALUABLE" if region != "NOT_EVALUABLE" else "NOT_EVALUABLE",
                "depth": item["depth"], "ref_count": pileup_count(item["pileup"], ref),
                "alt_count": pileup_count(item["pileup"], alt), "alt_fraction": None, "qual": None,
                "mapping_ambiguity": "BWA_MEM_A_MULTIMAPPING_RETAINED",
                "filter_reason": "POLYPOLISH_CHANGED",
                "allele_evidence": item["pileup"], "support_source": debug.name,
            })
    return rows


def cumulative_paf_ledger(taxon: str, arm: str, paf: Path, bed_path: Path) -> list[dict[str, object]]:
    bed = read_bed(bed_path)
    rows = []
    with paf.open() as handle:
        for raw in handle:
            fields = raw.rstrip().split("\t")
            tags = {field[:2]: field[5:] for field in fields[12:] if field.startswith("cs:Z:")}
            cs = tags.get("cs")
            if not cs:
                raise ValueError(f"missing cs tag in {paf}")
            if fields[4] != "+":
                raise ValueError(f"cumulative ledger requires same-orientation candidate alignment: {paf}")
            query, target = fields[0], fields[5]
            qpos, tpos = int(fields[2]), int(fields[7])
            tokens = CS_TOKEN.findall(cs)
            if "".join(tokens) != cs:
                raise ValueError(f"unsupported cs tokens in {paf}")
            for token in tokens:
                op, payload = token[0], token[1:]
                if op in (":", "="):
                    length = int(payload) if op == ":" else len(payload)
                    qpos += length
                    tpos += length
                    continue
                if op == "*":
                    ref, alt, kind = payload[0].upper(), payload[1].upper(), "SNV"
                    consumes_t, consumes_q = 1, 1
                elif op == "+":
                    ref, alt, kind = "-", payload.upper(), "INDEL"
                    consumes_t, consumes_q = 0, len(payload)
                elif op == "-":
                    ref, alt, kind = payload.upper(), "-", "INDEL"
                    consumes_t, consumes_q = len(payload), 0
                elif op == "~":
                    length = int(payload[2:-2])
                    ref, alt, kind = f"INTRON_{length}", "-", "STRUCTURAL_GAP"
                    consumes_t, consumes_q = length, 0
                else:
                    raise ValueError(f"unsupported cs operator {op}")
                region = region_at(bed, target, tpos)
                rows.append({
                    "taxon": taxon, "arm": arm, "route": "cumulative_candidate_vs_B0",
                    "contig": target, "position_1based": tpos + 1, "ref": ref, "alt": alt,
                    "variant_type": kind, "region": region,
                    "evaluation_status": "EVALUABLE" if region != "NOT_EVALUABLE" else "NOT_EVALUABLE",
                    "depth": None, "ref_count": None, "alt_count": None, "alt_fraction": None,
                    "qual": None, "mapping_ambiguity": f"ASSEMBLY_ALIGNMENT_MAPQ_{fields[11]}",
                    "filter_reason": "CUMULATIVE_PROVENANCE_NOT_RANKING_EVIDENCE",
                    "allele_evidence": f"query={query};query_pos_1based={qpos + 1}",
                    "support_source": paf.name,
                })
                tpos += consumes_t
                qpos += consumes_q
    return rows


LEDGER_FIELDS = [
    "taxon", "arm", "route", "contig", "position_1based", "ref", "alt", "variant_type",
    "region", "evaluation_status", "depth", "ref_count", "alt_count", "alt_fraction", "qual",
    "mapping_ambiguity", "filter_reason", "allele_evidence", "support_source",
]


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def fasta_content(path: Path) -> tuple[str, int, str]:
    records = []
    name = None
    parts: list[str] = []
    with path.open() as handle:
        for raw in handle:
            if raw.startswith(">"):
                if name is not None:
                    records.append((name, "".join(parts).upper()))
                name = raw[1:].split()[0]
                parts = []
            else:
                parts.append(raw.strip())
    if name is not None:
        records.append((name, "".join(parts).upper()))
    canonical = "".join(f">{record_name}\n{sequence}\n" for record_name, sequence in records)
    return hashlib.sha256(canonical.encode()).hexdigest(), sum(len(sequence) for _, sequence in records), ";".join(f"{record_name}:{len(sequence)}" for record_name, sequence in records)


def parse_polypolish_log(path: Path, taxon: str, arm: str) -> dict[str, object]:
    text = path.read_text()
    def value(pattern: str):
        match = re.search(pattern, text)
        return int(match.group(1).replace(",", "")) if match else None
    orientation = re.search(r"Automatically determined correct orientation: (\S+)", text)
    return {
        "taxon": taxon, "arm": arm,
        "matching_read_pairs": value(r"Matching read pairs: ([0-9,]+)"),
        "orientation": orientation.group(1) if orientation else None,
        "low_insert_threshold": value(r"Low threshold:\s+([0-9,]+)"),
        "high_insert_threshold": value(r"High threshold:\s+([0-9,]+)"),
        "alignments_before_filter": value(r"Alignments before filtering: ([0-9,]+)"),
        "alignments_after_filter": value(r"Alignments after filtering:\s+([0-9,]+)"),
        "log_sha256": sha256_file(path),
    }


def dominance(metrics: list[dict[str, object]], taxon: str) -> dict[str, object]:
    rows = [row for row in metrics if row["taxon"] == taxon]
    b0 = next(row for row in rows if row["arm"] == "B0")
    winners = []
    for row in rows:
        other = [candidate for candidate in rows if candidate is not row]
        if (
            all(row["residual_unsupported_loci"] < candidate["residual_unsupported_loci"] for candidate in other)
            and all(row["evaluable_homopolymer_discordances"] < candidate["evaluable_homopolymer_discordances"] for candidate in other)
            and row["heldout_core_concordance"] is not None
            and row["heldout_core_concordance"] >= b0["heldout_core_concordance"]
        ):
            winners.append(row["arm"])
    callable_values = {row["arm"]: row["callable_core_bases"] for row in rows}
    result = {
        "taxon": taxon,
        "preregistered_numeric_winners": winners,
        "scientific_outcome": "NUMERIC_DOMINANT_UNDER_PREREGISTERED_RULE" if len(winners) == 1 else "CONDITIONAL",
        "status": "INCONCLUSIVE", "assembly_grade": "CANDIDATE", "decision": "NOT_APPLICABLE",
        "callable_core_bases_by_arm": callable_values,
        "callable_core_spread_bases": max(callable_values.values()) - min(callable_values.values()),
        "callability_is_not_a_preregistered_ranking_metric": True,
        "interpretation_caveat": "Absolute residual counts must be read together with arm-specific callable bases; no post-hoc callability threshold was introduced.",
        "cycloneseq": "PENDING_REAL_DATA", "topology_claim": "PROHIBITED",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--execution-manifest", type=Path, required=True)
    args = parser.parse_args()
    root = args.result_root / "m4_hybrid_evaluation"
    execution = json.loads(args.execution_manifest.read_text())
    args.outdir.mkdir(parents=True, exist_ok=True)

    metrics = []
    for path in sorted((root / "m4_heldout_evaluate").glob("*.metrics.json")):
        metrics.append(json.loads(path.read_text()))
    if len(metrics) != 12 or {(row["taxon"], row["arm"]) for row in metrics} != {(t, a) for t in ("plant", "animal") for a in ARMS}:
        raise ValueError("expected exactly the registered six arms for both taxa")

    comparison_fields = [
        "taxon", "arm", "core_bases", "callable_core_bases", "residual_unsupported_loci",
        "evaluable_homopolymer_discordances", "heldout_core_concordance", "snvs", "indels",
        "outside_core_residuals", "status", "assembly_grade", "decision", "candidate_sha256",
    ]
    write_tsv(args.outdir / "six-arm-comparison.tsv", sorted(metrics, key=lambda row: (row["taxon"], ARMS.index(row["arm"]))), comparison_fields)
    (args.outdir / "six-arm-metrics.json").write_text(json.dumps(sorted(metrics, key=lambda row: (row["taxon"], ARMS.index(row["arm"]))), indent=2, sort_keys=True) + "\n")

    heldout_rows = []
    for path in sorted((root / "m4_heldout_evaluate").glob("*.heldout-edit-ledger.tsv")):
        with path.open() as handle:
            heldout_rows.extend(csv.DictReader(handle, delimiter="\t"))
    heldout_fields = list(heldout_rows[0]) if heldout_rows else [
        "taxon", "arm", "route", "contig", "position_1based", "ref", "alt", "variant_type",
        "region", "evaluation_status", "depth", "ref_count", "alt_count", "alt_fraction", "qual",
        "mapping_ambiguity", "filter_reason", "support_source",
    ]
    write_tsv(args.outdir / "heldout-residual-ledger.tsv", heldout_rows, heldout_fields)

    region_rows = []
    for row in metrics:
        for region, count in row["regional_residuals"].items():
            region_rows.append({"taxon": row["taxon"], "arm": row["arm"], "region": region, "residual_unsupported_loci": count, "evaluation_status": "EVALUABLE"})
        region_rows.append({"taxon": row["taxon"], "arm": row["arm"], "region": "outside_frozen_core", "residual_unsupported_loci": row["outside_core_residuals"], "evaluation_status": "NOT_EVALUABLE"})
    write_tsv(args.outdir / "region-summary.tsv", region_rows, ["taxon", "arm", "region", "residual_unsupported_loci", "evaluation_status"])

    ledgers = []
    arm_to_base = {"P0": "B0", "C0": "B0", "R1P1": "R1", "R1C1": "R1"}
    for taxon in ("plant", "animal"):
        for arm in ("P0", "R1P1"):
            debug = root / "m4_polypolish" / f"{taxon}.{arm}.polypolish-debug.tsv"
            bed = root / "m4_lift_mask" / f"{taxon}.{arm_to_base[arm]}.core.bed"
            rows = p_ledger(taxon, arm, debug, bed)
            write_tsv(args.outdir / f"{taxon}.{arm}.introduced-edit-ledger.tsv", rows, LEDGER_FIELDS)
            ledgers.extend(rows)

    cumulative_rows = []
    for taxon in ("plant", "animal"):
        source_bed = Path(execution["taxa"][taxon]["source_bed"])
        if not source_bed.is_absolute():
            source_bed = args.execution_manifest.resolve().parents[4] / source_bed
        for arm in ARMS:
            paf = root / "m4_candidate_to_b0" / f"{taxon}.{arm}.candidate-to-b0.paf"
            rows = cumulative_paf_ledger(taxon, arm, paf, source_bed)
            write_tsv(args.outdir / f"{taxon}.{arm}.cumulative-vs-B0-ledger.tsv", rows, LEDGER_FIELDS)
            cumulative_rows.extend(rows)
        for arm in ("C0", "R1C1"):
            base = arm_to_base[arm]
            vcf = root / "m4_bcftools_call_train" / f"{taxon}.{base}.train.filtered.vcf.gz"
            bed = root / "m4_lift_mask" / f"{taxon}.{base}.core.bed"
            rows = c_ledger(taxon, arm, vcf, bed)
            write_tsv(args.outdir / f"{taxon}.{arm}.introduced-edit-ledger.tsv", rows, LEDGER_FIELDS)
            ledgers.extend(rows)

    dominance_rows = [dominance(metrics, taxon) for taxon in ("plant", "animal")]
    (args.outdir / "dominance.json").write_text(json.dumps(dominance_rows, indent=2, sort_keys=True) + "\n")

    applicability = []
    for taxon in ("plant", "animal"):
        for arm in ("P0", "R1P1"):
            path = root / "m4_polypolish" / f"{taxon}.{arm}.polypolish-filter.log"
            applicability.append(parse_polypolish_log(path, taxon, arm))
    write_tsv(args.outdir / "polypolish-applicability.tsv", applicability, list(applicability[0]))

    candidate_rows = []
    for taxon in ("plant", "animal"):
        for arm in ARMS:
            if arm in ("B0", "R1"):
                path = Path(execution["taxa"][taxon][arm.lower()])
            elif arm in ("P0", "R1P1"):
                path = root / "m4_polypolish" / f"{taxon}.{arm}.fasta"
            else:
                path = root / "m4_bcftools_consensus" / f"{taxon}.{arm}.fasta"
            sequence_sha, bases, contigs = fasta_content(path)
            candidate_rows.append({
                "taxon": taxon, "arm": arm, "path": str(path), "file_sha256": sha256_file(path),
                "sequence_content_sha256": sequence_sha, "bases": bases, "contigs": contigs,
                "status": "INCONCLUSIVE", "assembly_grade": "CANDIDATE", "decision": "NOT_APPLICABLE",
            })
    write_tsv(args.outdir / "candidate-manifest.tsv", candidate_rows, list(candidate_rows[0]))

    junction_audit = {
        "schema_version": "m4-junction-audit-v1",
        "new_junction_claims": [],
        "result": "NOT_APPLICABLE_NO_NEW_JUNCTION_CLAIM",
        "plant_inherited_topology": "INCONCLUSIVE",
        "animal_inherited_topology": "INCONCLUSIVE",
        "note": "Polishing changed bases only; no arm is permitted to infer adjacency, circularity, or repeat copy number.",
    }
    (args.outdir / "junction-audit.json").write_text(json.dumps(junction_audit, indent=2, sort_keys=True) + "\n")

    trace_path = args.result_root / "run-metadata" / "trace.tsv"
    with trace_path.open() as handle:
        trace = list(csv.DictReader(handle, delimiter="\t"))
    write_tsv(args.outdir / "resource-trace.tsv", trace, list(trace[0]))
    status_counts = Counter(row["status"] for row in trace)
    audit = {
        "schema_version": "m4-execution-audit-v1", "registered_arms": list(ARMS),
        "metric_records": len(metrics), "introduced_edit_records": len(ledgers),
        "cumulative_vs_b0_records": len(cumulative_rows),
        "nextflow_tasks": len(trace), "task_status_counts": dict(status_counts),
        "all_tasks_exit_zero": all(row["exit"] == "0" for row in trace),
        "pmat2_invoked": any("PMAT2" in row["name"] for row in trace),
        "identify_or_decision_invoked": any(token in row["name"] for row in trace for token in ("IDENTIFY", "DECISION")),
        "status": "INCONCLUSIVE", "assembly_grade": "CANDIDATE", "decision": "NOT_APPLICABLE",
    }
    (args.outdir / "execution-audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")

    output_files = sorted(path for path in args.outdir.iterdir() if path.is_file() and path.name != "RESULT-MANIFEST.sha256")
    with (args.outdir / "RESULT-MANIFEST.sha256").open("w") as handle:
        for path in output_files:
            handle.write(f"{sha256_file(path)}  {path.name}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
