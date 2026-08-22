## Why

PMAT2 remains an unresolved `EXPERIMENTAL` comparator because the archived plant M3 run ended with exit 127 and produced no biological result. Issue #10 requires one bounded, evidence-preserving fix-or-drop decision so the registry no longer carries an indefinitely unavailable candidate.

## What Changes

- Permit exactly one apply-stage rebuild of the PMAT2 runtime image and require an executable preflight before any biological input is used.
- If that single repair succeeds, run PMAT2 once on the checksum-frozen plant recruited long-read subset and compare its interpretable assembly evidence with the archived Flye result.
- If the image repair fails, executable preflight fails, comparator run fails, or the comparator result cannot be interpreted under the pre-registered comparison contract, classify PMAT2 as `DROP` and remove it from the active candidate-tool list while preserving the failure evidence.
- Record either the retained comparator evaluation or the drop disposition in `registries/tools.yaml`, then close Issue #10 without treating exit 127 as a biological negative.
- Keep PMAT2 outside `IDENTIFY` and `DECISION`; the disposition does not block the animal line, M4-②, or existing plant/animal topology conclusions.
- Out of scope: repeated image repair, PMAT2 parameter searching, animal PMAT2 execution, CycloneSEQ transfer validation, production admission, and any revision of archived M3/M4 scientific conclusions.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `asset-tool-and-policy`: replace the unconditional PMAT2 candidate-registration requirement with an auditable one-attempt fix-or-drop lifecycle and terminal registry disposition.

## Impact

- OpenSpec delta: `asset-tool-and-policy`.
- Apply-stage assets: PMAT2 container recipe/lock evidence, executable preflight, comparator evidence bundle, `registries/tools.yaml`, Issue #10 closeout record, focused tests, and validation report.
- Frozen comparator input: the exact recruited plant long-read subset already recorded by the archived M3 validation; apply must verify the file exists, is non-empty, and matches its authoritative checksum before launch.
- No production route, authentication API, animal workflow, M4-② work, or topology state is changed.
