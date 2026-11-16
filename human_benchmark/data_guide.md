# Human benchmark data

Open `code and data files/.RData` in the [replication archive](raw/2016200data.zip). The four main treatments have 1,912 rows in `allocations` (239 participants × 8 rounds).

| `Treatment` | `4A_4AR` | `4P_4AR` | `2A2P_4AR` | `2P2A_4AR` |
| --- | ---: | ---: | ---: | ---: |
| Participants | 71 | 72 | 48 | 48 |

## Choices and revisions

Filter by `ParticipantID` and sort by `Round`. Allocations count tickets for household B (0–10). Household A gets the rest.

| Field | Meaning |
| --- | --- |
| `flip` | Winning group (`1` = computer, `2` = participant). |
| `Initial_Response` | First allocation. `0` gives all ten tickets to A. `NA` marks a skipped P round. |
| `Revised_Response` | Allocation after a revision offer, even if unchanged. |
| `Changed_Response` | `TRUE` = changed, `FALSE` = kept, `NA` = no offer. |
| `Final_Response` | Revised allocation if offered, otherwise the initial allocation. |

Rounds 1–4 follow the treatment prefix. In A, participants chose before learning which group won. In P, they chose only after their group won. In rounds 5–8 (Aᴿ), everyone allocated first and could revise when their group won (twice each). Of 478 offers, participants changed 315 allocations and kept 163.

Participant `R_3WZEL6rzPVZYO5D` (`4P_4AR`) skipped rounds 1 and 4. They left B’s allocation at 7 tickets in round 7 and raised it from 0 to 2 in round 8.

## Demographics

Join `participants` on `ParticipantID`. All 239 reported `Age`. For sex (`Gender`), the authors coded 105 as male and 134 as female, including two with raw code `3`. Their cleaning script gives no label for `3`.

`PoliticalStance` has 223 answers (16 declined) and `PoliticalStanceSafetyNet` has 216 (23 declined). The public files omit birthplace and religion.
