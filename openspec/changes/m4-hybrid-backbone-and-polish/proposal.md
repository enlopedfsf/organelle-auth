## Why

M3 established that long-read data can provide experimental organelle structure evidence, while plant IR topology and animal AT-rich repeat adjacency remain unresolved. M4 now needs a controlled hybrid reference-build evaluation that freezes the inputs and structural backbones, then evaluates a pre-registered six-arm polishing matrix for each taxon without promoting experimental outputs into authentication decisions.

## What Changes

- Add a capability contract for hybrid reference construction: long-read structure candidates, a six-arm polishing/evidence matrix, held-out evaluation, edit provenance, region-level validation, and audit packaging.
- Freeze B0, R1, deterministic 80/20 paired-read splits, and the animal double-assembler core mask before the twelve arm/taxon evaluations begin.
- Evaluate exactly B0, R1, B0-to-Polypolish, B0-to-bcftools, R1-to-Polypolish, and R1-to-bcftools for each taxon using one pre-registered metric and dominance rule.
- Separate plant and animal routing and report core, repeat/IR, control-region, homopolymer, and junction evidence independently.
- Keep all Flye, Racon, Polypolish, and bcftools-consensus outputs experimental; do not connect them to `IDENTIFY` or `DECISION`.
- Keep CycloneSEQ transfer validation and Go/No-Go as `PENDING_REAL_DATA` until real paired CycloneSEQ data exist.
- Exclude PMAT2 because Issue #10 remains OPEN; no new assembler admission is introduced by this change.

## Capabilities

### New Capabilities

- `hybrid-reference-build`: Controlled long-read-backbone plus parallel short-read polishing/evidence evaluation for plant and animal organelle candidates.

### Modified Capabilities

None. Existing decision, tool-admission, provenance, and validation contracts are consumed by this capability; this change does not weaken them.

## Impact

The change will add a hybrid reference-build subworkflow, frozen-input and held-out manifests, an animal core-mask manifest, per-base edit ledgers, region-level validation reports, status/evidence bundles, and engineering tests. It may add experimental policy and registry validation records, but it must not alter production routing, authentication decisions, existing M3 conclusions, or the PMAT2 gate.

Out of scope: applying the change, production qualification, CycloneSEQ transfer/Go-No-Go, PMAT2 execution, Medaka/Nanopolish/Clair3-ONT, HiFi-only assemblers, and declaring a de novo circular topology from a polished candidate alone.
