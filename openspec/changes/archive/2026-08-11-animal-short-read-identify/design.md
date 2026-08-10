## Context

M2-① is archived at `openspec/changes/archive/2026-08-10-animal-short-read-assembly-evidence/`. Its design §①→② contract is the zero-deviation input boundary: the animal assembly FASTA/scaffold, annotation, read-back BAM/depth/flagstat, assembly graph, and `stage = assembly_qc` status are read-only inputs. Its `VALIDATION-animal.md` records a normal DNBSEQ run that is 100% identical to `CM084263.1`, while `NC_023928` is only 87.62% identical and triggered the documented stop-and-report action. This change must preserve that distinction.

M1-②'s plant identify design supplies the symmetric gating pattern: `LOAD_REFERENCE_PACK` → callable-region/diagnostic-site evaluation → `DECISION_ENGINE` → identify status, with `DRAFT` allowed to authenticate only when identity evidence is complete and a structural warning is retained. The method specification anchors this design at DATA-005/006, SCI-001/003/005/007, ENG-POL-001/002/003/004/005, §5.5, §9, §13 and §14.

## Goals / Non-Goals

**Goals:**

- Add a CM084263-based animal reference pack v0.1 with explicit circularity disclosure and an unusable/quarantined NC_023928 record.
- Reuse the plant identify architecture while implementing animal-specific assembly/NUMT/DRAFT gates.
- Keep engineering-test policy values traceable placeholders and keep production policy all-null with honest `INCONCLUSIVE` behavior.
- Provide an empty SCI-007 marker interface that can later accept a real taxon-specific panel without changing the identify contract.
- Produce reproducible local three-scenario validation evidence and T1/T2/T3 CI coverage.

**Non-Goals:**

- No changes to M2-① output files, paths, or assembly-stage semantics.
- No real nuclear marker panel, NUMT confirmation, Kraken2 self-built DB, long-read/hybrid route, or threshold calibration.
- No claim of independent biological validation from CM084263: its shared BioProject provenance is a declared circularity limitation.

## Decisions

### 1. Reference pack: CM084263 is the decision reference; NC_023928 is quarantined

The pack has independent asset identity/versioning and at least these records:

- `CM084263.1`: `status: decision_reference`, with sequence checksum, source citation, BioProject identifier, and `circularity_disclosure` stating that the validation data and reference derive from the same BioProject. The validation claim is therefore workflow reproducibility, not independent biological qualification.
- `NC_023928`: `status: QUARANTINED`, with its checksum, 87.62% observed divergence against CM084263, a pointer to `VALIDATION-animal.md`'s stop-and-report section, and Ye et al. (2015) misidentification evidence. The loader rejects this record for decision use; it remains an audit/evidence record only.

The pack's diagnostic windows are selected from non-D-loop, non-gap intervals. The gap mask is derived from the M2-① normal assembly evidence, not inferred from a new alignment at runtime. If the resulting non-risk windows are not callable, the decision is `INCONCLUSIVE`.

#### Animal reference pack v0.1 content checklist (fixed before apply)

The files are apply-stage outputs, but the following content is a predeclared scientific contract. Apply SHALL materialize exactly this checklist; it MUST NOT invent coordinates or provenance while implementing the loader.

**Pack identity and CM084263.1 entry**

| Field | Required value |
|---|---|
| `pack_id` / `version` | `tcm-animal-cm084263` / `0.1.0` |
| `taxon_group` / `target` | `animal` / `mitome` |
| `reference_id` / `accession` | `CM084263.1` (decision reference) |
| `organism` / `isolate` | *Whitmania acranulata* / `jianxi01` |
| `source` | NCBI GenBank CM084263.1, `DEFINITION: Whitmania acranulata isolate jianxi01 mitochondrion, complete sequence, whole genome shotgun sequence`; `ACCESSION: CM084263 JBDFUC010000000`; `VERSION: CM084263.1` |
| `bioproject` / `biosample` | `PRJNA1072149` / `SAMN39735897` |
| `length_bp` / `topology` | `14505` / `circular` (the GenBank `LOCUS` is `circular CON`) |
| `circularity_disclosure` | “CM084263.1 and the M2-① validation reads are BioProject-derived from the same provenance chain; the observed agreement tests workflow reproducibility/lineage consistency, not independent biological validation.” |
| `source_citation` | Lin G., *Comparative genomics of three non-hematophagous leeches (Whitmania spp.): focusing on antithrombotic genes* (NCBI record, unpublished; direct submission 05-May-2024, School of Life Sciences, Jinggangshan University). |

