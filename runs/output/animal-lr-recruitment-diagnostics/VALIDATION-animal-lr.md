# Animal LR Recruitment Diagnostics and Closeout

Status: `EXPERIMENTAL_COMPLETE`
Platform: ONT
Decision: `NOT_APPLICABLE`
Topology: `INCONCLUSIVE`
Scope: A/B/B+ diagnostics, approved C/D repair, Flye sensitivity, Raven comparator, and HYP-DNA-002. PMAT2 remains gated by Issue #10.

## Executive closeout

The animal ONT pilot supports the M2-①-anchored mitochondrial core, but it does not uniquely resolve the AT-rich control-region adjacency or copy number. The failure attribution is a five-link chain:

1. **Environment bug:** the system Flye 2.9.3 installation lacked `flye-samtools`, producing an empty consensus false failure. A complete Flye 2.9.6 runtime removed that failure.
2. **Recruitment logic bug:** v0.2 combined evidence across different rotated-reference alignments. Coherent v0.2.1 requires one alignment to satisfy all recruitment criteria.
3. **Length-filter repair disproved:** coherent reads have a maximum length of 20,411 bp, so 25-kb and 30-kb upper bounds remove nothing and cannot explain outcome differences.
4. **Assembler run/order sensitivity:** byte-identical Flye inputs diverged, and three fixed read-order shuffles produced three graph structures. Raven also changed from 19,421 to 19,271 bp after read-order shuffling.
5. **AT-rich micro-edge remains unresolved:** Flye and Raven consistently recover the mitochondrial core but traverse/retain different amounts of AT-rich repeat sequence. Read-level evidence does not establish a same-orientation whole-mitogenome concatemer or a unique biological adjacency.

**Final scientific disposition:** animal ONT remains `EXPERIMENTAL`; topology remains `INCONCLUSIVE`; `decision=NOT_APPLICABLE`; outputs remain outside `IDENTIFY` and `DECISION`; PMAT2 remains gated by Issue #10. A circular/self-loop assembler output is not a topology upgrade.

## A — frozen subsample audit

| Field            | Evidence                                                                                              |
| ---------------- | ----------------------------------------------------------------------------------------------------- |
| Input            | `runs/output/animal-long-read-pilot/subsample/SRR27841065.seed11.p10.fastq.gz`                        |
| Compressed bytes | 2,181,678,470                                                                                         |
| Source bytes     | 21,337,311,171                                                                                        |
| Method           | `seqkit sample`, seed 11, fraction 0.1                                                                |
| Integrity        | `gzip -t` and `seqkit stats` user-verified in persistent Bash                                         |
| Provenance       | Recorded in `subsample/manifest.json`; original interactive shell history unavailable to this session |

The 3,734,912 bp / 824-read figure is **not** the subsample size; it is the downstream recruited subset.

## B — recruitment purity audit

Recruitment PAF SHA256: `e871671b2f86a4e3e0ff5e8eb499ef2926a7a6ed73c056afc804853f11d9010c`.

| Metric                                                           |             Result |
| ---------------------------------------------------------------- | -----------------: |
| Alignment records                                                |              5,816 |
| Unique recruited reads                                           |                824 |
| MAPQ 0 records                                                   |    5,215 (89.666%) |
| MAPQ >0 records                                                  |                601 |
| Read length range                                                |       85–70,627 bp |
| Mean read length                                                 |         4,532.7 bp |
| Mean PAF identity (matches/alignment length)                     |             0.9387 |
| Sequence entropy range (whole-read A/C/G/T Shannon, descriptive) | 1.2962–1.9887 bits |
| Mean sequence entropy                                            |        1.7854 bits |
| Reads also aligning to M2-① anchor                               | 743 / 824 (90.17%) |

The M2-① comparison used minimap2 `2.26-r1175`, `-x map-ont -c --cs=long --secondary=yes -N 20 -p 0.5 -t 4`, against `runs/input/whitmania/m2_anchor/WTM_NORMAL_mitogenome.scaffold.fasta`. It is an engineering evidence anchor, not independent biological truth. No complexity cutoff was applied.

## Interpretation and limits

