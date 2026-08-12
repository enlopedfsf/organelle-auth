## Why

The first animal ONT pilot retained 824 reads but 90% of alignment records were MAPQ=0 and Flye produced a 41 kb draft against a 14.5 kb target before empty-consensus failure. The input subsample is user-verified, but recruitment purity and the provenance of the retained subset require an evidence-first audit before any parameter change.

## What Changes

- Audit the complete 2.18 GB subsample, gzip integrity, read statistics, and fixed-seed sampling provenance.
- Stratify recruited reads by length, alignment span, identity, MAPQ, and low-complexity measures.
- Compare recruited read identities and sequence evidence with the frozen M2-① animal anchor.
- Produce an independent validation record covering the reviewed A/B diagnostics, approved C/D repair, Flye sensitivity controls, an independent Raven comparison, and HYP-DNA-002 read-level evidence.
- Close the animal ONT evaluation with a five-link failure attribution while preserving `EXPERIMENTAL`, topology `INCONCLUSIVE`, and `decision=NOT_APPLICABLE`.

## Capabilities

### New Capabilities

- `animal-long-read-analysis`: Diagnostic audit and evidence isolation for animal ONT recruitment, including the explicit rule that plant recruitment parameters cannot be reused as animal defaults.

### Modified Capabilities

- None.

## Impact

Adds diagnostic and read-audit scripts, machine-readable manifests, tests, Raven as an experimental comparator, and `VALIDATION-animal-lr.md` evidence under the animal experimental route. It does not modify plant routes, production decision paths, PMAT2 eligibility, or CycloneSEQ status.
