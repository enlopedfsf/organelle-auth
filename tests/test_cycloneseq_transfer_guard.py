import csv
import gzip
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "cycloneseq_transfer_guard.py"
SPEC = importlib.util.spec_from_file_location("cycloneseq_transfer_guard", SCRIPT)
GUARD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GUARD)

ENGINEERING_POLICY = (
    ROOT
    / "assets/policies/cycloneseq-transfer-validation/engineering-test-v0.1.json"
)
PRODUCTION_POLICY = (
    ROOT
    / "assets/policies/cycloneseq-transfer-validation/production-null-v0.1.json"
)
SCENARIOS = ROOT / "tests/fixtures/cycloneseq_transfer/outcome-scenarios.json"
HASH = "a" * 64


def write_fastq(path: Path, names=("read1", "read2")) -> None:
    records = []
    for name in names:
        records.extend((f"@{name}", "ACGT", "+", "IIII"))
    path.write_text("\n".join(records) + "\n", encoding="utf-8")


def file_record(path: Path, role: str) -> dict:
    return {
        "role": role,
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": GUARD.sha256_file(path),
        "format": "FASTQ",
        "compression": "NONE",
    }


def valid_arrival(tmp_path: Path) -> tuple[dict, dict[str, Path]]:
    data = tmp_path / "coded_data"
    data.mkdir(parents=True)
    long_reads = data / "BLIND-A.long.fastq"
    r1 = data / "BLIND-A.R1.fastq"
    r2 = data / "BLIND-A.R2.fastq"
    write_fastq(long_reads)
    write_fastq(r1, ("pair1/1", "pair2/1"))
    write_fastq(r2, ("pair1/2", "pair2/2"))
    common = {
        "taxon_group": "plant",
        "specimen_code": "SPEC-A",
        "dna_extract_code": "DNA-A",
        "relationship": "MATCHED_DNA",
        "comparability_reason": None,
        "batch_code": "BATCH-A",
        "library_protocol": "CODED-PROTOCOL",
        "sequencing_software": "CODED-SOFTWARE-1",
        "basecaller": "CODED-BASECALLER-1",
    }
    manifest = {
        "schema_version": "cycloneseq-arrival-manifest-v0.1",
        "manifest_id": "delivery-A",
        "manifest_version": 1,
        "supersedes_manifest_sha256": None,
        "signed_by": "delivery-owner",
        "signed_at": "2026-08-14T12:00:00+08:00",
        "signature": {
            "method": "OWNER_ATTESTATION_SHA256",
            "signer": "delivery-owner",
            "signed_payload_sha256": HASH,
        },
        "allowlisted_root": str(data),
        "samples": [
            {
                **common,
                "sample_code": "BLIND-A-LR",
                "platform": "CYCLONESEQ",
                "hmw_qc": {
                    "status": "AVAILABLE",
                    "method": "CODED-HMW-QC",
                    "artifact_sha256": HASH,
                    "missing_reason": None,
                },
                "files": [file_record(long_reads, "LONG_READS")],
            },
            {
                **common,
                "sample_code": "BLIND-A-SR",
                "platform": "DNBSEQ",
                "hmw_qc": {
                    "status": "NOT_APPLICABLE",
                    "method": None,
                    "artifact_sha256": None,
                    "missing_reason": None,
                },
                "files": [
                    file_record(r1, "SHORT_READ_R1"),
                    file_record(r2, "SHORT_READ_R2"),
                ],
            },
        ],
    }
    manifest["signature"]["signed_payload_sha256"] = GUARD.canonical_sha256(
        manifest, omit=("signature",)
    )
    return manifest, {"long": long_reads, "r1": r1, "r2": r2, "root": data}


def test_lifecycle_has_pre_entry_plus_exactly_six_active_stages():
    definition = GUARD.lifecycle_definition()
    assert definition["pre_entry_state"] == "PENDING_REAL_DATA"
    assert len(definition["active_stages"]) == 6
    current = definition["pre_entry_state"]
    for next_state in definition["active_stages"]:
        event = GUARD.advance_lifecycle(current, next_state, HASH)
        assert event["from_state"] == current
        assert event["to_state"] == next_state
        assert event["decision"] == "NOT_APPLICABLE"
        current = next_state


