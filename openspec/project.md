# organelle-auth — OpenSpec project

> 中药材细胞器基因组鉴定 pipeline (organelle-auth). OpenSpec-governed: every behavioral
> change flows through `openspec/changes/`; the applied, current behavior lives in
> `openspec/specs/`.

## 事实优先级 (Source-of-truth priority)

**openspec/specs 与活跃 change 是行为事实来源；docs/specification 总方案 v1.1.1 是冻结的需求与科学依据来源；两者冲突时以 specs 的现行状态为准，冲突必须通过正式 change 解决，禁止任何一方静默覆盖。**

Operational reading of the clause above:

- **Behavioral source of truth** = `openspec/specs/` (current applied spec) **and** `openspec/changes/` (active, unapplied deltas). If you want to know what the pipeline *actually does today*, read these. They win on behavior.
- **Frozen requirements & scientific rationale** = `docs/specification/中药材细胞器基因组鉴定与Nextflow规范开发总方案_v1.1.1.md` (the v1.1.1 总方案). It is the immutable requirements/science reference; it is NOT edited in place to match code.
- **On conflict**: the `specs/` current state governs. A conflict is a real disagreement that must be resolved by opening a formal `change/` (proposal → design → tasks → apply), never by silently editing either side. Editing the 总方案 to match code, or editing code/specs to match the 总方案 without a change, are BOTH forbidden silent overrides.
- **Rationale**: the 总方案 is large and freezes early; specs evolve change-by-change. Letting either side silently rewrite the other destroys traceability (`openspec/traceability.yaml`). Forcing conflicts through a change keeps the two in deliberate, auditable sync.
