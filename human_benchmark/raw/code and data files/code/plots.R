## plots.R
## Jeffrey Naecker
## Generate plots for fairness project

##### LIBRARIES ######
suppressPackageStartupMessages(library(ggplot2))
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(readr))
suppressPackageStartupMessages(library(reshape2))
suppressPackageStartupMessages(library(tidyr))
suppressPackageStartupMessages(library(stringr))
suppressPackageStartupMessages(library(forcats))
suppressPackageStartupMessages(library(knitr))
suppressPackageStartupMessages(library(kableExtra))
suppressPackageStartupMessages(library(magrittr))



##### CONSTANTS #####

# ggplot layers for bar plots
bar_options <- list(
  geom_bar(stat="identity"),
  theme_bw(),
  scale_fill_manual(values=c('#cccccc','#969696','#636363','#252525')),
  theme(axis.text.x = element_text(angle = 270)),
  theme(panel.grid = element_blank()),
  xlab("Choice category"),
  ylab("Frequency")
)

# ggplot layers for fingerprint plots
line_opts <- list(
  geom_line(),
  geom_point(),
  geom_errorbar(aes(ymin=mean-2*SE, ymax=mean+2*SE, width=.2), linetype = "solid", size = 0.2, width = 0.1),
  ylab("Tickets given to B"),
  scale_linetype_manual(values = c("solid", "dotted", "dotdash")),
  theme_bw(),
  theme(panel.grid = element_blank()),
  theme(plot.title = element_text(vjust=2))
)

# ggplot layers for fingerprint plots with initial and final lines
line_opts_extended <- line_opts
line_opts_extended[[5]] <- scale_linetype_manual(values = c("solid", "dashed", "dotted", "dotdash"))



##### FUNCTIONS ######

plot_sd <- function(x) {
  if (is.na(sd(x, na.rm=T)) | sd(x, na.rm = T) == 0) {
    return(NA)
  } else {
    return(sd(x, na.rm=T)/sqrt(length(!is.na(x))))
  }
}

##### DATA #######
load("data/clean/clean-data.rda")

##### SECTION 3.3: Details concerning implementation ##########
# number of participants
nrow(participants)

##### SECTION 4: Framing effects and choice reversals ######

##### SECTION 4.1: Experimental Design #######

# Table 3 and 4 (counts of subjects per treatment)
participants %>% group_by(Treatment) %>% count()

##### SECTION 4.2: Basic Framing Effects #######

## Figure 1: allocations.eps
## allocation in main two treatments, without error bars
(responses %>%
    filter(Treatment %in% c("4A_4AR", "4P_4AR") & Round <= 4 & !is.na(Response)) %>%
    select(-RoundGroup) %>%
    merge(consistency_categories %>% filter(RoundGroup == "Rounds 1-4" & Treatment %in% c("4A_4AR", "4P_4AR"))) %>%
    group_by(Category, Treatment, Consistency) %>%
    summarize(count = n(), SE = NA) %>%
    group_by(Treatment) %>%
    mutate(Mean = count/sum(count)) %>%
    {. ->> allocations_table} %>%
    ggplot(aes(x=Category, y=Mean, fill = Consistency)) +
      facet_wrap(~Treatment, ncol=2, labeller=labeller(Treatment = c("4A_4AR" = "Panel A: Ex Ante Frame", "4P_4AR" = "Panel B: Ex Post Frame"))) + 
      bar_options) %>%
  ggsave(filename = "output/plots/allocations.eps", height = 4, width = 8)

allocations_table %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/allocations-table.txt")

# consistent choosers
responses %>%
  filter(Treatment == "4A_4AR" & Round <= 4 & !is.na(Response)) %>%
  merge(consistency_categories %>% filter(RoundGroup == "Rounds 1-4" & Treatment == "4A_4AR")) %>%
  filter(Consistency == 1) %>%
  count(Category) %>%
  mutate(percent = n/sum(n))
  
# overall percentages for figure without intesity categories
responses %>%
  filter(Treatment %in% c("4A_4AR", "4P_4AR") & Round <=4 & !is.na(Response)) %>%
  group_by(Category, Treatment) %>%
  summarize(count = n(), SE = NA) %>%
  group_by(Treatment) %>%
  mutate(Mean = count/sum(count)) %>%
  select(Category, Treatment, Mean) %>%
  spread(Treatment, Mean) %>%
  mutate(Diff = `4A_4AR` - `4P_4AR`)

## Figure 2: allocations-with-alternating.eps
## allocation in main two treatments, without error bars, including alternating frames

# make helper data for adding frame-dependent label and background shading
frame_facet_data <- data.frame(
  Frame = c("EA", "EP", "EA", "EP", "EA", "EP", "EP", "EA", "EA", "EA", "EA", "EA"),
  Treatment = rep(c("4A_4AR", "4P_4AR", "2A2P_4AR", "2P2A_4AR"), 3),
  RoundGroup = c(rep("Rounds 1-2",4), rep("Rounds 3-4", 4), rep("Rounds 5-8", 4))
) %>%
  mutate(
    Position = if_else(Frame == "EA", 1, 5),
    )

# make graph
(responses %>%
    filter(Treatment %in% c("4A_4AR", "4P_4AR", "2A2P_4AR", "2P2A_4AR") & !is.na(Response)) %>%
    merge(consistency_categories %>% filter(RoundGroup != "Rounds 1-4" & Treatment %in% c("4A_4AR", "4P_4AR", "2A2P_4AR", "2P2A_4AR"))) %>%
    filter(!Revision) %>%
    group_by(Category, Treatment, RoundGroup, RoundTreatment, Consistency) %>%
    summarize(count = n(), SE = NA) %>%
    group_by(Treatment, RoundGroup, RoundTreatment) %>%
    mutate(Mean = count/sum(count)) %>%
    {. ->> allocations_with_alternating_table} %>%
    ggplot(aes(x=Category, y=Mean, fill=Consistency)) +
      facet_grid(Treatment~RoundGroup) + 
      geom_rect(data = subset(frame_facet_data, Frame == "EP"), fill="#d9d9d9", xmin = -Inf,xmax = Inf, ymin = -Inf,ymax = Inf, inherit.aes = F) +
      bar_options +
      geom_text(data = frame_facet_data, aes(y = 0.7, x = Position, label = Frame), inherit.aes = FALSE)) %>%
  ggsave(filename = "output/plots/allocations-with-alternating.eps", height = 7, width = 7)

