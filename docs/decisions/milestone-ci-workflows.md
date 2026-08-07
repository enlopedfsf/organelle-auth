# Milestone → CI workflow enablement

Per 总方案 v1.1.1 §14.1 / §12.7, **three T0 GitHub Actions are the ACTIVE M0 quality
gates**. The nf-core template's standard community workflows are RETAINED as scaffolding
— `nf-core pipelines lint` requires their presence, and they preserve the
`nf-core pipelines sync` path. They are not part of the M0 quality gate and most no-op
for a pipeline outside the nf-core organisation.

## Active T0 gates (M0)

| Workflow | Purpose |
|---|---|
| `spec-and-schema.yml` | `openspec validate --changes` + JSON/YAML schema + Requirement traceability matrix integrity |
| `linting.yml` | `nf-core pipelines lint` + pre-commit/format + Markdown/link basics |
| `template-check.yml` | minimal template-structure self-check |

## nf-core standard scaffolding (retained for lint compliance; not M0 gates)

`branch.yml`, `clean-up.yml`, `download_pipeline.yml`, `fix_linting.yml`, `nf-test.yml`,
`pr-comment.yml`, `template-version-comment.yml`.

## Per-milestone enablement

| Capability | Workflow(s) | Enabled at |
|---|---|---|
| T1 module / T2 subworkflow tests | `nf-test.yml` | M1 |
| T3 pipeline smoke (short/long/hybrid) | `nf-test.yml` | M1 |
| scheduled regression (T4 + container pullability + ref manifest) | new `scheduled-regression.yml` | M3 |
| release qualification (T4–T6 + records + compatibility) | new `release-qualification.yml` | M5 |
| release (packaging + checksums + RO-Crate + notes) | new `release.yml` | M5 |

## Decision history

- Initial plan (§12.7 literal): keep only 3 workflows, remove the rest.
- Adopted (Option K): removing nf-core standard workflows makes `nf-core pipelines lint`
  fail (it requires them), conflicting with the M0 acceptance "passes nf-core lint".
  Standard workflows are therefore retained; the three T0 gates above define what M0
  actually enforces. §12.7's intent — trim *implementation density*, not architecture
  (§12.7) — is preserved: only the 3 T0 gates are active M0 checks; the rest are dormant
  scaffolding until their milestone.
