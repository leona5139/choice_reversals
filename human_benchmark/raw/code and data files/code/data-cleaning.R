#### Libraries #####

library(dplyr)
library(reshape2)
library(tidyr)
library(purrr)
library(readr)
library(stringr)
library(ggplot2)
library(foreign)
library(lubridate)

#### Functions ####

read_responses <- function(x){
  cat("Reading", x, "\n")
  read_csv(file.path(x)) %>%
    rename_at(vars(contains('Response.ID')), funs(sub('Response.ID', 'ResponseID', .))) %>% # note that some files have ResponseID, some have Response.ID
    filter(Finished %in% c(1, "True")) %>%
    select(ResponseID, starts_with("choice"), matches("Commitment[0-9]"), matches("(switch)|(willing)")) %>%
    melt(id.vars = "ResponseID", value.name = "Response", variable.name = "Variable") %>%
    mutate(Response = as.character(Response)) %>%
    rename(ParticipantID = ResponseID)
}

read_randomization <- function(x){
  cat("Reading", x, "\n")
  read_csv(file.path(x)) %>%
    rename_at(vars(contains('Response.ID')), funs(sub('Response.ID', 'ResponseID', .))) %>% # note that some files have ResponseID, some have Response.ID
    filter(Finished %in% c(1, "True")) %>%
    select(ResponseID,  starts_with("flip"), matches("RandComm[0-9]$")) %>%
    melt(id.vars = "ResponseID", value.name = "Response", variable.name = "Variable") %>%
    mutate(Response = as.character(Response)) %>%
    rename(ParticipantID = ResponseID)
}

read_participants <- function(x){
  cat("Reading", x, "\n")
  read_csv(file.path(x)) %>%
    rename_at(vars(contains('Response.ID')), funs(sub('Response.ID', 'ResponseID', .))) %>% # note that some files have ResponseID, some have Response.ID
    rename_at(vars(contains('Start.Date')), funs(sub('Start.Date', 'StartDate', .))) %>% 
    rename_at(vars(contains('End.Date')), funs(sub('End.Date', 'EndDate', .))) %>% 
    filter(Finished %in% c(1, "True")) %>%
    select(ResponseID, StartDate, EndDate, matches("sex"), matches("political"), matches("How.old"), matches("What.factors.")) %>%
    rename(ParticipantID = ResponseID) %>% 
    mutate(
      StartDate = ymd_hms(StartDate),
      EndDate = ymd_hms(EndDate),
      Gender = if_else(`What.is.your.sex.` %in% c(1, "Male"), "Male", "Female"),
      PoliticalStance = as.character(What.is.your.political.stance.),
      PoliticalStanceSafetyNet = as.character(What.is.your.political.stance..on.issues.concerning.the.social.safety.net.),
      Age = as.numeric(How.old.are.you..in.years..)
    ) %>%
    rename_at(vars(contains("What.factors.did.you.consider.when.making.your.initial.allocation")), funs(sub('.*', 'InitialAllocationFactors', .))) %>%
    rename_at(vars(contains("What.factors.did.you.consider.when.deciding.whether.to.revise")), funs(sub('.*', 'RevisionFactors', .))) %>%
    filter(!str_detect(ParticipantID, "ImportId"))  %>% 
    select(ParticipantID, Gender, Age, StartDate, EndDate, PoliticalStance, PoliticalStanceSafetyNet, InitialAllocationFactors, RevisionFactors)
}


#### Constants ####

offsetting_amounts <- 
  tibble(
    Round = 1:8,
    OffsettingAmount = c(7,2,10,1,8,3,9,0),
    NoOffsettingAmount = rep(5, 8)
  )

#### SCRIPT #####
cat("\nBegin data cleaning:\n\n")

