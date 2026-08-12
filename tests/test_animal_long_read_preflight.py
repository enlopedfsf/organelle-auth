import json
import subprocess
from pathlib import Path


def test_animal_preflight_passed_real_inputs():
    d = json.loads(Path("runs/output/animal-long-read-pilot/preflight.json").read_text())
    assert d["status"] == "PASS"
    assert d["m2_status"]["assembly_grade"] == "DRAFT"
    assert d["decision"] == "NOT_APPLICABLE"
    assert d["cycloneseq"] == "PENDING_REAL_DATA"


def test_animal_preflight_fails_missing_input(tmp_path):
    out = tmp_path / "out.json"
    cmd = ["python3", "scripts/animal_long_read_preflight.py", "--reads", str(tmp_path / "missing"),
           "--reference", "assets/reference_packs/tcm-animal-cm084263-v0.1/CM084263.1.fasta",
           "--metadata", "assets/reference_packs/tcm-animal-cm084263-v0.1/manifest.json",
           "--anchor", "runs/input/whitmania/m2_anchor/WTM_NORMAL_mitogenome.scaffold.fasta",
           "--status", "runs/input/whitmania/m2_anchor/WTM_NORMAL.assembly_qc.status.json", "--output", str(out)]
    assert subprocess.run(cmd).returncode == 2
    assert json.loads(out.read_text())["status"] == "FAIL"