- The 2.18 GB subsample input is not shown to be truncated by this audit; its integrity is user-verified.
- Recruitment is highly ambiguous: 89.666% of alignment records are MAPQ 0, while 743 recruited read identities also align to the M2 anchor.
- The 41,025 bp Flye disjointig versus the 14,393–14,505 bp mitochondrial target remains a measured assembly discrepancy; this appendix does not assign causality.
- The evidence is sufficient to defer animal parameter selection to C. Plant recruitment parameters are not promoted as animal defaults.
- ONT outputs remain experimental and cannot enter `IDENTIFY` or `DECISION_ENGINE`; PMAT2 remains blocked by Issue #10.

## B+ — discrimination experiments (existing recruited subset only)

### Results

| Test                                                                          |                                                             Result | Assessment                                                                                                                                                                                   |
| ----------------------------------------------------------------------------- | -----------------------------------------------------------------: | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Reads >=2 kb / >=5 kb / >=6 kb / >=10 kb                                      |                                              381 / 191 / 169 / 100 | The 2 kb default overlap is not intrinsically impossible, but a 5 kb overlap would exclude most reads; the 5 kb hypothesis is supported as a parameter-risk, not proven as the sole failure. |
| Per-read aligned-fraction histogram                                           |          570/824 reads in 0.9–1.0 bin; 107 below 0.4; 30 below 0.1 | The “all reads only touch 10%” hypothesis is not supported globally; a minority of reads are edge-hit/partial and require stricter recruitment evidence.                                     |
| Identity histogram                                                            | Median 0.9666; mean 0.9387; 3,840/5,816 alignments in 0.95–1.0 bin | No clean two-component NUMT conclusion can be made from this distribution alone; the lower-identity tail is real and overlaps repeat/secondary evidence.                                     |
| M2-① anchor coverage                                                          |       144/144 100-bp bins covered; bin count 124–224, median 163.5 | Coverage is broad and not confined to a small local NUMT-like interval; this argues against a purely local contamination explanation, but does not exclude NUMTs.                            |
| Reads with rotation-0 alignments touching both target ends (<=500 / >=14,000) |                                                       166 read IDs | This is a candidate end-to-start signal only; it is not yet independent junction proof because rotation alignments and MAPQ-0 copies are not unique.                                         |
| Reads >=30 kb                                                                 |                                         13 reads, 565,557 bp total | Long reads exist and are sufficient for a focused repeat audit.                                                                                                                              |
| Preliminary self-alignment ~14.5 kb query-span heuristic                      |                              2 unique reads (4 reciprocal records) | Superseded by HYP-DNA-002: the heuristic measured alignment span rather than repeat offset and did not establish same-orientation anchor units. It must not be cited as multimer evidence.   |

### B+ interpretation

- **Recruitment fraction:** partially supports the concern. Most recruited reads have broad query coverage, so the 10% rule is not the explanation for all 824 reads; partial edge-hit reads are nevertheless present.
- **Flye overlap:** supports a parameter mismatch risk. Only 191 reads are >=5 kb and 169 >=6 kb; a 5-kb overlap policy would sharply reduce usable edges. The actual run used Flye's automatic 2-kb overlap, so the 5-kb setting was not the direct command-line cause of this run.
- **Tandem repeat:** unresolved at B+ and superseded by the direct HYP-DNA-002 audit below. The preliminary self-span count was not a valid whole-unit periodicity test.
- **NUMT:** unresolved. The identity tail and MAPQ-0 dominance are compatible with NUMT/repeat ambiguity, while broad anchor coverage argues against a purely local NUMT cluster. Nuclear-context evidence is absent.

Machine-readable B+ output: `Bplus/bplus.json`; long-read self-alignment: `Bplus/self.paf`.

## C/D — v0.2 repair and controlled Flye rerun

Approved v0.2 parameters were applied without MAPQ filtering: minimum aligned bases 1,000, minimum query aligned fraction 0.5, and minimum identity 0.88. This retained 452/824 reads (2,306,582 bp). Flye was then run with `--nano-raw --genome-size 15k --asm-coverage 50 --iterations 1 --threads 4`; automatic minimum overlap was explicitly recorded as 2,000 bp.

| Run      |      Reads / bases | Estimated coverage | Disjointig support | Draft/disjointig length | Final consensus |
| -------- | -----------------: | -----------------: | -----------------: | ----------------------: | --------------- |
| Original | 824 / 3,734,912 bp |               248x |           10 reads |               41,025 bp | empty; FAIL     |
| v0.2     | 452 / 2,306,582 bp |               153x |           14 reads |               53,672 bp | empty; FAIL     |