allocations_with_alternating_table %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/allocations-with-alternating-table.txt")

##### SECTION 4.3: Choice Reversals ######

## statistics on revision

# percent of choices revised
allocations %>% 
  filter(Treatment == "4A_4AR" & Round >=5 & !is.na(Changed_Response)) %>%
  count(Changed_Response) %>%
  mutate(percent = n/sum(n))

# percent of subjects who revised at least once
allocations %>% 
  filter(Treatment == "4A_4AR" & Round >=5 & !is.na(Changed_Response)) %>%
  group_by(ParticipantID) %>%
  mutate(`Revised at least once` = sum(Changed_Response) > 0)%>%
  group_by(`Revised at least once`) %>%
  count() %>%
  ungroup() %>%
  mutate(percent = n/sum(n))

# revision frequency by round
allocations %>% 
  filter(Treatment == "4A_4AR" & Round >=5 & !is.na(Changed_Response)) %>%
  group_by(Round) %>%
  count(Changed_Response) %>%
  mutate(percent = n/sum(n)) %>%
  select(-n) %>%
  spread(Changed_Response, percent)

# frequency of final category for those who revised
allocations %>% 
  filter(Treatment == "4A_4AR" & Round >=5 & Initial_Response != Final_Response) %>%
  count(Final_Category) %>%
  mutate(percent = n/sum(n)) %>%
  arrange(desc(percent))

## Figure 3 (revisions.eps)
## allocation categories of intial and revised allocations in first four treatments, rounds 5-8
## also include facet with revised decisions only
(allocations %>%
  select(ParticipantID, Treatment, Round, Changed_Response) %>%   # duplicate revisions with actual changes
  filter(Changed_Response) %>%
  merge(responses %>% filter(Revision)) %>% 
  rbind(responses %>% mutate(Changed_Response = F) %>% select(ParticipantID, Treatment, Round, Changed_Response, everything())) %>%
  filter(Treatment %in% c("4A_4AR", "4P_4AR", "2P2A_4AR", "2A2P_4AR")) %>%
  merge(consistency_categories %>% filter(RoundGroup == "Rounds 5-8" & Treatment %in% c("4A_4AR", "4P_4AR", "2P2A_4AR", "2A2P_4AR"))) %>%
  mutate(Group = case_when(
              !Revision ~ "Initial",
              Revision & !Changed_Response ~ "Final",
              Revision & Changed_Response ~ "Final (changes only)"
      )
    ) %>%
  mutate(Group = factor(Group, levels = c("Initial", "Final", "Final (changes only)"))) %>%
  group_by(Category, Group, Consistency) %>%
  summarize(count = n(), SE = NA) %>%
  group_by(Group) %>%
  mutate(Mean = count/sum(count)) %>%
  {. ->> revisions} %>%
  ggplot(aes(x=Category, y=Mean, fill=Consistency)) +
    facet_wrap(~ Group, nrow = 1) + 
    bar_options) %>%
  ggsave(filename = "output/plots/revisions.eps", height = 4, width = 9)
  
revisions %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/revisions-table.txt")

# percent of choices revised in different groups
allocations %>% 
  filter(Treatment %in% c("4P_4AR", "2A2P_4AR", "2P2A_4AR") & Round >=5 & !is.na(Changed_Response)) %>%
  group_by(Treatment) %>%
  count(Changed_Response) %>%
  mutate(percent = n/sum(n)) %>%
  filter(Changed_Response)

# frequency of final category for those who revised
allocations %>% 
  filter(Treatment %in% c("4P_4AR", "2A2P_4AR", "2P2A_4AR") & Round >=5 & Initial_Response != Final_Response) %>%
  count(Final_Category, Treatment) %>%
  group_by(Treatment) %>%
  mutate(percent = n/sum(n)) %>%
  select(-n) %>%
  spread(Treatment, percent)

## Figure 4 (revisions-joint.eps)
## joint distribution of intial and final categories for all four treatments jointly
(allocations %>%
  filter(Round >= 4 & Treatment %in% c("4A_4AR", "4P_4AR", "2P2A_4AR", "2A2P_4AR") & !is.na(Revised_Category)) %>%
  group_by(Initial_Category, Revised_Category) %>%
  summarize(count = n(), SE = NA) %>%
  ungroup() %>%
  mutate(Mean = count/sum(count)) %>%
  {. ->> revisions_joint} %>%
  ggplot(aes(x=Revised_Category, y=Mean)) +
    bar_options +
    facet_wrap(~Initial_Category, nrow = 1)) %>%
  ggsave(filename = "output/plots/revisions-joint.eps", height = 5, width = 10)

revisions_joint %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/revisions-joint-table.txt")

## joint distribution of intial and final categories for all four treatments individually
(allocations %>%
    filter(Round >= 4 & Treatment %in% c("4A_4AR", "4P_4AR", "2P2A_4AR", "2A2P_4AR") & !is.na(Revised_Category)) %>%
    group_by(Treatment, Initial_Category, Revised_Category) %>%
    summarize(count = n(), SE = NA) %>%
    ungroup() %>%
    group_by(Treatment) %>%
    mutate(Mean = count/sum(count)) %>%
    {. ->> revisions_joint_separate} %>%
    ggplot(aes(x=Revised_Category, y=Mean)) +
      bar_options +
      facet_grid(Treatment~Initial_Category))  %>%
    ggsave(filename = "output/plots/revisions-joint-separate.eps", height = 5, width = 10)

revisions_joint_separate %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/revisions-joint-separate-table.txt")

##### SECTION 4.4: Strictness of allocation preferences #####

