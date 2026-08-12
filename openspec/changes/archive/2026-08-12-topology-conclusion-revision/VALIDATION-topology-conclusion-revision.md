# Topology conclusion revision review

Platform: ONT  
Decision: `NOT_APPLICABLE`  
Formal topology: `INCONCLUSIVE`

## Frozen evidence

| Evidence | SHA-256 |
|---|---|
| `SRR38978847.reads_to_flye.paf` | `5c7b69fcf42aa1b22c6e9fa0c7ba571f06b99f9e86db590b76d82df92a09f460` |
| Flye candidate FASTA | `b8d56a6f4e8d38a08d5668faa36b481eb75e12133a67652d21c6d5871d55cf0b` |
| reference rotations FASTA | `2b5ebb51a10ddb7905a2743c75f67c6f29cc1f6d24adcc0b20e90c67cd5545db` |

The ledger uses 500-bp candidate contig-1-end and contig-2-start flanks, deduplicates by read
identity, and counts all target placements when evaluating unique anchoring.

## Ledger result

| Class | Reads |
|---|---:|
| All MAPQ-inclusive junction candidates | 587 |
| MAPQ-zero ambiguous | 517 |
| Copy-ambiguous (multiple flank placements) | 17 |
| Non-unique anchor (additional target placement) | 53 |
| Qualifying independent-support candidates | 0 |

Machine-readable evidence is in:
`runs/output/topology-conclusion-revision/evidence-ledger.json` and `.tsv`.

The 587 count is therefore not a qualifying independent-support count. Even the 53 reads with
one alignment on each requested flank have an additional target placement and fail the unique
anchor condition. The ledger deliberately does not treat MAPQ or two-copy weighting as proof of
uniqueness.

## Recommendation

The `6.5 independent_alignment_support` conditions are not satisfied by the current evidence.
The formal topology remains `INCONCLUSIVE`; no `CLOSED`, `CIRCULAR`, or `DE_NOVO` revision is
proposed. Archived M3 prose and all IDENTIFY/DECISION_ENGINE routes remain unchanged.
