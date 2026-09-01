## Why

M4-① established a frozen six-arm comparison but intentionally stopped at experimental candidate evidence. A separate audited selection/package step is needed to carry the supported plant route and bounded animal alternatives forward without overstating reference grade, topology, or production readiness.

## What Changes

- Consume the immutable M4-① and plant common-callability evidence rather than rerunning or retuning the six-arm experiment.
- Register plant `R1P1` as the primary candidate route for this audit because it retained the sole residual lead on the frozen common-callable denominator, while preserving all documented callability and topology caveats.
- Register the animal outcome as `CONDITIONAL`, retaining all tied eligible routes and prohibiting post-hoc selection of a single winner.
- Produce per-taxon candidate packages and a reproducible audit ledger covering provenance, checksums, route rationale, evaluable regions, unresolved loci, reference disagreements, topology exclusions, tool/container identities, and release blockers.
- Cap every produced assembly at `assembly_grade=CANDIDATE`, with `status=INCONCLUSIVE` and `decision=NOT_APPLICABLE`; do not emit `REFERENCE` grade.
- Preserve plant and animal topology as `INCONCLUSIVE` and prohibit this change from changing circularity, IR adjacency/copy number, animal AT-rich repeat adjacency/copy number, or authentication routing.
- Out of scope: new polishing arms, rerunning M4-①, threshold tuning, topology revision, reference-pack publication, production default selection, authentication decisions, and CycloneSEQ Go/No-Go.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `hybrid-reference-build`: add bounded post-comparison candidate-route selection and audit rules for plant R1P1 and the animal `CONDITIONAL` set.
- `provenance-and-release`: define the candidate-package audit manifest and explicit blockers that prevent accidental `REFERENCE` promotion or release.

## Impact

- OpenSpec deltas: `hybrid-reference-build` and `provenance-and-release`.
- Apply-stage assets: immutable-source manifest, per-taxon candidate manifests, audit ledger/report, machine-readable blockers, schema checks, focused tests, and CI assertions.
- Source evidence remains the archived M4-① and plant common-callability artifacts; their files and conclusions are not modified.
- No production reference pack, compatibility release, `IDENTIFY`/`DECISION` route, topology conclusion, or CycloneSEQ state is changed.