## Figure  (strictness-allocations.eps)
(responses %>% 
   filter(DecisionType == "Strictness" & !is.na(Response) & Treatment %in% c("4AR StriInitFin", "4AR StrFin", "4AR StrInit")) %>%
   mutate(
     `Prize Amount Deviation From 10` = abs(as.numeric(PieSize) - 10),
     Response = if_else(Treatment != "4AR StriInitFin", Response - 1, 2 - Response),
     Label = TreatmentLong
   ) %>%
   group_by(Label, `Prize Amount Deviation From 10`) %>%
   summarize(Demand = mean(Response, na.rm = T)) %>%
   {. ->> strictness_allocations} %>%
   ggplot(aes(x = `Prize Amount Deviation From 10`,  y= Demand, linetype = Label)) +
   geom_line() +
   theme_bw() + 
   theme(legend.title=element_blank())) %>%
  ggsave(filename = "output/plots/strictness-allocations.eps", height = 4, width = 7)

strictness_allocations %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/strictness-allocations-table.txt")

##### SECTION 5.1: Experimental Design #######

# distribution of intial choices
allocations %>% 
  filter(Treatment == "4AR_4AC" & Round <= 4) %>%
  count(Initial_Category) %>%
  mutate(percent = n/sum(n))

# percent of choices revised
allocations %>% 
  filter(Treatment == "4AR_4AC" & Round <= 4 & !is.na(Changed_Response)) %>%
  count(Changed_Response) %>%
  mutate(percent = n/sum(n))

# frequency of final category for those who revised
allocations %>% 
  filter(Treatment == "4AR_4AC" & Round <= 4 & !is.na(Changed_Response) & Initial_Response != Revised_Response) %>%
  count(Revised_Category) %>%
  mutate(percent = n/sum(n)) %>%
  arrange(desc(percent))

##### SECTION 5.2: Overall effects of commitment opportunities #######

# frequency of commitment choices
allocations %>% 
  filter(Treatment == "4AR_4AC" & Round >= 5) %>%
  count(CommitmentText) %>%
  mutate(percent = n/sum(n))

# frequency of commitment choices, by round
allocations %>% 
  filter(Treatment == "4AR_4AC" & Round >= 5) %>%
  group_by(Round) %>%
  count(CommitmentText) %>%
  mutate(percent = n/sum(n)) %>% 
  select(-n) %>%
  spread(CommitmentText, percent)

# frequency of revision
allocations %>% 
  filter((Treatment == "4AR_4AC" | Treatment == "4A_4AR" & Round >= 5) & flip == 2) %>%
  group_by(Treatment, FirstHalf) %>%
  count(Changed_Response) %>%
  mutate(Percent = n/sum(n))
  
# details on commitment and revision behavior
allocations %>% 
  filter((Treatment == "4AR_4AC" | Treatment == "4A_4AR" & Round >= 5) & flip == 2) %>%
  group_by(Treatment, FirstHalf) %>%
  select(Treatment, FirstHalf, ParticipantID, Round, flip, Commitment, RandComm, Changed_Response) %>%
  filter(Treatment == "4AR_4AC" & Round >= 5) %>%
  count(Commitment, RandComm, Changed_Response)

# percent of subjects who revised at least once
allocations %>% 
  filter((Treatment == "4A_4AR" & Round >=5 )| Treatment == "4AR_4AC") %>%
  group_by(ParticipantID, FirstHalf) %>%
  mutate(`Revised at least once` = sum(Changed_Response, na.rm = T) > 0) %>%
  group_by(Treatment, FirstHalf, `Revised at least once`) %>%
  count() %>%
  group_by(Treatment, FirstHalf) %>%
  mutate(percent = n/sum(n)) %>%
  filter(`Revised at least once`)

# regression to test for differce in revised at least once frequencies
allocations %>% 
  filter((Treatment == "4A_4AR" & Round >=5 )| Treatment == "4AR_4AC") %>%
  group_by(ParticipantID, FirstHalf, Treatment) %>%
  summarize(`Revised at least once` = sum(Changed_Response, na.rm = T) > 0) %>%
  lm(`Revised at least once` ~ FirstHalf + Treatment, data = .) %>%
  summary()

# distribution of categories with and without commitment
allocations %>% 
  filter(Treatment == "4AR_4AC") %>%
  group_by(FirstHalf) %>%
  count(Final_Category) %>%
  mutate(percent = n/sum(n)) %>%
  select(-n) %>%
  spread(FirstHalf, percent)

# distribution of revision types with and without commitment
allocations %>% 
  filter(Treatment == "4AR_4AC" & flip == 2) %>%
  group_by(FirstHalf) %>%
  count(Initial_Category, Final_Category) %>%
  mutate(percent =  n/sum(n)) %>% 
  arrange(desc(percent)) %>% 
  select(-n) %>%
  spread(FirstHalf, percent)

##### SECTION 5.3: Understanding the demand for flexibility and commitment ######

##### SECTION 5.3.1: Which subgroups exhibit the greatest demand for commitment? ######

# how does commitment choice depend on initial category of the same round?
allocations %>% 
  filter(Treatment == "4AR_4AC" & Round >= 5) %>%
  count(Initial_Category, Commitment) %>%
  group_by(Initial_Category) %>%
  mutate(percent = n/sum(n)) %>%
  reshape2::dcast(Initial_Category ~ Commitment, value.var = "percent")

# Figure 5 (commitment.eps)
# graph of commitment choices as function of revision behavior
(revision_categories %>% 
    subset(Treatment == "4AR_4AC") %>%
    group_by(SwitchingType) %>% 
    summarize(Count = n()) %>% 
    mutate(
      Percent = Count/sum(Count)*100,
      Label = paste(SwitchingType, "\n", round(Percent, 1), "% of subjects", sep = ""),
      Label = str_replace(Label, ",", ",\n")
    ) %>%
    merge(filter(responses, Treatment == "4AR_4AC", Round >=5, DecisionType == "Commitment")) %>%
    mutate(
      Response = case_when( # should be able to use recode here
        Response == 0 ~ "Flexibility",
        Response == 1 ~ "Committment",
        Response == 2 ~ "Indifference"
      ),
      Response = factor(Response, levels = c("Committment", "Indifference", "Flexibility")),
      Label = factor(Label, levels = c(
        "Never Revised\n19.4% of subjects",
        "Revised once,\n always EA to EP\n16.7% of subjects",
        "Revised once,\n never EA to EP\n13.9% of subjects",
        "Revised twice,\n one time EA to EP\n12.5% of subjects",
        "Revised twice,\n never EA to EP\n15.3% of subjects",
        "Revised twice,\n always EA to EP\n22.2% of subjects"
      ))) %>%
    group_by(Label, Response) %>%
    summarize(Count = n()) %>%
    mutate(Percentage = Count/sum(Count)) %>%
    {. ->> commitment} %>%
    ggplot() +
    geom_bar(aes(x = Label, y = Percentage, fill = Response), stat = "identity") +
    scale_fill_manual(values = c('#bdbdbd','#f0f0f0','#636363'), name = "Committment Choice") +
    theme_bw() + 
    xlab("Revision behavior in first four rounds") +
    coord_flip()) %>%
  ggsave(filename = "output/plots/commitment.eps", height = 5, width = 8)