def test_lifecycle_skips_and_automatic_go_fail_closed():
    with pytest.raises(GUARD.ContractError, match="invalid lifecycle transition"):
        GUARD.advance_lifecycle("PENDING_REAL_DATA", "PROTOCOL_FROZEN", HASH)
    with pytest.raises(GUARD.ContractError, match="invalid lifecycle transition"):
        GUARD.advance_lifecycle("OWNER_GO_NO_GO_REVIEW", "GO", HASH)


def test_policy_separation_and_production_null_contract():
    engineering = GUARD.load_json(ENGINEERING_POLICY)
    production = GUARD.load_json(PRODUCTION_POLICY)
    assert GUARD.validate_policy(engineering) == []
    null_paths = GUARD.validate_policy(production)
    assert len(null_paths) == 14
    assert all(value is None for _, value in GUARD.threshold_leaves(production["thresholds"]))
    assert "临时阈值未经标定" in engineering["_comment_1"]
    assert "不得用于科学结论" in engineering["_comment_1"]


def test_arrival_validates_integrity_pairing_provenance_and_matched_platforms(tmp_path):
    manifest, _ = valid_arrival(tmp_path)
    result = GUARD.validate_arrival(manifest)
    assert result == {
        "schema_version": "cycloneseq-arrival-status-v0.1",
        "status": "PASS",
        "decision": "NOT_APPLICABLE",
        "arrival_state": "ARRIVAL_VALIDATED",
        "cycloneseq": "REAL_DATA_ARRIVAL_VALIDATED",
        "manifest_id": "delivery-A",
        "manifest_version": 1,
        "arrival_manifest_sha256": GUARD.canonical_sha256(manifest),
        "reason_codes": [],
    }


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("empty", "FILE_EMPTY"),
        ("truncated", "FASTQ_INVALID"),
        ("checksum", "CHECKSUM_MISMATCH"),
        ("swapped_mates", "PAIRED_READ_IDS_MISMATCH"),
        ("duplicate_id", "DUPLICATE_SAMPLE_CODE"),
        ("identity", "MATCHED_PLATFORM_PAIR_MISSING"),
        ("missing_hmw", "HMW_QC_INCOMPLETE"),
        ("missing_provenance", "SCHEMA_INVALID"),
    ],
)
def test_arrival_failure_fixtures_fail_closed(tmp_path, mutation, reason):
    manifest, paths = valid_arrival(tmp_path)
    if mutation == "empty":
        paths["long"].write_text("")
    elif mutation == "truncated":
        paths["long"].write_text("@read1\nACGT\n+\n")
    elif mutation == "checksum":
        manifest["samples"][0]["files"][0]["sha256"] = "b" * 64
    elif mutation == "swapped_mates":
        write_fastq(paths["r2"], ("other1/2", "other2/2"))
        record = manifest["samples"][1]["files"][1]
        record.update(file_record(paths["r2"], "SHORT_READ_R2"))
    elif mutation == "duplicate_id":
        manifest["samples"][1]["sample_code"] = manifest["samples"][0]["sample_code"]
    elif mutation == "identity":
        manifest["samples"][1]["dna_extract_code"] = "DNA-B"
    elif mutation == "missing_hmw":
        manifest["samples"][0]["hmw_qc"]["status"] = "MISSING"
        manifest["samples"][0]["hmw_qc"]["method"] = None
        manifest["samples"][0]["hmw_qc"]["artifact_sha256"] = None
        manifest["samples"][0]["hmw_qc"]["missing_reason"] = "not delivered"
    elif mutation == "missing_provenance":
        del manifest["samples"][0]["basecaller"]
    result = GUARD.validate_arrival(manifest)
    assert result["status"] == "FAIL"
    assert result["cycloneseq"] == "PENDING_REAL_DATA"
    assert any(code.startswith(reason) for code in result["reason_codes"])


