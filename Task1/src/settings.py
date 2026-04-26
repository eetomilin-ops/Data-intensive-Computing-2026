# Shared configuration constants for local and Hadoop execution.

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent    # resolve project-relative paths from any source module
REQUIREMENTS_DIR = PROJECT_ROOT / "requirements"        # locate planning and requirement assets stored in the repository
ASSETS_DIR = REQUIREMENTS_DIR / "Assets"                # locate provided stopwords and local development input shards
STOPWORDS_PATH = ASSETS_DIR / "stopwords.txt"           # default stopword file used by preprocessing
LOCAL_DEV_INPUTS = (
    ASSETS_DIR / "reviews_devset.part_1.json",
    ASSETS_DIR / "reviews_devset.part_2.json",
    ASSETS_DIR / "reviews_devset.part_3.json",
    ASSETS_DIR / "reviews_devset.part_4.json",
)                                                       # default local development inputs for smoke tests and local runner checks
FULL_DATASET_HDFS_PATH = "/dic_shared/amazon-reviews/full/reviewscombined.json"    # default full-dataset HDFS input path for final cluster execution
DEV_DATASET_HDFS_PATH = "/dic_shared/amazon-reviews/full/reviews_devset.json"      # default development-set HDFS input path for cluster sanity checks
TARGET_PLATFORM = "LBD public Hadoop cluster via JupyterLab shell"    # verified deployment target for this project
TARGET_PYTHON_VERSION = "3.12"                                         # keep local implementation aligned with the cluster interpreter family
TARGET_HADOOP_VERSION = "3.3.6"                                        # record the verified Hadoop client and runtime version
TARGET_MRJOB_VERSION = "0.7.4"                                         # record the verified mrjob version on the target cluster
DEFAULT_LOCAL_RUNNER = "local"                                         # standard local execution mode for debugging and smoke tests
DEFAULT_CLUSTER_RUNNER = "hadoop"                                      # standard distributed execution mode for target runs
TOP_K_TERMS = 75                                                        # number of highest-scoring terms retained per category
MIN_TOKEN_LENGTH = 2                                                    # filter out single-character tokens after tokenization
TOKEN_DELIMITER_PATTERN = r"[\s\d\(\)\[\]\{\}\.\!\?\,\;\:\+\=\-_\"'`~#@&\*%€\$§\\/]+"    # assignment-defined delimiter pattern for unigram tokenization
COUNTER_TAG_TOTAL_DOCS = "N"                                           # tag global document count records emitted by the counting job
COUNTER_TAG_CATEGORY_DOCS = "NC"                                       # tag category-level document count records emitted by the counting job
COUNTER_TAG_TERM_DOCS = "NT"                                           # tag per-term document count records emitted by the counting job
COUNTER_TAG_TERM_CATEGORY_DOCS = "NTC"                                 # tag per-term-per-category document count records emitted by the counting job
DEFAULT_COUNTS_DIRNAME = "counts"                                      # standard intermediate output directory name for aggregated count records
DEFAULT_META_FILENAME = "meta.json"                                    # standard metadata file name for total and category document counts
DEFAULT_RANKED_DIRNAME = "ranked_terms"                                # standard intermediate output directory name for scored top-k results
DEFAULT_OUTPUT_FILENAME = "output.txt"                                 # required final output file name for the assignment
FULL_DATASET_HDFS_PATH = "/dic_shared/amazon-reviews/full/reviewscombined.json"    # default full-dataset HDFS input path for final cluster execution
DEV_DATASET_HDFS_PATH = "/dic_shared/amazon-reviews/full/reviews_devset.json"      # default development-set HDFS input path for cluster sanity checks
TARGET_PLATFORM = "LBD public Hadoop cluster via JupyterLab shell"                  # verified deployment target for this project
TARGET_PYTHON_VERSION = "3.12"                                                       # keep local implementation aligned with the cluster interpreter family
TARGET_HADOOP_VERSION = "3.3.6"                                                      # record the verified Hadoop client and runtime version
TARGET_MRJOB_VERSION = "0.7.4"                                                       # record the verified mrjob version on the target cluster
DEFAULT_LOCAL_RUNNER = "local"                                                       # standard local execution mode for debugging and smoke tests
DEFAULT_CLUSTER_RUNNER = "hadoop"                                                    # standard distributed execution mode for target runs
TOP_K_TERMS = 75                                                                      # number of highest-scoring terms retained per category
MIN_TOKEN_LENGTH = 2                                                                  # filter out single-character tokens after tokenization
TOKEN_DELIMITER_PATTERN = r"[\s\d\(\)\[\]\{\}\.\!\?\,\;\:\+\=\-_\"'`~#@&\*%€\$§\\/]+"    # assignment-defined delimiter pattern for unigram tokenization
COUNTER_TAG_TOTAL_DOCS = "N"                                                         # tag global document count records emitted by the counting job
COUNTER_TAG_CATEGORY_DOCS = "NC"                                                     # tag category-level document count records emitted by the counting job
COUNTER_TAG_TERM_DOCS = "NT"                                                         # tag per-term document count records emitted by the counting job
COUNTER_TAG_TERM_CATEGORY_DOCS = "NTC"                                               # tag per-term-per-category document count records emitted by the counting job
DEFAULT_COUNTS_DIRNAME = "counts"                                                    # standard intermediate output directory name for aggregated count records
DEFAULT_META_FILENAME = "meta.json"                                                  # standard metadata file name for total and category document counts
DEFAULT_RANKED_DIRNAME = "ranked_terms"                                              # standard intermediate output directory name for scored top-k results
DEFAULT_OUTPUT_FILENAME = "output.txt"                                               # required final output file name for the assignment