commitment %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/commitment-table.txt")

##### SECTION 5.3.2: How do subjects exercise flexibility when they intentionally retain it? ######

# exercising flexibility
allocations %>% 
  filter(Treatment == "4AR_4AC" & Round >= 5 & Commitment == 0 & !is.na(Changed_Response)) %>%
  count(Changed_Response) %>%
  mutate(percent = n/sum(n))

# intial behavior of subjects who opt for flexibility
allocations %>% 
  filter(Treatment == "4AR_4AC" & Round >= 5 & Commitment == 0) %>%
  count(Initial_Category) %>%
  mutate(percent = n/sum(n))

# revision behavior of subjects who opt for flexibility and choose EA fair intially
allocations %>% 
  filter(Treatment == "4AR_4AC" & Round >= 5 & Commitment == 0 & Initial_Category == "Ex Ante Equalizing") %>%
  count(Revised_Category) %>%
  filter(!is.na(Revised_Category)) %>%
  mutate(percent = n/sum(n))

# revision behavior of subjects who opt for flexibility
allocations %>% 
  filter(Treatment == "4AR_4AC" & Round >= 5 &  Commitment == 0 & !is.na(Revised_Category)) %>%
  count(Initial_Category, Revised_Category) %>%
  mutate(percent = n/sum(n)) 

# revision behavior of subjects who are indifferent
allocations %>% 
  filter(Treatment == "4AR_4AC" & Round >= 5 &  Commitment == 2 ) %>%
  count(Initial_Category, Final_Category) %>%
  mutate(percent = n/sum(n)) 


##### SECTION 5.4: Strictness of preferences for commitent and flexibility ######

# how many subjects 
table(participants$Treatment)

# inintial choices
allocations %>%
  subset(Treatment == "4AR_4AC StrComm") %>%
  count(Initial_Category) %>%
  mutate(percent = n/sum(n))

# revisions
allocations %>%
  subset(Treatment == "4AR_4AC StrComm" & !is.na(Revised_Category) & Changed_Response) %>%
  count(Revised_Category, FirstHalf) %>%
  group_by(FirstHalf) %>%
  mutate(percent = n/sum(n)) %>%
  select(-n) %>%
  spread(Revised_Category, percent)

# commitment choices 
responses %>%
  subset(Treatment == "4AR_4AC StrComm" & DecisionType == "Commitment") %>%
  count(Response) %>%
  mutate(percent = n/sum(n))

# Figure A.2 (strictness-commitment.eps)
## pull out commitment choices
strictness_helper <- 
  responses %>% 
  filter(Treatment == "4AR_4AC StrComm" & DecisionType == "Commitment") %>%
  mutate(CommitmentType = case_when(
    Response == 2 ~ "Indifferent",
    Response == 0 ~ "Flexible",
    Response == 1 ~ "Committed")
  ) %>%
  select(ParticipantID, Round, CommitmentType)

## create extra group
extra_strictness_group <- 
  responses %>% 
  filter(Treatment == "4AR_4AC StrComm" & DecisionType == "Strictness" & !is.na(Response) & SwitchingType == "Revised twice, always EA to EP") %>%
  mutate(Label = "Revised EA to EP both times") 

## graph strictness of decision
(responses %>% 
  filter(Treatment == "4AR_4AC StrComm" & DecisionType == "Strictness" & !is.na(Response)) %>%
  mutate(Label = if_else(SwitchingType %in% 
                           c("Revised once, always EA to EP", "Revised twice, one time EA to EP", "Revised twice, always EA to EP"), 
                         "Revised EA to EP at least once", "Never Revised EA to EP")) %>%
  bind_rows(extra_strictness_group) %>%
    merge(strictness_helper, all.x = T) %>%
    mutate(
      `Prize Amount Deviation From 10` = abs(as.numeric(PieSize) - 10),
      Response = Response - 1
    ) %>%
    filter(CommitmentType != "Indifferent") %>%
    group_by(CommitmentType, Label, `Prize Amount Deviation From 10`) %>%
    summarize(Demand = mean(Response, na.rm=T)) %>%
    {. ->> strictness_commitment} %>%
    ggplot(aes(x = `Prize Amount Deviation From 10`, y = Demand, linetype = Label)) +
      geom_line() +
      facet_wrap(~CommitmentType) + 
      theme_bw() + 
      theme(legend.title=element_blank())) %>%
  ggsave(filename = "output/plots/strictness-commitment.eps", height = 4, width = 7)

strictness_commitment %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/strictness-commitment-table.txt")


##### SECTION 6.2: Planned switching ######

# Figure 6 (contingent-plan.eps)
# graph of initial vs revised allocations for contingent plan treatment
(responses %>%
    filter(Round >=5 & Treatment %in% c("4AR Plan") & !is.na(Response) & DecisionType == "Allocation") %>%
    merge(consistency_categories %>% filter(RoundGroup == "Rounds 5-8" & Treatment %in% c("4AR Plan"))) %>%
    mutate(Revision = if_else(Revision, "Planned Revision", "Initial")) %>%
    group_by(Category, Revision, Consistency) %>%
    summarize(count = n(), SE = NA) %>%
    group_by(Revision) %>%
    mutate(Mean = count/sum(count)) %>%
    {. ->> contingent_plan} %>%
    ggplot(aes(x=Category, y=Mean, fill=Consistency)) +
      facet_wrap(~Revision, ncol=2)  + 
      bar_options) %>%
  ggsave(filename = "output/plots/contingent-plan.eps", height = 4, width = 8)