def test_repaired_delivery_requires_new_version_and_previous_hash(tmp_path):
    previous, _ = valid_arrival(tmp_path)
    previous_path = tmp_path / "previous.json"
    previous_path.write_text(json.dumps(previous), encoding="utf-8")
    repaired = deepcopy(previous)
    repaired["manifest_version"] = 2
    repaired["supersedes_manifest_sha256"] = GUARD.sha256_file(previous_path)
    repaired["signature"]["signed_payload_sha256"] = GUARD.canonical_sha256(
        repaired, omit=("signature",)
    )
    assert GUARD.validate_arrival(repaired, previous_path)["status"] == "PASS"
    repaired["manifest_version"] = 1
    result = GUARD.validate_arrival(repaired, previous_path)
    assert "REPAIR_VERSION_NOT_INCREMENTED" in result["reason_codes"]


def test_gzip_integrity_and_manifest_signature_are_machine_checked(tmp_path):
    manifest, paths = valid_arrival(tmp_path)
    compressed = paths["root"] / "BLIND-A.long.fastq.gz"
    with paths["long"].open("rb") as source, gzip.open(compressed, "wb") as target:
        target.write(source.read())
    manifest["samples"][0]["files"] = [
        {
            **file_record(compressed, "LONG_READS"),
            "compression": "GZIP",
        }
    ]
    manifest["signature"]["signed_payload_sha256"] = GUARD.canonical_sha256(
        manifest, omit=("signature",)
    )
    assert GUARD.validate_arrival(manifest)["status"] == "PASS"

    compressed.write_bytes(compressed.read_bytes()[:12])
    result = GUARD.validate_arrival(manifest)
    assert result["status"] == "FAIL"
    assert any(code.startswith("FASTQ_INVALID") for code in result["reason_codes"])

    manifest, _ = valid_arrival(tmp_path / "signature-case")
    manifest["samples"][0]["batch_code"] = "TAMPERED"
    result = GUARD.validate_arrival(manifest)
    assert "MANIFEST_SIGNATURE_SHA256_MISMATCH" in result["reason_codes"]


def test_arrival_path_outside_allowlist_fails_closed(tmp_path):
    manifest, paths = valid_arrival(tmp_path)
    outside = tmp_path / "outside.fastq"
    write_fastq(outside)
    manifest["samples"][0]["files"] = [file_record(outside, "LONG_READS")]
    manifest["signature"]["signed_payload_sha256"] = GUARD.canonical_sha256(
        manifest, omit=("signature",)
    )
    result = GUARD.validate_arrival(manifest)
    assert any(code.startswith("PATH_OUTSIDE_ALLOWLIST") for code in result["reason_codes"])


def test_blind_samplesheet_accepts_only_coded_allowlisted_fields(tmp_path):
    data = tmp_path / "coded_data"
    data.mkdir()
    input_path = data / "BLIND-A.fastq"
    write_fastq(input_path)
    samplesheet = tmp_path / "blind.csv"
    with samplesheet.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["sample_code", "taxon_group", "input_path", "route_role"]
        )
        writer.writeheader()
        writer.writerow(
            {
                "sample_code": "BLIND-A",
                "taxon_group": "plant",
                "input_path": str(input_path),
                "route_role": "HYBRID",
            }
        )
    assert len(GUARD.validate_blind_samplesheet(samplesheet, data)) == 1


def test_truth_bearing_blind_column_and_path_are_rejected(tmp_path):
    data = tmp_path / "coded_data"
    data.mkdir()
    samplesheet = tmp_path / "leak.csv"
    samplesheet.write_text(
        "sample_code,taxon_group,input_path,route_role,expected\n"
        f"BLIND-A,plant,{data / 'BLIND-A.fastq'},HYBRID,authentic\n",
        encoding="utf-8",
    )
    with pytest.raises(GUARD.ContractError, match="prohibited=.*expected"):
        GUARD.validate_blind_samplesheet(samplesheet, data)


