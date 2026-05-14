## task 2 requirements here

---

# Assignment 2 formal requirements

## Core information
- **Group work**: Same group as Assignment 1
- **Platform**: LBD Hadoop Cluster (lbd.tuwien.ac.at) with Spark
- **Dataset**: Amazon Review Dataset 2014 (same as Task 1)

## Dataset paths
- **Development set**: `hdfs:///dic_shared/amazon-reviews/full/reviews_devset.json`
- **Full dataset** (optional): `hdfs:///dic_shared/amazon-reviews/full/reviewscombined.json`
- **Local copy**: Available in Task1/requirements/Assets for development
- **Use development set for all submissions and comparisons**

## Environment details (from LDBvars.txt)
- **User**: e12533692
- **Home**: /home/e12533692
- **Host**: jupyter-e12533692
- **OS**: Ubuntu 24.04.3 LTS (Noble Numbat)
- **Kernel**: Linux 5.14.0-611.26.1.el9_7.x86_64
- **Memory**: 61GB total, 49GB available
- **CPUs**: 16 cores
- **Shell**: bash 5.2.21

## Dependencies on Task 1
- Reuses Amazon Review Dataset
- Builds on chi-square feature selection concept
- Compares outputs with Task 1 results (output.txt)
- Same preprocessing rules: tokenization, casefolding, stopword filtering
- Same stopwords.txt file from Task 1

## Part 1: RDDs
### Requirements
- Reimplement Task 1 chi-square calculation using Spark RDDs and transformations
- Calculate chi-square values for all unigram terms per category
- Sort and output top 75 terms per category (descending by chi-square)
- Generate merged dictionary (all terms, alphabetically sorted)
- Output format: identical to Task 1
  - One line per category: `<category> term_1:chi^2 term_2:chi^2 ... term_75:chi^2`
  - One line with merged dictionary (space-separated, alphabetical)

### Deliverables
- **output_rdd.txt**: Generated output from RDD implementation
- **Comparison**: Compare output_rdd.txt with Task 1 output.txt
- **Report section**: Describe observations from comparison

### Key constraints
- Use RDD API only (no DataFrames in this part)
- Apply same preprocessing as Task 1
- Maintain efficiency (runtime considerations apply)

## Part 2: DataFrames/Datasets with Spark ML
### Requirements
- Convert review texts to TF-IDF weighted vector space representation
- Use DataFrame/Dataset API exclusively
- Build transformation pipeline for Part 3
- Select 2000 top terms overall using chi-square

### Pipeline components (use built-in Spark functions)
1. **Tokenization**: whitespaces, tabs, digits, delimiters `()[]{}.!?,;:+=-_"'~#@&*%€$§\/`
2. **Casefolding**: lowercase conversion
3. **Stopword removal**: Use stopwords.txt from Task 1, filter 1-character tokens
4. **TF-IDF calculation**: Term frequency-inverse document frequency
5. **Chi-square selection**: Select 2000 top terms overall

### Deliverables
- **output_ds.txt**: Terms selected by chi-square (2000 terms)
- **Comparison**: Compare with Task 1 term selection
- **Report section**: Describe observations

### Key constraints
- Use Spark ML built-in functions only
- Results may differ from Task 1 (expected, document why)
- Pipeline must be reusable for Part 3

## Part 3: Text classification
### Requirements
- Train multi-class text classifier to predict product category from review text
- Extend Part 2 pipeline with SVM classifier
- Use binary classification strategy for multi-class problem
- Apply L2 vector normalization before classification

### ML experiment design
1. **Data split**: training, validation, test sets
2. **Reproducibility**: Make experiments reproducible
3. **Grid search**: Parameter optimization using Spark functions

### Grid search parameters
- **Chi-square features**: 
  - 2000 terms (from Part 2)
  - Heavier filtering with much less dimensionality (see Spark ML docs)
- **SVM regularization**: 3 different values
- **Standardization**: 2 values (on/off)
- **Max iterations**: 2 values
- **Total combinations**: 2 × 3 × 2 × 2 = 24 configurations

### Evaluation
- Use `MulticlassClassificationEvaluator`
- Metric: F1 measure
- Evaluate on test set
- Report performance indicators for all settings

### Deliverables
- Trained classifier pipeline
- Grid search results table
- Performance comparison
- Result interpretation in report

