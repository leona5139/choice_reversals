allocations %>%
  filter(str_detect(Treatment, "_4AR") & Round > 4) %>%
  filter(Initial_Category == "Ex Ante Equalizing" & Revised_Category == "Ex Post Equalizing") %>%
  count(ParticipantID) %>%
  filter(n == 2) %>%
  left_join(participants) %>%
  arrange(Treatment) %>% 
  select(Treatment, ParticipantID, InitialAllocationFactors, RevisionFactors) 