def test_result_freeze_hash_must_precede_authorized_unblinding():
    custody = {
        "record_type": "TRUTH_CUSTODY",
        "custodian": "truth-owner",
        "truthset_path": "/custody/truthset.csv",
        "truthset_sha256": "b" * 64,
        "analysis_access": "DENIED_UNTIL_RESULT_FREEZE",
        "access_log": [
            {
                "actor": "truth-owner",
                "action": "CUSTODY_CREATED",
                "timestamp": "2026-08-14T12:00:00+08:00",
            }
        ],
    }
    freeze = GUARD.finalize_result_freeze(
        {
            "owner": "evidence-owner",
            "frozen_at": "2026-08-14T12:30:00+08:00",
            "sample_results": [{"sample_code": "BLIND-A", "status": "INCONCLUSIVE"}],
            "exclusions": [],
            "deviations": [],
            "commands": ["synthetic-fixture-command"],
            "input_manifest_sha256": HASH,
        }
    )
    event = {
        "record_type": "UNBLINDING_EVENT",
        "authorized_by": "validation-owner",
        "custodian": "truth-owner",
        "unblinded_at": "2026-08-14T13:00:00+08:00",
        "truthset_sha256": custody["truthset_sha256"],
        "result_manifest_sha256": freeze["result_manifest_sha256"],
        "evaluation_command": "synthetic-unblind-evaluate",
    }
    GUARD.validate_unblinding(event, custody, freeze)
    freeze["sample_results"].append({"sample_code": "BLIND-B", "status": "PASS"})
    with pytest.raises(GUARD.ContractError, match="result freeze hash is invalid"):
        GUARD.validate_unblinding(event, custody, freeze)


def test_all_nine_outcome_branches_are_pre_registered_and_deterministic():
    fixture = GUARD.load_json(SCENARIOS)
    policy = GUARD.load_json(ENGINEERING_POLICY)
    observed = []
    for scenario in fixture["scenarios"]:
        metrics = {**fixture["base_metrics"], **scenario["override"]}
        first = GUARD.evaluate_outcome(policy, metrics)
        second = GUARD.evaluate_outcome(policy, metrics)
        assert first == second
        assert first["transfer_outcome"] == scenario["expected"]
        assert first["decision"] == "NOT_APPLICABLE"
        assert first["evidence_tier"] == "ENGINEERING_FIXTURE"
        assert first["branch_simulation"] is True
        assert first["scientific_conclusion_allowed"] is False
        assert first["cycloneseq"] == "PENDING_REAL_DATA"
        observed.append(first["transfer_outcome"])
    assert tuple(observed) == GUARD.OUTCOMES


def test_production_null_yields_threshold_not_configured_without_fallback():
    fixture = GUARD.load_json(SCENARIOS)
    result = GUARD.evaluate_outcome(GUARD.load_json(PRODUCTION_POLICY), fixture["base_metrics"])
    assert result["status"] == "INCONCLUSIVE"
    assert result["transfer_outcome"] == "INCONCLUSIVE_NOT_EVALUABLE"
    assert result["reason_codes"] == ["THRESHOLD_NOT_CONFIGURED"]


def test_no_data_production_state_is_protocol_only_and_pending():
    fixture = GUARD.load_json(SCENARIOS)
    result = GUARD.evaluate_outcome(
        GUARD.load_json(PRODUCTION_POLICY),
        {**fixture["base_metrics"], "real_data_present": False},
        route_role="CYCLONESEQ_ONLY_RESEARCH",
    )
    assert result["evidence_tier"] == "PROTOCOL_ONLY"
    assert result["cycloneseq"] == "PENDING_REAL_DATA"
    assert result["scientific_conclusion_allowed"] is False
    assert result["transfer_outcome"] == "PENDING_REAL_DATA"


def test_blinding_breach_is_explicitly_inconclusive_and_invalidated():
    fixture = GUARD.load_json(SCENARIOS)
    result = GUARD.evaluate_outcome(
        GUARD.load_json(ENGINEERING_POLICY),
        {**fixture["base_metrics"], "blinding_valid": False},
    )
    assert result["status"] == "INCONCLUSIVE"
    assert result["transfer_outcome"] == "INCONCLUSIVE_NOT_EVALUABLE"
    assert result["reason_codes"] == ["BLINDING_INVALIDATED"]


def test_output_isolation_and_optional_tool_gates_are_machine_asserted():
    fixture = GUARD.load_json(SCENARIOS)
    bundle = GUARD.evaluate_outcome(
        GUARD.load_json(ENGINEERING_POLICY),
        {**fixture["base_metrics"], "real_data_present": False},
        route_role="CYCLONESEQ_ONLY_RESEARCH",
    )
    assert bundle["channels"] == ["RESEARCH_EVIDENCE"]
    assert bundle["decision"] == "NOT_APPLICABLE"
    assert bundle["governance"]["pmat2"] == "GATED_ISSUE_10"
    assert bundle["governance"]["mitovgp"] == "OUT_OF_SCOPE_UNADMITTED"
    GUARD.validate_output_isolation(bundle)
    bundle["channels"] = ["IDENTIFY"]
    with pytest.raises(GUARD.ContractError):
        GUARD.validate_output_isolation(bundle)