### Key constraints
- Use development set for training/testing (may downsample for initial runs)
- Final evaluation on full development set (no downsampling)
- Stop Spark contexts after completion
- Shutdown kernels when done

## Code documentation
- Document all code, intermediate outputs, graphs
- Make choices traceable
- If using Spark jobs: very detailed documentation required
- Show data flow and transformations

## Report requirements
### Structure (max 8 pages A4, 11pt font, one column)
1. **Introduction**
2. **Problem overview**
3. **Methodology and approach**
   - Pipeline figure (max 1 page)
   - Illustrate strategy and data flow
4. **Results**
   - Performance indicators over different settings
   - Result interpretation
5. **Conclusions**

### Additional requirements
- List contributing group members at beginning
- Inactive members should not be listed (receive 0 points)
- If no names listed, all members considered contributing

## Submission files
Package as `<groupID>_DIC2026_Assignment_2.zip`:
```
output_rdd.txt           # Part 1 results
output_ds.txt            # Part 2 results
report.pdf               # Max 8 pages
src/                     # Source directory
  ├── notebook.ipynb     # Jupyter notebook(s) - preferred
  └── *.py               # Or documented Spark jobs
```

## Efficiency considerations
- Implementation efficiency crucial for scoring
- Avoid unnecessary overheads and calculations
- Test with small data samples first
- Do not probe data with non-Spark packages
- Monitor resource usage, kill jobs if needed
- Cluster has 48-hour kernel time limit (extended from 2 hours)
- Always stop Spark contexts after finishing
- Always shutdown kernels when not in use
- Plan ahead, avoid last-minute cluster congestion

## Execution modes
### Local development
1. Jupyter notebooks with local dataset files
2. Load reviews_devset parts from Task1/requirements/Assets
3. Develop and test locally first

### Cluster execution options
1. **JupyterHub environment** (interactive)
   - Best for development and testing
   - 48-hour kernel time limit
   - Stop kernels when done
   - Cannot directly access HDFS in notebook kernel

2. **spark-submit (local mode)**
   - Convert notebook: `jupyter nbconvert --to script script.ipynb`
   - Run: `spark-submit script.py`
   - Can use HDFS paths
   - Outputs to local filesystem/terminal

3. **spark-submit (distributed mode)**
   - Run: `spark-submit --master yarn --deploy-mode cluster script.py`
   - Can use HDFS paths
   - View logs: `yarn logs -applicationId <application_id>`
   - Write outputs to HDFS: `hdfs:///user/<username>/output`

4. **Interactive shells**
   - `pyspark` (Python)
   - `spark-shell` (Scala)

See `~/dataLAB/demos/pyspark_local_vs_yarn.ipynb` on cluster for examples.

## Scoring breakdown
| Component | Points |
|-----------|--------|
| Part 1 (RDDs) | 30 |
| Part 2 (DataFrames) | 25 |
| Part 3 (Classification) | 25 |
| Code documentation | 10 |
| Report | 10 |
| **Total** | **100** |

---

# Suggested technology stack

## Core requirements
- **Python**: 3.12.x (cluster version)
- **Apache Spark**: 3.x (cluster-provided)
- **PySpark**: Core API for all parts
- **Spark ML**: Built-in machine learning library
- **HDFS client**: Cluster-provided for data access
- **Jupyter**: Notebook environment (preferred)

## Python libraries (minimal dependencies)

### Required (cluster-provided)
```
pyspark              # Core Spark API
```

### Spark ML components (built-in, no install needed)
```python
# Part 1: RDD operations
from pyspark import SparkContext, SparkConf
from pyspark.rdd import RDD

# Part 2: DataFrame/Dataset operations
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import *
from pyspark.ml.feature import (
    Tokenizer,              # Or RegexTokenizer
    StopWordsRemover,
    HashingTF,             # Or CountVectorizer
    IDF,
    ChiSqSelector,
    Normalizer
)
from pyspark.ml import Pipeline

# Part 3: Classification
from pyspark.ml.classification import LinearSVC, OneVsRest
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.tuning import ParamGridBuilder, CrossValidator
```

### Optional (for development only)
```
jupyter              # Already on cluster
papermill            # If converting notebooks to scripts with outputs
```

