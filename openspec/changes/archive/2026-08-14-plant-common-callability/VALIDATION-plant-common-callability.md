# VALIDATION — plant common-callability addendum

## 1. Scope and status

This addendum answers one registered question: whether plant R1P1 retains the lowest held-out residual rate when all six M4-① arms are restricted to the same callable B0-coordinate bases. It does not rerun polishing, revise the archived M4-① comparison, rank homopolymer performance, resolve IR structure/topology, admit a production route, or emit an authentication decision.

| Field | Value |
|---|---|
| Change | `plant-common-callability` |
| Execution | `PASS` |
| Registered answer | `RETAINS_SOLE_LEAD` |
| Decision | `NOT_APPLICABLE` |
| CycloneSEQ | `PENDING_REAL_DATA` |
| PMAT2 / mitoVGP | unchanged |
| M4-① archive modification | none |

## 2. Pre-registration and frozen evidence

The proposal, spec delta, design, implementation, conclusion rule, and 20-input checksum manifest were committed before the successful result run:

- pre-result registration commit: `fef23eb48f1dff1578ab53aafd8df8030e255af4`;
- frozen input manifest SHA256: `87b124e76061776124f034aa52311e08eabd236e8119f7f5b29e4a6dbb89ffaa`;
- preregistration SHA256 after the schema-path correction: `230883a9b32957dd3f2101356af55524a7c73502495c7530fe4bcda8700b4adf`;
- parent archive tree at `origin/dev`: `f79bcb1bdbba52e110ca2635e9f4e379a7d0f6f1`;
- exact command: `evidence/execution-command.txt`;
- complete path/size/SHA256 ledger: `evidence/input-manifest.tsv`.

Inputs are the six frozen M4-① candidate-to-B0 PAFs, six held-out depth TSVs, six residual ledgers, the archived experimental evaluation policy, and the archived B0 plant-region BED. No FASTQ, BAM, VCF, FASTA, or historical `runs/` directory is copied into this change.

## 3. Execution history

1. The first invocation stopped before projections or results because the implementation requested a nonexistent JSON key, `heldout_read_evidence.minimum_callable_depth`.
2. The authoritative archived policy was machine-inspected and showed `alignment_filters.minimum_callable_depth = 10`.
3. Commit `c855e2739715f6423daad7588d30276366157879` corrected only the JSON field path and added a regression test. It did not alter the frozen threshold, inputs, coordinate rule, or conclusion rule.
4. The corrected invocation verified all frozen sizes/checksums and completed. A later output-format-only rerun removed a TSV header from `common-callable.bed`; all scientific counts and the answer remained unchanged.

## 4. Registered method

- Coordinate authority: the frozen plant B0 assembly and `plant-regions.bed`.
- Projection: primary (`tp:A:P`) candidate-to-B0 PAF alignments at MAPQ 60 with `cg`; only one-to-one `M`, `=`, and `X` base pairs are eligible.
- Ambiguity: a candidate or B0 base participating in more than one retained mapping is excluded; insertions/deletions do not invent base equivalence.
- Callability: unchanged held-out depth threshold `>=10` from the archived experimental policy; the common denominator is the exact intersection across B0/R1/P0/C0/R1P1/R1C1.
- Residuals: count unique `EVALUABLE` residual anchors only when their candidate base maps uniquely into the common B0 set. Unprojectable or non-common anchors remain in the exclusion audit and are never shifted.
- Primary conclusion: use only `all_regions`. R1P1 is sole leader, tied-lowest, or not leader according to its residual count/rate on the shared denominator.

## 5. Arm × region denominator result

The exact machine-readable table is `evidence/results/arm-region-denominators.tsv`. The common callable denominator is identical across arms by construction.

### 5.1 Combined registered comparison

| Arm | projected bases | common callable bases | callable fraction | residual loci | residual rate / 10 kb |
|---|---:|---:|---:|---:|---:|
| B0 | 200,144 | 105,154 | 0.525392 | 188 | 17.878540 |
| R1 | 199,956 | 105,154 | 0.525886 | 99 | 9.414763 |
| P0 | 200,144 | 105,154 | 0.525392 | 2 | 0.190197 |
| C0 | 200,144 | 105,154 | 0.525392 | 3 | 0.285296 |
| **R1P1** | **200,004** | **105,154** | **0.525759** | **1** | **0.095099** |
| R1C1 | 199,989 | 105,154 | 0.525799 | 3 | 0.285296 |

R1P1 is strictly lower than all five alternatives on the same 105,154-bp denominator. The registered answer is therefore **`RETAINS_SOLE_LEAD`**. P0 is second with two residual loci.

### 5.2 Regional denominator

| Region | common callable bases | interpretation |
|---|---:|---|
| `unique_or_unresolved_flank` | 104,592 | Supplies almost all bases in the registered comparison. |
| `ir_gap_closure_interval` | 562 | Only 1.48% of the approximately 37.85-kb projected interval is common-callable. |

The IR row is too restricted to support any IR-copy, adjacency, gap-closure, or topology claim. The combined R1P1 result is principally a flank/core sequence residual result.

## 6. Residual accounting

The residual projection audit accounts for every row in the six frozen source ledgers.

| Arm | included common-callable loci | excluded outside common set | excluded source-not-evaluable |
|---|---:|---:|---:|
| B0 | 188 | 43 | 0 |
| R1 | 99 | 4 | 4 |
| P0 | 2 | 0 | 0 |
| C0 | 3 | 8 | 0 |
| R1P1 | 1 | 0 | 0 |
| R1C1 | 3 | 0 | 1 |

No residual anchor was silently shifted to a nearby B0 base. Full row-level status and reasons are in `evidence/results/residual-projection-audit.tsv`.

## 7. Bounded conclusion

The archived statement that R1P1 was numerically ahead is robust to replacing arm-specific callable denominators with a six-arm common-callable denominator: R1P1 retains the sole lowest residual rate. This addendum strengthens only that narrow residual comparison.

It does **not** revise M4-①, establish a fully dominant production route, prove reference correctness, evaluate homopolymer superiority, validate CycloneSEQ transfer, or resolve plastome topology. Existing M4-① status and labels remain unchanged.

## 8. Verification

- focused implementation plus M4 regression tests: `38 passed`;
- OpenSpec strict validation: `11 passed, 0 failed`;
- common denominator equality across six arms: machine assertion PASS;
- BED bases equal summary total and regional totals: machine assertion PASS;
- residual audit row count equals all six source ledgers: machine assertion PASS;
- arithmetic reproduction of fractions/rates: machine assertion PASS;
- parent archive tree differs from `origin/dev`: no;
- local diff/whitespace and lightweight-evidence checks: PASS;
- PR/CI/merge/archive: pending governed closeout.
