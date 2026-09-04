## Why

M3 and M4 established ONT/public-data engineering baselines, but they cannot validate CycloneSEQ chemistry, error calibration, structural evidence, or incremental value. A result-blind, arrival-gated protocol must be frozen before real paired CycloneSEQ data are inspected so that transfer and Go/No-Go conclusions cannot be selected after observing outcomes.

## What Changes

- Add a versioned CycloneSEQ transfer-validation protocol covering matched plant and animal DNBSEQ/CycloneSEQ inputs, provenance, error spectra, callable sequence, structural evidence, resources, failure rate, and incremental gain.
- Add a fail-closed data-arrival gate that verifies file identity/integrity and specimen/platform provenance before any scientific analysis; absent real data remains `PENDING_REAL_DATA`.
- Add explicit blind-sample custody, analysis/truth separation, pre-unblinding result freeze, authorized unblinding, and deviation invalidation rules.
- Pre-write all negative branches: absent data, arrival failure, non-evaluable platform/QC, no independent gain, harmful regression/false structure, mixed evidence, and insufficient validation scope. None may be rewritten after results are known.
- Separate engineering smoke checks from real-data scientific transfer; engineering PASS cannot yield CycloneSEQ admission or Go/No-Go.

Out of scope: executing real CycloneSEQ analysis in this proposal change; choosing calibrated numeric thresholds without real protocol approval; changing M3/M4 archived conclusions; changing production defaults; activating PMAT2 while Issue #10 remains unresolved; admitting or running mitoVGP; modifying `IDENTIFY`/`DECISION`; or treating pure CycloneSEQ as a terminal authentication sequence. Those require subsequent apply/data-bearing execution and separately governed decisions.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `validation-and-go-no-go`: Add the concrete CycloneSEQ arrival, blinding, protocol-freeze, evidence, and pre-written outcome contracts needed before transfer validation can execute.

## Impact

- Planning artifacts and one delta under the existing `validation-and-go-no-go` capability.
- Later implementation will add machine-readable arrival manifests, blind ledgers, frozen protocol/threshold records, comparison matrices, error-spectrum evidence, and a Go/No-Go record.
- Historical worktrees and `runs/` data remain untouched. PMAT2, mitoVGP, ONT isolation, `decision=NOT_APPLICABLE`, and CycloneSEQ `PENDING_REAL_DATA` remain unchanged at proposal time.