contingent_plan %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/contingent-plan-table.txt")

# total heights for bars
contingent_plan %>%
  group_by(Revision, Category) %>%
  summarize(sum(Mean))


##### APPENDIX B: Differentiating between competing formulations of fairness preferences #####

##### APPENDIX B.3: Results #####

# figure B.1 (allocations_dollars.eps) labeller=labeller(Treatment = c("4A_4AR" = "Panel A: Ex Ante Frame", "4P_4AR" = "Panel B: Ex Post Frame"))
(responses %>%
   filter(Treatment == "4A_4AR Dollars" & !is.na(Response)) %>%
   select(-RoundGroup) %>%
   merge(consistency_categories %>% filter(Treatment== "4A_4AR Dollars")) %>%
   group_by(Category, Revision, FirstHalf, Consistency) %>%
   summarize(count = n(), SE = NA) %>%
   group_by( Revision, FirstHalf) %>%
   mutate(
     Mean = count/sum(count),
     Label = case_when(
       !Revision & FirstHalf  ~ "Panel A: Distribution of choices, Rounds 1-4",
       !Revision & !FirstHalf ~ "Panel B: Distribution of original choices, Rounds 5-8",
       Revision  & !FirstHalf ~ "Panel C: Distribution of final choices, Rounds 5-8",
     )
   ) %>%
   {. ->> allocations_dollars_table} %>%
   ggplot(aes(x=Category, y=Mean, fill = Consistency)) +
      facet_wrap(~Label, nrow=2) + 
      bar_options) %>%
  ggsave(filename = "output/plots/allocations_dollars.eps", height = 6, width = 8)

allocations_dollars_table %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/allocations-dollars-table.txt")

# percent of choices revised
allocations %>% 
  filter(Treatment == "4A_4AR Dollars" & Round >=5 & !is.na(Changed_Response)) %>%
  count(Changed_Response) %>%
  mutate(percent = n/sum(n))

# percent of subjects who revised at least once
allocations %>% 
  filter(Treatment == "4A_4AR Dollars" & Round >=5 & !is.na(Changed_Response)) %>%
  group_by(ParticipantID) %>%
  mutate(`Revised at least once` = sum(Changed_Response) > 0)%>%
  group_by(`Revised at least once`) %>%
  count() %>%
  ungroup() %>%
  mutate(percent = n/sum(n))

# frequency of final category for those who revised
allocations %>% 
  filter(Treatment == "4A_4AR Dollars" & Round >=5 & Initial_Response != Final_Response) %>%
  count(Final_Category) %>%
  mutate(percent = n/sum(n)) %>%
  arrange(desc(percent))

## Figure B.2 (revisions-dollar.eps)
## joint distribution of intial and final categories split-the-dollars treatment
(allocations %>%
    filter(Round >= 4 & Treatment == "4A_4AR Dollars" & !is.na(Revised_Category)) %>%
    group_by(Initial_Category, Revised_Category) %>%
    summarize(count = n(), SE = NA) %>%
    ungroup() %>%
    mutate(Mean = count/sum(count)) %>%
    {. ->> revisions_dollar} %>%
      ggplot(aes(x=Revised_Category, y=Mean)) +
      bar_options +
      facet_wrap(~Initial_Category, nrow = 1)) %>%
  ggsave(filename = "output/plots/revisions-dollar.eps", height = 5, width = 10)

revisions_dollar %>%
  arrange(desc(Mean)) %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/revisions-dollar-table.txt")

##### APPENDIX C.1: Further analyses of basic framing effects #####

## Figure C.1: allocations-by-round.eps
## allocation in main two treatments, by round
(responses %>%
   filter(Treatment %in% c("4A_4AR", "4P_4AR") & Round <= 4 & !is.na(Response)) %>%
   select(-RoundGroup) %>%
   merge(consistency_categories %>% filter(RoundGroup == "Rounds 1-4" & Treatment %in% c("4A_4AR", "4P_4AR"))) %>%
   group_by(Category, Round, Treatment, Consistency) %>%
   summarize(count = n(), SE = NA) %>%
   group_by(Treatment, Round) %>%
   mutate(Mean = count/sum(count)) %>%
   {. ->> allocations_by_round_table} %>%
   ggplot(aes(x=Category, y=Mean, fill = Consistency)) +
    facet_grid(Treatment~Round) + 
    bar_options) %>%
  ggsave(filename = "output/plots/allocations-by-round.eps", height = 4, width = 8)

allocations_by_round_table %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/allocations-by-round-table.txt")

## Figure C.2: allocations-exposure.eps
## allocation in last 4 rounds of 4P_4AR
(responses %>%
    filter(Treatment %in% c("4P_4AR") & Round >= 5 & !is.na(Response) & !Revision) %>%
    select(-RoundGroup) %>%
    merge(consistency_categories %>% filter(RoundGroup == "Rounds 5-8" & Treatment %in% c("4P_4AR"))) %>%
    group_by(Category, Consistency) %>%
    summarize(count = n(), SE = NA) %>%
    ungroup() %>%
    mutate(Mean = count/sum(count)) %>%
    {. ->> allocations_exposure_table} %>%
      ggplot(aes(x=Category, y=Mean, fill = Consistency)) +
      bar_options) %>%
  ggsave(filename = "output/plots/allocations-exposure.eps", height = 4, width = 8)

allocations_exposure_table %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/allocations-exposure.txt")

# compare frequency of ex ante and ex post choices in round 5-8 of 4P_4AR with rounds 1-4 of 4A_4AR
responses %>%
  filter((Treatment %in% c("4A_4AR") & Round <= 4) | (Treatment %in% c("4P_4AR") & Round >= 5 & !Revision)) %>%
  count(Category, Treatment) %>%
  group_by(Treatment) %>%
  mutate(percent = n/sum(n)) %>% 
  select(-n) %>%
  spread(Category, percent)

