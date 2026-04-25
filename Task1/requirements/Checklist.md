**index**
1. Project setup
2. Input and schema validation
3. Text preprocessing
4. Chi-square pipeline
5. Output generation
6. Report and documentation
7. Packaging and submission

**check1**
[ ] Use python mrjob for the implementation.
[ ] Keep all paths relative inside the submitted solution.
[ ] Parameterize the input path so the dev set and full HDFS dataset can both be supplied.
[ ] Prepare a run script that executes all jobs in the correct order with all required parameters.

**check2**
[ ] Read input as line-delimited JSON where each line is one review document.
[ ] Validate that required fields are handled correctly, especially reviewText and category.
[ ] Confirm the implementation works with the provided dev-set files.
[ ] Treat the split dev-set parts as equivalent to the original dev set for local testing.

**check3**
[ ] Tokenize reviewText into unigrams.
[ ] Use whitespaces, tabs, digits, and the characters ()[]{}.!?,;:+=-_"'`~#@&*%€$§\/ as delimiters.
[ ] Apply case folding.
[ ] Remove stopwords using stopwords.txt.
[ ] Remove tokens that consist of only one character.

**check4**
[ ] Compute chi-square values for unigram terms for each category.
[ ] Use document-per-category counting, not raw term frequency.
[ ] Count a term once per review document for category statistics.
[ ] Design efficient MapReduce key-value pairs for intermediate and final stages.
[ ] Keep the implementation efficient enough for the full dataset evaluation.
[ ] Rank terms within each category by descending chi-square value.
[ ] Retain exactly the top 75 terms per category.
[ ] Merge retained terms from all categories into one dictionary.

**check5**
[ ] Generate output.txt from the development set.
[ ] Output one line per category in alphabetic order.
[ ] Format each category line as <category name> term:chi^2_value term:chi^2_value ...
[ ] Ensure each category line contains exactly 75 terms.
[ ] Add one final line with the merged dictionary.
[ ] Sort merged dictionary terms alphabetically and separate them with spaces.

**check6**
[ ] Document all code clearly.
[ ] Explain method signatures.
[ ] Explain all chosen <key,value> pairs for map, combine, partition, sort, and reduce stages.
[ ] Write report.pdf with Introduction, Problem Overview, Methodology and Approach, and Conclusions.
[ ] Include one pipeline figure in the Methodology and Approach section.
[ ] Show data flow and all input, intermediate, and output key-value pairs in the figure.
[ ] Keep the report within 8 A4 pages.

**check7**
[ ] Create the submission archive named <groupID>_DIC2026_Assignment_1.zip.
[ ] Include output.txt in the archive.
[ ] Include report.pdf in the archive.
[ ] Include src/ with all documented source code.
[ ] Include the run script in the archive.
[ ] Verify the submission is ready before April 28, 2026 at 23:59.