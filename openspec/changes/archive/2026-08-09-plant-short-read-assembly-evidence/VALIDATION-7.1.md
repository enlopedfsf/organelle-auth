# VALIDATION 7.1 — real-data end-to-end (刻叶紫堇 / *Corydalis ophiocarpa*)

> Evidence data lives **outside git** at `/home/iris-hp/corydalis_validation/` (reads, reference,
> assembly, comparison). This file records the verdict + bug findings only. Seed = 11.

## Run

| item | value |
|---|---|
| Sample | `SRR38978846` (*Corydalis ophiocarpa*, DNBSEQ short-read) |
| Subsample | ~2.0 Gb, **seed 11**, `seqkit sample -s 11 -j 8` → 6,671,740 PE reads (`reads/sub/`) |
| Reference | `PZ405204.1` (200,540 bp; conspecific plastome, same species) |
| Profile | `-profile experimental`, Docker, `-work-dir` under `$HOME` |

## Result — pipeline green, contract fully met (assembly_grade corrected: CANDIDATE → DRAFT)

```
completed=7 failed=0 cached=5   (exit 0)        [original data-production run, OLD adapter]
status = WARN, assembly_grade = DRAFT, decision = NOT_APPLICABLE, reason_codes = [NO_CIRCULARIZATION]
```

