## Context

The canonical `validation-and-go-no-go` spec already separates engineering and scientific validation, forbids validation-set retuning, and requires independent long-read gain. M3/M4 provide ONT/public-data baselines but explicitly leave CycloneSEQ `PENDING_REAL_DATA`. This design turns the future real-data study into a staged, auditable protocol without yet running it or inventing numeric scientific thresholds.

## Goals / Non-Goals

**Goals:**

- Make data arrival, blinding, protocol freeze, execution, unblinding, and owner review separate machine-visible states.
- Freeze all result-sensitive rules before scientific outcomes are accessible.
- Compare short-read, CycloneSEQ-only research, and hybrid routes on matched eligible samples with explicit denominators.
- Pre-write negative and inconclusive branches so that lack of gain or harmful evidence cannot be narrated away.

**Non-Goals:**

- Executing real data, qualifying CycloneSEQ, setting production thresholds, or issuing GO in this proposal.
- Reusing ONT Q thresholds/models as CycloneSEQ facts.
- Changing M3/M4 archives, authentication routing, PMAT2 Issue #10, or mitoVGP admission.

## Decisions

### 1. Use a six-state gated lifecycle

The implementation state machine will be:

```text
PENDING_REAL_DATA
  → ARRIVAL_QUARANTINE
  → ARRIVAL_VALIDATED
  → PROTOCOL_FROZEN
  → BLINDED_RESULTS_FROZEN
  → UNBLINDED_EVALUATION
  → OWNER_GO_NO_GO_REVIEW
```

Each transition requires a checksum-able artifact and fails closed. Skipping a state invalidates confirmatory interpretation. `OWNER_GO_NO_GO_REVIEW` means only that evidence is eligible for human review, never automatic GO.

### 2. Treat the signed delivery manifest as arrival authority

Before reading scientific content, a deterministic preflight will compare delivered files and metadata to a signed/approved manifest. It will record sample code, specimen/DNA relationship, role, platform, library preparation, sequencing and basecalling identifiers/versions, batch, declared files, expected sizes/checksums, and HMW/QC metadata. FASTQ format/compression, non-emptiness, pairing, read-name compatibility, and checksum checks are machine tasks.

Arrival failures yield precise operational reason codes and do not enter performance denominators. A repaired delivery becomes a new manifest version; it never silently replaces the failed package.

### 3. Separate truth custody from analysis

The analysis owner receives coded sample IDs only. The truth custodian holds `truthset.csv` outside analysis-visible paths and does not tune or run the workflow. Before unblinding, the validation/evidence owner freezes:

- sample-level candidates, evidence/status JSON, exclusions, and route failures;
- tool/container/reference/policy/input manifests and commands;
- metric numerators/denominators that do not require truth;
- deviations and missing evidence;
- a top-level result-manifest SHA256.

Unblinding records both truthset and result-manifest hashes. Any truth leak or post-unblinding tuning moves the affected evidence to `BLINDING_INVALIDATED`; it may become exploratory but not confirmatory.

### 4. Register scope and thresholds without fabricating numbers

This proposal fixes metric names, evidence semantics, and outcome branches. Numeric pass/harm thresholds, minimum sample/batch scope, acceptable failure/resource bounds, and orthogonal-validation quotas remain explicit nulls until an owner-reviewed protocol revision can justify them before outcome access. Production execution must fail fast on null required gates rather than substitute defaults.

The real protocol must declare at least one eligible plant scope and one eligible animal scope, matched or documented-comparable DNBSEQ/CycloneSEQ evidence, batch/individual roles, and any discovery versus independent validation partition. A small feasibility pilot may yield method evidence but cannot claim broad production GO unless it satisfies the pre-frozen scope gate.

### 5. Use three fixed evidence roles, not tool-driven arm expansion

The conceptual comparison is:

- short-read baseline;
- CycloneSEQ-only research evidence (never terminal decision);
- hybrid long-read backbone/structure plus short-read sequence support.

