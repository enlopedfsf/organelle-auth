## 1. Pre-registration and freeze

- [x] 1.1 Validate the proposal, design, and `hybrid-reference-build` delta with OpenSpec strict mode before computing results.
- [x] 1.2 Freeze SHA256, size, and absolute path for all six PAF/depth/residual triplets plus the plant region BED and evaluation policy.
- [x] 1.3 Record the exact command, implementation version, B0 coordinate rule, and three-state R1P1 conclusion rule before execution.

## 2. Deterministic implementation

- [x] 2.1 Implement candidate-to-B0 CIGAR projection with forward/reverse handling and exact-one projection enforcement.
- [x] 2.2 Implement unchanged held-out depth callability and the exact six-arm B0 intersection.
- [x] 2.3 Implement B0 region assignment, residual-anchor projection/exclusion audit, denominator metrics, and the `all_regions` summary.
- [x] 2.4 Add focused synthetic tests for indels, reverse projection, ambiguity exclusion, common intersection, zero denominators, and the three conclusion states.

## 3. Evidence execution

- [x] 3.1 Verify all frozen parent inputs exist, are non-empty, and match the input manifest without modifying historical `runs/` data.
- [x] 3.2 Execute the pre-registered analysis once and emit `common-callable.bed`, `arm-region-denominators.tsv`, residual audit, summary JSON, and command provenance.
- [x] 3.3 Produce `VALIDATION-plant-common-callability.md` with the bounded answer, exclusions, limitations, and explicit non-modification of M4-①.
- [x] 3.4 Generate and verify `MANIFEST.sha256` for all committed lightweight evidence; exclude FASTQ/BAM/VCF/FASTA and run directories.

## 4. Verification and closeout

- [x] 4.1 Run focused tests and assert each region has identical common callable bases across all six arms.
- [x] 4.2 Assert the combined denominator is non-empty, rates are arithmetically reproducible, and the summary conclusion follows the pre-registered rule.
- [x] 4.3 Run `openspec validate --all --strict`, repository lint/test gates in scope, and confirm no archived M4-① file changed.
- [x] 4.4 Submit the scoped implementation through commit, PR #23, green CI, acceptance, and merge into `dev`.
- [x] 4.5 After implementation merge, archive the change with spec sync and submit the archive as separately validated PR #24; authoritative CI/merge state remains in GitHub.
