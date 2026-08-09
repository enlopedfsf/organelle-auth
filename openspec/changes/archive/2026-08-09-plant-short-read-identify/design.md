## Context

① `plant-short-read-assembly-evidence` is **archived** (PR#4 → `dev`, 2026-08-09). Its frozen
①→② interface contract lives at
`openspec/changes/archive/2026-08-09-plant-short-read-assembly-evidence/design.md` §1-4 and is the
zero-deviation input anchor for this change. See `proposal.md` for *why* ② is needed.

Two facts from ① constrain this design:
1. A **normal** plant sample (刻叶紫堇 SRR38978846) produces a **6-scaffold `DRAFT`** at **99.95 %
   identity** (① `VALIDATION-7.1`). So `DRAFT` is a normal outcome, not an anomaly — forcing it to
   `INCONCLUSIVE` would make the pipeline useless for its primary (authentication) purpose.
2. The applied `plant-short-read-analysis` spec ends at `stage = assembly_qc`,
   `decision = NOT_APPLICABLE`. The decision semantics (SCI-001 evidence-combination, SCI-005
   no-forced-call, the `decision` enum) and the policy/reference-pack governance (ENG-POL-002,
   DATA-005) are already specified in `evidence-decision-and-status` / `asset-tool-and-policy` /
   `scope-routing-and-input`. ② *implements* them for the plant short-read identify path; it does
   not re-specify them.

## Goals / Non-Goals

**Goals**
- A reference-first `IDENTIFY` subworkflow that consumes ①'s frozen outputs and emits
  `stage = identify` with `decision` filled, governed by policy thresholds + reference-pack rules.
- An explicit, defensible `assembly_grade ↔ decision` gating decision (the question ① surfaced).
- A threshold-from-policy mechanism where a `null` threshold yields `INCONCLUSIVE` at the module
  layer (no crash), reconciled with the `ENG-POL-002` production startup gate.
- A test reference pack (v0.1, `PZ405204`) + an engineering-test policy so the decision *logic* can
  be validated end-to-end on real data without pretending the numbers are calibrated.

**Non-Goals** (design-level; proposal lists scope non-goals)
- No calibration of the engineering-test thresholds as scientific (that is M3 experiments + M5
  policy v1.0). The numbers are placeholders to exercise the flow.
- No new on-disk reference-pack *schema* file in this change — the loader treats the pack as the
  unit resolved by `reference_pack_id` (concept mechanism from `asset-tool-and-policy`); a formal
  pack schema is a separate change if needed.
- No Kraken2 self-built db (separate change) — contamination stays on the M1 read-back/assembly
  signal.

## Decisions

### 决策 1: `assembly_grade ↔ decision` 门控矩阵（① surfacing 的必答决策）

| ① `assembly_grade` | 诊断位点状态 | callable 覆盖 | `decision` | `status` | `reason_codes` |
|---|---|---|---|---|---|
| `CANDIDATE` | 全部 callable 且一致性满足规则 | 充足 | `AUTHENTIC` | `PASS` | `[]` |
| `DRAFT` | 全部 callable 且一致性满足规则 | 充足 | `AUTHENTIC` | `WARN` | `[INCOMPLETE_ASSEMBLY]` |
| `DRAFT` | 全部 callable 且一致性满足规则 | 不足 | `INCONCLUSIVE` | `INCONCLUSIVE` | `[LOW_COVERAGE]` |
| any | **诊断位点落缺失/不可判区**（即使全局一致性高） | — | `INCONCLUSIVE` | `INCONCLUSIVE` | `[DIAGNOSTIC_SITES_NOT_CALLABLE]` |
| any | 全部 callable 但落入 `uncertainty_zone` 灰区 | — | `INCONCLUSIVE` | `INCONCLUSIVE` | `[]` |
| any | 全部 callable 但低于 `conflict_rules` 阈值 | — | `NON_AUTHENTIC` | `PASS`/`WARN` | `[IDENTITY_BELOW_THRESHOLD]` |
| `NOT_APPLICABLE` / ① `FAIL` | — | — | `INCONCLUSIVE` | `INCONCLUSIVE` | 透传 ① reason |
| — (污染信号) | — | — | `INCONCLUSIVE` | `INCONCLUSIVE` | `[CONTAMINATION_SUSPECTED]` |
| — (policy `null`) | — | — | `INCONCLUSIVE` | `INCONCLUSIVE` | `[THRESHOLD_NOT_CONFIGURED]` |

> **"高一致性"的精确定义**：不是全局一致性数值，而是 **reference pack 定义的全部诊断位点（`diagnostic_sites`）均被组装覆盖且可判（callable），且其一致性满足 pack 规则**。全局一致性高但诊断位点落缺失/不可判区 → `INCONCLUSIVE + [DIAGNOSTIC_SITES_NOT_CALLABLE]`（即使已组装部分 100% 一致）。这是位点级身份判定的核心约束，防止一个"恰好删掉诊断区的大缺口"被全局一致性掩盖。

**Rationale.** organelle-auth authenticates species **identity**. Crucially, that identity evidence
is **site-level, not a global number**: all pack-defined diagnostic sites must be covered and
callable, and their identity must satisfy the pack rules (evidence combination, not a single mash
distance — SCI-001). A high global identity that hides a gap over the diagnostic region yields
`INCONCLUSIVE + [DIAGNOSTIC_SITES_NOT_CALLABLE]`, never `AUTHENTIC`. Given callable diagnostic sites,
99.95 % identity is overwhelming identity evidence; a 6-scaffold `DRAFT` is then a
**structural-completeness** caveat, not an identity problem. `DRAFT → always INCONCLUSIVE` would
mean a normal sample (per ①) can never be authenticated → defeats the pipeline's purpose. `DRAFT →
AUTHENTIC + WARN [INCOMPLETE_ASSEMBLY]` reports the identity honestly while flagging the incomplete
assembly. `INCONCLUSIVE` is reserved for genuinely undecidable cases (diagnostic sites not callable,
low coverage, grey-zone identity, contamination, missing threshold, ①-unusable). `NON_AUTHENTIC` is
a clear conflict (wrong species / adulterant) per the pack's `conflict_rules`.

**Alternatives considered.**
- (A) `DRAFT → INCONCLUSIVE` unconditionally — **rejected**: makes the primary use case
  unauthenticatable; contradicts the ① finding that `DRAFT` is normal.
- (B) `DRAFT → AUTHENTIC` silently (no WARN) — **rejected**: loses the structural-caveat signal,
  violates SCI-005's honesty (don't paper over incomplete evidence).
- (C) chosen (`AUTHENTIC + WARN [INCOMPLETE_ASSEMBLY]`) — identity decisive, caveat explicit.
- The `callable + diagnostic` evidence combination (not a single distance) is what satisfies SCI-001
  for the `AUTHENTIC` call; a mash/ANI number alone would not.

### 决策 2: policy `null` → `INCONCLUSIVE`（模块层防御）与 `ENG-POL-002`（启动门）并存

Two independent defense layers, by design:
- **`ENG-POL-002` startup gate** (already specified): a *production* run fails fast at launch if the
  loaded policy has a `null` rule-referenced threshold. Production should never reach `IDENTIFY`
  with a null threshold.
- **`IDENTIFY` module layer** (this change): if a null/uncalibrated threshold is encountered at
  runtime (e.g. an experimental policy, or a production misconfiguration that slipped the gate), the
  module outputs `INCONCLUSIVE + [THRESHOLD_NOT_CONFIGURED]` — it **does not crash and does not
  force a call** (SCI-005 spirit). "无法判定" is a legitimate quality output, not a pipeline failure.

**一句话分工**：`ENG-POL-002` 启动门拦截 **production profile + 全 null policy**（launch 时 fail-fast）；模块层 `[THRESHOLD_NOT_CONFIGURED]` 拦截 **任何 profile 下部分阈值字段为 null**（运行时 → `INCONCLUSIVE`，不崩溃）。两层互补：启动门挡住"整包未标定的 production"，模块层兜住"逐字段遗漏"。

**Rationale.** Defense-in-depth: the startup gate is the primary control; the module layer guarantees
that even if a null threshold reaches it, the pipeline degrades to an honest `INCONCLUSIVE` rather
than throwing or fabricating a decision. This is the reconciliation the handoff flagged — both layers
coexist, neither replaces the other.

### 决策 3: reference pack 加载 + DATA-005 + 规则取自 pack

`samplesheet.reference_pack_id` → a loader resolves the pack → **DATA-005 fail-fast** on
missing/incompatible (no silent fallback to any public DB). The decision engine reads
`required_evidence`/`supporting_evidence`/`conflict_rules`/`callable_regions`/`diagnostic_sites`/
`uncertainty_rules`/`known_exceptions`/`nuclear_evidence_requirement` from the pack (§7.2); no
"正品四要素" natural language is hardcoded (SCI-001). **de novo fallback** starts only when all four
§5.3 conditions are met and labels the result `candidate`/`inconclusive`.

**Test reference pack v0.1** = built from `PZ405204.1` (conspecific with the Corydalis normal
scenario). It is a *test* pack (declared scope, not a production release); used to exercise the
normal → `AUTHENTIC + WARN` path.

### 决策 4: engineering-test policy（逻辑验证专用，非科学标定）

A new policy file whose name contains `engineering-test`, `status: experimental`, with
`callable_site`/`uncertainty_zone` filled with **measured placeholder numbers** (from the Corydalis
run: ~99.95 % identity, ~92 % callable coverage). A header comment states: *"临时阈值未经标定，仅用于
验证流程逻辑，不得用于科学结论或生产默认值"* (thresholds uncalibrated; logic-validation only; not for
scientific conclusions or production defaults). This lets the four-scenario validation exercise the
decision flow end-to-end. Real calibration is M3 + M5; conflating these placeholders with scientific
thresholds is explicitly forbidden.

### 决策 5: `IDENTIFY` 架构（reference-first stages）

`LOAD_REFERENCE_PACK` → (re-map ①'s selected plastome to the reference where the pack requires
diagnostic-site identity, reusing ①'s `minimap2`/`samtools`) → `EVALUATE_CALLABLE_REGIONS` (depth
from ① readback intersected with the pack's `callable_regions`) → `EVALUATE_DIAGNOSTIC_SITES`
(identity at `diagnostic_sites`) → `DECISION_ENGINE` (apply pack rules + 决策 1 matrix + policy
thresholds; null → 决策 2) → `EMIT_IDENTIFY_STATUS` (`stage = identify`). ① outputs are read-only
inputs; nothing in ① is regenerated.

### 决策 6: `reason_codes.yaml` 扩展（+ 新增 `non_authentic` 类别）

Add **five** identify-stage codes. `IDENTITY_BELOW_THRESHOLD` drives a definitive `NON_AUTHENTIC`,
which the existing three categories (`scientific_inconclusive`/`warn`/`engineering_fail`) do not
cover honestly — so ② adds a fourth category `non_authentic` ("证据明确否定正品——确定性非正品判定").
Proposed:
- `INCOMPLETE_ASSEMBLY` — `warn` — "身份已确认（诊断位点全部 callable 且一致性满足），但组装结构不完整（DRAFT）；AUTHENTIC+WARN"
- `DIAGNOSTIC_SITES_NOT_CALLABLE` — `scientific_inconclusive` — "参考 pack 诊断位点落在组装缺失/不可判区，即使全局一致性高也无法做位点级身份判定；INCONCLUSIVE（决策 1）"
- `CONTAMINATION_SUSPECTED` — `scientific_inconclusive` — "read-back/组装图污染或 NUMT/MTPT 信号；INCONCLUSIVE，不强判"
- `THRESHOLD_NOT_CONFIGURED` — `scientific_inconclusive` — "policy 判定阈值为 null（模块层防御，决策 2）；输出 INCONCLUSIVE，非崩溃"
- `IDENTITY_BELOW_THRESHOLD` — `non_authentic` (new) — "诊断位点一致性低于 reference-pack conflict 阈值；NON_AUTHENTIC"

## Risks / Trade-offs

- **[engineering-test 阈值被误当科学阈值]** → 决策 4：文件名 + 文件头注释 + `status: experimental` 三重标识；标定属 M3/M5，本变更不主张科学性。
- **[`DRAFT → AUTHENTIC` 放行过宽？]** → 仅当 callable+diagnostic 一致性满足 pack 规则且覆盖充足时；不一致/灰区仍 INCONCLUSIVE/NON_AUTHENTIC。WARN+[INCOMPLETE_ASSEMBLY] 保留可追溯 caveat。
- **[reference pack 无磁盘 schema]** → 决策 3：本变更把 pack 作 `reference_pack_id` 解析单元（概念机制）；若需正式 schema 文件另开 change，不在 ② 内擅加。
- **[污染检测仍是 M1 临时方案]** → 沿用 ① 决策 6（read-back/组装信号），Kraken2 自建库 change 落地后细化 `CONTAMINATION_SUSPECTED` 触发逻辑。
- **[`ENG-POL-002` 与模块层 null 行为表面冲突]** → 决策 2：分层防御，design 显式写明两者并存。
- **[已知局限 — reference pack v0.1 诊断位点为退化形态]** reference pack v0.1 **无伪品（adulterant）对照**，故决策 1 中的诊断位点（`diagnostic_sites`）机制当前为**退化形态**：以全局/区间比对代替真位点级诊断判定。当接入**含伪品对照**的 reference pack 时，诊断位点机制**必须完整实装**（含 `conflict_rules`/`diagnostic_sites` 的真位点级 identity 判定与冲突裁决），**不得继续以全局比对代替**。此局限显式记录，防止退化形态被当作终态。

## Migration Plan

Greenfield on top of ① (which is archived on `dev`). Rollback = remove the `IDENTIFY` subworkflow +
identify modules + the new policy/reason-code entries + test reference pack; ① and the
`assembly_qc` stage are untouched. No migration of existing data (no identify outputs exist yet).

## Open Questions

- `IDENTITY_BELOW_THRESHOLD` 的 `non_authentic` 新类别是否需同步更新报告生成器（若已硬编码三类）——apply 时确认；不改 spec 行为。
- 测试 reference pack v0.1 的最小字段集（FASTA + diagnostic_sites + callable_regions + 一条 conflict 规则）是否足以跑通四场景，或需补 `uncertainty_rules` ——apply 时按场景收敛。
