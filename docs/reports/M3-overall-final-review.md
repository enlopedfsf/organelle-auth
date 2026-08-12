# M3 Overall Final Review

**Review date:** 2026-08-12  
**Scope:** plant and animal long-read evaluation closeout  
**Basis:** merged `dev` at `ed12882d8c9684b1a3cb10d70cff437a2d1c86b3`

## Executive verdict

M3 is complete as an experimental evaluation milestone. It is **not** a production authentication release and does not authorize a topology upgrade or CycloneSEQ transfer claim.

| Area                                | Final state                              | Evidence                                                                 |
| ----------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------ |
| Plant ONT route                     | `EXPERIMENTAL`                           | `docs/reports/M3-plant-long-read-reference-first-technical-report.md`    |
| Plant IR gap                        | `CLOSED` as a structural evidence result | 37 independent spanning-read candidates are recorded in the plant report |
| Plant whole-plastome topology       | `INCONCLUSIVE`                           | archived topology experiment and conclusion-revision reports             |
| Animal ONT route                    | `EXPERIMENTAL_COMPLETE`                  | `runs/output/animal-lr-recruitment-diagnostics/VALIDATION-animal-lr.md`  |
| Animal mitochondrial core           | supported against M2-① anchor            | Flye/Raven core agreement and anchor evidence                            |
| Animal repeat adjacency/copy number | unresolved                               | HYP-DNA-002 and Raven insertion audit                                    |
| Animal topology                     | `INCONCLUSIVE`                           | animal validation report and `animal-long-read-analysis` spec            |
| IDENTIFY / DECISION                 | unchanged; ONT excluded                  | animal and plant specs                                                   |
| PMAT2                               | gated by Issue #10                       | animal/plant governance records                                          |
| CycloneSEQ transfer and Go/No-Go    | `PENDING_REAL_DATA`                      | plant report and capability specs                                        |

## Plant review

The reference-first ONT route successfully recruited a high-depth chloroplast subset, completed the Flye engineering route, and supplied independent read evidence for closure of the M1 IR gap. The formal result remains two contigs rather than a single de novo circular molecule. The archived topology follow-up and topology-conclusion review both preserve `INCONCLUSIVE`; MAPQ-inclusive or copy-weighted junction counts were not treated as sufficient independent support.

The plant result is therefore suitable as an experimental structural-evidence baseline, not as a production circular-topology or authentication claim.

## Animal review

The animal closeout resolves the failure attribution and validates the experimental route:

1. the incomplete system Flye runtime caused a false empty-consensus failure;
2. recruitment was corrected to require one coherent alignment satisfying all criteria;
3. the 25-kb/30-kb length controls did not remove any coherent reads;
4. Flye showed run- and read-order-sensitive repeat-graph paths;
5. Raven independently recovered the mitochondrial core but not a unique repeat adjacency;
6. the 13 excluded long reads did not establish a same-orientation whole-mitogenome multimer.

The animal evidence supports the core sequence but cannot resolve AT-rich repeat adjacency or copy number. It remains outside `IDENTIFY` and `DECISION`; PMAT2 remains gated.

## Governance checks

- M3 evidence is in the merged `dev` history through PRs #12, #13, and #14.
- The merged branch passed all required CI gates, including nf-core lint, pre-commit, nf-test, Docker shards, MitoFinder image build, and T1–T3 smoke tests.
- `openspec validate --all --strict` passed on the merged `dev` state.
- The current local working tree contains unsubmitted C-class material. It is deliberately excluded from this review and must not be batch-committed.

## Release decision

**M3: COMPLETE for experimental evaluation; NOT READY for M4 execution.**

Before M4 work begins, the project must merge the independent C1 runs-directory policy, then archive the two topology changes (C2) and the superseded failed animal pilot (C3). CycloneSEQ preparation may proceed in parallel, but no transfer or Go/No-Go claim is permitted without real paired data.
