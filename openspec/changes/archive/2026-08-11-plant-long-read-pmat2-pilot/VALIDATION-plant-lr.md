# VALIDATION-plant-lr (M3 reference-first correction)

## Scope and claim boundary

This is an ONT-only method exercise using public `SRR38978847`, paired with the actual M1
DNBSEQ/GetOrganelle result for `SRR38978846`. It is not CycloneSEQ evidence and it does not emit
an authentication decision. The route remains `EXPERIMENTAL`; `IDENTIFY` and `DECISION_ENGINE`
receive none of its outputs. CycloneSEQ transferability and Go/No-Go remain
`PENDING_REAL_DATA`.

The historical PMAT2-first attempt sent the whole shallow-WGS background into
PMAT2/NextDenovo correction and stopped on a whole-genome seed-depth assumption. That stopped
run is preserved as evidence; it is not counted as a successful M3 result. The corrected route
is:

`2G-base processing budget -> sensitive rotated-reference mapping -> complete-read recruitment
-> target evidence gate -> Flye subset primary -> one rescue pass -> final Flye -> structural
read-back evidence`, with PMAT2 `-p 0` retained only as an optional comparator.

## Verified inputs

All required files were checked before launch and were non-empty. The ONT gzip stream passed
`pigz -t`; `seqkit stats` parsed it as FASTQ.

| Input | Verified result |
|---|---|
| bounded source ONT FASTQ | 234,066 reads; 2,002,472,632 bp; mean 8,555.2 bp; max 150,493 bp; compressed size 2,026,829,691 bytes |
| ONT input SHA-256 | `76203ec06e2f8c94155dcd696d2b5052c30c629dfdfc15e51830d690aef57490` |
| canonical reference | `PZ405204.1`, one contig, 200,540 bp; SHA-256 `a300e1ba69903c88a2d9ac02f0163092e89fab854093047af3784e094114625b` |
| M1 anchor | actual GetOrganelle output, six scaffolds, 139,697 bp; SHA-256 `c933858a9399c06806e90c23d0312624dd53d52e2edb1bba8cdaa937f353556b` |

The M1 anchor is not replaced by the complete reference. This is essential: the 38 kb gap test
compares long-read evidence against the actual fragmented short-read result.

## Policy and exact route

- Raw input budget: 2,000,000,000 bases, deterministic seed 11, explicitly a processing budget
  rather than a biological sufficiency threshold. It selected 233,787 reads / 2,000,164,198 bp.
- Recruitment mapping: minimap2 2.26-r1175, `-x map-ont -c --cs=long --secondary=yes
  -N 20 -p 0.5`, against four fixed circular-reference rotations.
- Selection retains complete source reads using policy-controlled aligned bases, query fraction,
  and divergence; MAPQ is never the sole exclusion rule.
- Experimental gate values are versioned hypotheses. Production scientific thresholds remain
  null and return `INCONCLUSIVE + THRESHOLD_NOT_CONFIGURED`.
- Flye primary: Flye 2.9.6-b1802, `--nano-hq --genome-size 250k --asm-coverage 50
  --iterations 1 --min-overlap 5000`. The 50x value is an experimental processing cap above
  Flye's documented typical 40x disjointig recommendation, not a production threshold.
- PMAT2 comparator command is fixed to `PMAT autoMito ... -t ont -x 0 -p 0` on the identical
  recruited-subset checksum. Full-background PMAT2 is disabled and is not a fallback.

## Real ONT result

Canonical output root:
`/home/iris-hp/corydalis_validation/out_lr_reference_first_v4/`.

The final pass-one/pass-two metric merge was recomputed with the tested final helper and is under
`plant_long_read_evaluation/lr_gate_final_merged/`; the full Flye and structural outputs are the
successful v4 run.

