## Why

M3 established that long-read data can provide experimental organelle structure evidence, while plant IR topology and animal AT-rich repeat adjacency remain unresolved. M4 now needs a controlled hybrid reference-build evaluation that freezes one long-read backbone and compares two independent short-read polishing/evidence routes without promoting experimental outputs into authentication decisions.

## What Changes

- Add a capability contract for hybrid reference construction: long-read structure candidate, parallel short-read polishing/evidence routes, edit provenance, region-level validation, and audit packaging.
- Freeze the Flye/Racon backbone and the paired short-read inputs before polishing; run Polypolish and bcftools-call/consensus from the same backbone in parallel.
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

The change will add a hybrid reference-build subworkflow, frozen-input manifests, per-base edit ledgers, region-level validation reports, status/evidence bundles, and engineering tests. It may add experimental policy and registry validation records, but it must not alter production routing, authentication decisions, existing M3 conclusions, or the PMAT2 gate.

Out of scope: applying the change, production qualification, CycloneSEQ transfer/Go-No-Go, PMAT2 execution, Medaka/Nanopolish/Clair3-ONT, HiFi-only assemblers, and declaring a de novo circular topology from a polished candidate alone.
