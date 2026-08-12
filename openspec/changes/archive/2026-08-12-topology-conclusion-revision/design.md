## Context

The topology experiment demonstrated that MAPQ filtering changes aggregate counts but did not establish unique flanking anchors. This change is an evidence-audit layer over immutable M3 and experiment outputs.

## Goals / Non-Goals

**Goals:** create a per-read support ledger, apply the complete 6.5 contract, and issue a governed conclusion recommendation.

**Non-Goals:** new assembly, parameter search, production calibration, or authentication.

## Decisions

- Use existing read-to-contig PAF and candidate/reference alignments as immutable inputs; re-mapping is allowed only if needed to recover missing tags and must be versioned.
- Classify every candidate as `QUALIFYING`, `COPY_AMBIGUOUS`, `NON_UNIQUE_ANCHOR`, or `INSUFFICIENT_FLANK`; no aggregate shortcut.
- Emit recommendation and formal state separately; archived files remain unchanged until a later approved sync.

## Risks / Trade-offs

- [PAF lacks anchor uniqueness metadata] → require explicit reference-anchor remapping or classify as unassessable.
- [MAPQ is not a uniqueness proof] → use sequence-coordinate uniqueness and read identity, not MAPQ alone.
- [Evidence may overturn an earlier label] → preserve append-only provenance and require separate approval.

## Migration Plan

Run as an isolated review, archive the report, and sync the main capability spec only after review approval.