##### APPENDIX C.2: Further analyses of revisions #####

## Figure C.3 (revision-types.eps)  
(allocations %>%
  filter(!RevisionType %in% c("NA", "No Change")) %>%
  filter(Treatment %in% c("4A_4AR", "4P_4AR", "2A2P_4AR", "2P2A_4AR", "4A_4AR Dollars")) %>%
  mutate(Treatment = factor(Treatment, levels = c("4A_4AR", "4P_4AR", "2A2P_4AR", "2P2A_4AR", "4A_4AR Dollars"))) %>%
  count(Treatment, RevisionType) %>%
  group_by(Treatment) %>%
  mutate(Mean = n/sum(n)) %>%
  {. ->> revision_types_table} %>%
  ggplot(aes(x=RevisionType, y=Mean, fill=RevisionType)) +
    geom_bar(stat="identity") +
    theme_bw() +
    scale_fill_manual(values=c('#cccccc','#969696','#636363','#252525')) +
    theme(axis.text.x = element_blank()) +
    theme(panel.grid = element_blank()) +
    facet_wrap(~Treatment, nrow = 1)) %>%
  ggsave(filename = "output/plots/revision-types.eps", height = 4, width = 8)
  
revision_types_table %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/revision-types.txt")

## Figure C.4 (marginal-final.eps)
(allocations %>%
    filter(Treatment %in% c("4P_4AR", "2P2A_4AR", "2A2P_4AR") & Round >= 5 & !is.na(Revised_Category)) %>%
    merge(consistency_categories %>% filter(RoundGroup == "Rounds 5-8" & Treatment %in% c("4P_4AR", "2P2A_4AR", "2A2P_4AR") & Revision)) %>%
    group_by(Treatment, Revised_Category, Consistency) %>%
    summarize(count = n(), SE = NA) %>%
    group_by(Treatment) %>%
    mutate(Mean = count/sum(count)) %>%
    {. ->> marginal_final} %>%
      ggplot(aes(x=Revised_Category, y=Mean, fill=Consistency)) +
      facet_wrap(~ Treatment, nrow = 1) + 
      geom_bar(stat="identity") +
      theme_bw() +
      scale_fill_manual(values=c('#969696','#252525')) +
      theme(axis.text.x = element_text(angle = 270)) +
      theme(panel.grid = element_blank()) +
      xlab("Choice category") +
      ylab("Frequency")) %>%
    ggsave(filename = "output/plots/marginal-final.eps", height = 4, width = 9)

marginal_final %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/marginal-final-table.txt")


  
  
##### APPENDIX C.3: Further analyses of choices between commitment and flexibility #####

# Figure C.5 (commitment-by-round.eps)
(responses %>%
  filter(Treatment == "4AR_4AC" & Round >=5 & DecisionType == "Commitment") %>%
  mutate(
    Response = case_when( # should be able to use recode here
      Response == 0 ~ "Flexibility",
      Response == 1 ~ "Committment",
      Response == 2 ~ "Indifference"
    )
  ) %>%
  count(Round, Response) %>%
  group_by(Round) %>%
  mutate(Percentage = n/sum(n)) %>%
  {. ->> commitment_by_round} %>%
    ggplot() +
    geom_bar(aes(x = Round, y = Percentage, fill = Response), stat = "identity") +
    scale_fill_manual(values = c('#bdbdbd','#f0f0f0','#636363'), name = "Committment Choice") +
    theme_bw() + 
    xlab("Round") +
    coord_flip()) %>%
  ggsave(filename = "output/plots/commitment-by-round.eps", height = 2, width = 8)

commitment_by_round %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/commitment-by-round-table.txt")

# Figure C.6 (commitment-by-initial-category.eps)
(allocations %>%
    filter(Treatment == "4AR_4AC" & Round >=5) %>%
    mutate(
      Commitment = case_when( # should be able to use recode here
        Commitment == 0 ~ "Flexibility",
        Commitment == 1 ~ "Committment",
        Commitment == 2 ~ "Indifference"
      )
    ) %>%
    count(Commitment, Initial_Category) %>%
    group_by(Initial_Category) %>%
    mutate(Percentage = n/sum(n)) %>%
    {. ->> commitment_by_initial_category} %>%
    ggplot() +
      geom_bar(aes(x = Initial_Category, y = Percentage, fill = Commitment), stat = "identity") +
      scale_fill_manual(values = c('#bdbdbd','#f0f0f0','#636363'), name = "Committment Choice") +
      theme_bw() + 
      xlab("Initial Category") +
      coord_flip()) %>%
  ggsave(filename = "output/plots/commitment-by-intial-category.eps", height = 2, width = 8)

commitment_by_initial_category %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/commitment-by-initial-category.txt")

## Is naivete a plausible explanation?

# choices that where intial ex ante and then committed, in last four rounds
allocations %>% 
  subset(Treatment == "4AR_4AC" & Round >= 5 & Initial_Category == "Ex Ante Equalizing" & Commitment == 1) %>% 
  {. ->> ex_ante_commit} %>%
  summarize(
    participants = unique(ParticipantID) %>% length(),
    choices = n()
  )

# of the ex ante + commit choices in rounds 5-8, how many came from subjects who switched ex ante to ex post 0, 1, or 2 times in rounds 1-4
allocations %>% 
  subset(ParticipantID %in% ex_ante_commit$ParticipantID & Round <= 4) %>%
  mutate(count = Initial_to_Revised_Category == "Ex Ante Equalizing to Ex Post Equalizing") %>%
  group_by(ParticipantID) %>%
  summarize(count = sum(count)) %>%
  merge(allocations %>% subset(Treatment == "4AR_4AC" & Round >= 5 & Initial_Category == "Ex Ante Equalizing" & Commitment == 1)) %>%
  count(count) %>%
  mutate(percent = n/sum(n))


# choices that where intial ex ante, chose flex, then changed to ex post, in last four rounds
allocations %>% 
  subset(Treatment == "4AR_4AC" & Round >= 5 & Initial_Category == "Ex Ante Equalizing" & Final_Category == "Ex Post Equalizing" & Commitment != 1 ) %>% 
  {. ->> ex_ante_flex} %>%
  summarize(
    participants = unique(ParticipantID) %>% length(),
    choices = n()
  ) 

