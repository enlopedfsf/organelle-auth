## Context

M3 is closed on `origin/dev` with plant topology and animal repeat adjacency still experimental/inconclusive. Flye, Racon, Polypolish, and bcftools-consensus are registered as `EXPERIMENTAL`; PMAT2 remains gated by OPEN Issue #10. See the proposal and the existing SCI-003/004/005, DATA-001/002/004, ENG-POL-003/004, TEST-003, and REL-001 contracts.

## Goals / Non-Goals

**Goals:**

- Build a reproducible hybrid evaluation around frozen B0 and R1 long-read structural candidates.
- Evaluate the pre-registered six-arm matrix causally, including the incremental effect of Racon and the two short-read polishing routes.
- Make every base edit, region, junction, and unresolved repeat claim auditable.
- Keep public-data experiments distinct from CycloneSEQ transfer validation and authentication decisions.

**Non-Goals:**

- No production reference-grade promotion, IDENTIFY/DECISION integration, or Go/No-Go claim.
- No PMAT2 execution while Issue #10 is OPEN.
- No Medaka, Nanopolish, Clair3-ONT, Oatk, MitoHiFi, or other prohibited tools.
- No forced circularization or inference that a polished candidate proves topology.

## Decisions

1. **Capability-domain spec.** Use `hybrid-reference-build`; the change name is not a spec domain. Existing governance domains remain authoritative for input, tool admission, status, validation, and release.

2. **Frozen backbone strata.** The unpolished long-read candidate (B0) is assembled/selected once and checksum-frozen. R1 is produced from B0 by exactly two Racon rounds; each round maps the same frozen taxon-specific recruited long-read set to the current candidate with minimap2 `-x map-ont`, then runs `racon -w 500 -q 10.0 -e 0.3 -m 3 -x -5 -g -4 -t 4` without `-u`, `--no-trimming`, or CUDA flags. Round two remaps the same reads to the round-one candidate. The Racon version/container is selected under the existing tool-admission contract and checksum-frozen before execution. The stop rule is exactly two rounds: result-driven extra rounds and alternate read types are forbidden. B0 and R1 are frozen before any P/C arm starts; reassembly per polishing route would confound structure and polishing effects.

3. **Pre-registered six-arm matrix.** For each taxon, the capped matrix is exactly twelve evaluations total (six arms × two taxa): B0 (unpolished backbone), R1 (Racon only), P0 (B0→Polypolish), C0 (B0→bcftools call/consensus), R1→P1 (Racon→Polypolish), and R1→C1 (Racon→bcftools call/consensus). No extra combination, polishing round, or alternate read type may be added during execution; a new arm is a new hypothesis and requires a change revision.

4. **Parallel short-read routes.** The Polypolish and explicit align→call→consensus arms use the same paired reads and the declared B0 or R1 backbone. They are parallel candidates within each backbone stratum, not sequential alternatives. Insert size, pairing, multi-mapping, and repeat behavior are evidence fields, not a single automatic skip threshold.

5. **Deterministic training/held-out split.** Before backbone freeze, each taxon's paired short reads are split deterministically 80/20 while preserving mate pairs. The canonical pair identifier is the first whitespace-delimited read-name token with a terminal `/1` or `/2` removed. Compute SHA256 over the UTF-8 string `m4-hybrid-v1\t<canonical_pair_id>`, interpret the first eight hexadecimal digits as an unsigned integer, and assign residues modulo 10: 0-1 to held-out and 2-9 to training. The seed/salt is therefore exactly `m4-hybrid-v1`. Training and held-out FASTQs, pair counts, command/rule text, and SHA256 checksums are frozen with B0/R1. Training reads may polish and define callability; the held-out set is used only for final arm evaluation and cannot tune parameters, masks, or candidates.

6. **Uniform metrics and proxy-reference caveat.** The frozen held-out set is aligned independently to every final candidate with the same registered alignment and callability policy. Within the frozen evaluable core, every arm reports the same primary metric: `residual_unsupported_loci`, the count of candidate positions that are callable in held-out reads but unsupported by their read-backed allele evidence. `introduced_edits` are reported separately as step-local and cumulative candidate-versus-input-backbone edits; they are provenance, not a B0-favoring substitute for the uniform residual metric. Every arm also reports held-out core concordance, held-out-supported evaluable homopolymer discordances, SNVs, indels, residuals by region, resources, and manual-review burden. Reference comparisons remain proxy measures: reference disagreement does not equal assembly error, and discordant sites are adjudicated by this sample's reads.