Exact executable routes and frozen candidates will be specified in the apply-stage protocol using already admitted baselines. Optional tools cannot add arms mid-run. Any new tool hypothesis requires a change revision before outcome access.

### 6. Keep platform, structure, and decision evidence separate

The result schema will distinguish:

- platform/read evidence: length, yield, Q calibration, identity/error spectrum;
- sequence evidence: callable bases, supported edits, homopolymer/AT-rich behavior;
- structure evidence: junction-spanning independent reads and false structures;
- decision evidence: blind truth comparison and incremental resolution over short-read baseline;
- operations: failure, compute, storage, review time, reproducibility.

No reference disagreement is automatically an error; sample read evidence and declared orthogonal evidence arbitrate. Non-callable regions do not vanish from denominators.

### 7. Freeze a deterministic negative-outcome table

The apply-stage protocol will encode this precedence before unblinding:

1. no real data → `PENDING_REAL_DATA`;
2. delivery identity/integrity failure → `ARRIVAL_BLOCKED`;
3. valid delivery but insufficient callable/QC evidence → `INCONCLUSIVE_NOT_EVALUABLE`;
4. negative/contamination control violates its frozen boundary → `NO_GO_CONTROL_FAILURE`;
5. harm/unsupported false structure crosses its frozen boundary → `NO_GO_HARM_OR_FALSE_STRUCTURE`;
6. no frozen independent gain over short-read baseline → `NO_GO_NO_INDEPENDENT_GAIN`;
7. mixed non-dominating gains/regressions → `CONDITIONAL_MIXED_EVIDENCE`;
8. evidence quality passes but declared scope is incomplete → `INSUFFICIENT_SCOPE_FOR_GO`;
9. every frozen gate passes → `ELIGIBLE_FOR_GO_REVIEW`.

These labels are `transfer_outcome` reason codes, not new machine-status values: `status` remains restricted to `PASS|WARN|FAIL|INCONCLUSIVE`, and `decision=NOT_APPLICABLE`. Higher-priority negative branches cannot be overruled by a favorable lower-priority metric after results are seen. Final GO/NO-GO remains an owner decision in a separate change.

### 8. Preserve existing red lines

Until real data pass the lifecycle, CycloneSEQ remains `PENDING_REAL_DATA`; outputs remain outside `IDENTIFY`/`DECISION`; pure CycloneSEQ stays research-only. PMAT2 is not executed while Issue #10 is open. mitoVGP remains unadmitted and out of scope. No historical worktree or `runs/` evidence is deleted or moved.

## Risks / Trade-offs

- [Risk] Sample or truth identity leaks through filenames/metadata. → Use coded delivery names, allow-listed metadata schema, custodian review, and leakage tests before analysis.
- [Risk] Threshold nulls delay execution when data arrive. → This is intentional fail-closed governance; fill them only through owner-reviewed pre-outcome protocol revision.
- [Risk] Matched DNA is unavailable. → Require documented comparability and classify scope limitations before execution; do not silently claim paired transfer.
- [Risk] Small sample counts produce enticing but weak gains. → Separate feasibility evidence from scope eligibility and pre-write `INSUFFICIENT_SCOPE_FOR_GO`.
- [Risk] Reference concordance favors the wrong biological sequence. → Keep references proxy-only and require read/orthogonal adjudication for disputed sites/structures.
- [Risk] Optional assembler evaluation expands indefinitely. → Core roles are capability-based; new tools require their own admission/revision and cannot block the core study.

## Migration Plan

1. Review and approve this proposal-only change while CycloneSEQ remains `PENDING_REAL_DATA`.
2. After approval, implement schemas/state records and engineering fixtures without claiming scientific transfer.
3. When a signed real-data arrival package exists, open a data-bearing protocol revision to fill justified null thresholds/scope before outcome access.
4. Execute blinded analysis, freeze results, unblind, and emit one pre-written outcome.
5. Only `ELIGIBLE_FOR_GO_REVIEW` may start a separate owner-reviewed Go/No-Go change.

Rollback of planning artifacts changes no data or scientific state.