## extract randomization info
randomization <- 
  tibble(SourceFile = list.files("data/de-identified", full.names = T)) %>%  
  mutate(responses = map(SourceFile, ~suppressMessages(read_randomization(.)))) %>%
  unnest() %>%
  filter(!str_detect(ParticipantID, "ImportId")) %>%
  mutate(
    Treatment = factor(str_extract(SourceFile, "(EA_EASR)|(EP_EASR)|(EAEP_EASR)|(EPEA_EASR)|(EASR_EACAR)|(StrFlexComm)|(Pre-Rev)|(Revision Preferences)|(Dol)|(v41_EA_)|(v41_EASR_)")),
    Round = case_when(
      # do flip variable first
      Variable == "flipD1" ~ 1,
      Variable == "flipD2" ~ 2,
      Variable == "flipD3" ~ 3,
      Variable == "flipD4" ~ 4,
      Variable == "flip1" ~ 5,
      Variable == "flip2" ~ 6,
      Variable == "flip3" ~ 7,
      Variable == "flip4" ~ 8,
      # then do RandComm variable
      Variable == "RandComm1" & Treatment == "EASR_EACAR" ~ 5,
      Variable == "RandComm2" & Treatment == "EASR_EACAR" ~ 6,
      Variable == "RandComm3" & Treatment == "EASR_EACAR" ~ 7,
      Variable == "RandComm4" & Treatment == "EASR_EACAR" ~ 8,
      Variable == "RandComm1" & Treatment == "StrFlexComm" ~ 1,
      Variable == "RandComm2" & Treatment == "StrFlexComm" ~ 2,
      Variable == "RandComm3" & Treatment == "StrFlexComm" ~ 3,
      Variable == "RandComm4" & Treatment == "StrFlexComm" ~ 4
    ),
    Variable = str_extract(Variable, "(flip)|(RandComm)")
  ) %>% 
  dcast(ParticipantID + Round ~ Variable, value.var = "Response")

## response level data set
responses_raw <-
  tibble(SourceFile = list.files("data/de-identified", full.names = T)) %>%  
  mutate(responses = map(SourceFile, ~suppressMessages(read_responses(.)))) %>%
  unnest() %>%
  filter(!str_detect(ParticipantID, "ImportId"))
  
