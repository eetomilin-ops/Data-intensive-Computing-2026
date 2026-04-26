import re, sys, os, json, subprocess, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from settings import LOCAL_DEV_INPUTS, TOP_K_TERMS

SRC_DIR = os.path.join(os.path.dirname(__file__), "..")

_PAIR_RE = re.compile(r'^[^:\s]+:-?\d+(?:\.\d+)?$')

def _run_pipeline(outdir):
    result = subprocess.run(
        ["bash", os.path.join(SRC_DIR, "run_pipeline.sh"), "--output", outdir],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"pipeline failed:\n{result.stderr}"
    output_file = os.path.join(outdir, "output.txt")
    assert os.path.isfile(output_file), "output.txt not produced"
    return open(output_file).read().splitlines()

# runs the full local pipeline against the dev shards and checks output.txt exists
def test_smoke_local():
    with tempfile.TemporaryDirectory() as outdir:
        lines = _run_pipeline(outdir)
        # last line is the merged dictionary, lines before are category lines
        assert len(lines) >= 2, "expected at least one category line plus dictionary"
        # each category line must start with a word and contain term:score pairs
        first_cat = lines[0].strip().split()
        assert len(first_cat) > 1
        assert ":" in first_cat[1]

# validates structural format of the full pipeline output
def test_output_format():
    with tempfile.TemporaryDirectory() as outdir:
        lines = _run_pipeline(outdir)
        assert len(lines) >= 2, "need at least one category line plus dictionary"
        category_lines = lines[:-1]
        dict_line      = lines[-1]

        # categories must be alphabetically sorted
        cats = [ln.split()[0] for ln in category_lines if ln.split()]
        assert cats == sorted(cats), f"categories not alphabetical: {cats}"

        # each category line must have exactly TOP_K_TERMS term:score pairs, scores non-increasing
        all_terms = []
        for i, ln in enumerate(category_lines, start=1):
            parts = ln.split()
            pairs = parts[1:]
            assert len(pairs) == TOP_K_TERMS, (
                f"line {i} ({parts[0]}): expected {TOP_K_TERMS} pairs, got {len(pairs)}"
            )
            scores = []
            for tok in pairs:
                assert _PAIR_RE.match(tok), f"line {i}: malformed token {tok!r}"
                term, score_str = tok.rsplit(":", 1)
                all_terms.append(term)
                scores.append(float(score_str))
            for j in range(len(scores) - 1):
                assert scores[j] >= scores[j + 1], (
                    f"line {i} ({parts[0]}): scores not non-increasing at position {j}"
                )

        # dictionary line must be alphabetically sorted, no duplicates, equal to union of category terms
        dterms = dict_line.split()
        assert dterms == sorted(dterms), "dictionary line not alphabetically sorted"
        assert len(dterms) == len(set(dterms)), "dictionary line has duplicate terms"
        union_terms = sorted(set(all_terms))
        assert dterms == union_terms, (
            f"dictionary mismatch: missing={sorted(set(union_terms)-set(dterms))[:5]}, "
            f"extra={sorted(set(dterms)-set(union_terms))[:5]}"
        )

if __name__ == "__main__":
    test_smoke_local()
    print("smoke test passed")