# of the ex ante + commit choices in rounds 5-8, how many came from subjects who switched ex ante to ex post 0, 1, or 2 times in rounds 1-4
allocations %>% 
  subset(ParticipantID %in% ex_ante_flex$ParticipantID & Round <= 4) %>%
  mutate(count = Initial_to_Revised_Category == "Ex Ante Equalizing to Ex Post Equalizing") %>%
  group_by(ParticipantID) %>%
  summarize(count = sum(count)) %>%
  merge(allocations %>% subset(Treatment == "4AR_4AC" & Round >= 5 & Initial_Category == "Ex Ante Equalizing" &  Final_Category == "Ex Post Equalizing" & Commitment != 1), all.y = T) %>%
  count(count) %>%
  mutate(percent = n/sum(n))

##### APPENDIX C.4: Fingerprint Analyses #####

## Figure C.7 (fingerprints.eps)
(allocations %>%
  filter(Treatment %in% c("4A_4AR", "4P_4AR") & Round <= 4) %>%
  select(Round, Treatment, OffsettingAmount, NoOffsettingAmount, Initial_Response) %>%
  gather(Allocation, value, -Round, -Treatment) %>%
  mutate(
    Allocation = fct_recode(Allocation, "Actual Average" = "Initial_Response", "Ex Ante Fair" = "OffsettingAmount", "Ex Post Fair" = "NoOffsettingAmount"),
    value = as.numeric(value)
    ) %>%
  group_by(Round, Treatment, Allocation) %>%
  summarize(
    mean = mean(value, na.rm = T),
    SE = plot_sd(value)
  ) %>%
  {. ->> fingerprints} %>%
  ggplot(aes(x = Round, y = mean, linetype = Allocation)) +
    facet_wrap(~Treatment, ncol = 1) +
    line_opts) %>%
  ggsave(filename = "output/plots/fingerprints.eps", height = 5, width = 8)

fingerprints %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/fingerprints.txt")

## Figure C.8 (fingerprints-exposure.eps)
(allocations %>%
    filter(Treatment %in% c("4A_4AR", "4P_4AR", "2P2A_4AR", "2A2P_4AR") & Round >= 5) %>%
    select(Round, Treatment, OffsettingAmount, NoOffsettingAmount, Initial_Response) %>%
    gather(Allocation, value, -Round, -Treatment) %>%
    mutate(
      Allocation = fct_recode(Allocation, "Actual Average" = "Initial_Response", "Ex Ante Fair" = "OffsettingAmount", "Ex Post Fair" = "NoOffsettingAmount"),
      value = as.numeric(value)
      ) %>%
    group_by(Round, Treatment, Allocation) %>%
    summarize(
      mean = mean(value, na.rm = T),
      SE = plot_sd(value)
    ) %>%
    {. ->> fingerprints_exposure} %>%
    ggplot(aes(x = Round, y = mean, linetype = Allocation)) +
      facet_wrap(~Treatment, ncol = 2) +
      line_opts) %>%
  ggsave(filename = "output/plots/fingerprints-exposure.eps", height = 5, width = 8)

fingerprints_exposure %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/fingerprints-exposure.txt")

## Figure C.9 (fingerprints-intial-final.eps)
(allocations %>%
  filter(Treatment %in% c("4A_4AR", "4P_4AR", "2P2A_4AR", "2A2P_4AR") & Round >= 5) %>%
  select(Round, Treatment, OffsettingAmount, NoOffsettingAmount, Initial_Response, Final_Response) %>%
  gather(Allocation, value, -Round, -Treatment) %>%
  mutate(
    Allocation = fct_recode(Allocation, "Original" = "Initial_Response", "Final" = "Final_Response", "Ex Ante Fair" = "OffsettingAmount", "Ex Post Fair" = "NoOffsettingAmount"),
    value = as.numeric(value)    
    ) %>%
  mutate(value = as.numeric(value)) %>%
  group_by(Round, Treatment, Allocation) %>%
  summarize(
    mean = mean(value, na.rm = T),
    SE = plot_sd(value)
  ) %>%
  {. ->> fingerprints_intial_final} %>%
  ggplot(aes(x = Round, y = mean, linetype = Allocation)) +
    facet_wrap(~Treatment, ncol = 2) +
    line_opts_extended) %>%
  ggsave(filename = "output/plots/fingerprints-intial-final.eps", height = 5, width = 8)

fingerprints_intial_final %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/fingerprints-intial-final.txt")

## Figure C.10 (fingerprints-dollars.eps)
(allocations %>%
    filter(Treatment %in% c("4A_4AR Dollars")) %>%
    select(Round, Treatment, OffsettingAmount, NoOffsettingAmount, Initial_Response, Final_Response) %>%
    gather(Allocation, value, -Round, -Treatment) %>%
    mutate(
      Allocation = fct_recode(Allocation, "Original" = "Initial_Response", "Final" = "Final_Response", "Ex Ante Fair" = "OffsettingAmount", "Ex Post Fair" = "NoOffsettingAmount"),
      value = as.numeric(value)    
    ) %>%
    mutate(value = as.numeric(value)) %>%
    filter(!(Round <= 4 & Allocation == "Final")) %>%
    group_by(Round, Allocation) %>%
    summarize(
      mean = mean(value, na.rm = T),
      SE = plot_sd(value)
    ) %>%
    {. ->> fingerprints_dollars} %>%
    ggplot(aes(x = Round, y = mean, linetype = Allocation)) +
    line_opts_extended) %>%
  ggsave(filename = "output/plots/fingerprints-dollars.eps", height = 5, width = 8)

fingerprints_dollars %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/fingerprints-dollars.txt")



##### APPENDIX C.5: Consistent choosers #####

# define consistency
consistency_helper <- 
  allocations %>%
  group_by(Treatment, ParticipantID, FirstHalf) %>%
  filter(!is.na(Initial_Category)) %>%
  summarize(ConsistentChooser = length(unique(Initial_Category)) == 1) %>%
  ungroup()

## basic framing effects

