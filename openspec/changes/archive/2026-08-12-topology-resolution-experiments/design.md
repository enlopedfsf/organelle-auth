## Context

The archived M3 run used Flye 2.9.6-b1802 with `--asm-coverage 50 --min-overlap 5000` on the final 122,132,426-bp recruited subset (SHA-256 `93f4fd3bc3969e5d4d3577870b32f4a63d99ddc57a325f84403d7f089531f3c8`). It produced two contigs totalling 200,144 bp. Existing structural evidence is useful but does not establish a single circular topology. See the archived pilot artifacts and M3 report for the complete provenance.

## Goals / Non-Goals

**Goals:**

- Test processing-cap and overlap sensitivity with a small, auditable grid.
- Recount junction evidence without MAPQ-only exclusion and with copy-aware IR handling.
- Produce a standalone result appendix with explicit negative/ambiguous outcomes.

**Non-Goals:**

- No production threshold calibration, PMAT2 run, reference scaffolding, forced circularization, or decision-path integration.
- No edits to archived validation prose or existing topology labels.

## Decisions

1. **Use a manifest-selected six-run maximum.** The requested Cartesian space has twelve combinations, so the executable manifest selects at most six pre-declared combinations while retaining the control `(50, 5000)` and covering each requested coverage and overlap level. This preserves the experimental budget; silently running all twelve was rejected.

2. **Reuse the exact recruited FASTQ and provenance.** The input is verified by the archived checksum before any Flye task. Re-recruitment was rejected because it would confound parameter effects with changed read selection.

3. **Keep each run isolated.** Each grid point writes under a stable parameter-labelled directory and records full command/version/resource metadata. Shared output filenames and `-resume` across parameter points are rejected because they risk cross-contamination.

4. **Separate raw and weighted junction evidence.** The recount emits raw read-identity counts, alignment-class counts, and copy-aware weighted support. A MAPQ cutoff is retained only as a comparison stratum, never as the eligibility rule. Counting alignments rather than read identities was rejected because IR multi-mapping would inflate support.

5. **Append-only validation.** The implementation writes `VALIDATION-topology-experiments.md` and machine-readable tables; it does not patch the archived validation document. Any proposed topology change is a later OpenSpec change.

## Risks / Trade-offs

- [Twelve requested value combinations exceed the six-run cap] → select and record a balanced six-point manifest before execution.
- [Parameter sensitivity can be mistaken for biology] → report all metrics and preserve `INCONCLUSIVE`; no threshold is promoted.
- [IR copy assignment is intrinsically ambiguous] → retain raw/weighted strata, identity deduplication, and uncertainty notes.
- [Historical cache may be missing] → fail on checksum mismatch and search the documented current, raw-data, and legacy work roots before declaring unavailable.
- [Large assembly outputs] → use fixed `runs/work` and `runs/output` roots with one directory per parameter point.

## Migration Plan

No production migration. Run the experiment in the fixed repository roots, review the appendix, then archive this change with its manifests and checksums. Rollback is deleting only the new experiment output tree; archived M3 artifacts remain untouched.