The initial v0.2 run under the system Flye 2.9.3 package did not produce a valid final contig. Subsequent forensics established that this was an **environmental false failure**: the installed Flye Python consensus reader invokes `flye-samtools`, but the executable was absent from the system package. The unchecked subprocess failure yielded zero parsed alignments, `Alignment error rate: 0.000000`, an empty consensus FASTA, and the downstream repeat-parser error. A manually reconstructed BAM contained 1,434 mapped records at mean depth 41.26x, disproving zero read support.

The repository already had a complete flat Mamba environment at `/home/iris-hp/miniconda3/envs/flye` with Flye 2.9.6, `flye-minimap2`, and `flye-samtools`. With the v0.2 reads and scientific parameters unchanged, the corrected runtime completed successfully:

| Runtime                                    | Result                                         |
| ------------------------------------------ | ---------------------------------------------- |
| system Flye 2.9.3, missing `flye-samtools` | false FAIL; empty consensus                    |
| Mamba Flye 2.9.6 complete runtime          | PASS; one 22,967 bp contig, 119x, non-circular |

The successful graph contains a 14,303 bp core edge at 119x and an 894 bp AT-rich repeat edge at 552x. Flye traversed that repeat edge 16 times (`edge_1+, edge_2+ x16`). Alignment to M2-① covers the mitochondrial core with 99.93–100% identity; the remaining length is repeat expansion. This is a candidate expanded control-region/tandem-repeat structure, not yet a qualified topology claim.

Filtering forensics also found that v0.2 incorrectly combined query intervals across four rotations and used the best identity from a different alignment. Forty-four reads had no single alignment satisfying all three thresholds, including 10 of the 40 longest reads selected by `--asm-coverage 50`. The corrected v0.2.1 semantics require one coherent alignment record to satisfy aligned bases >=1,000, aligned fraction >=0.5, and identity >=0.88; MAPQ remains unfiltered. It retains 408 reads / 1,895,308 bp. Its controlled Flye 2.9.6 rerun is recorded separately and must be compared before final structural interpretation.

The corrected v0.2.1 rerun completed rather than producing an empty consensus:

| Corrected input                            | Contigs | Total length | Largest contig | Mean coverage | Circular | Disjointig support                          |
| ------------------------------------------ | ------: | -----------: | -------------: | ------------: | -------- | ------------------------------------------- |
| v0.2.1 coherent (408 reads / 1,895,308 bp) |       3 |    17,641 bp |      10,805 bp |          104x | no       | 9 reads (38,338 bp) and 3 reads (27,497 bp) |

The three contigs are 10,805 bp (coverage 130, non-repeat), 3,243 bp (coverage 96, non-repeat), and 3,593 bp (coverage 36, repeat). Anchor alignments cover the core in separate pieces at 99.92–100% identity, while the 3,593-bp repeat contig does not obtain a reliable whole-anchor alignment. The graph has three disconnected paths and no link records connecting the repeat contig to the core. Therefore this run is a completed assembly with unresolved repeat adjacency, not a circular mitochondrial assembly.

The repeat evidence was audited at read level. Among 98 coherent reads with edge-2 (the 894-bp AT-rich repeat edge) alignments, 18 have repeat hits wholly inside a primary anchor-aligned interval, 52 have terminal-overhang hits, and the remainder are boundary or internally unaligned hits (379 repeat alignment records total). Among 72 primary reads spanning anchor coordinates 6,800–8,300, the largest aggregate internal CIGAR insertion was 55 bp and no read contained a kilobase-scale insertion. This does not prove the repeat is absent biologically, but it does not support a 3.6–8.6-kb insertion between unique anchor flanks. The 22,967-bp legacy v0.2 contig, whose path repeats the 894-bp edge 16 times, is consequently an assembly-graph hypothesis and must not be used as a copy-number or topology conclusion.

**C/D disposition:** the runtime defect and the cross-rotation filter defect are fixed and reproducible. The scientific result remains `INCONCLUSIVE`: the animal ONT data support the mitochondrial core but do not resolve the AT-rich repeat adjacency/copy number. ONT stays outside `IDENTIFY`/`DECISION`; PMAT2 stays gated by Issue #10. The approved Raven and HYP-DNA-002 closeout evidence follows below.

## Runtime-tail and length-sensitivity follow-up

