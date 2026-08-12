import json, subprocess, sys
from pathlib import Path

def test_diagnostics_manifest_has_mapq0_and_deduped_anchor():
    p=Path('runs/output/animal-lr-recruitment-diagnostics/B/diagnostics.json')
    d=json.loads(p.read_text())
    assert d['B']['alignment_records']==5816
    assert d['B']['unique_recruited_reads']==824
    assert d['B']['mapq']['mapq0']==5215
    assert d['B']['anchor_intersection']==743

def test_diagnostics_script_help():
    assert subprocess.run([sys.executable,'scripts/animal_lr_diagnostics.py','--help'],capture_output=True).returncode==0
