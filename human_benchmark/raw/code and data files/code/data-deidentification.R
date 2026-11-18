### data-deidentification.R
### 
### This script reads in all the files in the raw data folder,
### strips them of selected information that could be used to identify
### the individual, and writes the de-identified data to the 
### data/deidentified folder.


#### Libraries ####

suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(purrr))
suppressPackageStartupMessages(library(stringr))

#### Constants ####

num_skipped <- 0
num_deidentified <-0


#### Script #####

cat("\n\nStarting data de-identification...\n")

for (filename in list.files("data/raw/", pattern="*csv")) {  # don't include any non-csv files
    paste("data/raw/", filename, sep="") %>%
      read.csv(skip=1, encoding="latin1") %>%
      select(-matches("(born)|(relig)")) %>% # remove data on where participant was born and their religion
      write.csv(paste("data/de-identified/", filename, sep=""))
    cat("De-identified:", filename, "\n")
    num_deidentified <- num_deidentified+1
  # }
}
 
cat("\nData de-identification complete!")
cat("\tDe-identified: ", num_deidentified)
cat("\tSkipped: ", num_skipped)
cat("\n\n\n")