**NC_023928.1 quarantined evidence entry**

The manifest MUST retain an evidence-only record with `reference_id: NC_023928.1`, `status: QUARANTINED`, `decision_eligible: false`, `organism: Whitmania acranulata`, `source_bioproject: PRJNA927338`, and `observed_divergence_vs_CM084263: 87.62%` (`0.8762`). The evidence pointer is the archived M2-① record [`VALIDATION-animal.md`](../archive/2026-08-10-animal-short-read-assembly-evidence/VALIDATION-animal.md), specifically the “参考考据 B：Whitmania 公共库物种错误鉴定” and stop/report record. The record MUST cite Ye et al. (2015), the literature basis recorded in that validation section. Loader tests MUST assert that a `QUARANTINED` entry cannot be selected as the decision reference, even if its FASTA is present.

**Diagnostic and exclusion coordinates (CM084263.1, 1-based inclusive)**

M2-① `wtm_final.1coords` reports 14,399 aligned reference bases and 106 unaligned reference bases. The fixed gap mask is therefore `1..64` and `14464..14505`; it is carried as `gap_mask.bed` (0-based half-open conversion `0..64`, `14463..14505`) and is never recomputed at decision time. M2-①'s assembly annotation supplies the scaffold-to-reference circular rotation used below. The windows are all inside annotated protein-coding sequence, not the unannotated/high-variation D-loop/control-region space; each is at least 50 bp from a coding-feature boundary and at least 300 bp from the measured gap mask.

| Window ID | CM084263.1 coordinates | M2-① scaffold mapping / feature | Selection evidence |
|---|---:|---|---|
| `ATP6_W1` | `500..700` | scaffold `11981..12181`, ATP6 | Internal ATP6 coding sequence; 278 bp from the scaffold feature start and 184 bp from its end. It is outside the D-loop/non-coding space and 436 bp from the nearest measured reference-gap boundary (`1..64`). |
| `CYTB_W1` | `1800..2000` | scaffold `13281..13481`, CYTB | Internal CYTB coding sequence; 798 bp from the feature start and 147 bp from its end. It is a conserved coding window, not D-loop, and is separated from the measured gap mask by >1.7 kb. |
| `ND6_W1` | `2200..2350` | scaffold `13681..13831`, ND6 | Internal ND6 coding sequence; 51 bp from the feature start and 257 bp from its end. It avoids the D-loop/non-coding interval and remains >2.1 kb from the measured gap mask. |

These are deliberately conservative engineering-test windows, not a biological marker panel. CI SHALL reject any future window that is outside `1..14505`, overlaps `gap_mask.bed`, overlaps the declared D-loop/non-coding exclusion mask, or lacks the feature/boundary rationale above. If these windows are not callable, the engine returns `INCONCLUSIVE + DIAGNOSTIC_SITES_NOT_CALLABLE`; it must not relocate them automatically.

**On-disk format and CI correspondence**

