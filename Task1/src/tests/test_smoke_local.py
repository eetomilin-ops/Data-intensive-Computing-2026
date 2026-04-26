import sys, os, json, subprocess, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from settings import LOCAL_DEV_INPUTS

SRC_DIR = os.path.join(os.path.dirname(__file__), "..")

# runs the full local pipeline against the dev shards and checks output.txt exists
def test_smoke_local():
    with tempfile.TemporaryDirectory() as outdir:
        result = subprocess.run(
            ["bash", os.path.join(SRC_DIR, "run_pipeline.sh"), "--output", outdir],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"pipeline failed:\n{result.stderr}"
        output_file = os.path.join(outdir, "output.txt")
        assert os.path.isfile(output_file), "output.txt not produced"
        lines = open(output_file).readlines()
        # last line is the merged dictionary, lines before are category lines
        assert len(lines) >= 2, "expected at least one category line plus dictionary"
        # each category line must start with a word and contain term:score pairs
        first_cat = lines[0].strip().split()
        assert len(first_cat) > 1
        assert ":" in first_cat[1]

if __name__ == "__main__":
    test_smoke_local()
    print("smoke test passed")