# count of consistent subjects by treatment and first vs second half
consistency_helper %>%
  group_by(Treatment, FirstHalf) %>%
  count(ConsistentChooser) %>%
  mutate(percent = n/sum(n)) %>%
  filter(Treatment %in% c("4A_4AR", "4P_4AR", "2P2A_4AR", "2A2P_4AR", "4AR_4AC") & ConsistentChooser)

# allocations by consistent choosers, at subject level
allocations %>%
  merge(consistency_helper) %>%
  filter(ConsistentChooser & Treatment %in% c("4A_4AR", "4P_4AR", "2P2A_4AR", "2A2P_4AR",  "4AR_4AC") & !is.na(Initial_Category)) %>%
  group_by(Treatment, FirstHalf, ParticipantID) %>%
  summarize(Category = Initial_Category[1]) %>%
  count(Treatment, FirstHalf, Category) %>%
  group_by(Treatment, FirstHalf) %>%
  mutate(percent = n/sum(n)) %>%
  print(n = 50)

# test fraciton of consistent subjects in rounds 5-8 in treatments 4A_4AR and 4P_4AR
consistency_helper %>%
  filter(Treatment %in% c("4A_4AR", "4P_4AR") & !FirstHalf) %>% 
  t.test(ConsistentChooser ~ Treatment, data = .)

## revisions

# define consistency across 8 rounds for 4A_4AR
consistency_helper_2 <- 
  allocations %>%
  filter(Treatment == "4A_4AR") %>%
  count(ParticipantID, Initial_Category) %>%
  group_by(ParticipantID) %>%
  summarize(ConsistentChooser = max(n) >= 7) %>%
  ungroup()

# percent of consistent choosers by this definition
mean(consistency_helper_2$ConsistentChooser)

# intial categories for consistent and inconsistent choosers
allocations %>%
  filter(Treatment == "4A_4AR") %>%
  merge(consistency_helper_2) %>%
  count(ConsistentChooser, FirstHalf, Initial_Category) %>%
  group_by(FirstHalf, ConsistentChooser) %>%
  mutate(percent = n/sum(n)) %>%
  reshape2::dcast(ConsistentChooser + FirstHalf ~ Initial_Category, value.var = "percent")

# frequency of revision
allocations %>%
  filter(Treatment == "4A_4AR" & Round >= 5 & !is.na(Changed_Response)) %>%
  merge(consistency_helper_2) %>%
  count(ConsistentChooser, Changed_Response) %>%
  group_by(ConsistentChooser) %>%
  mutate(percent = n/sum(n))
  
# revision patterns
allocations %>%
  filter(Treatment == "4A_4AR" & Round >= 5 & !is.na(Changed_Response)) %>%
  merge(consistency_helper_2) %>%
  count(ConsistentChooser, Initial_to_Revised_Category) %>%
  group_by(ConsistentChooser) %>%
  mutate(percent = n/sum(n)) %>%
  arrange(desc(ConsistentChooser), desc(percent))

## commitment vs flexibility

# Figure C.11 (commitment-consistent.eps)
(responses %>%
    merge(consistency_helper) %>%
    filter(Treatment == "4AR_4AC" & Round >=5 & DecisionType == "Commitment") %>%
    mutate(
      Response = case_when( # should be able to use recode here
        Response == 0 ~ "Flexibility",
        Response == 1 ~ "Committment",
        Response == 2 ~ "Indifference"
      )
    ) %>%
    count(ConsistentChooser, Response) %>%
    group_by(ConsistentChooser) %>%
    mutate(Percentage = n/sum(n)) %>%
    {. ->> commitment_consistent} %>%
    ggplot() +
    geom_bar(aes(x = ConsistentChooser, y = Percentage, fill = Response), stat = "identity") +
    scale_fill_manual(values = c('#bdbdbd','#f0f0f0','#636363'), name = "Committment Choice") +
    theme_bw() + 
    xlab("Consistent Chooser") +
    coord_flip()) %>%
  ggsave(filename = "output/plots/commitment-consistent.eps", height = 2, width = 8)

commitment_consistent %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/commitment-consistent.txt")

# consistent in both first half and second half
consistency_helper %>%
  filter(Treatment == "4AR_4AC") %>%
  group_by(ParticipantID) %>%
  summarize(consistent_in_both = sum(ConsistentChooser) == 1) %>%
  count(consistent_in_both)

## Figure C.12 (allocations-consistent-choosers.eps)
(allocations %>%
  merge(consistency_helper) %>%
  filter(Treatment == "4AR_4AC" & Initial_Category == "Ex Ante Equalizing" & ConsistentChooser & flip == 2) %>%
  mutate(RoundGroup = if_else(RoundGroup == "Rounds 5-8", "Rounds 5-8", "Rounds 1-4")) %>%
  count(Final_Category, RoundGroup) %>%
  group_by(RoundGroup) %>%
  mutate(Mean = n/sum(n)) %>%
  {. ->> allocations_consistent_choosers} %>%
  ggplot(aes(x = Final_Category, y = Mean)) +
    facet_wrap(~RoundGroup, ncol = 2) + 
    bar_options) %>%
  ggsave(filename = "output/plots/allocations-consistent-choosers.eps", height = 4, width = 8)

allocations_consistent_choosers %>%
  knitr::kable() %>%
  capture.output(file = "output/tables/allocations-consistent-choosers.txt")
  
##### APPENDIX D: Treatment Details #####

## make balance table
participants %>%
  group_by(Treatment) %>%
  summarize(
    `Average Age` = mean(Age),
    `Fraction Female` = mean(Gender == "Female"),
    `Fraction Liberal` = mean(PoliticalStance %in% c("Somewhat Liberal", "Strongly Liberal"), na.rm = T)
    ) %>%
  kable(format = "latex", digits = c(0,1,2,2), booktabs = T, linesep = "") %>%
  cat(., file = "output/tables/balance.tex")

lm(Age ~ Treatment, data = participants) %>% summary()

lm(Gender == "Female" ~ Treatment, data = participants) %>% summary()

lm(PoliticalStance %in% c("Somewhat Liberal", "Strongly Liberal") ~ Treatment, data = participants) %>% summary()