Apply writes `assets/reference_packs/tcm-animal-cm084263-v0.1/{manifest.json,CM084263.1.fasta,diagnostic_sites.tsv,callable_regions.tsv,gap_mask.bed,provenance.yaml}`. `manifest.json` contains the field values above, SHA-256 digests, the quarantined record, and relative evidence links; `diagnostic_sites.tsv` carries the three window IDs and coordinates; `callable_regions.tsv` and `gap_mask.bed` use the coordinate conventions stated above. CI validates JSON/schema and digest presence, accession/topology/length, bounds and non-overlap, QUARANTINED exclusion, evidence-link existence, and the exact circularity wording. This is implemented by tasks 1.1–1.2 and 1.5, exercised by 3.1–3.3, and enforced by 4.1/4.4 and 5.2 (`openspec validate --strict`).

**Alternatives considered:** using NC_023928 because it is a RefSeq record was rejected by the recorded 87.6% conflict and stop-and-report rule; using every public accession was rejected because public species labels are not sufficient provenance; placing diagnostic sites in D-loop was rejected because it is a high-variation region and was explicitly excluded by the user contract.

### 2. Reuse `LOAD_REFERENCE_PACK` / `DECISION_ENGINE`; preserve the ① contract

The animal path consumes the M2-① status and evidence without regeneration or mutation:

```text
LOAD_REFERENCE_PACK
  → LOAD_POLICY_PACK
  → LOAD_NUCLEAR_MARKER_INTERFACE (empty panel allowed, never invented)
  → READ_ASSEMBLY_QC_INPUTS (read-only)
  → EVALUATE_CALLABLE_WINDOWS
  → EVALUATE_DIAGNOSTIC_SITES
  → DECISION_ENGINE (animal gate matrix)
  → EMIT_IDENTIFY_STATUS
```

Identify output goes under a separate identify-stage directory and retains links to all assembly evidence. No identify step may overwrite an assembly FASTA, read-back artifact, or `assembly_qc` JSON.

### 3. Animal gate matrix

The matrix is evaluated from evidence, not from a single global identity number:

| Assembly input | Diagnostic windows | Policy | NUMT / marker state | Decision | Status/reasons |
|---|---|---|---|---|---|
| `CANDIDATE` | all non-risk windows callable and satisfy pack rules | engineering-test configured | marker interface present or explicitly non-required by pack | `AUTHENTIC` | `PASS` |
| `CANDIDATE` | all non-risk windows callable and satisfy pack rules | engineering-test configured | `NUMT_RISK_SUSPECTED` hit, but risk does not make diagnostic evidence uncallable | `AUTHENTIC` | `WARN + NUMT_RISK_SUSPECTED` (never silently ignored) |
| `DRAFT` | all non-risk windows callable and satisfy pack rules | engineering-test configured | no blocking conflict and no NUMT hit | `AUTHENTIC` | `WARN + INCOMPLETE_ASSEMBLY` |
| `DRAFT` | all non-risk windows callable and satisfy pack rules | engineering-test configured | `NUMT_RISK_SUSPECTED` hit, but risk does not make diagnostic evidence uncallable | `AUTHENTIC` | `WARN + INCOMPLETE_ASSEMBLY + NUMT_RISK_SUSPECTED` (never silently ignored) |
| any | NUMT signal overlaps a diagnostic window, invalidates callable evidence, or combines with another blocking uncertainty | configured | `NUMT_RISK_SUSPECTED` | `INCONCLUSIVE` | `INCONCLUSIVE + NUMT_RISK_SUSPECTED` (risk causes downgrade) |
| any | diagnostic window missing/un-callable | configured | any | `INCONCLUSIVE` | `INCONCLUSIVE + DIAGNOSTIC_SITES_NOT_CALLABLE` |
| any | evidence conflict under pack rules | configured | any | `NON_AUTHENTIC` | controlled identity-conflict reason code |
| any | callable evidence but required marker panel absent | configured | empty/missing SCI-007 panel | `INCONCLUSIVE` | marker-missing reason |
| any | required threshold is `null` at runtime | any non-production profile | any | `INCONCLUSIVE` | `THRESHOLD_NOT_CONFIGURED` |
| production | any rule-referenced threshold is `null` | production all-null policy | any | fail-fast before conclusion | no formal decision |
| `FAIL`/`NOT_APPLICABLE` | — | any | any | `INCONCLUSIVE` | transmit M2-① failure reasons |

