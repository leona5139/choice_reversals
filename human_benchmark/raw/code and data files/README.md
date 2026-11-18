# Fairness and Time Inconsistency

This repo contains the files needed to generate the manuscript for our paper.

## Automatic running

1. Downloand/clone this repo
2. Run the Makefile in the Fairness folder

## How this works

The Makefile does the following steps:

- Strips some columms from the raw data CSV files, saving the output in `data-deidentified`.
- Cleans the de-identified data using R, saving it in `data-clean`
- Runs Stata file `code/regressions.do` on this clean data to create some of the regressions
- Runs R script `code/plots.R` to create the plots and descriptive statistics, saving them in `output/plots`
- Runs `latexmk` on the paper TeX source file to compile the paper PDF

## Where to find results

All results in the paper can be verified in either `code/plots.R` or `code/regressions.do`.  The R script contains the code for all figures, as well as various descriptive statistics and tables in the text. All regression results are calculated in the Stata file.  The code in these two files should appear in the same order as the corresponding results in the text.


