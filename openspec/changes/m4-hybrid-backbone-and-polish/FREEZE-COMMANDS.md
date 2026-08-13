# M4 pre-arm freeze commands

All commands below ran before any of the twelve arm/taxon evaluations. Public evaluation short reads use the established seed-11 approximately 2 Gb paired inputs; no full-data override was authorized. CycloneSEQ remains `PENDING_REAL_DATA`.

## Deterministic paired split

Both taxa used `scripts/m4_freeze_inputs.py` with salt `m4-hybrid-v1`, source selection seed 11, `source-data-type public_evaluation`, pigz 2.8 with `-n -1 -p 4 -c`, and separate `short-read-splits-v2` directories. Exact source/output paths and hashes are in the two JSON manifests and `MANIFEST.sha256`.

Plant result: 6,671,740 total pairs = 5,336,938 training + 1,334,802 held-out. Animal result: 6,659,067 total pairs = 5,328,722 training + 1,330,345 held-out. Four source gzip files and eight split gzip files passed full integrity checks. Assignment is exclusive by construction and both manifests record pair-ID-stream hashes.

## R1 reproduction

For each taxon, round one used:

```text
flye-minimap2 -x map-ont -t 4 B0.fasta recruited.fastq.gz > round1.paf
racon -w 500 -q 10.0 -e 0.3 -m 3 -x -5 -g -4 -t 4 recruited.fastq.gz round1.paf B0.fasta > round1.fasta
```

Round two remapped the same frozen recruited reads to `round1.fasta`, ran the identical Racon command, and stopped. Runtime: Flye-bundled minimap2 `2.24-r1155-dirty`; compatible Racon `v1.4.20`. Fresh `backbones-v2` reproduction yielded SHA256 values identical to the prior R1 outputs for both taxa: plant `6744d1...0735`, animal `c7f60c...cc47`.

## Animal core-mask candidate

Assembler and M2-anchor projections used Flye-bundled minimap2 `2.24-r1155-dirty`:

```text
flye-minimap2 -x asm5 -c --cs=long --secondary=yes -N 20 -t 4 animal.B0 animal.Raven > raven-vs-b0.paf
flye-minimap2 -x asm5 -c --cs=long --secondary=yes -N 20 -t 4 animal.B0 M2-anchor.fasta > m2-anchor-vs-b0.paf
```

Training callability used no held-out reads:

```text
flye-minimap2 -ax sr --sam-hit-only -t 4 animal.B0 animal.train.R1.fastq.gz animal.train.R2.fastq.gz |
  samtools view -b -F 0x904 -q 20 - |
  samtools sort -@ 4 -o training.primary.q20.bam -
samtools depth -aa -q 20 -Q 20 training.primary.q20.bam > training.depth.tsv
```

`scripts/m4_build_animal_core_mask.py` then retained Flye non-repeat single-edge contigs with exactly-one local MAPQ-60 Raven and M2-anchor target projection and training depth at least one, excluding multiply projected bases and trimming 500 bp at each continuous block boundary. The candidate BED contains 10,692 bp: `contig_1:500-2441`, `contig_3:515-3800`, and `contig_3:4839-10305`. Flye repeat `contig_2`, the 39-bp multiply projected overlap, unanchored sequence, and junction flanks are excluded. These are local sequence-evaluation blocks only; global query order and adjacency are not interpreted. This BED remains pending validation/evidence-owner review and is not yet an authorization to start the twelve arms.

```bash
python3 scripts/m4_build_animal_core_mask.py \
  --assembly-info /home/iris-hp/Project/organelle-auth-ci-fix/runs/output/animal-lr-recruitment-diagnostics/D/flye-baseline-rep1-2.9.6/assembly_info.txt \
  --raven-paf openspec/changes/m4-hybrid-backbone-and-polish/evidence/animal-core-mask/raven-vs-b0.paf \
  --anchor-paf openspec/changes/m4-hybrid-backbone-and-polish/evidence/animal-core-mask/m2-anchor-vs-b0.paf \
  --depth openspec/changes/m4-hybrid-backbone-and-polish/evidence/animal-core-mask/training.depth.tsv \
  --bed openspec/changes/m4-hybrid-backbone-and-polish/evidence/animal-core-mask/animal-core.bed \
  --metadata openspec/changes/m4-hybrid-backbone-and-polish/evidence/animal-core-mask/animal-core.metadata.json \
  --boundary-trim 500 --minimum-depth 1
```

## Frozen P/C and held-out protocols

P arms use BWA-MEM `0.7.19` build `h577a1d6_1`: `bwa index candidate.fasta`; `bwa mem -t 4 -a candidate.fasta train.R1.fastq.gz > train.R1.sam`; the same command for R2; then `polypolish filter --orientation auto --low 0.1 --high 99.9` and one `polypolish polish --debug polypolish.debug.tsv` pass with Polypolish 0.7.1 defaults and without `--careful`.

C arms use `flye-minimap2 -ax sr --sam-hit-only -t 4`, samtools 1.20 primary mapped filter `-F 0x904 -q 20`, sort/index, followed by bcftools 1.21 `mpileup -Ou -q 20 -Q 20 -d 20000000 -L 20000000 -a FORMAT/DP,FORMAT/AD -f`, `call --ploidy 1 -m -v -Ou`, `norm -f -m -both -Oz`, and the frozen training-only filter `QUAL>=30 && FORMAT/DP[0]>=10 && FORMAT/AD[0:1]/FORMAT/DP[0]>=0.8`; the filtered VCF is indexed and applied once with `consensus -f`. The high ceilings are nonbinding for the frozen input and prevent default high-copy truncation. No held-out evidence, result-driven filters, or extra rounds are allowed. Machine-readable commands are in `evidence/arm-protocols.json`.

Held-out candidate evaluation repeats the registered minimap2/samtools mapping independently for each arm. `evidence/evaluation-policy.json` freezes callability and allele evidence at MAPQ 20, baseQ 20, depth 10, QUAL 30, ALT fraction 0.8, and homopolymer run length 4. These are experiment-only preregistered values, not production thresholds.