7. **Pre-registered winner rule.** An eligible arm is dominant only when, within the same taxon and frozen evaluable core, it (a) has fewer `residual_unsupported_loci` than every other eligible arm, (b) has fewer held-out-supported evaluable homopolymer discordances than every other eligible arm, and (c) does not reduce held-out core concordance relative to B0. The two counts plus the non-regression condition are the complete ranking combination. `introduced_edits` and reference-only metrics cannot select a winner. If no arm satisfies all three conditions, the scientific conclusion is multiple routes retained as `CONDITIONAL`; the machine result status remains `INCONCLUSIVE`, and no post hoc winner narrative is permitted.

8. **Animal core-mask freeze.** Before any of the twelve arm/taxon evaluations, the validation/evidence owner creates and signs the animal evaluable-core BED in the B0/Flye coordinate frame. The algorithm aligns the frozen unpolished Flye and Raven candidates, retains only collinear same-orientation intervals represented exactly once in each assembler, intersects them with positions callable from the frozen 80% training reads, and excludes non-unique sequence, unresolved AT-rich/D-loop repeats, ambiguous graph edges, and unresolved junctions. The manifest records the aligner and fixed parameters, exact retained/excluded coordinates, callability and uniqueness rules, coordinate frame/liftover rule, owner, and BED SHA256. These rules and thresholds are frozen before results and cannot be tuned with held-out reads.

9. **Backbone-freeze responsibility.** The validation/evidence owner records the freeze checklist: assembly graph/path, contig status, core coverage, structural evidence, two-round Racon ledger, long-read manifest, training/held-out manifests, animal core-mask manifest, and SHA256 values. A route cannot silently replace a frozen input, split, backbone, or mask.

10. **Evidence over reference concordance.** A related reference may be used as secondary context, but it cannot by itself validate edits or junctions. The primary ledger records read-backed support, ambiguity, and region-specific residuals; any in-sample validation is labeled as such.

11. **Taxon-separated evaluation.** Plant IR/repeat regions and animal D-loop/AT-rich regions are evaluated separately. A successful plant route cannot qualify the animal route, and vice versa. Animal polishing may run over the full backbone, but ranking metrics are restricted to the frozen Flye/Raven-consensus core; edits inside unresolved regions are counted separately as `NOT_EVALUABLE` and cannot rank routes.

12. **Status and tier isolation.** `EXPERIMENTAL` is an evidence/tool tier, not a result status. Every produced candidate records exactly `status=INCONCLUSIVE`, `assembly_grade=CANDIDATE`, and `decision=NOT_APPLICABLE`. Long-read/CycloneSEQ evidence stays outside `IDENTIFY` and `DECISION`; CycloneSEQ transfer remains `PENDING_REAL_DATA`; PMAT2 remains excluded while Issue #10 is OPEN.

13. **Deterministic reproducibility.** Record fixed seeds, ordering, tool versions, containers, parameters, and checksums. Use attribute-based assertions for non-deterministic assembly outputs; exact output hashes are not scientific contracts unless the tool/runtime is proven deterministic.

## Risks / Trade-offs

- [Risk] Polypolish may be inapplicable to a particular library or multi-mapping pattern → Mitigation: preserve applicability evidence and report inapplicable rather than silently substituting a validated claim.
- [Risk] Reusing polishing reads for evaluation inflates apparent support → Mitigation: require the frozen deterministic 80/20 split; train/polish on 80% and rank every final arm only with the untouched 20% held-out set.
- [Risk] Repeat traversal can create unsupported length or circularity → Mitigation: require read-level junction/unique-flank evidence and report repeat regions separately.
- [Risk] Public data may not represent CycloneSEQ chemistry → Mitigation: mark transfer and Go/No-Go `PENDING_REAL_DATA`.
- [Risk] Experimental tools can drift → Mitigation: pin versions/containers and retain an audit bundle; no production default changes in this proposal.

## Migration Plan

No production migration is authorized. After proposal review, implementation would add the subworkflow and tests behind an experimental/reference-build route. Rollback is removal of the experimental route and its evidence bundle; existing M3 conclusions and decision routing remain unchanged.
