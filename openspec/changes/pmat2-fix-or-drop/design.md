## Context

Issue #10 is open because the archived PMAT2 attempt exited 127. The planned action is a bounded registry decision, not a new assembly study.

## Goals / Non-Goals

**Goals:** make one reproducible runtime repair attempt; protect the frozen plant input; emit either an interpretable comparator record or an auditable DROP.

**Non-Goals:** repeated debugging, parameter optimization, animal execution, production admission, or topology/authentication changes.

## Decisions

1. **One-attempt state machine.** States are `OPEN → PREFLIGHT → COMPARE` or `OPEN → PREFLIGHT → DROP`; any failed preflight is terminal. This prevents exit-127 retries from becoming an unbounded project.
2. **CI-authoritative runtime evidence before data.** The sole repair attempt is a CI job that builds the PMAT2 image, pushes it to GHCR, pulls it by immutable digest, and verifies the executable with `--help`/version before opening the frozen FASTQ. Local absence of Docker/Apptainer is not counted as an attempt. The input is copied from the historical work directory into `runs/input/` and all subsequent records use that fixed path and checksum.
3. **Comparison contract.** Compare only common, explicitly documented observations against the archived Flye result (contig count/length, core alignment identity/coverage, and runtime status). Non-comparable output routes to DROP; no post-hoc success criterion.
4. **Registry-only disposition.** Update `registries/tools.yaml` and an Issue #10 closeout record only during apply. No decision route or topology conclusion is touched.

## Risks / Trade-offs

- [Image repair remains unavailable] → preserve logs and terminal DROP; do not infer biology.
- [Comparator differs in tool semantics] → classify uninterpretable unless the pre-registered common metrics can be computed.
- [Frozen input missing] → fail before launch and report the missing checksum/path.

## Migration Plan

Apply once, validate, then archive the issue record. Rollback is removal of the new disposition record only; archived M3 evidence remains immutable.
