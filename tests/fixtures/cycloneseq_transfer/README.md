# CycloneSEQ transfer engineering fixtures

These fixtures exercise contract logic only. They contain no real CycloneSEQ observation, no calibrated scientific threshold, and no truth-bearing production sample identity.

FASTQ integrity, pairing, checksum, manifest-repair, and allow-list cases are generated inside a temporary test directory so committed fixtures cannot be mistaken for delivered data. `outcome-scenarios.json` exercises all nine pre-written outcome branches under the explicitly uncalibrated engineering-test policy.