responses <- 
  responses_raw %>%
  mutate(
    ResponseText = Response,
    Response = recode(Response, 
                      # these are raw text responses from StrFlexComm treatment
                      `I am indifferent`                                            = "2", 
                      `I do not want the option to confirm or revise my allocation` = "1", 
                      `I want the option to confirm or revise my allocation.`       = "0",
                      # Coding responses to match 1=switch, 2=stay from other strictness treatments
                      `Yes, I would be willing to give up my option to confirm or revise my original allocation.`    = "1",     
                      `Yes, I would be willing to have the option to confirm or revise my original allocation.`      = "1",      
                      `No, I would not be willing to have the option to confirm or revise my original allocation.`   = "2",
                      `No, I would not be willing to give up my option to confirm or revise my original allocation.` = "2"
                      )
  ) %>%
  mutate(
    Response = as.numeric(Response),
    Treatment = factor(str_extract(SourceFile, "(EA_EASR)|(EP_EASR)|(EAEP_EASR)|(EPEA_EASR)|(EASR_EACAR)|(StrFlexComm)|(Pre-Rev)|(Revision Preferences)|(Dol)|(v41_EA_)|(v41_EASR_)")),
    Round = case_when(
      str_detect(.$Variable, "(\\.$)")  & Treatment %in%  c("v41_EA_", "v41_EASR_") ~ 1,
      str_detect(.$Variable, "(\\.1$)") & Treatment %in%  c("v41_EA_", "v41_EASR_") ~ 2,
      str_detect(.$Variable, "(\\.2$)") & Treatment %in%  c("v41_EA_", "v41_EASR_") ~ 3,
      str_detect(.$Variable, "(\\.3$)") & Treatment %in%  c("v41_EA_", "v41_EASR_") ~ 4,
      # revision preferences treatment revision strictness questions have Prize in them
      str_detect(.$Variable, "(D1)|(\\.\\.\\.Prize)")  ~ 1, 
      str_detect(.$Variable, "(D2)|(\\.\\.Prize.*0$)") ~ 2,
      str_detect(.$Variable, "(D3)|(\\.\\.Prize.*1$)") ~ 3,
      str_detect(.$Variable, "(D4)|(\\.\\.Prize.*2$)") ~ 4,
      # fix rounds because of bug in StrFlexComm Treatment strictness question wording (Round 5, 12.50 pie)
      str_detect(.$Variable, "instead.*12\\.50")     &  Treatment != "v41_EASR_" ~ 5,                     
      str_detect(.$Variable, "have.*12\\.50\\.$")    &  Treatment != "v41_EASR_" ~ 6,
      str_detect(.$Variable, "have.*12\\.50\\.\\.1") &  Treatment != "v41_EASR_" ~ 7,
      str_detect(.$Variable, "have.*12\\.50\\.\\.2") &  Treatment != "v41_EASR_" ~ 8,
      # StrFlexComm Treatment strictness questions identified by end of question
      str_detect(.$Variable, "(choice1)|(Commitment1)|(\\.$)")  & !Treatment %in%  c("v41_EA_", "v41_EASR_") ~ 5, 
      str_detect(.$Variable, "(choice2)|(Commitment2)|(\\.1$)") & !Treatment %in%  c("v41_EA_", "v41_EASR_") ~ 6,
      str_detect(.$Variable, "(choice3)|(Commitment3)|(\\.2$)") & !Treatment %in%  c("v41_EA_", "v41_EASR_") ~ 7,
      str_detect(.$Variable, "(choice4)|(Commitment4)|(\\.3$)") & !Treatment %in%  c("v41_EA_", "v41_EASR_") ~ 8
    ),
    Revision = str_detect(Variable, ".*r"),
    DecisionType = case_when(
      str_detect(.$Variable, "Commitment")         ~ "Commitment",
      str_detect(.$Variable, "choice")             ~ "Allocation",
      str_detect(.$Variable, "(switch)|(willing)") ~ "Strictness",
      TRUE ~ ""
    ),
    PieSize = str_extract(Variable, "(5\\.00)|(8\\.00)|(9\\.00)|(9\\.50)|(9\\.90)|(10\\.10)|(10\\.25)|(10\\.50)|(11)|(11\\.00)|(12\\.00)|(12\\.50)|(15)")
    ) %>%
  mutate(
    RoundTreatment = case_when(
      .$Treatment == "EP_EASR"    & .$Round %in% c(1:4) ~ "EP",
      .$Treatment == "EPEA_EASR"  & .$Round %in% c(1,2) ~ "EP",
      .$Treatment == "EAEP_EASR"  & .$Round %in% c(3,4) ~ "EP",
      .$Treatment == "EASR_EACAR" & .$Round %in% c(5:8) ~ "EACAR",
      TRUE                                              ~ "EA"
    ),
    RoundGroup = case_when(
      .$Round %in% c(1,2) ~ "Rounds 1-2",
      .$Round %in% c(3,4) ~ "Rounds 3-4",
      .$Round %in% c(5:8) ~ "Rounds 5-8"
    ),
    FirstHalf = (Round <= 4)
  ) %>%
  merge(offsetting_amounts) %>%
  merge(randomization, all.y = T) %>%
  mutate(
    alpha = ifelse(DecisionType == "Allocation", (Response - 5)/(OffsettingAmount - 5), NA),
    Category = case_when(
      alpha < 0             ~ "Reinforcing",
      alpha == 0            ~ "Ex Post Equalizing",
      0 < alpha & alpha < 1 ~ "Mixed",
      alpha == 1            ~ "Ex Ante Equalizing",
      alpha > 1             ~ "Overcompensating"
    ),
    Category = factor(Category, levels = c("Overcompensating", "Ex Ante Equalizing", "Mixed", "Ex Post Equalizing", "Reinforcing")),
    DistanceFromOffsetting = ifelse(DecisionType == "Allocation", abs(Response - OffsettingAmount), NA),
    DistanceFromNoOffsetting = ifelse(DecisionType == "Allocation", abs(Response - 5), NA),
    DistanceFromReinforcing = ifelse(DecisionType == "Allocation", abs(Response - (10 - OffsettingAmount)), NA)
  ) %>%
  filter(
    !str_detect(SourceFile, "EASR_EACAR.*Session_(1|2|3)") # exclude first three sessions of this treatment due to Qualtrics error not showing pages correctly to participants
  ) %>% 
  mutate(
    TreatmentLong = case_when(
      Treatment == "EA_EASR"               ~  "4A_4AR",
      Treatment == "Dol"                   ~  "4A_4AR Dollars",
      Treatment == "EP_EASR"               ~  "4P_4AR",
      Treatment == "EAEP_EASR"             ~  "2A2P_4AR",
      Treatment == "EPEA_EASR"             ~  "2P2A_4AR",
      Treatment == "EASR_EACAR"            ~  "4AR_4AC",
      Treatment == "Pre-Rev"               ~  "4AR Contingent Plan",
      Treatment == "v41_EA_"               ~  "Strictness of Initial Allocation",
      Treatment == "v41_EASR_"             ~  "Strictness of Final Allocation",
      Treatment == "Revision Preferences"  ~  "Strictness of Initial vs Final Allocation",
      Treatment == "StrFlexComm"           ~  "Strictness of Committment Decision"
    ),  
    Treatment = case_when(
      Treatment == "EA_EASR"               ~  "4A_4AR",
      Treatment == "Dol"                   ~  "4A_4AR Dollars",
      Treatment == "EP_EASR"               ~  "4P_4AR",
      Treatment == "EAEP_EASR"             ~  "2A2P_4AR",
      Treatment == "EPEA_EASR"             ~  "2P2A_4AR",
      Treatment == "EASR_EACAR"            ~  "4AR_4AC",
      Treatment == "Pre-Rev"               ~  "4AR Plan",
      Treatment == "v41_EA_"               ~  "4AR StrInit",
      Treatment == "v41_EASR_"             ~  "4AR StrFin",
      Treatment == "Revision Preferences"  ~  "4AR StriInitFin",
      Treatment == "StrFlexComm"           ~  "4AR_4AC StrComm"
    )
  ) %>%
  as_tibble() %>%
  select(Treatment, ParticipantID, Round, flip, RandComm, DecisionType, Revision, Category, PieSize, Response, everything()) %>%
  arrange(Treatment, ParticipantID, Round)

