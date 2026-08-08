## ADDED Requirements

### Requirement: compatibility manifest 框架

The system SHALL provide a compatibility manifest framework per §10.3 with fields `compatibility_id`, `pipeline`, `method_spec`, `reference_pack`, `kraken_db`, `policy_pack`, `validation_dataset`. Pipeline, method specification, reference pack, Kraken DB, policy pack and validation dataset SHALL be versioned **independently** and reconciled by `compatibility_id` — they MUST NOT be forced to a single shared version number.

#### Scenario: 独立版本可声明

- **WHEN** a compatibility manifest is authored
- **THEN** each asset carries its own version, reconciled by `compatibility_id`, rather than a single shared version
