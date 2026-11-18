#### LIBRARIES ####

library(testthat)

#### SCRIPT ####

load("data/clean/clean-data.rda") 

test_that("Number of treatments is correct in all data sets",
          {
            expect_that(length(unique(responses$Treatment)), equals(11))
            expect_that(length(unique(allocations$Treatment)), equals(11))
            expect_that(length(unique(participants$Treatment)), equals(11))
            }          
)