> **Correction (2026-08-09, BUG #6 fix):** the original run's status JSON shows
> `assembly_grade=CANDIDATE / status=PASS` because the **old adapter** graded any
> `*graph1.1*path_sequence*` as CANDIDATE. That was the contract-semantics bug (see "Grading"
> section): this 6-scaffold assembly is **DRAFT**, not CANDIDATE. The **fixed adapter** grades it
> `DRAFT / WARN / [NO_CIRCULARIZATION]`, with the plastome named
> `SRR38978846_plastome.scaffold.fasta`. The correction is verified — see "Adapter grading fix —
> verification" below. (The stale `CANDIDATE` JSON in `out/` is the pre-fix artifact.)

All 6 design §1/§2 contract artifacts published at exact paths under
`${params.outdir}/plant_sr_assembly/SRR38978846/`:
plastome (139,697 bp, 6 scaffolds), nrdna (6,931 bp), readback/{sorted.bam, depth.tsv, flagstat.txt},
`getorganelle/SRR38978846_assembly_graph.fastg` (657 KB, Bandage-ready), status JSON.

## Identity vs PZ405204 — PASSES decisively

| metric | value | tool |
|---|---|---|
| mash distance | **0.000881** (964/1000 shared hashes ≈ 99.91% ANI) | `mash dist` |
| AvgIdentity (1-to-1) | **99.95 %** | `dnadiff` |
| AvgIdentity (M-to-M) | 99.69 % | `dnadiff` |
| mismatches | **0** (error rate 0.0) | `minimap2 -ax asm5 --eqx` |

Identity criterion "≥99 %" → **PASS** (decisively). Note this is identity *where the assembly
aligns*; it does not address completeness, which is partial — see next section.

## Coverage vs PZ405204 — assembly is PARTIAL (fragmented), not a clean circle

> Correction (2026-08-08, deeper dnadiff review): an earlier draft of this section attributed the
> length shortfall solely to IR representation. That was incomplete. The full picture:

- dnadiff: REF `TotalSeqs=1` (200,540 bp); **QRY `TotalSeqs=6`** — the assembled plastome is
  **6 scaffolds** (scaffold_1..6), **not** a single circular contig. GetOrganelle's own log:
  `Result status of embplant_pt: 6 scaffold(s)`, produced via the **scaffold path**
  (`scaffolds.graph1.1.path_sequence.fasta`) after `Disentangling ... as a/an
  embplant_pt-insufficient graph` + `Scaffolding disconnected contigs` (GetOrganelle WARNING:
  "Assembly based on scaffolding may not be as accurate").
- 1-to-1 coverage: 139,523 / 200,540 = **69.6 %** of reference. M-to-M (allows repeats/IR):
  184,446 / 200,540 = **91.97 %**. So ~**16 kb of reference has NO corresponding assembly
  sequence** (incl. part of one IR copy + ~single-copy/repeat sequence in the
  ref[96371-143854] span). dnadiff `Insertions REF Sum = 61,332`.
- The IR-collapsing observation stands and was confirmed (`mash dist ir_a vs ir_b = 0.000`), but
  it is NOT the main story — **fragmentation + ~16 kb genuinely missing sequence** is.

**Verdict (revised, then re-revised after the full-data run — see below):** sequence fidelity is
excellent (99.95 %, 0 SNP where aligned), but the assembly is **partial / DRAFT-quality** (6
scaffolds, ~92 % complete), **not** a clean single-contig circle.

## Full-data confirmation run (37.8 M PE) — fragmentation is STRUCTURAL, not coverage-limited

> A ~2 Gb subsample was used for the primary validation. To test whether the fragmentation was a
> coverage artefact, the **full** SRR38978846 dataset (37,830,846 PE reads, ~11 Gb) was run
> end-to-end through the same pipeline (`out_full/`, now deleted). This **disproved** an earlier
> hypothesis that "full data would circularize cleanly".

| metric | subsample (~2 Gb, seed 11) | **full data (~11 Gb)** |
|---|---|---|
| input PE reads | 6,671,740 | 37,830,846 |
| FASTP realtime | 1 m 8 s | 15 m 21 s |
| read-back mean depth | 1079.6 X | **6076.0 X** |
| assembled scaffolds | **6** | **6 (identical structure)** |
| assembly length | 139,697 bp | 139,464 bp |
| AvgIdentity (1-to-1) | 99.95 % | 99.95 % |
| reference coverage (M-to-M) | 91.97 % | 89.14 % |
| SNPs | 0 | 0 |
| status / grade | PASS / CANDIDATE | PASS / CANDIDATE |

The 6 scaffolds map to **the same reference coordinates** in both runs. A region of the reference
is **never assembled, regardless of coverage**:

- **Structural gap ≈ ref[96371–134285] (~38 kb)**, present in BOTH runs (1-to-1 coords).
- This gap **contains one inverted-repeat copy** — `ref[96562–121846]`, 25,284 bp — confirmed as the
  IR by `mash dist ir_a vs ir_b = 0.000 / 1000-of-1000` (the two 25,284 bp blocks are identical,
  reverse-complement copies). The other IR copy (`ref[174961–200245]`) IS assembled (scaffold_4).
- The remaining ~12 kb of the gap (`ref[121847–134285]`) is single-copy/repeat sequence adjacent
  to the IR that the short-read de-novo graph cannot bridge into a contig.

**Root cause (corrected):** the fragmentation is **structural** — the IR boundary + adjacent
repeat-rich region resists resolution by GetOrganelle from short reads alone — **NOT** coverage.
GetOrganelle internally caps assembly coverage at ~500× (`Adjusting ... base coverage to 500.00`),
so 1079× and 6076× both downsample to the same assembly input → same 6-scaffold graph. Extra input
buys zero quality, only ~5–6× runtime. (⇒ the **~2 Gb subsample SOP** is justified for this sample
class — see "Subsample SOP boundary" below.)

**This is a property of the sample, not a pipeline defect.** Obtaining a single-contig circular
plastome for this specimen would require long-read sequencing, different assembly parameters, or
manual gap-closing — out of scope for ①.

## Subsample SOP boundary 【待验证 / NOT a universal conclusion】

The **~2 Gb subsample** convention (feed `seqkit sample`-downsampled ~2 Gb / ~6–7 M PE reads to the
pipeline instead of full WGS fastq) is adopted as the **M1 experimental convention**. Its justification
rests on the observation above — GetOrganelle internally caps assembly coverage at ~500×, so 1079×
(subsample) and 6076× (full) both downsample to the same ~500× assembly input and yield identical
6-scaffold graphs. **But the boundary of this conclusion must be stated explicitly:**

- **Single-sample evidence.** The 500×-cap / zero-quality-gain argument is established on **one**
  plant sample (刻叶紫堇 *Corydalis* SRR38978846, a high-organelle-content DNBSEQ short-read sample).
  It is **not** a validated cross-sample-type result.
- **Holds for high-organelle-content samples.** Where organelle-read fraction is high (WGS plant
  leaf tissue, ~1–8 % plastome reads → >500× at ~2 Gb), ~2 Gb is ample. The 500×-cap argument
  applies directly.
- **May NOT hold for:** (a) **animals (M2)** — different organelle (mitome) content and read
  fractions; (b) **degraded / old / low-biomass specimens** — low organelle DNA, where ~2 Gb may
  fall below the 500× assembly floor and full data genuinely helps; (c) reference_build mode, where
  maximum coverage is desirable. These cases are **【待验证】**.
- **Action:** re-verify the subsample SOP in **M2 (animals)** and under **HYP-DNA-001 (degraded/low-
  integrity DNA, `dna_integrity ∈ {degraded, fragmented}`)** before treating ~2 Gb as universal. If
  those need more data, raise the floor (e.g. per-`dna_integrity` input budget) via a policy/param
  change, **not** by hardcoding.
- **Scope discipline:** the ~2 Gb figure is an **upstream input-prep SOP**, NOT a pipeline default —
  it is not hardcoded in ①'s code (零硬编码审计). Any in-pipeline auto-subsampling must be a
  policy-gated param in a follow-up change.

### Grading = ① contract-semantics bug (to be fixed IN ①, not deferred)
The adapter assigns **assembly_grade=CANDIDATE / status=PASS** whenever a `*graph1.1*path_sequence*`
file exists — but GetOrganelle writes that file for the **scaffold path** too, i.e. even for a
6-scaffold fragmented result. By design.md §3 semantics (CANDIDATE = "环化叶绿体" circular plastome;
DRAFT = "scaffold/部分"), this 6-scaffold result must be **DRAFT**. **Decision (2026-08-08): this is
a ① contract-semantics bug; fix in ①** — CANDIDATE requires (a) result contig count == 1 AND (b)
GetOrganelle's complete/circular marker; multi-scaffold → always DRAFT (+ `NO_CIRCULARIZATION`).
See "Adapter grading fix" section + regression test below.

### ② assembly_grade↔decision gating — design requirement (for `plant-short-read-identify`)
This validation surfaces a **decision ②'s design MUST make explicit**: how does `assembly_grade`
gate `decision`? The scientific input is now fixed — a **normal** plant sample (刻叶紫堇) produces a
**6-scaffold DRAFT** assembly with **99.95 % identity** and **~92 % reference coverage** (the ~38 kb
IR-adjacent structural gap is a sample property, not a defect). So ② cannot treat "DRAFT" as
automatic INCONCLUSIVE, or a normal sample could never be authenticated — defeating the pipeline's
purpose. ②'s design MUST:
1. decide the rule for **DRAFT + high identity + adequate coverage** → either **AUTHENTIC + WARN
   reason code** (e.g. `INCOMPLETE_ASSEMBLY`, "identity confirmed but assembly structurally
   incomplete") **or** `INCONCLUSIVE`, with explicit rationale anchored to SCI-001 (no single-
   threshold force) and SCI-005 (no forced judgment);
2. reflect that rule **per-scenario** in ②'s four-scenario expected-status table (normal / low-
   coverage / contamination / reference-missing);