## Project structure
```
Task2/
├── materials/
│   ├── Assignment_2_Instructions.pdf
│   └── req.md                          # This file
├── src/
│   ├── part1_rdd.ipynb                 # Part 1: RDD implementation
│   ├── part2_pipeline.ipynb            # Part 2: DataFrame pipeline
│   ├── part3_classification.ipynb      # Part 3: SVM classifier
│   ├── common.py                       # Shared utilities
│   ├── settings.py                     # Configuration (paths, params)
│   └── run_all.py                      # Execute all parts sequentially
├── output/
│   ├── output_rdd.txt                  # Part 1 results
│   └── output_ds.txt                   # Part 2 results
└── report/
    └── report.pdf                      # Final report
```

## Implementation strategy

### Phase 1: Setup and data loading
1. Create SparkSession with appropriate configuration
2. Load development dataset (local or HDFS)
3. Parse JSON reviews into DataFrame/RDD
4. Load stopwords from Task1/requirements/Assets/stopwords.txt

### Phase 2: Part 1 (RDD approach)
1. Extract (category, reviewText) pairs
2. Tokenize using string operations
3. Apply stopword filtering
4. Calculate document-term presence matrix
5. Compute chi-square statistics per category
6. Sort and select top 75 terms per category
7. Merge and sort all unique terms
8. Format output matching Task 1

### Phase 3: Part 2 (DataFrame approach)
1. Build Spark ML pipeline:
   - RegexTokenizer → StopWordsRemover → CountVectorizer → IDF → ChiSqSelector
2. Fit pipeline on dataset
3. Extract selected 2000 terms
4. Save pipeline for Part 3

### Phase 4: Part 3 (Classification)
1. Extend Part 2 pipeline with Normalizer
2. Add LinearSVC with OneVsRest for multi-class
3. Split data: train/validation/test
4. Configure ParamGridBuilder with specified parameters
5. Run CrossValidator or TrainValidationSplit
6. Evaluate best model on test set
7. Record F1 scores for all configurations

### Phase 5: Comparison and reporting
1. Compare output_rdd.txt vs output.txt (Task 1)
2. Compare output_ds.txt vs Task 1 terms
3. Analyze performance metrics
4. Create pipeline visualization
5. Write report sections

## Configuration recommendations

### Spark session configuration
```python
spark = SparkSession.builder \
    .appName("Task2-Assignment2") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()
```

### Local development paths
```python
LOCAL_DEVSET = "../Task1/requirements/Assets/reviews_devset.part_*.json"
LOCAL_STOPWORDS = "../Task1/requirements/Assets/stopwords.txt"
```

### HDFS paths (for cluster submission)
```python
HDFS_DEVSET = "hdfs:///dic_shared/amazon-reviews/full/reviews_devset.json"
HDFS_FULL = "hdfs:///dic_shared/amazon-reviews/full/reviewscombined.json"
```

### Chi-square selector settings
```python
# Part 2: Select top 2000 terms overall
chi_selector = ChiSqSelector(
    numTopFeatures=2000,
    featuresCol="tfidf_features",
    outputCol="selected_features",
    labelCol="category_index"
)

# Part 3: Grid search with heavier filtering
chi_params = [2000, 500]  # or [2000, 1000], etc.
```

### SVM grid search parameters
```python
from pyspark.ml.tuning import ParamGridBuilder

param_grid = ParamGridBuilder() \
    .addGrid(chi_selector.numTopFeatures, [2000, 500]) \
    .addGrid(svm.regParam, [0.01, 0.1, 1.0]) \
    .addGrid(svm.standardization, [True, False]) \
    .addGrid(svm.maxIter, [50, 100]) \
    .build()
```

## Best practices
1. **Start small**: Test on subset of development set first
2. **Cache strategically**: Cache RDDs/DataFrames used multiple times
3. **Monitor resources**: Check Spark UI for job progress
4. **Fail fast**: Set reasonable timeouts
5. **Clean up**: Always call `spark.stop()` at end
6. **Version control**: Track notebook versions locally
7. **Document inline**: Add comments explaining each step
8. **Reproducibility**: Set random seeds for train/test splits

## Risk mitigation
- **Cluster downtime**: Develop locally with sample data first
- **Kernel timeouts**: Break work into smaller execution blocks
- **Memory issues**: Reduce data sample size for initial testing
- **HDFS access**: Test HDFS paths with small reads first

## Notes
- Spark ML may produce different results than Task 1 mrjob implementation
- Document and explain any differences in report
- Focus on correctness, efficiency, and clear documentation

---

# Project structure

