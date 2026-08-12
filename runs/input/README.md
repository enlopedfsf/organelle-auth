# Canonical input directory

Put the samplesheet used by the fixed launcher here as:

```text
runs/input/samplesheet.csv
```

The samplesheet may reference FASTQ files elsewhere (absolute paths are recommended for
external storage). To intentionally use another samplesheet, set `ORG_AUTH_INPUT` when
calling `scripts/run_organelleauth_fixed.sh`.

The current canonical Corydalis M3 inputs are symlinked under `runs/input/corydalis/`:

```text
SRR38978847-ont-2Gb.fastq.gz       ONT processing input (~2 Gb)
SRR38978846_M1_plastome.fasta      M1 GetOrganelle anchor
```

The launcher automatically supplies the M1 anchor when this file exists. Set
`ORG_AUTH_M1_ANCHOR` only when intentionally using another verified anchor.

The canonical run layout is:

```text
runs/input/   input samplesheet and optional staged inputs
runs/output/  published results and pipeline reports
runs/work/    Nextflow task work directories and resume cache
```

The canonical Whitmania animal pilot inputs are under `runs/input/whitmania/`:

```text
SRR27841065-long.fastq.gz  symlink to the preserved raw file on /mnt/ssd_pool
m2_anchor/                 frozen M2-① WTM_NORMAL DRAFT scaffold and QC evidence
CHECKSUMS.sha256           checksums for the staged anchor files
```

The raw ONT file is intentionally not copied into the repository. Its authoritative
location is `/mnt/ssd_pool/home/iris-hp/zhongyao/whitmania_test/SRR27841065-long.fastq.gz`;
its size is recorded in `source-manifest.tsv` (hashing this 21 GB file is deliberately
not part of staging).
Nextflow runs must use `${projectDir}/runs/input`, `${projectDir}/runs/output`, and
`${projectDir}/runs/work`; do not launch from ad-hoc directories or publish into hashed
`work/` paths as a user-facing result location.

If an input or result appears missing, search in this order: (1) this directory and
`runs/output/`, (2) the current repository caches `runs/work/` and `work/`, (3) the
preserved raw-data root `/mnt/ssd_pool/home/iris-hp/zhongyao/`, including
`whitmania_test/m2_animal_identify_validation_v2/normal_isolated/`,
`normal_production_null/`, and `work_normal/`, (4) the legacy repository's `work/`
and `runs/work/`, and only then other legacy paths. Historical Nextflow `work/<hash>/`
trees are cache/intermediate locations, not canonical evidence paths; when a cache
contains authoritative evidence, copy or register a stable manifest under `runs/input/`
or `runs/output/` rather than relying on its hash directory.
```
