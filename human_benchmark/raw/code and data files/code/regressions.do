*--------------------------------------------------
* Fairness
* regressions.do
* Jeffrey Naecker and Deniz Aydin
*--------------------------------------------------

/*
Description: Multinomial logit regressions for Fairness paper

Most of the tests can be run as regressions using responses.dta,
which has each response for the participant as one observation.  
For example, inital and final allocations are taken as separate observations.
Some other regressions (particularly when looking at joint distribution
results) must be run from allocations.dta, which takes as its level of 
observation the subject-to-household-pair interaction. In this data set,
for example, initial and revised allocations are in the same observation but
coded as different variables.
*/

*********************
******* SETUP *******
*********************
{
***** set preferences *****
{
*version 14              // Set Version number for backward compatibility
set more off            // Disable partitioned output
clear all               // Start with a clean slate
set linesize 80         // Line size limit to make output more readable
macro drop _all         // clear all macros
capture log close       // Close existing log files
}

***** constants *****
{
* cluster on participants throughout
global cluster="vce(cluster ParticipantID)"
}

***** prepare responses.dta *****
{
* dont change this; use File > Change Working Directory instead
use "data/clean/responses.dta", replace

* create aditional variables to go in mlogit regressions
encode Treatment, 					generate(X_Treat)
encode SwitchingType, 				generate(X_SwitchingType)
encode Category if Category!="NA", 	generate(Y_Category)
tab Treatment, 						gen(D_Treat_)
tab SwitchingType, 					gen(D_SwitchingType_)

save responses-temp, replace
}

***** prepare allocations.dta *****
{
* dont change this; use File > Change Working Directory instead
use "data/clean/allocations.dta", replace

* create aditional variables to go in mlogit regressions
encode Treatment, 											generate(X_Treat)
encode SwitchingType, 										generate(X_SwitchingType)
encode Initial_Category if Initial_Category!="NA", 			generate(Y_Initial_Category)
encode Revised_Category if Revised_Category!="NA", 			generate(Y_Revised_Category)
encode Final_Category if Final_Category!="NA", 				generate(Y_Final_Category)
encode Initial_to_Revised_Category if Final_Category!="NA", generate(Y_Initial_to_Revised_Category)
encode RevisionType,                                        generate(Y_RevisionType)
tab Treatment, 										 		generate(D_Treat_)
tab SwitchingType, 											generate(D_SwitchingType_)

save allocations-temp, replace
}

***** prepare participants.dta *****
{
* dont change this; use File > Change Working Directory instead
use "data/clean/participants.dta", replace

* create aditional variables to go in mlogit regressions
encode PoliticalStance if PoliticalStance!="NA", 					generate(Y_Pol_1)
encode PoliticalStanceSafetyNet if PoliticalStanceSafetyNet!="NA", 	generate(Y_Pol_2)
encode Gender if Gender!="NA", 										generate(Y_Gender)
tab Treatment, 														generate(Dtreat)

save participants-temp, replace
}
}
**********************************************************
***** SECTION 4: Framing effects and choice reversals ****
**********************************************************
{
use "responses-temp.dta"

***** SECTION 4.2: Basic Framing Effects *****
{
// Test corresponding to Figure 1 (allocations.pdf)

// Hypothesis: framing does not affects initial perspective in Rounds 1-4 of 4A_4AR vs Rounds 1-4 of 4P_4AR
mlogit Y_Cat X_Treat if (Treatment=="4A_4AR"|Treatment=="4P_4AR") & inrange(Round,1,4), $cluster
test X_Treat

// Tests corresponding to Figure 2 (allocations-with-alternating.pdf)
// Goal: show intial framing does not establish a persistent perspective

// Hypothesis: frame has no effect on allocations in Rounds 1-4 of 4P_4AR, 4A_4AR, 2A2P_4AR, and 2P2A_4AR
gen X_Frame=(Treatment=="4P_4AR" & inrange(Round,1,4))|(Treatment=="2A2P_4AR" & inrange(Round,3,4))|(Treatment=="2P2A_4AR" & inrange(Round,1,2))
mlogit Y_Cat X_Frame D_Treat_1* if inrange(Round,1,4) & (Treatment=="4A_4AR"|Treatment=="4P_4AR"|Treatment=="2A2P_4AR"|Treatment=="2P2A_4AR"), $cluster
test X_Frame  

// Hypothesis: treatment has no effect on allocations (using same regression as above)
test D_Treat_1 D_Treat_10 D_Treat_11  

// Hypothesis: allocations last 4 rounds of all treatments are indistinguishable
mlogit Y_Cat X_Treat if (Treatment=="4A_4AR"|Treatment=="4P_4AR"|Treatment=="2A2P_4AR"|Treatment=="2P2A_4AR") & inrange(Round,5,8), $cluster
test X_Treat 
}
***** SECTION 4.3: Choice Reversals *****
{
// Tests corresponding to Figure 3 (revisions.pdf)

// Hypothesis: initial and revised allocation distributions are the same
// in rounds 5-8 of of 4P_4AR, 4A_4AR, 2A2P_4AR, and 2P2A_4AR
mlogit Y_Cat Revision if inrange(Round,5,8) & (Treatment=="4A_4AR"|Treatment=="4P_4AR"|Treatment=="2A2P_4AR"|Treatment=="2P2A_4AR"), $cluster
test Revision 

// Hypothesis: distribution of revision types is the same 
// in rounds 5-8 of of 4P_4AR, 4A_4AR, 2A2P_4AR, and 2P2A_4AR
save responses-temp, replace
use "allocations-temp.dta"
mlogit Y_Initial_to_Revised_Category X_Treat if inrange(Round,5,8) & (Treatment=="4A_4AR"|Treatment=="4P_4AR"|Treatment=="2A2P_4AR"|Treatment=="2P2A_4AR")
test X_Treat
}
}
**********************************************	
**** SECTION 5: Commitment Opportunities *****
**********************************************
{
**** SECTION 5.1: Experimental Design ******
{

// test for diffence of intial and revised behavior in second half of 4A_4AR with first half of 4AR_4AC

// intial
mlogit Y_Initial_Category X_Treat if (Treatment=="4A_4AR" & inrange(Round,5,8))|(Treatment=="4AR_4AC" & inrange(Round,1,4)), $cluster
test X_Treat 

// revised 
mlogit Y_Final_Category X_Treat if (Treatment=="4A_4AR" & inrange(Round,5,8))|(Treatment=="4AR_4AC" & inrange(Round,1,4)), $cluster
test X_Treat 

}
**** SECTION 5.2: Overall effects of commitment opportunities ******
{

// test for difference of frequency of revision across treatments
// difference between first half and second half of 4AR_4AC
gen   X_test = inrange(Round,1,4)
gen   Changed_Response_2 = Changed_Response
replace Changed_Response_2 = 0 if Changed_Response == .z
logit Changed_Response_2 X_test if Treatment=="4AR_4AC" & flip == "2", $cluster
test  X_test
drop  X_test

// difference between second half of 4A_4AR and seccond half of 4AR_4AC
gen   X_test = Treatment == "4AR_4AC"
logit Changed_Response_2 X_test if (Treatment=="4AR_4AC" | Treatment == "4A_4AR") & inrange(Round,5,8) & flip == "2", $cluster
test  X_test
drop  X_test

// test for difference of frequency of revised at least once across treatments
// second half of 4AR_4AC vs first half of same treatment
egen i_Revised = max(Changed_Response_2), by(ParticipantID Round)
egen tag_ir = tag(ParticipantID Round)
gen  X_test = inrange(Round,1,4)
reg  i_Rev X_test if Treatment=="4AR_4AC" & tag_ir
test X_test
drop X_test

// second half of 4AR_4AC vs second half of 4AR_4AC
gen  X_test = Treatment == "4AR_4AC"
reg  i_Rev X_test if (Treatment=="4AR_4AC" | Treatment == "4A_4AR") & inrange(Round,5,8) & tag_ir
test X_test
drop X_test

//test for difference of initial categories between first and second half of 4AR_4AC
mlogit Y_Initial_Category FirstHalf if Treatment=="4AR_4AC", $cluster
test FirstHalf

//test for difference of final categories between first and second half of 4AR_4AC
mlogit Y_Final_Category FirstHalf if Treatment=="4AR_4AC", $cluster
test FirstHalf
}
**** SECTION 5.3: Understanding the demand for flexibility and commitment ******
{
// Test corresponding to commitment.pdf
// Hypothesis: commitment choices in rounds 5-8 do not depend on 
// revision behavior in rounds 1-4 of treatment 4AR_4AC
save allocations-temp, replace
use "responses-temp.dta"
mlogit Response D_SwitchingType_* if DecisionType == "Commitment" & inrange(Round,5,8) & Treatment=="4AR_4AC", $cluster
test D_SwitchingType_2 D_SwitchingType_3 D_SwitchingType_4 D_SwitchingType_5

*** TODO: p-values in 5.3.3 ***
}
}
*****************************************
**** SECTION 6: Contingent planning *****
*****************************************
{
**** SECTION 6.2: Planned switching *****
{
// Test to compare initial allocations in last four rounds of 4A_4AR and 4A_4AP
mlogit Y_Cat X_Treat if inrange(Round,5,8) & (Treatment=="4AR Plan" | Treatment=="4A_4AR") & !Revision, $cluster
test X_Treat 

// test if initial allocations and contingent plan revisions allocations are the same
mlogit Y_Cat Revision if inrange(Round,1,5) & Treatment=="4AR Plan", $cluster
test Revision 

// test for similarity of revision patterns in 4A_4AR and 4A_4AP
save responses-temp, replace
use "allocations-temp.dta"
mlogit Y_Initial_to_Revised_Category X_Treat if inrange(Round,5,8) & (Treatment=="4A_4AR"|Treatment=="4AR Plan")
test X_Treat
}
}
*****************************************
**** APPENDIX C *************************
*****************************************
{
**** Appendix C.1: Further analyses of basic framing effects
{
use "responses-temp.dta"

**** formal tests involving figure 2
// first two rounds of 2A2P_ and 4A_
mlogit Y_Cat X_Treat if (Treatment=="2A2P_4AR"|Treatment=="4A_4AR") & inrange(Round,1,2), $cluster
test X_Treat

// first two rounds of 2P2A_ and 4P_
mlogit Y_Cat X_Treat if (Treatment=="2P2A_4AR"|Treatment=="4P_4AR") & inrange(Round,1,2), $cluster
test X_Treat

// rounds 1-2 vs rounds 3-4 of mixed treatments
gen X_test = inrange(Round,1,2)
mlogit Y_Cat X_test if Treatment=="2A2P_4AR" & inrange(Round,1,4), $cluster
test X_test

mlogit Y_Cat X_test if Treatment=="2P2A_4AR" & inrange(Round,1,4), $cluster
test X_test
drop X_test

// rounds 3-4 of 2A2P_ vs 4P_
mlogit Y_Cat X_Treat if (Treatment=="2A2P_4AR"|Treatment=="4P_4AR") & inrange(Round,3,4), $cluster
test X_Treat

// rounds 3-4 of 2P2A_ vs 4A_
mlogit Y_Cat X_Treat if (Treatment=="2P2A_4AR"|Treatment=="4A_4AR") & inrange(Round,3,4), $cluster
test X_Treat

// rounds 5-8 of 2P2A_ vs 4A_
mlogit Y_Cat X_Treat if (Treatment=="2P2A_4AR"|Treatment=="4A_4AR") & inrange(Round,5,8) & !Revision, $cluster
test X_Treat

// rounds 5-8 of 2A2P_ vs 4A_
mlogit Y_Cat X_Treat if (Treatment=="2A2P_4AR"|Treatment=="4A_4AR") & inrange(Round,5,8) & !Revision, $cluster
test X_Treat

**** effect of extended exposure
// rounds 1-4 vs 5-8 of 4P_4AR
mlogit Y_Cat FirstHalf if Treatment=="4P_4AR" & !Revision, $cluster
test FirstHalf

// rounds 5-8 of 4P_4AR vs 4A_4AR
mlogit Y_Cat X_Treat if (Treatment=="4P_4AR"|Treatment=="4A_4AR") & inrange(Round,5,8) & !Revision, $cluster
test X_Treat
}
**** Appendix C.2: Futher analyses of revisions
{
// test for differences across treatments in revision types
use "allocations-temp.dta", replace

mlogit Y_RevisionType X_Treat if (Treatment=="4A_4AR"|Treatment=="4P_4AR") & inrange(Round,5,8) & RevisionType != "NA" & RevisionType != "No Change",  $cluster
test   X_Treat

mlogit Y_RevisionType X_Treat if (Treatment=="4A_4AR"|Treatment=="2A2P_4AR") & inrange(Round,5,8) & RevisionType != "NA" & RevisionType != "No Change", $cluster
test   X_Treat

mlogit Y_RevisionType X_Treat if (Treatment=="4A_4AR"|Treatment=="2P2A_4AR") & inrange(Round,5,8) & RevisionType != "NA" & RevisionType != "No Change", $cluster
test   X_Treat

// distribution of revised categories of 2A2P_4AR, 2P2A_4AR, and 4P_4AR vs 4A_4AR
mlogit Y_Revised_Category X_Treat if (Treatment=="2A2P_4AR"|Treatment=="4A_4AR") & inrange(Round,5,8), $cluster
test   X_Treat

mlogit Y_Revised_Category X_Treat if (Treatment=="2P2A_4AR"|Treatment=="4A_4AR") & inrange(Round,5,8), $cluster
test   X_Treat

mlogit Y_Revised_Category X_Treat if (Treatment=="4P_4AR"|Treatment=="4A_4AR") & inrange(Round,5,8), $cluster
test   X_Treat
}
**** Appendix C.4: Fingerprint Regressions
{
use "responses-temp.dta", replace

// fingerprints for non-mixed treatments
reg Response OffsettingAmount if Treatment == "4A_4AR" & Round <= 4, $cluster
reg Response OffsettingAmount if Treatment == "4P_4AR" & Round <= 4, $cluster
// test of difference 
reg Response OffsettingAmount if Treatment == "4A_4AR" & Round <= 4
est store fingerprint1
reg Response OffsettingAmount if Treatment == "4P_4AR" & Round <= 4
est store fingerprint2
suest fingerprint1 fingerprint2, $cluster
test [fingerprint1_mean]OffsettingAmount = [fingerprint2_mean]OffsettingAmount

// fingerprints after varying experience in first 4 rounds
reg Response OffsettingAmount if Treatment == "4A_4AR" & Round >= 5 & !Revision, $cluster
reg Response OffsettingAmount if Treatment == "4P_4AR" & Round >= 5 & !Revision, $cluster
reg Response OffsettingAmount if Treatment == "2A2P_4AR" & Round >= 5 & !Revision, $cluster
reg Response OffsettingAmount if Treatment == "2P2A_4AR" & Round >= 5 & !Revision, $cluster
// test of difference
reg Response OffsettingAmount if Treatment == "4A_4AR" & Round >= 5 & !Revision
est store fingerprint1
reg Response OffsettingAmount if Treatment == "4P_4AR" & Round >= 5 & !Revision
est store fingerprint2
reg Response OffsettingAmount if Treatment == "2A2P_4AR" & Round >= 5 & !Revision
est store fingerprint3
reg Response OffsettingAmount if Treatment == "2P2A_4AR" & Round >= 5 & !Revision
est store fingerprint4
suest fingerprint1 fingerprint2 fingerprint3 fingerprint4, $cluster
test [fingerprint1_mean]OffsettingAmount = [fingerprint2_mean]OffsettingAmount = [fingerprint3_mean]OffsettingAmount  = [fingerprint4_mean]OffsettingAmount

// fingerprints of intial and revised 
reg Response OffsettingAmount if Treatment == "4A_4AR" & Round >= 5 & Revision, $cluster
reg Response OffsettingAmount if Treatment == "2A2P_4AR" & Round >= 5 & Revision, $cluster
reg Response OffsettingAmount if Treatment == "2P2A_4AR" & Round >= 5 & Revision, $cluster
reg Response OffsettingAmount if Treatment == "4P_4AR" & Round >= 5 & Revision, $cluster

// fingerprints for split-the-prize
reg Response OffsettingAmount if Treatment == "4A_4AR Dollars" & Round <= 4, $cluster
reg Response OffsettingAmount if Treatment == "4A_4AR Dollars" & Round >= 5 & !Revision, $cluster
reg Response OffsettingAmount if Treatment == "4A_4AR Dollars" & Round >= 5 & Revision, $cluster
}
}
