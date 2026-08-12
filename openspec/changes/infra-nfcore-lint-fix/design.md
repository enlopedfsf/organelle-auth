## Context

See `proposal.md`. CI uses nf-core/tools 4.1.0 and currently reports repository-wide metadata and template hygiene failures.

## Goals / Non-Goals

### Goals

- Make the nf-core lint check pass with minimal, reviewable edits.
- Preserve all workflow behavior and scientific contracts.
- Make unresolved real work visible as tracked issues.

### Non-Goals

- No `nf-core pipelines lint --fix` bulk rewrite.
- No changes to Nextflow logic, parameters, modules, subworkflow wiring, runs policy, proxy policy, or M3 evidence.

## Decisions

1. **Manual edits only.** Automatic fixing is rejected because it can rewrite unrelated template files.
2. **Metadata follows existing repository conventions.** Missing `meta.yml` files will describe name, purpose, inputs, outputs, components, and authors only; they will not invent runtime contracts.
3. **TODOs are classified before editing.** Pure nf-core scaffolding is removed; policy, threshold, admission, and scientific TODOs become explicit issues or remain documented.
4. **Behavioral regression is required.** Compare the changed tree against the baseline with nf-test and static source checks; only metadata/docs/CI files may differ.

## Risks / Trade-offs

- [Risk] A metadata description could drift from a workflow interface → Mitigation: derive fields from existing `take`/`emit` declarations and run lint.
- [Risk] Removing a TODO could hide real work → Mitigation: classify every occurrence and preserve unresolved items as issues.
- [Risk] Local lint tooling differs from CI → Mitigation: use CI as authoritative and record local dependency limitations.

## Migration Plan

1. Implement the isolated metadata/TODO/version edits.
2. Run focused lint, schema, and nf-test checks.
3. Open an independent PR and wait for CI and review.
4. Rollback is a normal revert; no data migration exists.