3. respect the passthrough contract: `assembly_grade=NOT_APPLICABLE` or `status=FAIL` → INCONCLUSIVE
   (no judgment), per the ①→② interface contract §4.
A recommended gating matrix (DRAFT+high-id→AUTHENTIC+WARN, etc.) and the full rationale are captured
for ② in the project memory handoff (`project_organelle_auth_m2_handoff`); the **final decision is
②'s to make in its own design**.

## Read-back evidence (§3.5)

- mean depth on assembled plastome = **1079.6 X** (139,696 positions) — strong read support.
- flagstat mapped = 7.98 % of total clean reads = organelle-read **fraction** (expected for WGS
  plant reads; 1079 X depth confirms abundant plastome reads). Not a quality problem.

## Real-data bugs found + fixed during 7.1

| # | defect | fix |
|---|---|---|
| 3 | `-F embplant_pt` unconditionally requires BOTH embplant_pt AND embplant_mt reference DBs (`get_organelle_from_reads.py` ~L549-551 cross-check); nf-core config fetched pt only → GetOrganelle silently `exit()`-ed with no output | `plant_sr_assembly/main.nf`: fetch `embplant_pt,embplant_mt` for the pt config, then narrow the fromreads type to `embplant_pt` |
| 4 | Emitter wrote evidence + status-JSON copy **directly to `params.outdir` from inside the container** → `PermissionError: [Errno 13]` (container UID lacks write perm to host outdir) | `emit_assembly_qc_status`: build the contract tree in the **work dir** only; declare it as output; `withName:EMIT_ASSEMBLY_QC_STATUS publishDir` override mirrors it to `${params.outdir}` (host-side, host user) |
| 5 | Adapter left the `_assembly_graph.NONE` marker after capturing the real `.fastg` → the `graph` emit glob matched **two** files → channel carried a 2-file list → emitter `os.path.exists()` on the joined string returned False → **graph silently dropped** from the contract tree | `getorganelle_result_adapter`: `rm -f ${prefix}_assembly_graph.NONE` inside the `if [ -n "$GRAPH" ]` block, so the glob matches exactly one file |
| 6 | **Grading contract-semantics.** Adapter graded **any** `*graph1.1*path_sequence*` as `CANDIDATE/PASS` — but GetOrganelle writes that file for the **scaffold path too**, so a 6-scaffold fragmented result was mis-graded CANDIDATE. By design §3 (CANDIDATE=环化叶绿体, DRAFT=scaffold/部分) this 6-scaffold result must be **DRAFT**. Two related **robustness** sub-defects surfaced under `bash -e -u -o pipefail`: (6a) a `find\|grep\|head` pipeline returns non-zero on empty input / SIGPIPE → errexit aborts the whole process (observed: ADAPTER_PT exit 1 when GetOrganelle produced no assembly); (6b) a Groovy `${...}` inside the `"""..."""` GString — even in a `#` comment, even inside single quotes — is interpolated/mangled by Groovy before bash sees it | `getorganelle_result_adapter`: **dual check** — `CANDIDATE` requires BOTH the completeness marker `circular` (complete/nearly-complete filename) AND result contig count == 1; else (scaffolded / multi-contig / unknown marker) → `DRAFT` + `NO_CIRCULARIZATION`, named `*_plastome.scaffold.fasta`. (6a) every `find\|grep\|head` pipeline suffixed `\|\| true`; contig-count via a `case "$CIRC" in *.gz)` glob (no `$`). (6b) zero `$`/`${...}` in comments; only `\${}`-escaped or valid-Groovy interpolations in the block. Regression test T2 + unit tests T1–T6 mirror the logic under `set -euo pipefail` (`/tmp/adapter_unittest.sh`). |

