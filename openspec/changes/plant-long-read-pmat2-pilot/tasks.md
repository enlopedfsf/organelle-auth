## 1. Contracts, assets, and experimental routing

- [ ] 1.1 Add an explicit `long_read_pilot` samplesheet/parameter contract for paired plant short-read and ONT long-read inputs; reject missing, empty, corrupt, or mismatched pairs before execution (DATA-006).
- [x] 1.2 Add a pilot-specific output root and route that is unreachable from `IDENTIFY`/`DECISION_ENGINE`; add schema/traceability entries documenting research-only PMAT2 evidence (SCI-003, SCI-006, REL).
- [x] 1.3 Verify the local `corydalis-test-0.1` PZ405204 asset and the archived M1 SRR38978846 assembly/read-back contract; create an evaluation manifest containing the M1 38 kb IR-gap coordinates or an explicit `not_assessable` state.
- [ ] 1.4 Verify `/mnt/ssd_pool/home/iris-hp/zhongyao/corydalis_test/SRR38978846_{1,2}.fastq.gz` and `SRR38978847-long.fastq.gz` exist, are non-empty, and pass gzip/FASTQ integrity checks before any pipeline run.

## 2. Long-read QC and PMAT2 modules

- [ ] 2.1 Add NanoPlot QC using an nf-core module with descriptive pre/post-filter reports and no production threshold defaults (TEST-001).
- [ ] 2.2 Add the local filtlong process, its container/environment metadata, experimental-only parameter injection, stub, and `versions.yml`; record filtered-read counts and checksums.
- [ ] 2.3 Probe and pin a bioconda/container PMAT2 version and digest; implement the local PMAT2 process with `-t ont -x 0`, deterministic output staging, resource trace, version report, and stub behavior.
- [ ] 2.4 Add PMAT2 output validation: non-empty assembly, expected metadata/graph handling, structured `FAIL`/`INCONCLUSIVE` status, and no identify/decision channel emission.

## 3. Evaluation workflow

- [ ] 3.1 Implement the plant long-read pilot subworkflow consuming filtered ONT reads and M1 short-read evidence read-only.
- [ ] 3.2 Implement sequence comparison against PZ405204 and the M1 short-read assembly, recording aligned span, identity, conflicts, gaps, tool versions, and command provenance without hardcoded acceptance thresholds.
- [ ] 3.3 Implement coordinate-aware circularity and 38 kb IR-gap closure assessment with `closed`/`not_closed`/`not_assessable` outcomes and evidence references; never force circularization or gap filling.
- [ ] 3.4 Implement the reusable homopolymer error-spectrum procedure: scan maximal SR homopolymer intervals, lift through the fixed alignment, stratify LR-vs-SR substitutions/indels and run-length deltas by reference run length, record callable/ambiguous coordinates, and emit versioned TSV/JSON outputs that can be rerun unchanged for CycloneSEQ.
- [ ] 3.5 Add normalized resource accounting (wall time, CPU, peak memory, disk, input/output sizes) and a machine-readable evaluation JSON.

## 4. Tests and regression protection

- [ ] 4.1 Add T1 tests for paired-input validation, NanoPlot/filtlong parameter provenance, PMAT2 arguments, version/output contracts, and empty-output failure.
- [ ] 4.2 Add T2 tests for pilot routing isolation, M1 read-only consumption, IR-gap result states, error/resource records, and failure propagation.
- [ ] 4.3 Record T3 as intentionally not run because the ONT fixture is too large for a routine smoke; ensure CI does not report it as green or silently skip the rationale.
- [ ] 4.4 Run plant/animal short-read regression tests and existing T0 schema/lint gates to prove no M1/M2 decision route changes.

## 5. Real-data validation and Go/No-Go record

- [ ] 5.1 Run PMAT2 end-to-end on the Corydalis ONT fixture with the paired SR anchor and record the exact command, platform, versions, digest, and resource trace.
- [ ] 5.2 Write `VALIDATION-plant-lr.md` with input integrity, QC, assembly status, circularity, IR-gap closure, PZ405204/SR concordance, homopolymer spectrum, resources, and explicit ONT/CycloneSEQ limitations.
- [x] 5.3 Write the M3 Go/No-Go document skeleton; populate ONT evidence and leave CycloneSEQ transfer fields `PENDING_REAL_DATA`.
- [x] 5.4 Update `registries/tools.yaml` validation_record for PMAT2 without changing `EXPERIMENTAL` admission, and reconcile the compatibility manifest versions.

## 6. Final validation

- [ ] 6.1 Run `openspec validate --all --strict`, JSON/YAML/schema checks, nf-core lint, and affected nf-test suites; resolve all failures.
- [ ] 6.2 Confirm PMAT2 output is absent from IDENTIFY/DECISION inputs and that archived M1/M2 artifacts and plant/animal short-read behavior are unchanged.
- [ ] 6.3 Review the pilot's Go/No-Go evidence and explicitly record that no CycloneSEQ transfer or admission-tier promotion is authorized by this change.