## aggregate to allocation level
allocations <- responses %>%
  filter(DecisionType == "Allocation") %>%
  select(ParticipantID, Treatment, Round, RoundGroup, FirstHalf, Revision, Response, Category, OffsettingAmount, NoOffsettingAmount, flip, RandComm) %>%
  melt(id.vars = c("ParticipantID", "Treatment", "Round", "RoundGroup", "FirstHalf", "Revision", "OffsettingAmount", "NoOffsettingAmount", "flip", "RandComm")) %>%
  mutate(Revision = if_else(Revision, "Revised", "Initial")) %>%
  dcast(ParticipantID + Treatment + Round + RoundGroup + FirstHalf + OffsettingAmount + NoOffsettingAmount + flip + RandComm ~ Revision + variable) %>%
  mutate(
    Changed_Response = if_else(!is.na(Revised_Response), Initial_Response != Revised_Response, NA),
    Initial_to_Revised_Category = if_else(!is.na(Initial_Category) & !is.na(Revised_Category), paste(Initial_Category, "to", Revised_Category, sep=" "), "NA"),
    Initial_Category = factor(Initial_Category, levels = c("Overcompensating", "Ex Ante Equalizing", "Mixed", "Ex Post Equalizing", "Reinforcing")),
    Revised_Category = factor(Revised_Category, levels = c("Overcompensating", "Ex Ante Equalizing", "Mixed", "Ex Post Equalizing", "Reinforcing")),
    Changed_Category = if_else(!is.na(Revised_Category), Initial_Category != Revised_Category, NA),
    Final_Response = if_else(is.na(Revised_Response), Initial_Response, Revised_Response),
    Final_Category = if_else(is.na(Revised_Category), Initial_Category, Revised_Category),
    RevisionType = case_when(
      is.na(Revised_Response)                                                                                                       ~ "NA",
      Revised_Response == Initial_Response                                                                                          ~ "No Change",
      Revised_Response == 5                                                                                                         ~ "To 50-50",
      (Revised_Response > 5 & Initial_Response <= 5) | (Revised_Response < 5 & Initial_Response >= 5)                               ~ "Past 50-50",
      (Initial_Response >= Revised_Response & Revised_Response > 5) | (Initial_Response <= Revised_Response & Revised_Response < 5) ~ "Towards 50-50",
      TRUE                                                                                                                          ~ "Away from 50-50"
    )) %>%
  # add in commitment 
  merge(responses %>% filter(DecisionType == "Commitment") %>% select(ParticipantID, Round, Response) %>% rename(Commitment = Response), all.x = T) %>%
  mutate(CommitmentText = case_when(
    Commitment == 0 ~ "Flexibility",
    Commitment == 1 ~ "Committment",
    Commitment == 2 ~ "Indifference"
  ))

