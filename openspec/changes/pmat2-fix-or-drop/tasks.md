## 1. Freeze and preflight

- [x] 1.1 Locate the authoritative plant recruited-read checksum and verify the FASTQ exists and is non-empty.
- [x] 1.2 In CI, rebuild the PMAT2 image exactly once, push it to GHCR, pull by immutable digest, and record image digest, version, absolute executable path, and successful executable preflight. (Build failed before image creation; no digest/preflight exists.)
- [x] 1.3 If any preflight step fails, write the immutable terminal DROP evidence and do not open biological input.

## 2. Bounded comparator

- [ ] 2.1 If CI preflight passes, run PMAT2 once in CI on `runs/input/SRR38978847.final-recruited.fastq.gz` with all commands and resources recorded.
- [ ] 2.2 Compute the registered common comparison metrics against the archived Flye result.
- [ ] 2.3 Classify the outcome as retained comparator or DROP; never add retries or parameter arms.

## 3. Registry and closeout

- [x] 3.1 Update `registries/tools.yaml` with the terminal disposition and evidence links.
- [x] 3.2 Write Issue #10 closeout evidence, explicitly stating runtime/package failure is not biological evidence.
- [x] 3.3 Assert PMAT2 remains outside `IDENTIFY`/`DECISION` and animal/M4 work remains unblocked.
- [x] 3.4 Run focused tests and `openspec validate --all --strict`; stop for review before apply/issue closure.
