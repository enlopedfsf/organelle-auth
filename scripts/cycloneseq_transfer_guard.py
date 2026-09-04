#!/usr/bin/env python3
"""Deterministic engineering guard for CycloneSEQ transfer validation.

This module validates governance artifacts and synthetic fixtures. It does not
run biological analysis, calibrate thresholds, or emit an authentication call.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets" / "cycloneseq-transfer-validation"
SCHEMA_ROOT = ROOT / "assets" / "schemas" / "cycloneseq-transfer-validation"
POLICY_ROOT = ROOT / "assets" / "policies" / "cycloneseq-transfer-validation"

PRE_ENTRY_STATE = "PENDING_REAL_DATA"
ACTIVE_STAGES = (
    "ARRIVAL_QUARANTINE",
    "ARRIVAL_VALIDATED",
    "PROTOCOL_FROZEN",
    "BLINDED_RESULTS_FROZEN",
    "UNBLINDED_EVALUATION",
    "OWNER_GO_NO_GO_REVIEW",
)
OUTCOMES = (
    "PENDING_REAL_DATA",
    "ARRIVAL_BLOCKED",
    "INCONCLUSIVE_NOT_EVALUABLE",
    "NO_GO_CONTROL_FAILURE",
    "NO_GO_HARM_OR_FALSE_STRUCTURE",
    "NO_GO_NO_INDEPENDENT_GAIN",
    "CONDITIONAL_MIXED_EVIDENCE",
    "INSUFFICIENT_SCOPE_FOR_GO",
    "ELIGIBLE_FOR_GO_REVIEW",
)
STATUS_BY_OUTCOME = {
    "PENDING_REAL_DATA": "INCONCLUSIVE",
    "ARRIVAL_BLOCKED": "FAIL",
    "INCONCLUSIVE_NOT_EVALUABLE": "INCONCLUSIVE",
    "NO_GO_CONTROL_FAILURE": "FAIL",
    "NO_GO_HARM_OR_FALSE_STRUCTURE": "FAIL",
    "NO_GO_NO_INDEPENDENT_GAIN": "FAIL",
    "CONDITIONAL_MIXED_EVIDENCE": "WARN",
    "INSUFFICIENT_SCOPE_FOR_GO": "INCONCLUSIVE",
    "ELIGIBLE_FOR_GO_REVIEW": "PASS",
}
ROUTE_ROLES = ("SHORT_READ_BASELINE", "CYCLONESEQ_ONLY_RESEARCH", "HYBRID")
PROHIBITED_BLIND_COLUMNS = {
    "truth",
    "expected",
    "species",
    "identity",
    "reference_label",
    "label",
    "free_text",
    "control_type",
}
PROHIBITED_PATH_TOKENS = {
    "truth",
    "expected",
    "positive_control",
    "negative_control",
    "authentic",
    "non_authentic",
}


class ContractError(ValueError):
    """Raised when a transfer-validation contract fails closed."""


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ContractError(f"JSON object required: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: dict[str, Any], omit: Iterable[str] = ()) -> str:
    canonical = {key: item for key, item in value.items() if key not in set(omit)}
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_schema(instance: dict[str, Any], schema_name: str) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - dependency failure is explicit
        raise ContractError("jsonschema is required for contract validation") from exc
    schema = load_json(SCHEMA_ROOT / schema_name)
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        messages = [f"{'/'.join(map(str, error.path)) or '<root>'}: {error.message}" for error in errors]
        raise ContractError("schema validation failed: " + " | ".join(messages))


def threshold_leaves(value: Any, prefix: str = "thresholds") -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        leaves: list[tuple[str, Any]] = []
        for key in sorted(value):
            leaves.extend(threshold_leaves(value[key], f"{prefix}.{key}"))
        return leaves
    return [(prefix, value)]


def validate_policy(policy: dict[str, Any]) -> list[str]:
    status = policy.get("status")
    thresholds = policy.get("thresholds")
    if not isinstance(thresholds, dict):
        raise ContractError("policy thresholds object is required")
    leaves = threshold_leaves(thresholds)
    if status == "engineering_test":
        header = " ".join(
            str(policy.get(key, "")) for key in ("_comment_1", "_comment_2")
        )
        required = ("临时阈值未经标定", "不得用于科学结论", "ENGINEERING-TEST ONLY")
        if any(text not in header for text in required):
            raise ContractError("engineering-test policy disclaimer is incomplete")
        if policy.get("scientific_conclusion_allowed") is not False:
            raise ContractError("engineering-test policy must prohibit scientific conclusions")
        nulls = [path for path, value in leaves if value is None]
        if nulls:
            raise ContractError("engineering-test branch fixtures require explicit values: " + ", ".join(nulls))
    elif status == "production":
        configured = [path for path, value in leaves if value is not None]
        if configured:
            raise ContractError("production placeholder thresholds must all be null: " + ", ".join(configured))
    else:
        raise ContractError(f"unsupported policy status: {status!r}")
    return [path for path, value in leaves if value is None]


def validate_protocol(
    protocol: dict[str, Any], policy: dict[str, Any], policy_sha256: str | None = None
) -> None:
    validate_schema(protocol, "transfer-protocol.schema.json")
    validate_policy(policy)
    if set(protocol["scope"]["taxa"]) != {"plant", "animal"}:
        raise ContractError("transfer protocol must declare both plant and animal scope")
    if protocol["threshold_policy"]["status"] != policy["status"]:
        raise ContractError("protocol and threshold policy status mismatch")
    null_paths = [path for path, value in threshold_leaves(policy["thresholds"]) if value is None]
    if protocol["execution_scope"] == "REAL_DATA":
        if policy["status"] != "production":
            raise ContractError("real-data protocol cannot use an engineering-test policy")
        if null_paths:
            raise ContractError("THRESHOLD_NOT_CONFIGURED: real-data protocol cannot freeze null gates")
    expected_policy_sha256 = policy_sha256 or canonical_sha256(policy)
    if protocol["policy_sha256"] != expected_policy_sha256:
        raise ContractError("protocol policy SHA256 mismatch")
    if protocol["threshold_policy"]["sha256"] != protocol["policy_sha256"]:
        raise ContractError("threshold-policy and protocol SHA256 fields differ")


def lifecycle_definition() -> dict[str, Any]:
    definition = load_json(ASSET_ROOT / "lifecycle-v0.1.json")
    if definition["pre_entry_state"] != PRE_ENTRY_STATE:
        raise ContractError("lifecycle pre-entry state drift")
    if tuple(definition["active_stages"]) != ACTIVE_STAGES:
        raise ContractError("six-stage lifecycle drift")
    return definition


def advance_lifecycle(current: str, next_state: str, artifact_sha256: str) -> dict[str, Any]:
    definition = lifecycle_definition()
    if not re.fullmatch(r"[0-9a-f]{64}", artifact_sha256):
        raise ContractError("transition artifact SHA256 is required")
    allowed = definition["allowed_transitions"].get(current)
    if allowed is None or next_state not in allowed:
        raise ContractError(f"invalid lifecycle transition: {current} -> {next_state}")
    return {
        "schema_version": "cycloneseq-lifecycle-event-v0.1",
        "from_state": current,
        "to_state": next_state,
        "artifact_sha256": artifact_sha256,
        "decision": "NOT_APPLICABLE",
    }


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _open_fastq(path: Path, compression: str):
    if compression == "GZIP":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open(encoding="utf-8")


def _fastq_ids(path: Path, compression: str) -> list[str]:
    ids: list[str] = []
    with _open_fastq(path, compression) as handle:
        while True:
            header = handle.readline()
            if not header:
                break
            sequence = handle.readline()
            plus = handle.readline()
            quality = handle.readline()
            if not (sequence and plus and quality):
                raise ContractError(f"truncated FASTQ: {path}")
            if not header.startswith("@") or not plus.startswith("+"):
                raise ContractError(f"invalid FASTQ record: {path}")
            if len(sequence.rstrip("\r\n")) != len(quality.rstrip("\r\n")):
                raise ContractError(f"FASTQ sequence/quality length mismatch: {path}")
            token = header[1:].split()[0]
            ids.append(re.sub(r"/(1|2)$", "", token))
    if not ids:
        raise ContractError(f"empty FASTQ: {path}")
    return ids


def validate_arrival(
    manifest: dict[str, Any], previous_manifest_path: Path | None = None
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        validate_schema(manifest, "arrival-manifest.schema.json")
    except ContractError as exc:
        errors.append(f"SCHEMA_INVALID:{exc}")
        return _arrival_result(errors, manifest)

    root = Path(manifest["allowlisted_root"]).expanduser().resolve()
    sample_codes: set[str] = set()
    specimen_platforms: dict[tuple[str, str], set[str]] = {}

    signature = manifest["signature"]
    if signature["signer"] != manifest["signed_by"]:
        errors.append("SIGNER_IDENTITY_MISMATCH")
    if signature["signed_payload_sha256"] != canonical_sha256(manifest, omit=("signature",)):
        errors.append("MANIFEST_SIGNATURE_SHA256_MISMATCH")

    if previous_manifest_path is not None:
        previous = load_json(previous_manifest_path)
        if manifest["manifest_id"] != previous.get("manifest_id"):
            errors.append("REPAIR_MANIFEST_ID_MISMATCH")
        if manifest["manifest_version"] <= previous.get("manifest_version", 0):
            errors.append("REPAIR_VERSION_NOT_INCREMENTED")
        if manifest.get("supersedes_manifest_sha256") != sha256_file(previous_manifest_path):
            errors.append("REPAIR_SUPERSEDES_SHA256_MISMATCH")

    for sample in manifest["samples"]:
        code = sample["sample_code"]
        if code in sample_codes:
            errors.append(f"DUPLICATE_SAMPLE_CODE:{code}")
        sample_codes.add(code)
        group = (sample["specimen_code"], sample["dna_extract_code"])
        specimen_platforms.setdefault(group, set()).add(sample["platform"])

        if sample["relationship"] == "DOCUMENTED_COMPARABLE" and not sample.get(
            "comparability_reason"
        ):
            errors.append(f"COMPARABILITY_REASON_MISSING:{code}")
        hmw = sample["hmw_qc"]
        if sample["platform"] == "CYCLONESEQ":
            if hmw["status"] != "AVAILABLE" or not hmw["method"] or not hmw["artifact_sha256"]:
                errors.append(f"HMW_QC_INCOMPLETE:{code}")

        roles: dict[str, tuple[Path, str]] = {}
        for entry in sample["files"]:
            path = Path(entry["path"]).expanduser().resolve()
            role = entry["role"]
            if role in roles:
                errors.append(f"DUPLICATE_FILE_ROLE:{code}:{role}")
                continue
            roles[role] = (path, entry["compression"])
            if not _inside(path, root):
                errors.append(f"PATH_OUTSIDE_ALLOWLIST:{code}:{role}")
                continue
            if not path.is_file():
                errors.append(f"FILE_MISSING:{code}:{role}")
                continue
            if path.stat().st_size == 0:
                errors.append(f"FILE_EMPTY:{code}:{role}")
                continue
            if path.stat().st_size != entry["size_bytes"]:
                errors.append(f"SIZE_MISMATCH:{code}:{role}")
            if sha256_file(path) != entry["sha256"]:
                errors.append(f"CHECKSUM_MISMATCH:{code}:{role}")
            try:
                _fastq_ids(path, entry["compression"])
            except (ContractError, gzip.BadGzipFile, EOFError, UnicodeDecodeError) as exc:
                errors.append(f"FASTQ_INVALID:{code}:{role}:{exc}")

        expected_roles = (
            {"LONG_READS"}
            if sample["platform"] == "CYCLONESEQ"
            else {"SHORT_READ_R1", "SHORT_READ_R2"}
        )
        if set(roles) != expected_roles:
            errors.append(f"FILE_ROLES_INVALID:{code}")
        if sample["platform"] == "DNBSEQ" and expected_roles.issubset(roles):
            try:
                r1 = _fastq_ids(*roles["SHORT_READ_R1"])
                r2 = _fastq_ids(*roles["SHORT_READ_R2"])
                if r1 != r2:
                    errors.append(f"PAIRED_READ_IDS_MISMATCH:{code}")
            except (ContractError, gzip.BadGzipFile, EOFError, UnicodeDecodeError):
                pass

    for group, platforms in specimen_platforms.items():
        if platforms != {"CYCLONESEQ", "DNBSEQ"}:
            errors.append(f"MATCHED_PLATFORM_PAIR_MISSING:{group[0]}:{group[1]}")
    return _arrival_result(errors, manifest)


def _arrival_result(errors: list[str], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    passed = not errors
    return {
        "schema_version": "cycloneseq-arrival-status-v0.1",
        "status": "PASS" if passed else "FAIL",
        "decision": "NOT_APPLICABLE",
        "arrival_state": "ARRIVAL_VALIDATED" if passed else "ARRIVAL_QUARANTINE",
        "cycloneseq": "REAL_DATA_ARRIVAL_VALIDATED" if passed else "PENDING_REAL_DATA",
        "manifest_id": None if manifest is None else manifest.get("manifest_id"),
        "manifest_version": None if manifest is None else manifest.get("manifest_version"),
        "arrival_manifest_sha256": None if manifest is None else canonical_sha256(manifest),
        "reason_codes": errors,
    }


def validate_blind_samplesheet(path: Path, allowlisted_root: Path) -> list[dict[str, str]]:
    root = allowlisted_root.expanduser().resolve()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        allowed_fields = {"sample_code", "taxon_group", "input_path", "route_role"}
        if fields != allowed_fields:
            prohibited = fields & PROHIBITED_BLIND_COLUMNS
            detail = f" prohibited={sorted(prohibited)}" if prohibited else ""
            raise ContractError(f"blind samplesheet columns must equal {sorted(allowed_fields)};{detail}")
        rows = list(reader)
    if not rows:
        raise ContractError("blind samplesheet is empty")
    seen: set[str] = set()
    for row in rows:
        code = row["sample_code"]
        if not re.fullmatch(r"BLIND-[A-Z0-9_-]+", code):
            raise ContractError(f"invalid blind sample code: {code}")
        if code in seen:
            raise ContractError(f"duplicate blind sample code: {code}")
        seen.add(code)
        if row["taxon_group"] not in {"plant", "animal"}:
            raise ContractError(f"invalid taxon group: {row['taxon_group']}")
        if row["route_role"] not in ROUTE_ROLES:
            raise ContractError(f"invalid route role: {row['route_role']}")
        data_path = Path(row["input_path"]).expanduser().resolve()
        if not _inside(data_path, root):
            raise ContractError(f"blind input path outside allowlist: {data_path}")
        lowered = str(data_path).lower()
        if any(token in lowered for token in PROHIBITED_PATH_TOKENS):
            raise ContractError(f"truth-bearing input path rejected: {data_path}")
    return rows


def finalize_result_freeze(record: dict[str, Any]) -> dict[str, Any]:
    frozen = deepcopy(record)
    frozen["record_type"] = "RESULT_FREEZE"
    frozen["result_manifest_sha256"] = canonical_sha256(
        frozen, omit=("result_manifest_sha256",)
    )
    validate_schema(frozen, "custody-freeze.schema.json")
    return frozen


def validate_unblinding(
    event: dict[str, Any], custody: dict[str, Any], freeze: dict[str, Any]
) -> None:
    validate_schema(custody, "custody-freeze.schema.json")
    validate_schema(freeze, "custody-freeze.schema.json")
    validate_schema(event, "custody-freeze.schema.json")
    expected_freeze_hash = canonical_sha256(freeze, omit=("result_manifest_sha256",))
    if freeze["result_manifest_sha256"] != expected_freeze_hash:
        raise ContractError("result freeze hash is invalid")
    if event["result_manifest_sha256"] != freeze["result_manifest_sha256"]:
        raise ContractError("unblinding event references the wrong result freeze")
    if event["truthset_sha256"] != custody["truthset_sha256"]:
        raise ContractError("unblinding event references the wrong truthset")
    if event["custodian"] != custody["custodian"]:
        raise ContractError("unblinding custodian mismatch")


def _threshold(policy: dict[str, Any], *path: str) -> Any:
    value: Any = policy["thresholds"]
    for key in path:
        value = value[key]
    return value


def _outcome_bundle(
    outcome: str,
    reason_codes: list[str],
    metrics: dict[str, Any],
    route_role: str = "HYBRID",
) -> dict[str, Any]:
    if outcome not in OUTCOMES:
        raise ContractError(f"unregistered transfer outcome: {outcome}")
    engineering_fixture = metrics.get("_policy_status") == "engineering_test"
    bundle = {
        "schema_version": "cycloneseq-transfer-evidence-v0.1",
        "status": STATUS_BY_OUTCOME[outcome],
        "decision": "NOT_APPLICABLE",
        "transfer_outcome": outcome,
        "reason_codes": sorted(set(reason_codes)),
        "cycloneseq": "PENDING_REAL_DATA"
        if engineering_fixture or outcome in {"PENDING_REAL_DATA", "ARRIVAL_BLOCKED"}
        else "REAL_DATA_ARRIVAL_VALIDATED",
        "evidence_tier": (
            "ENGINEERING_FIXTURE"
            if engineering_fixture
            else "PROTOCOL_ONLY"
            if outcome in {"PENDING_REAL_DATA", "ARRIVAL_BLOCKED"}
            else "SCIENTIFIC_TRANSFER"
        ),
        "branch_simulation": engineering_fixture,
        "scientific_conclusion_allowed": False,
        "route_role": route_role,
        "channels": ["RESEARCH_EVIDENCE"]
        if engineering_fixture or route_role == "CYCLONESEQ_ONLY_RESEARCH"
        else ["VALIDATE"],
        "governance": {
            "pmat2": "GATED_ISSUE_10",
            "mitovgp": "OUT_OF_SCOPE_UNADMITTED",
            "cycloneseq_only_terminal_decision": "PROHIBITED",
        },
        "denominators": {
            "eligible_samples": int(metrics.get("eligible_samples", 0)),
            "attempted_routes": int(metrics.get("attempted_routes", 0)),
            "declared_sequence_bases": int(metrics.get("declared_sequence_bases", 0)),
            "callable_sequence_bases": int(metrics.get("callable_sequence_bases", 0)),
            "declared_junctions": int(metrics.get("declared_junctions", 0)),
        },
        "evidence": {
            "platform": metrics.get("platform", {}),
            "sequence": metrics.get("sequence", {}),
            "structure": metrics.get("structure", {}),
            "blind_decision": metrics.get("blind_decision", {}),
            "operations": metrics.get("operations", {}),
        },
    }
    validate_output_isolation(bundle)
    return bundle


def evaluate_outcome(
    policy: dict[str, Any], metrics: dict[str, Any], route_role: str = "HYBRID"
) -> dict[str, Any]:
    validate_policy(policy)
    metrics = {**metrics, "_policy_status": policy["status"]}
    if not metrics.get("real_data_present", False):
        return _outcome_bundle("PENDING_REAL_DATA", ["REAL_DATA_NOT_PRESENT"], metrics, route_role)
    if not metrics.get("arrival_valid", False):
        return _outcome_bundle("ARRIVAL_BLOCKED", ["ARRIVAL_GATE_FAILED"], metrics, route_role)
    if policy["status"] == "production":
        return _outcome_bundle(
            "INCONCLUSIVE_NOT_EVALUABLE", ["THRESHOLD_NOT_CONFIGURED"], metrics, route_role
        )
    if not metrics.get("blinding_valid", False):
        return _outcome_bundle(
            "INCONCLUSIVE_NOT_EVALUABLE", ["BLINDING_INVALIDATED"], metrics, route_role
        )
    if not metrics.get("qc_evaluable", False) or metrics.get("callable_fraction", 0.0) < _threshold(
        policy, "quality", "min_callable_fraction"
    ) or metrics.get("route_failure_fraction", 1.0) > _threshold(
        policy, "quality", "max_route_failure_fraction"
    ):
        return _outcome_bundle(
            "INCONCLUSIVE_NOT_EVALUABLE", ["QUALITY_OR_CALLABILITY_INSUFFICIENT"], metrics, route_role
        )
    if metrics.get("failed_controls", 0) > _threshold(policy, "controls", "max_failed_controls"):
        return _outcome_bundle(
            "NO_GO_CONTROL_FAILURE", ["CONTROL_BOUNDARY_VIOLATED"], metrics, route_role
        )
    if metrics.get("unsupported_false_structures", 0) > _threshold(
        policy, "harm", "max_unsupported_false_structures"
    ) or metrics.get("residual_error_regression_per_10kb", 0.0) > _threshold(
        policy, "harm", "max_residual_error_regression_per_10kb"
    ):
        return _outcome_bundle(
            "NO_GO_HARM_OR_FALSE_STRUCTURE", ["HARM_BOUNDARY_VIOLATED"], metrics, route_role
        )
    if metrics.get("incremental_resolved_samples", 0) < _threshold(
        policy, "gain", "min_incremental_resolved_samples"
    ) or metrics.get("incremental_gain_fraction", 0.0) < _threshold(
        policy, "gain", "min_incremental_gain_fraction"
    ):
        return _outcome_bundle(
            "NO_GO_NO_INDEPENDENT_GAIN", ["INDEPENDENT_GAIN_NOT_MET"], metrics, route_role
        )
    if metrics.get("mixed_evidence", False):
        return _outcome_bundle(
            "CONDITIONAL_MIXED_EVIDENCE", ["NON_DOMINATING_GAINS_AND_REGRESSIONS"], metrics, route_role
        )

    scope_ok = all(
        (
            metrics.get("eligible_plant_samples", 0)
            >= _threshold(policy, "scope", "min_eligible_plant_samples"),
            metrics.get("eligible_animal_samples", 0)
            >= _threshold(policy, "scope", "min_eligible_animal_samples"),
            metrics.get("independent_batches", 0)
            >= _threshold(policy, "scope", "min_independent_batches"),
            metrics.get("orthogonal_validation_samples", 0)
            >= _threshold(policy, "scope", "min_orthogonal_validation_samples"),
            metrics.get("replicate_concordance_fraction", 0.0)
            >= _threshold(policy, "reproducibility", "min_replicate_concordance_fraction"),
            metrics.get("compute_time_multiplier", float("inf"))
            <= _threshold(policy, "operations", "max_compute_time_multiplier"),
            metrics.get("storage_multiplier", float("inf"))
            <= _threshold(policy, "operations", "max_storage_multiplier"),
        )
    )
    if not scope_ok:
        return _outcome_bundle(
            "INSUFFICIENT_SCOPE_FOR_GO", ["SCOPE_REPRODUCIBILITY_OR_RESOURCE_GATE_NOT_MET"], metrics, route_role
        )
    return _outcome_bundle(
        "ELIGIBLE_FOR_GO_REVIEW", ["ALL_ENGINEERING_FIXTURE_GATES_MET"], metrics, route_role
    )


def validate_output_isolation(bundle: dict[str, Any]) -> None:
    validate_schema(bundle, "evidence-outcome.schema.json")
    if bundle["decision"] != "NOT_APPLICABLE":
        raise ContractError("transfer evidence cannot emit an authentication decision")
    if bundle["scientific_conclusion_allowed"] is not False:
        raise ContractError("transfer evidence cannot self-authorize a scientific conclusion")
    if {"IDENTIFY", "DECISION"} & set(bundle["channels"]):
        raise ContractError("CycloneSEQ transfer evidence entered a prohibited channel")
    if bundle["route_role"] == "CYCLONESEQ_ONLY_RESEARCH" and bundle["channels"] != [
        "RESEARCH_EVIDENCE"
    ]:
        raise ContractError("CycloneSEQ-only output must remain research evidence")
    if bundle["evidence_tier"] == "ENGINEERING_FIXTURE":
        if not bundle["branch_simulation"]:
            raise ContractError("engineering fixture must be labelled as branch simulation")
        if bundle["cycloneseq"] != "PENDING_REAL_DATA":
            raise ContractError("engineering fixture cannot advance CycloneSEQ scientific state")
        if bundle["channels"] != ["RESEARCH_EVIDENCE"]:
            raise ContractError("engineering fixture must remain research evidence")
    if bundle["evidence_tier"] == "PROTOCOL_ONLY" and bundle["cycloneseq"] != "PENDING_REAL_DATA":
        raise ContractError("protocol-only evidence cannot advance CycloneSEQ scientific state")
    if bundle["governance"] != {
        "pmat2": "GATED_ISSUE_10",
        "mitovgp": "OUT_OF_SCOPE_UNADMITTED",
        "cycloneseq_only_terminal_decision": "PROHIBITED",
    }:
        raise ContractError("optional-tool or decision isolation drift")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    arrival = subparsers.add_parser("arrival")
    arrival.add_argument("--manifest", type=Path, required=True)
    arrival.add_argument("--previous-manifest", type=Path)
    arrival.add_argument("--output", type=Path, required=True)

    transition = subparsers.add_parser("transition")
    transition.add_argument("--current", required=True)
    transition.add_argument("--next-state", required=True)
    transition.add_argument("--artifact-sha256", required=True)
    transition.add_argument("--output", type=Path, required=True)

    blind = subparsers.add_parser("blind")
    blind.add_argument("--samplesheet", type=Path, required=True)
    blind.add_argument("--allowlisted-root", type=Path, required=True)

    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--record", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)

    unblind = subparsers.add_parser("unblind")
    unblind.add_argument("--event", type=Path, required=True)
    unblind.add_argument("--custody", type=Path, required=True)
    unblind.add_argument("--freeze", type=Path, required=True)

    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--policy", type=Path, required=True)
    evaluate.add_argument("--metrics", type=Path, required=True)
    evaluate.add_argument("--route-role", choices=ROUTE_ROLES, default="HYBRID")
    evaluate.add_argument("--output", type=Path, required=True)

    isolation = subparsers.add_parser("isolation")
    isolation.add_argument("--bundle", type=Path, required=True)

    protocol = subparsers.add_parser("protocol")
    protocol.add_argument("--record", type=Path, required=True)
    protocol.add_argument("--policy", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "arrival":
        result = validate_arrival(load_json(args.manifest), args.previous_manifest)
        write_json(args.output, result)
    elif args.command == "transition":
        write_json(
            args.output,
            advance_lifecycle(args.current, args.next_state, args.artifact_sha256),
        )
    elif args.command == "blind":
        validate_blind_samplesheet(args.samplesheet, args.allowlisted_root)
    elif args.command == "freeze":
        write_json(args.output, finalize_result_freeze(load_json(args.record)))
    elif args.command == "unblind":
        validate_unblinding(load_json(args.event), load_json(args.custody), load_json(args.freeze))
    elif args.command == "evaluate":
        write_json(
            args.output,
            evaluate_outcome(load_json(args.policy), load_json(args.metrics), args.route_role),
        )
    elif args.command == "isolation":
        validate_output_isolation(load_json(args.bundle))
    elif args.command == "protocol":
        validate_protocol(
            load_json(args.record), load_json(args.policy), sha256_file(args.policy)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
