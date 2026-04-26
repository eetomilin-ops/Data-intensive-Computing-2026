**index**
1. Submission package
2. Dataset and schema
3. Text preprocessing
4. Chi-square interpretation
5. Output format
6. Report requirements
7. Implementation constraints
8. Scoring and deadline
9. Verified target environment
10. Planned source layout


**req1**
Output is a single file named <groupID>_DIC2026_Assignment_1.zip.
The archive must contain output.txt.
The archive must contain report.pdf.
The archive must contain src/ with all documented source code of the MapReduce implementation.
The archive must contain a script that runs all jobs in the correct order with all necessary parameters.

**req2**
Dataset entries are JSON dictionaries and every input line is one review.
reviewerID - string - the ID of the author of the review.
asin - string - unique product identifier.
reviewerName - string - name of the reviewer.
helpful - array of two integers [a,b] - helpfulness rating of the review: a out of b customers found the review helpful.
reviewText - string - the content of the review and the text to be processed.
overall - float - rating given to product asin by reviewer reviewerID.
summary - string - the title of the review.
unixReviewTime - integer - timestamp of when review was created in UNIX format.
reviewTime - string - date when review was created in human readable format.
category - string - the category that the product belongs to.
JSON loaded should conform to the expected types and structure.
Development data is the provided dev set.
Final evaluation data is the full HDFS dataset reviewscombined.json.

**req3**
Text preprocessing must tokenize to unigrams.
Use whitespaces, tabs, digits, and the characters ()[]{}.!?,;:+=-_"'`~#@&*%€$§\/ as delimiters.
Apply case folding.
Filter stopwords using stopwords.txt.
Filter out tokens consisting of only one character.

**req4**
Calculate chi-square values for all unigram terms for each category.
Chi-square interpretation is document per category.
Use document presence counts per review-category combination rather than raw term frequency counts.
Order the terms by chi-square value within each category.
Preserve the top 75 terms per category.
Merge the retained terms over all categories.

**req5**
Produce output.txt from the development set.
Output one line for each product category in alphabetic order.
Each category line must contain the top 75 most discriminative terms in descending chi-square order.
Required line format is <category name> term_1st:chi^2_value term_2nd:chi^2_value ... term_75th:chi^2_value.
Add one line containing the merged dictionary with all terms space-separated and ordered alphabetically.

**req6**
Produce report.pdf with at least four sections.
Section 1 is Introduction.
Section 2 is Problem Overview.
Section 3 is Methodology and Approach.
Section 4 is Conclusions.

Methodology and Approach section must include one figure that illustrates the full strategy and pipeline.

Figure must show the data flow clearly and indicate all chosen <key,value> pairs for input, intermediate, and output stages.

Overall report must not exceed 8 pages in A4 format.

**req7**
Use the python-based mrjob implementation.
Efficiency is a crucial requirement because final evaluation runs on the full dataset. Reference runtime from previous semesters is under 20 minutes for strong Python implementations.

Document all code, including method signatures and explanations of the <key,value> pairs and all processing classes or stages.

Make sure all paths are relative.
Do not assume files or dependencies outside the submitted archive.
Parameterize the HDFS input path so the full dataset can be supplied easily.

The provided local assets include four split dev-set files and a helper script showing that the original dev set was partitioned round-robin.

**req8**
Conform to the task description and requirements stated in Assignment_1_Instructions.pdf.

**req9**
Target platform is the LBD public Hadoop cluster accessed through a JupyterLab shell.
Verified target Python version is 3.12.3.
Verified target mrjob version is 0.7.4.
Verified target Hadoop and HDFS client version is 3.3.6.
Use Python 3.12 compatible code for implementation and local validation.
Assume the target shell environment is Linux with bash available.
The Jupyter shell currently exposes 16 CPUs and about 61 GiB RAM, but final design should still prioritize Hadoop job efficiency over local machine capacity.

**req10**
Planned source tree must include src/settings.py for shared constants used by all jobs and scripts.
Planned source tree must include src/common.py for parsing, tokenization, scoring, and formatting helpers.
Planned source tree must include src/job_count_stats.py for the first mrjob counting stage.
Planned source tree must include src/job_score_topk.py for the chi-square scoring and top-k stage.
Planned source tree must include src/build_output.py for metadata extraction, output formatting, and packaging helpers.
Planned source tree must include src/run_pipeline.sh for cluster and local orchestration.
Planned source tree must include src/run_local_debug.sh for fast local smoke runs.
Planned source tree may include src/tests/ for narrow local validation.