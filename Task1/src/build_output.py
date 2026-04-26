from __future__ import annotations
import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any
from settings import (
    COUNTER_TAG_CATEGORY_DOCS, COUNTER_TAG_TOTAL_DOCS,
    DEFAULT_COUNTS_DIRNAME, DEFAULT_META_FILENAME,
    DEFAULT_OUTPUT_FILENAME, DEFAULT_RANKED_DIRNAME,
    TOP_K_TERMS,
)

# reads the first-job output directory and extracts N and all Nc values
# into a small dict that the scoring job can load from a single file
def extract_meta_counts(counts_path: str | Path) -> dict[str, Any]:
    meta = {"N": 0, "Nc": {}}
    counts_path = Path(counts_path)
    for part in sorted(counts_path.glob("part-*")):
        with open(part, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                raw_key, raw_value = line.split("\t", 1)
                key = json.loads(raw_key)
                value = json.loads(raw_value)
                tag = key[0]
                if tag == COUNTER_TAG_TOTAL_DOCS:
                    meta["N"] += int(value)
                elif tag == COUNTER_TAG_CATEGORY_DOCS:
                    cat = key[1]
                    meta["Nc"][cat] = meta["Nc"].get(cat, 0) + int(value)
    return meta

def write_meta_json(meta: dict[str, Any], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(meta, f)
    return output_path

# reads the second-job output directory; each line is (category, "t1:s1 t2:s2 ...")
def read_ranked_terms(ranked_path: str | Path) -> dict[str, list[tuple[str, float]]]:
    result = {}
    ranked_path = Path(ranked_path)
    for part in sorted(ranked_path.glob("part-*")):
        with open(part, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                raw_key, raw_value = line.split("\t", 1)
                cat = json.loads(raw_key)
                terms_str = json.loads(raw_value)
                pairs = []
                for fragment in terms_str.split():
                    term, score = fragment.rsplit(":", 1)
                    pairs.append((term, float(score)))
                result[cat] = pairs
    return result

# formats one category line in the required output format
def format_category_line(cat: str, ranked: list[tuple[str, float]]) -> str:
    parts = " ".join(f"{t}:{s:.4f}" for t, s in ranked[:TOP_K_TERMS])
    return f"{cat} {parts}"

def merge_dictionary(category_terms: dict[str, list[tuple[str, float]]]) -> list[str]:
    vocab = set()
    for pairs in category_terms.values():
        for term, _ in pairs:
            vocab.add(term)
    return sorted(vocab)

def write_output(
    category_terms: dict[str, list[tuple[str, float]]],
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for cat in sorted(category_terms):
            f.write(format_category_line(cat, category_terms[cat]) + "\n")
        merged = merge_dictionary(category_terms)
        f.write(" ".join(merged) + "\n")
    return output_path

# bundles src/, output.txt, and report.pdf into the submission zip
def package_submission(
    source_root: str | Path,
    output_txt: str | Path,
    report_pdf: str | Path,
    archive_path: str | Path,
) -> Path:
    archive_path = Path(archive_path)
    source_root  = Path(source_root)
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(output_txt, "output.txt")
        if Path(report_pdf).exists():
            zf.write(report_pdf, "report.pdf")
        src_dir = source_root / "src"
        for fpath in sorted(src_dir.rglob("*.py")) + sorted(src_dir.rglob("*.sh")):
            zf.write(fpath, Path("src") / fpath.relative_to(src_dir))
    return archive_path

def main():
    import argparse
    parser = argparse.ArgumentParser(description="build output.txt and optionally package submission")
    parser.add_argument("--counts",  required=True, help="path to CountStatsJob output dir")
    parser.add_argument("--ranked",  required=True, help="path to ScoreTopKJob output dir")
    parser.add_argument("--output",  default=DEFAULT_OUTPUT_FILENAME)
    parser.add_argument("--meta",    default=DEFAULT_META_FILENAME)
    parser.add_argument("--package", default=None, help="if set, path for the submission zip")
    parser.add_argument("--src-root",default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--report",  default="report/report.pdf")
    args = parser.parse_args()
    meta = extract_meta_counts(args.counts)
    write_meta_json(meta, args.meta)
    ranked = read_ranked_terms(args.ranked)
    write_output(ranked, args.output)
    print(f"output written to {args.output}")
    if args.package:
        pkg = package_submission(args.src_root, args.output, args.report, args.package)
        print(f"submission archive: {pkg}")

if __name__ == "__main__":
    main()