The formal plant M3 validation records Flye `2.9.6-b1802` and a non-empty consensus. The only archived 2.9.3 system-runtime products found in this checkout are the topology-experiment retry logs/manifests under `runs/output/topology-resolution-experiments/`; the retry was terminated during minimizer construction before assembly FASTA or GFA output. The archived topology-conclusion-revision inputs are the MAPQ-inclusive PAF/junction recount artifacts and do not reference any 2.9.3 consensus. Thus no archived conclusion is shown to depend on a 2.9.3 consensus product.

The corrected animal length controls were run with Flye `2.9.6-b1802`. The effective FASTQ content (read IDs and sequences) for `v0.2.1-full`, `v0.3-25k`, and `v0.3-30k` is identical because the coherent input's maximum read length is 20,411 bp. Their assembly outcomes were nevertheless not identical: full and 30k produced the same three-contig result (17,641 bp), while the independent 25k run produced one 21,031-bp contig. Therefore the observed difference cannot be attributed to reads removed by the 25-kb cutoff. It is recorded as a repeat-graph/run sensitivity signal pending controlled read-order shuffles, not as evidence that the length filter repaired the assembly.

The 25k and 30k runs used freshly created output directories, no `--resume`, the same Flye version, identical scientific parameters, four requested threads, automatic 2,000-bp minimum overlap, and the same 11,043-bp graph-read cutoff. Their decompressed read-ID/sequence checksum is identical. This excludes stale output state and effective-input differences as explanations for their divergent assemblies.

### Flye run and read-order sensitivity

| Run                  | Input treatment                  | Contigs | Total bp | Circular contig             | Graph interpretation                                                                                                  |
| -------------------- | -------------------------------- | ------: | -------: | --------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| full                 | original order                   |       3 |   17,641 | no                          | 10,805-bp core + 3,243-bp core + 3,593-bp repeat                                                                      |
| 25k                  | byte-identical effective reads   |       1 |   21,031 | no                          | 14,305-bp core edge plus repeated 621/641-bp AT-rich edges; path `2,2,2,3,1` followed by additional edge-1 traversals |
| 30k                  | byte-identical to 25k            |       3 |   17,641 | no                          | same structure as full                                                                                                |
| baseline replicate 1 | exact 25k bytes, fresh directory |       3 |   17,641 | no                          | same structure and assembly SHA-256 as baseline replicate 2                                                           |
| baseline replicate 2 | exact 25k bytes, fresh directory |       3 |   17,641 | no                          | same structure and assembly SHA-256 as baseline replicate 1                                                           |
| shuffle seed 11      | same reads, shuffled order       |       3 |   17,641 | no                          | same structure as full                                                                                                |
| shuffle seed 22      | same reads, shuffled order       |       3 |   15,832 | 2,187-bp repeat contig only | alternative repeat resolution                                                                                         |
| shuffle seed 33      | same reads, shuffled order       |       2 |   16,054 | 1,750-bp repeat contig only | 14,304-bp core plus alternative repeat resolution                                                                     |

The byte-identical 25k/30k pair directly demonstrates run-level nondeterminism under the fixed four-thread command. The exact baseline replicates show that divergence is intermittent rather than guaranteed on every run. The three shuffle outcomes demonstrate an additional read-order sensitivity: three seeds produced three assembly structures. These observations agree with the Flye FAQ statement that Flye is not fully deterministic. Flye 2.9.6 exposes `--deterministic`, whose local help defines it as single-threaded disjointig assembly; upstream Issue #640 records that other random sources remain. The option is therefore a variance-reduction control, not a bit-for-bit reproducibility guarantee.

**Governance consequence:** future authoritative Flye runs use the pinned complete runtime plus `--deterministic`, record effective threads and graph properties, and use property-based CI assertions. Exact assembly hashes, exact lengths, and a single circularity outcome are prohibited as scientific pass/fail contracts. The present divergent graphs reinforce `INCONCLUSIVE`; none qualifies a topology claim.

## Raven independent OLC-family comparator

Raven assembler 1.8.3 was installed in the dedicated flat environment `/home/iris-hp/miniconda3/envs/raven-assembler`; its package LICENSE is MIT. The unrelated Python monitoring package exposed as `/home/iris-hp/miniconda3/bin/raven` version 6.10.0 was explicitly rejected. Raven is registered `EXPERIMENTAL`, comparator-only, and cannot feed `IDENTIFY` or `DECISION`.

The coherent 25-kb and 30-kb inputs are byte-identical, so they were not redundantly run under two labels. Raven instead compared the original coherent order with fixed shuffle seed 22 using `--disable-checkpoints -t 4` in fresh directories.

