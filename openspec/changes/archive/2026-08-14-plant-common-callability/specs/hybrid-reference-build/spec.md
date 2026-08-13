## ADDED Requirements

### Requirement: Plant polishing preferences use a pre-registered common-callable denominator

When arm-specific callable denominators materially differ and a plant polishing preference is assessed, the capability SHALL permit a separate pre-registered common-callability addendum. The addendum MUST use the frozen held-out evidence, candidates, region definitions, and experimental policy from the parent evaluation; MUST intersect uniquely projected callable B0-coordinate bases across all six arms; and MUST NOT alter the parent candidates, thresholds, historical metrics, or conclusion (SCI-004, SCI-005, ENG-POL-003, TEST-005).

#### Scenario: Six-arm common intersection is computed

- **WHEN** all six frozen plant arms provide checksum-matching candidate-to-B0 projections, held-out depth records, residual ledgers, region definitions, and evaluation policy
- **THEN** the addendum emits a B0-coordinate common-callable intersection shared by all six arms
- **AND** every retained base is uniquely projected and meets the unchanged held-out callability rule in every arm

#### Scenario: Missing or ambiguous evidence blocks comparison

- **WHEN** a required artifact is missing, empty, checksum-inconsistent, multiply projected, or cannot be assigned under the pre-registered coordinate rule
- **THEN** the analysis fails closed or excludes that base with a machine-readable reason
- **AND** it does not infer a denominator or route preference from incomplete evidence

#### Scenario: Fair denominator table is emitted

- **WHEN** the common-callable intersection is non-empty
- **THEN** every arm and region reports `projected_bases`, `callable_bases`, `callable_fraction`, `residual_loci`, and `residual_rate_per_10kb`
- **AND** the combined common-callable denominator is identical across arms

#### Scenario: Addendum answers only the registered residual-lead question

- **WHEN** residual loci are recounted on the common-callable intersection
- **THEN** the addendum classifies R1P1 as `RETAINS_SOLE_LEAD`, `TIED_LOWEST`, or `DOES_NOT_LEAD` using the pre-registered combined residual-rate rule
- **AND** region rows remain descriptive and cannot override the combined result
- **AND** the result is not represented as a new topology, authentication, production-default, or full M4 dominance decision

#### Scenario: Parent evidence remains immutable

- **WHEN** the common-callability addendum is completed
- **THEN** the archived M4-① evidence and validation text remain byte-for-byte unchanged
- **AND** the addendum records its own provenance, commands, checksums, exclusions, and validation status
