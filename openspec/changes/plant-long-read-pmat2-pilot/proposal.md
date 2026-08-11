## Why

> **SUPERSEDED:** The full-background PMAT2-first routing assumption in this unarchived change is superseded by `correct-plant-long-read-reference-first`. Preserve this artifact and its run evidence for audit, but do not archive its conflicting `plant-long-read-analysis` delta independently.

M3 needs an evidence-first long-read pilot before any CycloneSEQ transfer decision or production
integration. The repository already contains paired plant short-read and ONT public long-read data
for *Corydalis* in `/mnt/ssd_pool/home/iris-hp/zhongyao/corydalis_test`; this change uses that pair
to evaluate PMAT2 as an EXPERIMENTAL assembly tool, with the M1 short-read assembly as an evidence
anchor rather than as a truth source for production authentication.

## What Changes

- Add a taxon-agnostic long-read QC path using NanoPlot for descriptive QC and one explicitly
  selected read-filter tool (filtlong or chopper), with parameters confined to the experimental
  profile.
- Add a containerized local PMAT2 module, including the method-specified ONT parameters (`-t ont
  -x 0`), version reporting, stub behavior, and T1/T2 tests.
- Add an evaluation workflow comparing PMAT2 output against the M1 short-read evidence anchor and
  PZ405204, including circularity, closure of the M1-measured 38 kb IR gap, sequence concordance,
  homopolymer error-spectrum analysis, and resource-use reporting.
- Record the ONT pilot in `VALIDATION-plant-lr.md` and create a Go/No-Go M3 record with ONT
  evidence populated and CycloneSEQ transfer fields explicitly pending.
- Keep PMAT2 output on the research/evaluation branch: it MUST NOT feed IDENTIFY or DECISION, and
  this change MUST NOT alter PMAT2's EXPERIMENTAL admission tier.

Out of scope: CycloneSEQ transfer validation (the next real-data step), animal long-read work (a
separate change), hybrid assembly (M4), production thresholds, PMAT2 admission-tier promotion, and
any final authentication call from pure long-read evidence.

## Capabilities

### New Capabilities

- `plant-long-read-analysis`: Experimental plant long-read QC, PMAT2 assembly evaluation,
  evidence comparison, resource/error reporting, and M3 Go/No-Go record scaffolding.

### Modified Capabilities

- None. The pilot is deliberately isolated from the existing plant/animal identify and decision
  requirements.

## Impact

- New local Nextflow modules, subworkflow wiring, experimental configuration, container/version
  metadata, and T1/T2 nf-test fixtures.
- New validation and Go/No-Go documents linked through the tool registry and compatibility
  manifest; no production reference pack, policy pack, or decision schema is changed.
- New evaluation outputs will consume the existing M1 plant assembly/read-back contract and the
  ONT dataset `SRR38978847`; platform labels MUST state “ONT platform; CycloneSEQ transferability
  pending real-data validation.”