| Raven input             | Contigs |  Total / max bp | GFA self-loop | Anchor breadth | Full-alignment identity | Gap-compressed core identity | Query insertion vs anchor |
| ----------------------- | ------: | --------------: | ------------- | -------------: | ----------------------: | ---------------------------: | ------------------------: |
| original coherent order |       1 | 19,421 / 19,421 | yes           |           100% |                73.9441% |                     99.9700% |                  5,067 bp |
| shuffle seed 22         |       1 | 19,271 / 19,271 | yes           |           100% |                74.4823% |                     99.9756% |                  4,919 bp |

The low full-alignment identities reflect the large insertions and must not be reported as mitochondrial-core substitution identity. Both assemblies cover the entire 14,393-bp anchor with approximately 99.97% gap-compressed core identity, but their inferred repeat-containing lengths differ by 150 bp. Flye outputs likewise recover high-identity anchor pieces/core while varying in AT-rich repeat traversal. Thus the two assembler families agree on the mitochondrial core and disagree on unique repeat resolution. Raven self-loops are experimental graph evidence, not independent proof of biological circular topology.

### Raven insertion-region read audit

The Raven original-order anchor PAF places the largest inserted segment in assembly coordinates approximately 7,454–12,522 (derived from the `4281M5068I` CIGAR operation). Re-aligning the 408 coherent reads to this Raven assembly finds 28 reads whose assembly-target alignments span both inferred insertion boundaries. This is **support for the assembled path only**, because the reads were aligned to the candidate assembly; it is not an independent proof that those bases occur between the corresponding unique anchor flanks in vivo. The 28 read IDs and PAF are retained at `E/raven-original/reads-vs-assembly.paf`.

The independent unique-flank audit remains the stronger adjacency test: among 72 reads spanning anchor coordinates 6,800–8,300, the largest internal CIGAR insertion was 55 bp and no read contained a kilobase-scale insertion. Accordingly, the evidence does **not** justify the absolute statement that no single read contains any kb-scale insertion, nor does it justify declaring every Raven/Flye inserted base a graph artifact. The defensible conclusion is narrower: the assemblies contain approximately 4.9–5.1 kb of repeat-like sequence, while the current reads do not independently validate its unique-flank adjacency or copy number. Real repeat length and adjacency remain unresolved; topology remains `INCONCLUSIVE`.

Machine-readable evidence: `E/raven-comparison.json` and `E/raven-comparison.tsv`; assemblies/GFAs/logs are under `E/raven-original/` and `E/raven-shuffle-22/`.

## HYP-DNA-002 — AT-rich repeat adjacency and copy-number audit

All 13 reads of at least 30 kb excluded by coherent recruitment were audited directly. The audit used permissive anchor alignments, existing read self-alignments, per-read anchor/query breadth, orientation, identity, flanking sequence, and one SVG dotplot per read. Coherent-filter exclusion was not treated as proof of contamination.

| Classification       | Reads | Evidence grade     |
| -------------------- | ----: | ------------------ |
| `TRUE_MULTIMER`      |     0 | no qualifying read |
| `NUMT_FLANK_CHIMERA` |     1 | `SUGGESTIVE`       |
| `CHIMERIC_JUNK`      |    12 | `SUGGESTIVE`       |

`SRR27841065.1280039` contains a 2,024-bp, 93.29%-identity mt-like segment inside a 48,612-bp read and is therefore suggestive of a NUMT/flank chimera; a nuclear reference is unavailable, so it is not confirmed. `SRR27841065.2946767` is the only read with two near-complete anchor-scale groups, but the groups are in opposite orientations and the second group is below the 0.88 identity audit threshold. It is suggestive of a chimeric structure, not a same-direction mitochondrial concatemer. The other 11 reads contain only short/weak local anchor matches or none.

The audit rule for a near-complete unit was at least 80% anchor breadth and at least 0.88 alignment identity; `TRUE_MULTIMER` additionally required two such units in the same orientation. These are explicit experiment-level classification rules, not production policy thresholds.

**HYP-DNA-002 disposition:** `SUGGESTIVE` for unresolved AT-rich repeat adjacency/copy number because both assemblers retain variable repeat expansions, but the true same-orientation whole-mitogenome multimer sub-hypothesis is `REJECTED` by these 13 reads. No unique-flank/junction/copy-number conclusion is established, so topology remains `INCONCLUSIVE`.

