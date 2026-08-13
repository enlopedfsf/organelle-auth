## Context

M3 is closed on `origin/dev` with plant topology and animal repeat adjacency still experimental/inconclusive. Flye, Racon, Polypolish, and bcftools-consensus are registered as `EXPERIMENTAL`; PMAT2 remains gated by OPEN Issue #10. See the proposal and the existing SCI-003/004/005, DATA-001/002/004, ENG-POL-003/004, TEST-003, and REL-001 contracts.

## Goals / Non-Goals

**Goals:**

- Build a reproducible hybrid evaluation around one frozen long-read structural candidate.
- Compare two short-read routes causally: Polypolish versus explicit alignment, variant calling, and consensus.
- Make every base edit, region, junction, and unresolved repeat claim auditable.
- Keep public-data experiments distinct from CycloneSEQ transfer validation and authentication decisions.

**Non-Goals:**

- No production reference-grade promotion, IDENTIFY/DECISION integration, or Go/No-Go claim.
- No PMAT2 execution while Issue #10 is OPEN.
- No Medaka, Nanopolish, Clair3-ONT, Oatk, MitoHiFi, or other prohibited tools.
- No forced circularization or inference that a polished candidate proves topology.

## Decisions

1. **Capability-domain spec.** Use `hybrid-reference-build`; the change name is not a spec domain. Existing governance domains remain authoritative for input, tool admission, status, validation, and release.

2. **Frozen common backbone.** The long-read candidate is assembled/selected once, optionally Racon-polished under an explicitly recorded experimental arm, checksum-frozen, and then supplied unchanged to both short-read routes. Reassembling separately per polishing route would confound structure and polishing effects.

3. **Pre-registered six-arm matrix.** For each taxon, the capped matrix is exactly twelve evaluations total (six arms × two taxa): B0 (unpolished backbone), R1 (Racon only), P0 (B0→Polypolish), C0 (B0→bcftools call/consensus), R1→P1 (Racon→Polypolish), and R1→C1 (Racon→bcftools call/consensus). No extra combination, polishing round, or alternate read type may be added during execution; a new arm is a new hypothesis and requires a change revision.

4. **Parallel short-read routes.** The Polypolish and explicit align→call→consensus arms use the same paired reads and the declared B0 or R1 backbone. They are parallel candidates within each backbone stratum, not sequential alternatives. Insert size, pairing, multi-mapping, and repeat behavior are evidence fields, not a single automatic skip threshold.

5. **Common metrics and proxy-reference caveat.** Every arm reports the same metric set: core-region identity, read-back consistency, SNV count, indel count, homopolymer error count, unsupported-edit count, residual conflicts by region, and resource/manual-review burden. Any metric comparing with a reference is explicitly a proxy measure: disagreement with a reference does not equal assembly error. A discordant site is adjudicated by this sample's read-level evidence, not by reference authority.

6. **Pre-registered winner rule.** A route can be called dominant only if it has fewer unsupported edits and fewer evaluable homopolymer errors than every competing arm while its core-region identity does not decrease relative to the common baseline. If no arm dominates under all three conditions, the outcome is `CONDITIONAL` with multiple routes retained; no post hoc winner narrative is permitted.

7. **Backbone-freeze responsibility.** The validation/evidence owner records the freeze checklist: assembly graph/path, contig status, core coverage, structural evidence, Racon round and edit ledger, and SHA256. B0 and R1 are both frozen before any P/C arm starts; a route cannot silently replace the declared backbone.

4. **Evidence over reference concordance.** A related reference may be used as secondary context, but it cannot by itself validate edits or junctions. The primary ledger records read-backed support, ambiguity, and region-specific residuals; any in-sample validation is labeled as such.

8. **Taxon-separated evaluation.** Plant IR/repeat regions and animal D-loop/AT-rich regions are evaluated separately. A successful plant route cannot qualify the animal route, and vice versa. For animal candidates, polishing may run over the full backbone, but comparison metrics are restricted to the double-assembler-consensus core; edits inside unresolved AT-rich repeats are counted separately and marked `NOT_EVALUABLE`, never included in route ranking.

9. **Status isolation.** All outputs remain `EXPERIMENTAL`; long-read/CycloneSEQ evidence stays outside `IDENTIFY` and `DECISION`. CycloneSEQ transfer remains `PENDING_REAL_DATA`; PMAT2 is excluded while Issue #10 is OPEN.

10. **Deterministic reproducibility.** Record fixed seeds, ordering, tool versions, containers, parameters, and checksums. Use attribute-based assertions for non-deterministic assembly outputs; exact output hashes are not scientific contracts unless the tool/runtime is proven deterministic.

## Risks / Trade-offs

- [Risk] Polypolish may be inapplicable to a particular library or multi-mapping pattern → Mitigation: preserve applicability evidence and report inapplicable rather than silently substituting a validated claim.
- [Risk] Reusing polishing reads for evaluation inflates apparent support → Mitigation: use a deterministic held-out subset where feasible; otherwise label all metrics in-sample and prohibit qualification claims.
- [Risk] Repeat traversal can create unsupported length or circularity → Mitigation: require read-level junction/unique-flank evidence and report repeat regions separately.
- [Risk] Public data may not represent CycloneSEQ chemistry → Mitigation: mark transfer and Go/No-Go `PENDING_REAL_DATA`.
- [Risk] Experimental tools can drift → Mitigation: pin versions/containers and retain an audit bundle; no production default changes in this proposal.

## Migration Plan

No production migration is authorized. After proposal review, implementation would add the subworkflow and tests behind an experimental/reference-build route. Rollback is removal of the experimental route and its evidence bundle; existing M3 conclusions and decision routing remain unchanged.