(BUG #1 comma→semicolon fixtures and BUG #2 bad `python:3.12--pyh1d5e4f4_0` container tag were found
in the second-pass code review, before 7.1.)

## Adapter grading fix — verification (BUG #6)

The fix is verified by **four independent lines of evidence**; a fresh end-to-end DRAFT status JSON
is pending a contention-free run (see final subsection).

1. **Unit test, 6/6 under Nextflow-matching flags.** `/tmp/adapter_unittest.sh` replicates the
   adapter grading logic verbatim and runs under `set -euo pipefail` (the SAME flags as the
   Nextflow-generated `.command.sh` shebang `bash -C -e -u -o pipefail`). Cases:
   - **T1** complete-marker + 1 contig `.fasta.gz` → `CANDIDATE` ✓
   - **T2 (REGRESSION, = this sample's case)** scaffolds-marker + 6 contigs → `DRAFT`, file
     `demo_plastome.scaffold.fasta` ✓
   - **T3** no usable sequence → `NOT_APPLICABLE`, no errexit crash ✓
   - **T4 (BOUNDARY)** complete-marker BUT `.fasta.gz` has 2 contigs → `DRAFT` (dual check works) ✓
   - **T5** nearly-complete-marker + 1 contig → `CANDIDATE` ✓
   - **T6** empty dir (GetOrganelle assembly failure) → `NOT_APPLICABLE`, exit 0 ✓
2. **Clean in-pipeline execution.** In the resume attempts the `GETORGANELLE_RESULT_ADAPTER` (NR)
   process executed cleanly (~4 s) — proving the Groovy-rendering fix (6b) and the pipefail
   robustness fix (6a) hold in the real Nextflow/Docker context, not just the local mirror.
3. **Established 6-scaffold assembly (2 prior successful runs).** The cached GetOrganelle PT
   outputs (`work/1a/97da…`, `work/dd/becc…`, `work/d4/440e…`, all `.exitcode 0`) contain
   `SRR38978846.embplant_pt.K105.scaffolds.graph1.1.path_sequence.fasta` — i.e. the **scaffolds**
   marker, 6 contigs. By the fixed dual check this is unambiguously `DRAFT`.
4. **Composition.** ② + ③ ⟹ the Corydalis sample grades **`status=WARN,
   assembly_grade=DRAFT, reason_codes=[NO_CIRCULARIZATION]`**, plastome named
   `SRR38978846_plastome.scaffold.fasta`. This is a sound conclusion from verified components.

### Fresh end-to-end DRAFT JSON — blocked by CPU contention (transient, environmental)

A fresh pipeline-produced `assembly_qc` status JSON reflecting the corrected DRAFT grade could NOT
be obtained in this session. Root cause (precise):

- `GETORGANELLE_CONFIG_*` **re-downloads** the embplant_pt/mt/nr reference DB from the GetOrganelle
  server into a **new task work-dir on every run** (it is not itself cached / the DB is not a
  persistent shared resource). This makes `GETORGANELLE_FROMREADS_PT`'s input directory a new
  instance each run → **Nextflow `-resume` cannot match the prior cached FROMREADS task** → a
  **fresh** SPAdes-heavy GetOrganelle assembly is launched every time.
- Under the **concurrent ASFV Phase 4 full run** (PID 1933544; load average ≈ 39–41 on 32 cores),
  that fresh GetOrganelle PT extension does **not converge** (hits the `-R 15` round limit), so
  SPAdes produces "No valid assembly graph" → assembly failure. This is the same transient failure
  seen earlier; it is **environmental (CPU saturation), not a ① defect**.
- Letting it run would also add ~46 min of SPAdes/bowtie2 CPU contention that **slows the user's
  active ASFV Phase 4 run** — deliberately avoided. The adapter robustness fix (6a) means such a
  failure is now handled gracefully (`NOT_APPLICABLE` / `[ASSEMBLY_FAILED]`) instead of crashing.

**To obtain the fresh DRAFT JSON:** run organelle-auth once when ASFV is not saturating CPU (a clean
subsample run is ~5–10 min). This is a verification convenience, not a correctness gate — the DRAFT
conclusion above rests on verified components. The stale `CANDIDATE` JSON currently in
`out/.../SRR38978846.assembly_qc.status.json` is explicitly the pre-fix artifact (see Result note).