`NUMT_RISK_SUSPECTED` is never silently ignored: it either attaches a WARN to an otherwise supportable identity result or downgrades the result to `INCONCLUSIVE` when the risk overlaps/blocks diagnostic evidence. It is never a standalone negative identity call. A DRAFT is not unconditionally inconclusive: it can support identity when all diagnostic evidence is callable, while its structural incompleteness remains visible.

### 4. Policy separation and placeholder traceability

The engineering-test policy uses the normal SRR27841063/CM084263 same-data high-consistency expectation only to exercise control flow. Its header records the validation artifact, measured values/range, selected placeholder values, rationale, and the explicit uncalibrated/M3 replacement disclaimer. Production policy remains all-null. Two defenses coexist:

1. the production startup gate rejects rule-referenced nulls (ENG-POL-002); and
2. the module-level decision engine emits `INCONCLUSIVE + THRESHOLD_NOT_CONFIGURED` if a null reaches it.

No scientific number is copied into source code, a default config, or a production policy.

### 5. SCI-007 interface is a typed empty slot

The input contract carries `taxon_group`, `marker_panel_id`, `marker_panel_version`, evidence paths, callable state, summary, and provenance. For M2-② the animal panel is empty/placeholder. The status output preserves this explicit absence; it does not invent a marker or fall back to ITS2. A future marker change can populate the same interface without changing M2-① or the identify status schema.

### 6. Validation and CI gate

`VALIDATION-animal-identify.md` records fixed inputs, reference/policy IDs, status JSON, expected state, actual state, and interpretation for:

1. normal reads: engineering-test policy may produce a callable identify result;
2. low coverage: `INCONCLUSIVE` or an explicit downgrade; and
3. missing reference: fail-fast before decision.

The same normal sample is rerun under production all-null policy and MUST produce `INCONCLUSIVE + THRESHOLD_NOT_CONFIGURED`. T1 covers module logic/reason codes, T2 covers animal routing and state propagation, and T3 covers the end-to-end stub. M2-② cannot be archived until issue #6's image/publish problem is resolved, T1–T3 CI are all green, artifacts are traceable, and `openspec validate --strict` passes.

## Risks / Trade-offs

- **[CM084263 circularity]** → Make the shared BioProject provenance prominent in the pack and validation record; do not call it independent biological validation.
- **[Public-record misidentification]** → Keep NC_023928 quarantined with evidence and block it in the loader; never silently use its label or sequence for calls.
- **[D-loop/gap exclusion reduces available sites]** → Fail closed to `INCONCLUSIVE` when non-risk windows are not callable; never move windows into excluded regions automatically.
- **[Engineering placeholders may leak into production]** → Separate policy IDs/status, header audit trail, startup null gate, runtime null reason code, and CI assertion.
- **[DRAFT identity may be over- or under-called]** → Require callable diagnostic evidence for an `AUTHENTIC` decision and retain `INCOMPLETE_ASSEMBLY`/NUMT warnings.
- **[Empty marker panel limits biological conclusiveness]** → Propagate missing SCI-007 evidence as an explicit gate; do not fabricate marker data.

## Migration Plan

Implement on top of the archived M2-① branch without editing its outputs. Add the animal pack, policy, interface, identify modules/subworkflow, reason codes, tests, and validation record. Run T0/T1/T2/T3 and local three-scenario validation. Resolve the image push/CI issue tracked by #6, then require all T1–T3 jobs green and `openspec validate --strict` before archive. Rollback removes only the new identify assets/modules and change artifacts; M2-① assembly outputs and specs remain intact.

## Open Questions

- The exact minimal on-disk field set for the future real nuclear marker panel can be finalized when SCI-007 is implemented; this change fixes only the empty interface.
- The final independent biological qualification and threshold calibration protocol belongs to later validation work; it cannot alter this change's production-null behavior.
