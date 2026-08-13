## Why

M4-① ranked the six plant polishing arms on arm-specific callable bases, while the archived validation explicitly recorded a 106,968–137,114 bp callability spread and therefore limited the R1P1 preference pending a separately pre-registered common-callability analysis. This change supplies that fair denominator without reopening, rewriting, or replacing the archived M4-① result.

## What Changes

- Pre-register a deterministic six-arm plant callable intersection from the frozen M4-① held-out alignments and unchanged experimental evaluation policy.
- Emit an `arm × region` denominator table with exactly `projected_bases`, `callable_bases`, `callable_fraction`, `residual_loci`, and `residual_rate_per_10kb`.
- Recount existing held-out residual loci only inside the frozen common-callable intersection and answer one question: whether R1P1 still leads on the fair denominator.
- Preserve M4-① as immutable historical evidence; publish this analysis as a separate addendum with its own inputs, checksums, commands, and conclusion.

Out of scope: changing any M4-① candidate, rerunning polishing, changing the held-out set or thresholds, evaluating animal arms, making topology claims, admitting PMAT2 or mitoVGP, interpreting CycloneSEQ, changing production defaults, or emitting an authentication decision. CycloneSEQ remains `PENDING_REAL_DATA`; any transfer validation belongs to the later `cycloneseq-transfer-validation` change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `hybrid-reference-build`: Require a separately pre-registered common-callability addendum when arm-specific callable denominators materially differ and a route preference is being assessed across plant polishing arms.

## Impact

- Adds a deterministic plant common-callability summarizer and focused contract tests.
- Adds lightweight BED/TSV/JSON/checksum evidence under this change; no FASTQ, BAM, CRAM, or historical `runs/` data enter Git.
- Reads the archived M4-① candidates, held-out alignment/callability artifacts, residual ledger, region definitions, and evaluation policy without modifying them.
- Does not alter `IDENTIFY`, `DECISION`, production routing, tool admission tiers, or any archived M4-① file.
