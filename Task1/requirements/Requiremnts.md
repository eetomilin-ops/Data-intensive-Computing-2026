**req1**
Output is  single file named <groupID>_DIC2026_Assignment_1.zip that contains:
 - output.txt: results obtained
 - report.pdf: a written report
 - src/: subdirectory containing all documented source code of your MapReduce implementation 
 - script to run all jobs in the correct order with all necessary parameters.

**req2**
Dataset meta
dictionary:
reviewerID - string - the ID of the author of the review
asin - string - unique product identifier
reviewerName - string - name of the reviewer
helpful - array of two integers [a,b] - helpfulness rating of the review: a out of b customers
found the review helpful
reviewText - string - the content of the review; this is the text to be processed
overall - float - rating given to product asin by reviewer reviewerID
summary - string - the title of the review
unixReviewTime - integer - timestamp of when review was created in UNIX format
reviewTime - string - date when review was created in human readable format
category - string - the category that the product belongs to

JSON loaded should conform types and structure

**req3**
conform task description and requirements stated in Assignment_1_Instructions.pdf