| Metric | Observed result |
|---|---|
| pass-one recruited subset | 14,784 complete reads; 122,124,762 bp |
| one rescue pass | 2 new reads; hard stop at two passes |
| final recruited subset | 14,786 complete reads; 122,132,426 bp; SHA-256 `93f4fd3bc3969e5d4d3577870b32f4a63d99ddc57a325f84403d7f089531f3c8` |
| merged aligned target bases | 119,250,856 bp |
| estimated target depth | 594.6487x |
| reference breadth | 1.0 |
| median eligible divergence | 0.05077776 |
| circular-origin support | 609 read identifiers |
| M1 gap left/right boundary support | 882 / 937 read identifiers |
| final gate | `ELIGIBLE_EXPERIMENTAL`, no authentication decision |
| final Flye assembly | PASS; 2 contigs: 104,098 bp and 96,046 bp; total 200,144 bp; N50 104,098 bp; mean Flye coverage 595x |
| assembly/reference evidence | reference-coordinate union span 200,521/200,540 bp; best-alignment identity 0.9971434; two forward alignments |
| M1 38 kb IR gap | `closed`: `contig_1` spans `PZ405204.1:96371..134285`; projected candidate interval 99..37957 (0-based); 37 independent ONT reads span with policy flanks |
| topology claim | not a complete single circle: two final contigs remain |
| PMAT2 comparator | `WARN + COMPARATOR_ASSEMBLY_FAILED`, exit 127, `tool_version=UNAVAILABLE`; no comparator assembly is claimed |
| Flye-versus-PMAT2 | `comparator_not_assessable` |
| route decision | `NOT_APPLICABLE` throughout |

The IR result is supported by the candidate/reference alignment and 37 independent read IDs in
`SRR38978847.structural-evidence.json`; it is not inferred from Flye exit status, total length, or
a circular label. Conversely, reference union coverage near 100% is not reported as a single
circular plastome because the candidate has two contigs.

## Homopolymer evidence

The fixed-alignment method scans maximal runs on the M1 anchor and lifts them through minimap2
CIGAR operations; it does not zip sequences by array position. For ONT:

- 337 anchor-run records were emitted;
- 327 were callable (1,175 callable run bases), 10 were unliftable;
- 315/327 callable runs had zero run-length delta;
- 11 runs had delta -1 and one had delta -3;
- aggregate callable events were 0 substitutions, 14 deleted run bases, and 0 inserted run bases.

These observations describe this ONT/M1 alignment only and cannot be transferred to CycloneSEQ.

## Runtime and provenance

The successful v4 run completed 21/21 processes. Selected execution-trace observations:

| Stage | Wall time | Peak RSS |
|---|---:|---:|
| deterministic 2G-base budget | 3m 8s | 23.6 MB |
| pass-one minimap2 mapping | 3m 32s | 2.9 GB |
| pass-one evidence selection | 13.7s | 2.4 GB |
| preliminary Flye | 14m 21s | 5.9 GB |
| rescue mapping | 1m 0s | 2.9 GB |
| final Flye | 13m 3s | 5.7 GB |
| final read-to-candidate mapping | 53.9s | 2.4 GB |
| structural evidence | 2.6s | 344.4 MB |

Nextflow execution trace, timeline, report, DAG, and params JSON are preserved under v4
`pipeline_info/`. Exact minimap2/Flye/PMAT2 commands and observed versions are published beside
each stage artifact.

## Engineering validation

- T1 helper tests: 8/8 PASS, including rotations/quarantine, MAPQ-zero secondary evidence,
  whole-read extraction, two-pass union, production-null gating, route guard, IR closure, and
  CIGAR-based homopolymer lifting.
- T2: full-background guard closed; PMAT2 comparator isolated; LR subworkflow has no channel to
  IDENTIFY/DECISION; identical final subset SHA-256 is recorded for Flye and PMAT2.
- Affected `nf-test`: 2/2 PASS. The M3 stub asserts all 21 processes complete and the isolated
  structural-evidence artifact is published; stubs are not counted as biological success.
- T3: bounded non-stub synthetic 21/21-process route PASS with 440 recruited reads, 21.9408x
  target depth, the two-pass maximum recorded, and Flye invoked with `--asm-coverage 50`. It
  honestly produced three contigs and `not_closed`, proving the test does not force a positive
  structural conclusion. PMAT2 remained a structured unavailable-comparator WARN.
- Real T4-like ONT evidence: successful route and `closed` IR-gap result above. This does not
  satisfy the pending CycloneSEQ transfer gate.
- `openspec validate correct-plant-long-read-reference-first --type change --strict
  --no-interactive`: PASS.

## Final interpretation

The correction succeeds as an engineering and ONT method validation: reference-first recruitment
reduces a 2.0G-base background to a 122.1M-base target subset, Flye assembles a near-reference-size
two-contig candidate, and independent reads support closure of the prior M1 IR gap. It does not
yet deliver a single circular plastome, a working local PMAT2 comparator, a CycloneSEQ transfer
result, or a production authentication decision. Those fields remain explicitly pending or
not assessable.
