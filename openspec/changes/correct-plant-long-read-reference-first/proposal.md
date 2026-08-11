## Why

The current M3 plant long-read pilot sends the complete filtered shallow-WGS background into PMAT2, which contradicts the reference-first IDENTIFY/VALIDATE route required by SCI-001 and the M3 delivery contract in TEST-004. The real 2 GB ONT trial also demonstrated that whole-background correction is neither eligible nor resource-proportionate at shallow nuclear depth, so the route must be corrected before its behavior is treated as an M3 validation result.

## What Changes

- Replace the whole-background-first pilot with sensitive recruitment against a validated organelle reference set, retaining complete reads and tolerating repeat-derived secondary/supplementary mappings.
- Add an auditable two-pass recruitment option: the first pass uses circular reference rotations; an optional second pass maps all input reads to preliminary organelle candidates and unions complete read identifiers, with a hard maximum of two passes.
- Gate assembly on target-organelle evidence (recruited yield, estimated target depth, breadth, and junction support) rather than inferred nuclear-genome depth or a fixed raw-GB rule.
- Make Flye assembly of the recruited whole-read subset the primary long-read assembly route.
- Run PMAT2 with `-p 0` on the same recruited subset as an EXPERIMENTAL comparator; retain full-background PMAT2 only as an explicitly eligible, high-coverage de novo fallback when no adequate reference exists.
- Replace positional sequence comparison with alignment-based structural evidence: reference alignment, IR-boundary comparison, circular/junction-spanning read support, and comparison with the M1 short-read anchor.
- Distinguish the default raw-input processing budget (approximately 2 GB unless overridden) from the coverage-aware recruited subset; neither value becomes a universal biological threshold.
- Preserve the isolated `long_read_pilot` route and its EXPERIMENTAL status. It remains disconnected from production IDENTIFY/DECISION, and CycloneSEQ admission plus Go/No-Go stay pending real data.
- **BREAKING** for the experimental pilot interface: PMAT2 is no longer the primary consumer of all filtered reads, and new reference-recruitment evidence is required before subset assembly.

Out of scope: calibrated production thresholds, CycloneSEQ admission, animal long-read implementation, reference-free shallow-depth de novo assembly, hybrid polishing, a nuclear-marker panel, and any terminal authentication decision. Production calibration and CycloneSEQ transfer remain in the later M3 validation work; animal long-read symmetry belongs in its own capability change.

## Capabilities

### New Capabilities

- `plant-long-read-analysis`: Establish the corrected experimental plant long-read capability as reference-first shallow-WGS recruitment, target-evidence gating, subset assembly, and structural validation. This definition supersedes the unarchived capability delta of the same name in `plant-long-read-pmat2-pilot`.

### Modified Capabilities

None.

## Impact

- Nextflow: `workflows/organelleauth.nf`, local modules/subworkflows for long-read QC, recruitment, gating, Flye, PMAT2, and structural evidence.
- Configuration and schema: experimental route parameters, reference rotations, recruitment policy, target-evidence policy, tool resources, and output contracts.
- Testing: T0/T1 module contracts, T2 route and guardrail tests, T3 synthetic/integration coverage, plus T4 real-data evidence without pretending skipped real-data work passed.
- Validation records: `VALIDATION-plant-lr.md` must distinguish the failed whole-background experiment from the corrected route and leave CycloneSEQ/Go-No-Go unresolved until real evidence exists.
- Dependencies: minimap2, samtools/seqkit-compatible whole-read extraction, Flye, PMAT2 `-p 0`, and alignment/structural evidence tooling; all versions and commands remain traceable.
- Governance: this change supersedes the routing assumption in the active `plant-long-read-pmat2-pilot` change while preserving that change's EXPERIMENTAL isolation and non-decision constraints.