def test_protocol_schema_requires_frozen_roles_hashes_and_both_taxa():
    protocol = {
        "schema_version": "cycloneseq-transfer-protocol-v0.1",
        "protocol_id": "engineering-fixture-protocol",
        "version": "0.1.0",
        "owner": "validation-owner",
        "status": "FROZEN",
        "execution_scope": "ENGINEERING_FIXTURE",
        "scope": {
            "taxa": ["plant", "animal"],
            "sample_roles": ["feasibility"],
            "batches": ["BATCH-A"],
            "discovery_validation_partition": "synthetic-only",
        },
        "route_roles": ["SHORT_READ_BASELINE", "CYCLONESEQ_ONLY_RESEARCH", "HYBRID"],
        "metrics": ["callable_fraction", "incremental_gain_fraction"],
        "denominators": {"eligible_samples": "all arrival-valid coded samples"},
        "threshold_policy": {
            "path": str(ENGINEERING_POLICY.relative_to(ROOT)),
            "sha256": GUARD.sha256_file(ENGINEERING_POLICY),
            "status": "engineering_test",
        },
        "orthogonal_evidence": {"required": True},
        "versions": {"guard": "0.1.0"},
        "input_manifest_sha256": HASH,
        "policy_sha256": GUARD.sha256_file(ENGINEERING_POLICY),
    }
    GUARD.validate_protocol(
        protocol, GUARD.load_json(ENGINEERING_POLICY), GUARD.sha256_file(ENGINEERING_POLICY)
    )
    protocol["scope"]["taxa"] = ["plant"]
    with pytest.raises(GUARD.ContractError, match="both plant and animal"):
        GUARD.validate_protocol(
            protocol, GUARD.load_json(ENGINEERING_POLICY), GUARD.sha256_file(ENGINEERING_POLICY)
        )


def test_real_data_protocol_cannot_use_engineering_or_null_production_policy():
    engineering = GUARD.load_json(ENGINEERING_POLICY)
    protocol = {
        "schema_version": "cycloneseq-transfer-protocol-v0.1",
        "protocol_id": "real-data-protocol",
        "version": "0.1.0",
        "owner": "validation-owner",
        "status": "FROZEN",
        "execution_scope": "REAL_DATA",
        "scope": {
            "taxa": ["plant", "animal"],
            "sample_roles": ["validation"],
            "batches": ["BATCH-A"],
            "discovery_validation_partition": "pre-registered",
        },
        "route_roles": ["SHORT_READ_BASELINE", "CYCLONESEQ_ONLY_RESEARCH", "HYBRID"],
        "metrics": ["callable_fraction"],
        "denominators": {"eligible_samples": "arrival-valid coded samples"},
        "threshold_policy": {
            "path": str(ENGINEERING_POLICY.relative_to(ROOT)),
            "sha256": GUARD.sha256_file(ENGINEERING_POLICY),
            "status": "engineering_test",
        },
        "orthogonal_evidence": {"required": True},
        "versions": {"guard": "0.1.0"},
        "input_manifest_sha256": HASH,
        "policy_sha256": GUARD.sha256_file(ENGINEERING_POLICY),
    }
    with pytest.raises(GUARD.ContractError, match="cannot use an engineering-test"):
        GUARD.validate_protocol(protocol, engineering, GUARD.sha256_file(ENGINEERING_POLICY))

    production = GUARD.load_json(PRODUCTION_POLICY)
    protocol["threshold_policy"] = {
        "path": str(PRODUCTION_POLICY.relative_to(ROOT)),
        "sha256": GUARD.sha256_file(PRODUCTION_POLICY),
        "status": "production",
    }
    protocol["policy_sha256"] = GUARD.sha256_file(PRODUCTION_POLICY)
    with pytest.raises(GUARD.ContractError, match="THRESHOLD_NOT_CONFIGURED"):
        GUARD.validate_protocol(protocol, production, GUARD.sha256_file(PRODUCTION_POLICY))