```
Task2/
├── .venv/                       # Virtual environment (ignored)
├── .gitignore
│
├── data/
│   └── readme.md                # Local dev data location
│
├── materials/
│   ├── Assignment_2_Instructions.pdf
│   └── req.md
│
├── src/
│   ├── settings.py              # Paths, constants, Spark configs
│   ├── common.py                # Shared utilities (load stopwords, helpers)
│   │
│   ├── part1_runner.py          # Part 1: Execute full RDD pipeline
│   ├── part1_load.py            # Load JSON as RDD
│   ├── part1_tokenize.py        # Tokenization + stopword filter (RDD ops)
│   ├── part1_chi_square.py      # Chi-square calculation (RDD ops)
│   ├── part1_aggregate.py       # Top-k selection and merge (RDD ops)
│   ├── part1_output.py          # Format and save output_rdd.txt
│   │
│   ├── part2_runner.py          # Part 2: Execute DataFrame pipeline
│   ├── part2_load.py            # Load JSON as DataFrame
│   ├── part2_tokenizer.py       # Tokenizer transformer setup
│   ├── part2_stopwords.py       # StopWordsRemover transformer setup
│   ├── part2_vectorizer.py      # CountVectorizer/HashingTF transformer
│   ├── part2_idf.py             # IDF estimator setup
│   ├── part2_chi_selector.py    # ChiSqSelector transformer setup
│   ├── part2_pipeline.py        # Build and fit ML Pipeline
│   ├── part2_output.py          # Extract terms, save output_ds.txt
│   │
│   ├── part3_runner.py          # Part 3: Execute classification pipeline
│   ├── part3_data_split.py      # Train/validation/test split
│   ├── part3_normalizer.py      # Normalizer transformer setup
│   ├── part3_svm_estimator.py   # LinearSVC estimator setup
│   ├── part3_pipeline.py        # Extend Part 2 pipeline with classifier
│   ├── part3_grid_builder.py    # ParamGridBuilder configuration
│   ├── part3_cross_validator.py # CrossValidator setup and execution
│   ├── part3_evaluator.py       # MulticlassClassificationEvaluator
│   └── part3_output.py          # Save metrics, F1 scores, comparison
│   │
│   └── run_all.py               # Master script: runs all 3 parts sequentially
│
├── output/
│   ├── output_rdd.txt           # Part 1 results
│   ├── output_ds.txt            # Part 2 results
│   ├── part3_metrics.json       # Part 3 grid search results
│   └── part3_comparison.txt     # Part 3 performance comparison
│
└── presentation/
    └── presentation.md          # Report draft
```
- Use development set for all deliverables (avoid full dataset to reduce cluster load)

---

# Development log

## 2026-05-13: Project initialization

### Structure created
- 27 Python modules organized by functional Spark blocks
- Part 1: RDD operations (6 modules)
- Part 2: DataFrame/Pipeline transformers and estimators (8 modules)
- Part 3: Classification with grid search (9 modules)
- Core: settings.py, common.py, run_all.py

### Settings configuration
Updated `settings.py` with runtime environment switching:
- **RUN_LOCAL** env var: Toggle between local and cluster execution
- **Local mode**: Uses merged devset from data/, 4GB memory, local[*] master
- **Cluster mode**: Uses HDFS paths, 8GB memory, YARN master with 4 executors
- Separate Spark configs for each environment
- Path resolution via pathlib for cross-platform compatibility
- Debug flag via DEBUG env var

### Dependencies
Created `requirements.txt` with minimal dependency:
- **pyspark==4.1.1** - Only external dependency required
- All other functionality uses Python stdlib (os, pathlib, json, re)
- Cluster already provides PySpark, requirements.txt for local development only

### Runner architecture
**Why runners are .py not .sh:**
- Python runners can import modules, manage SparkSession lifecycle
- Direct Spark configuration and orchestration in Python
- Executable via `python part1_runner.py` locally or `spark-submit part1_runner.py` on cluster
- Shell scripts would add unnecessary indirection layer
- Python runners maintain type safety and can use shared utilities

### Runtime usage
```bash
# Local execution
RUN_LOCAL=true python src/part1_runner.py

# Cluster execution
RUN_LOCAL=false spark-submit src/part1_runner.py

# Or via run_all
python src/run_all.py
```

### Shell wrappers
Created executable shell scripts for clean invocation:
- `run_part1.sh`, `run_part2.sh`, `run_part3.sh` - Individual part runners
- `run_all.sh` - Master orchestrator