Machine-readable evidence: `F/hyp-dna-002.json` and `F/hyp-dna-002.tsv`; 13 per-read dotplots are under `F/dotplots/`.

## Verification and infrastructure disposition

- Focused regression suite: `17 passed` (`test_animal_lr_filter_v02.py`, `test_animal_lr_diagnostics.py`, `test_organelle_lr_evidence.py`, and `test_animal_lr_closeout.py`).
- Evidence-format checks: both JSON records and `registries/tools.yaml` parsed successfully; all 13 SVG dotplots parsed as XML; both new Python scripts passed bytecode compilation.
- OpenSpec: `openspec validate --strict animal-lr-recruitment-diagnostics` passed.
- nf-test: two attempts, including the required proxy-enabled retry, stopped before test discovery while loading `https://github.com/askimed/nf-test-plugins/main/plugins.json` with `java.io.FileNotFoundException`. This is recorded as `INFRASTRUCTURE_BLOCKED_PLUGIN_REGISTRY`, not a failed test case. No further network retry was made under the two-attempt rule; CI remains authoritative for nf-test execution.

These checks establish local archive readiness while preserving the nf-test infrastructure qualification. They do not change the animal scientific status or decision isolation.

## Reproducibility and local-intermediate policy

The FASTQ, BAM, Flye work directories, indexes, and other large interim files under this run are intentionally excluded from Git. Their SHA-256 values and fixed repository-relative paths are recorded in `MANIFEST.sha256`; the manifest itself is versioned with the closeout evidence. The original long-read source is SRA accession `SRR27841065` and can be re-downloaded. The bounded subsample can be regenerated deterministically with the recorded seed `11` and fraction `0.1`, subject to the recorded source checksum and tool version. Therefore the local intermediates are not the sole copy of the scientific input, while exact output provenance remains auditable through the manifest and commands below.

## Commands

```bash
gzip -t runs/output/animal-long-read-pilot/subsample/SRR27841065.seed11.p10.fastq.gz
seqkit stats -a runs/output/animal-long-read-pilot/subsample/SRR27841065.seed11.p10.fastq.gz
minimap2 -x map-ont -c --cs=long --secondary=yes -N 20 -p 0.5 -t 4 \
  runs/input/whitmania/m2_anchor/WTM_NORMAL_mitogenome.scaffold.fasta \
  runs/output/animal-long-read-pilot/recruited/SRR27841065.recruited.final.fastq.gz \
  > runs/output/animal-lr-recruitment-diagnostics/B/anchor.paf

/home/iris-hp/miniconda3/envs/raven-assembler/bin/raven --disable-checkpoints -t 4 \
  -F runs/output/animal-lr-recruitment-diagnostics/E/raven-original/assembly.gfa \
  runs/output/animal-lr-recruitment-diagnostics/D/recruited.v02.1-coherent.fastq.gz \
  > runs/output/animal-lr-recruitment-diagnostics/E/raven-original/assembly.fasta

/home/iris-hp/miniconda3/envs/raven-assembler/bin/raven --disable-checkpoints -t 4 \
  -F runs/output/animal-lr-recruitment-diagnostics/E/raven-shuffle-22/assembly.gfa \
  runs/output/animal-lr-recruitment-diagnostics/D/recruited.shuffle-22.fastq.gz \
  > runs/output/animal-lr-recruitment-diagnostics/E/raven-shuffle-22/assembly.fasta

/home/iris-hp/miniconda3/envs/minimap2/bin/minimap2 -x map-ont -c --cs=long \
  --secondary=yes -N 100 -p 0.01 \
  runs/input/whitmania/m2_anchor/WTM_NORMAL_mitogenome.scaffold.fasta \
  runs/output/animal-lr-recruitment-diagnostics/Bplus/longreads.fastq \
  > runs/output/animal-lr-recruitment-diagnostics/Bplus/longreads-vs-anchor.paf

python scripts/animal_lr_hyp_dna002.py \
  --reads runs/output/animal-lr-recruitment-diagnostics/Bplus/longreads.fastq \
  --self-paf runs/output/animal-lr-recruitment-diagnostics/Bplus/self.paf \
  --anchor-paf runs/output/animal-lr-recruitment-diagnostics/Bplus/longreads-vs-anchor.paf \
  --anchor-length 14393 \
  --output runs/output/animal-lr-recruitment-diagnostics/F/hyp-dna-002.json \
  --dotplot-dir runs/output/animal-lr-recruitment-diagnostics/F/dotplots
```
