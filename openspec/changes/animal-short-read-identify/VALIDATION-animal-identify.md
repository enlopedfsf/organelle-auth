# M2-② animal identify validation (engineering record)

Status: implementation in progress; no scientific call is claimed until the CI/image gate in issue #6 is green.

The local data files were verified non-empty before any pipeline attempt:

| Scenario | Input | Reference/policy | Expected |
|---|---|---|---|
| normal | `/mnt/ssd_pool/home/iris-hp/zhongyao/whitmania_test/SRR27841063_{1,2}.fastq.gz` | `tcm-animal-cm084263-v0.1` + `tcm-animal-engineering-test-0.1.0` | callable engineering result; DRAFT may be `AUTHENTIC + WARN` |
| low coverage | M2-① low-coverage fixture/read-back evidence | same pack + engineering policy | `INCONCLUSIVE` or explicit downgrade; never a forced call |
| reference missing | normal input with pack path removed | no fallback | fail-fast before `DECISION_ENGINE` |
| production replay | normal input | `tcm-animal-production-null-0.1.0` | `INCONCLUSIVE + THRESHOLD_NOT_CONFIGURED` |

The CM084263 match is circular by construction: the reference and validation data share the BioProject provenance chain. It is workflow reproducibility/lineage consistency, not independent biological validation. `NC_023928.1` remains `QUARANTINED` and is not decision-eligible; the 87.62% divergence and Ye et al. (2015) evidence are linked from the pack manifest to the archived M2-① validation record.

The first stub-run attempt was blocked before workflow execution because the workstation sandbox could not fetch the remote Nextflow config dependency (`curl: (7) failed to open socket: Operation not permitted`). This is an execution-environment blocker, not a passed scenario. T1–T3 and the real-data JSON outputs remain pending until the canonical CI image/config path is available; issue #6 is the hard archive gate.