**Features:**
- Auto-detect RUN_LOCAL env var (defaults to true)
- Local mode: calls `python part*_runner.py`
- Cluster mode: calls `spark-submit part*_runner.py`
- Pass through all arguments: `./run_part1.sh --arg value`
- Set exec permissions via `chmod +x`

**Usage:**
```bash
# Local execution (default)
./src/run_part1.sh

# Cluster execution
RUN_LOCAL=false ./src/run_part1.sh

# Run all parts
./src/run_all.sh

# With output redirection
./src/run_part1.sh > logs/part1.log 2>&1
```

**Packaging-ready:** Common pattern for distributable Python projects - abstracts runtime details from users.

### Common utilities
Updated `common.py` with Task1-aligned constants and functions:

**Field name constants:**
- All JSON field names from Amazon review dataset as constants
- Makes code more maintainable and refactor-safe

**Tokenization constants:**
- `TOKEN_DELIMITER_PATTERN` - Same regex as Task1 for consistency
- `MIN_TOKEN_LENGTH = 2` - Filter single-character tokens

**Functions:**
- `load_stopwords()` - Load stopword set from file
- `create_spark_session()` - Uses settings.SPARK_CONFIG for environment-aware session
- `safe_parse_review()` - JSON parsing with error handling
- `extract_category_text()` - Extract (category, reviewText) tuple
- `tokenize_text()` - Split text using delimiter pattern
- `filter_tokens()` - Remove stopwords and short tokens
- `compute_chi_square()` - Chi-square statistic on 2x2 contingency table (document-presence)

All utilities adapted from Task1 for compatibility and reuse existing logic.

### Sample data extraction
Created `data/extract_sample.sh` for cluster execution:

**Purpose:** Extract 5000-record sample from cluster HDFS for local development

**Features:**
- Reads from `hdfs:///dic_shared/amazon-reviews/full/reviews_devset.json`
- Outputs `reviews_devset_5k.json` (5000 records)
- Copies `stopwords.txt` from Task1
- Validates JSON format
- Shows sample record for verification
- Provides scp download commands

**Usage on cluster:**
```bash
cd ~/Task2/data
./extract_sample.sh

# Then download to local machine:
scp e12533692@lbd.tuwien.ac.at:~/Task2/data/reviews_devset_5k.json .
scp e12533692@lbd.tuwien.ac.at:~/Task2/data/stopwords.txt .
```

**Why 5000 records:**
- Full devset is ~14k records (0.1% sample of 14M)
- 5k provides sufficient variety for local testing
- Fast iteration during development
- Keeps git repo size manageable

### Data extraction fixes (2026-05-13)
Fixed `data/extract_sample.sh` path resolution:

- Uses `SCRIPT_DIR` (script location) to resolve all paths absolutely
- Derives repo root from script location: `SCRIPT_DIR/../..`
- Tries 3 stopwords sources in order:
  1. `$REPO_ROOT/Task1/requirements/Assets/stopwords.txt` (git repo)
  2. `$SCRIPT_DIR/stopwords.txt` (already downloaded)
  3. `/dic_shared/assets/stopwords.txt` (HDFS mirror, if cluster provides it)
- Outputs to `$SCRIPT_DIR/reviews_devset_5k.json`
- Added tarball packaging hint for scp download

Updated `settings.py`:
- `LOCAL_DEVSET` checks for `data/reviews_devset_5k.json` first (extracted sample), falls back to Task1 dev parts
- `LOCAL_STOPWORDS` checks `data/stopwords.txt` first, falls back to Task1 assets

Updated `.gitignore`:
- Excludes extracted data files: `reviews_devset_5k.json`, `stopwords.txt`, `task2_dev_data.tar.gz`

### Schema verification (2026-05-14)
Verified DataFrame column mapping against sample data:

- 5000 rows, 0 nulls on reviewText and category
- FIELD_REVIEW_TEXT = "reviewText" matches schema
- FIELD_CATEGORY = "category" matches schema
- Spark 4.1.1 + Java 21 required for local dev (Java 25 incompatible with Hadoop viewfs)

Path fix in common.py:
- `load_reviews_df()` reads locally via Python `open()` then `parallelize()` to avoid Hadoop GlobFilter issues with `[]` in workspace paths.
- On cluster HDFS paths are passed directly to `spark.read.json()`.