## calculate consistency of allocation categorizations by round group
consistency_categories <-  
  responses %>%
  filter(Round <= 4) %>% # need to create duplicates for rounds 1-4 in addition to rounds 1-2 and rounds 3-4 grouping
  mutate(RoundGroup = "Rounds 1-4") %>%
  rbind(responses) %>%
  filter(DecisionType == "Allocation" & !is.na(Response)) %>%
  group_by(ParticipantID, RoundGroup, Treatment, Revision, Category) %>%
  summarize(Consistency = n()) %>%
  mutate(Consistency = factor(Consistency/sum(Consistency))) %>%
  mutate(Consistency = factor(Consistency, levels = c("0.25", "0.5", "0.75", "1")))

## assign revision categories for 4AR_4AC treatment
revision_categories <- 
  allocations %>%
  filter(Treatment %in% c("4AR_4AC", "4AR_4AC StrComm") & Round <= 4 & !is.na(Revised_Category)) %>%
  mutate(
    Revised = Revised_Response != Initial_Response,
    Revised_EA_to_EP = (Initial_Category== "Ex Ante Equalizing" & Revised_Category == "Ex Post Equalizing")
  ) %>%
  group_by(ParticipantID, Treatment) %>%
  summarize(
    Num_Revised = sum(Revised),
    Num_Revised_EA_to_EP = sum(Revised_EA_to_EP)
  ) %>%
  mutate(
    SwitchingType = case_when(
      Num_Revised == 0 ~ "Never Revised",
      Num_Revised == 1 & Num_Revised_EA_to_EP == 1 ~ "Revised once, always EA to EP",
      Num_Revised == 1 & Num_Revised_EA_to_EP == 0 ~ "Revised once, never EA to EP",
      Num_Revised == 2 & Num_Revised_EA_to_EP == 2 ~ "Revised twice, always EA to EP",
      Num_Revised == 2 & Num_Revised_EA_to_EP == 1 ~ "Revised twice, one time EA to EP",
      Num_Revised == 2 & Num_Revised_EA_to_EP == 0 ~ "Revised twice, never EA to EP"
    )
  )  

## merge revision categories into allocations and responses
allocations <-
  merge(allocations, revision_categories, all.x = T, by = c("ParticipantID", "Treatment"))

responses <-
  merge(responses, revision_categories, all.x = T, by = c("ParticipantID", "Treatment"))

## participant level data set
participants <- 
  tibble(SourceFile = list.files("data/de-identified", full.names = T)) %>%  
  mutate(
    responses = map(SourceFile, ~suppressMessages(read_participants(.)))
  ) %>% 
  unnest() %>%
  mutate(
    Gender = factor(Gender),
    Session = factor(str_extract(str_extract(SourceFile, "Sess(ion(_|\\s))?[0-9]"), "[0-9]")),
    # we have to recode the political stance questions because some were downloaded from Qualtrics as numerics and some as text
    PoliticalStance = factor(recode(PoliticalStance, 
                                    "1" = "Strongly Liberal",
                                    "2" = "Somewhat Liberal",
                                    "3" = "Moderate",
                                    "4" = "Somewhat Conservative",
                                    "5" = "Strongly Conservative",
                                    "6" = "Decline to State")),
    PoliticalStanceSafetyNet = factor(recode(PoliticalStanceSafetyNet, 
                                             "1" = "Strongly Liberal",
                                             "2" = "Somewhat Liberal",
                                             "3" = "Moderate",
                                             "4" = "Somewhat Conservative",
                                             "5" = "Strongly Conservative",
                                             "6" = "Decline to State")),
    # we also have to recode age because some treatments were downloaded as 1 = age 17, 2 = age 18, etc
    Age = if_else(Age <= 17, Age+16, Age)
  ) %>%
  select(-SourceFile) %>%
  merge(allocations %>% select(ParticipantID, Treatment) %>% unique()) # add in treatment info

## save treatment summary to file
responses %>% 
  group_by(Treatment, TreatmentLong) %>% 
  summarize(
    Treatments = length(unique(SourceFile)),
    Subjects = length(unique(ParticipantID))
  ) %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/treatment-summary.txt")

## save data in R format
save(responses, allocations, participants, consistency_categories, revision_categories, file="data/clean/clean-data.rda") # R data format

## save data in stata format
# Stata data format version is necessary for correct encoding; write.dta only goes up to 12 but seems to work with my stata 14
write.dta(responses, file = "data/clean/responses.dta", version  = 12, convert.factors = "string") 
write.dta(allocations, file = "data/clean/allocations.dta", version  = 12, convert.factors = "string")
write.dta(participants, file = "data/clean/participants.dta", version  = 12, convert.factors = "string")

cat("\nData cleaning complete \n")
