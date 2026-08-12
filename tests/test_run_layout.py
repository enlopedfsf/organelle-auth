from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_canonical_paths_are_declared():
    config = (ROOT / "nextflow.config").read_text()
    launcher = (ROOT / "scripts/run_organelleauth_fixed.sh").read_text()
    assert 'run_root                   = "${projectDir}/runs"' in config
    assert 'outdir                       = "${projectDir}/runs/output"' in config
    assert 'work_dir                    = "${projectDir}/runs/work"' in config
    assert 'INPUT_DIR="${PROJECT_ROOT}/runs/input"' in launcher
    assert 'OUTPUT_DIR="${PROJECT_ROOT}/runs/output"' in launcher
    assert 'WORK_DIR="${ORG_AUTH_WORK:-${PROJECT_ROOT}/runs/work}"' in launcher


def test_launcher_has_fail_fast_input_guard_and_no_data_deletion():
    launcher = (ROOT / "scripts/run_organelleauth_fixed.sh").read_text()
    assert '[[ ! -s "${INPUT_FILE}" ]]' in launcher
    assert "rm -" not in launcher
    assert "mv " not in launcher


def test_input_policy_documents_legacy_cache_safety():
    readme = (ROOT / "runs/input/README.md").read_text()
    assert "runs/output/" in readme
    assert "runs/work/" in readme
    assert "do not launch from ad-hoc directories" in readme
