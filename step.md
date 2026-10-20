# Patient History Assistant: steps (single source of truth)

Owner: Kanchan Kharat · Reviewer: Hitesh Gupta · Hypothesis doc: V1.0 (15 Oct 2026)
Last updated: 20 Oct 2026

Sources: Hypothesis doc V1.0, Hitesh's messages, and his
[2-week build plan](https://docs.google.com/document/d/17S2Tf-rt3yNDxn-C4pcxm6BkGK_HXAgZM6TQMISPCS0/edit)
and [architecture diagram](https://drive.google.com/file/d/1AX43tpPmd9OqQ5AJG6bTq6x4MBUm8A3B/view).
If this file and those disagree, the plan doc wins; fix this file.

## What we are building

An AI assistant that turns **written** (synthetic) doctor-patient consultation transcripts into
structured patient-history summaries and **recall cards** for follow-up visits in small clinics.
No audio, no real patient data, no HIS integration in the MVP.

## Hypothesis (short)

- We believe small-clinic GPs struggle to quickly review a repeat patient's previous visit.
- If we build the assistant, then on 20 synthetic transcripts at least 18/20 summaries keep every
  required detail, and 3 role-playing doctors find the key details on the recall card in a median
  under 15 s, at least 2x faster than reading the transcript.
- We are wrong if: fewer than 16/20 summaries are correct after two prompt iterations, any wrong
  dose is saved as approved without a flag, or the card is less than 2x faster than the transcript.
  16 or 17 of 20 = inconclusive: fix and re-run once.

## Pass bars (tests T1 to T5)

| # | Test | Pass bar |
|---|------|----------|
| T1 | Summary accuracy (20 transcripts) | >= 18/20 keep medicine name, dose, frequency, symptom, duration, relevant history |
| T2 | Medicine-dose safety (10 of 20 have 1 planted error: 5 wrong names, 5 wrong doses) | 10/10 planted errors flagged; 0 unflagged mismatches saved as approved |
| T3 | Recall-card accuracy (20 fictional patients) | Correct previous visit on 20/20; 4/4 fields (visit date, main complaint, medicines with doses, follow-up advice) on all 20 |
| T4 | Review time (3 people role-playing doctors) | Median review + approval < 30 s |
| T5 | Multilingual (5 code-mixed Hindi-English transcripts) | >= 4/5 keep required meaning and details |

Test rules:
1. Every "Then" has a number.
2. Re-run the same 20 transcripts after every change.
3. LLM temperature 0; record exact model name/version (note it if the provider cannot pin one).
4. Mark Pass/Fail only after running. Never record a target as a result.

## MVP user flow (synthetic transcripts)

1. Search and open a fictional patient record (shows previous visits).
2. Enter or select a synthetic written transcript (English, Hindi, or code-mixed Hindi-English).
3. AI generates a structured summary: symptoms, duration, medical history, medicines.
4. Medicine names and doses are extracted into separate fields.
5. Rules compare transcript vs summary and flag medicine/dose mismatches and uncertain details.
6. Reviewer (role-playing doctor) corrects and approves on the approval screen. Nothing is saved
   until approved; AI makes no medical decisions.
7. Next visit: recall card shows the correct previous visit (date, main complaint, medicines with
   doses, follow-up advice).

### Later: live recording flow (not in MVP)

1. Explain purpose and get the patient's informed **consent** before recording.
2. Record and transcribe the consultation.
3. Generate summary; flag uncertain details and medicine-dose mismatches.
4. Doctor reviews and approves before saving.

## Out of scope

Live recording / speech-to-text, real patient data, diagnosis or medicine recommendations,
prescription photo storage / OCR, HIS integration, WhatsApp summaries to patients.

## Data and privacy (DPDP)

- Synthetic data only; stored in the shared `test_data/` Drive folder; access limited to owner and
  reviewers.
- Retention: test data kept 90 days after testing ends, then deleted. Early deletion on request,
  done within 7 days. (Hitesh's proposal; Kanchan to confirm or object.)
- Before any real data: privacy notice, consent, access controls, secure storage, retention limits
  and deletion procedure must exist.

## Timeline and steps

| Step | Task | Due | Status |
|------|------|-----|--------|
| 0a | Hypothesis doc V1.0 in Margadeshaka template, two Patient History copies merged | 16 Oct | Done |
| 0b | Accept or reject all ~25 of Hitesh's suggestions in the doc (incl. hypothesis statement, 90d/7d retention); reply "Done" on the Ideas task | now | **Open** |
| S1 | 20 synthetic transcripts + hand-written expected summaries (>= 5 code-mixed); send Hitesh the count | 19 Oct | **Overdue** |
| S2 | 20 fictional patients with previous visits | 20 Oct | **Due today** |
| S3 to S12 | Remaining stories, each with a numeric test (summaries, dose flags, recall card, approval screen, timing, etc.) | 21 to 27 Oct | See plan doc |
| Gate | If T1 < 14/20 after first prompt fix, next week goes to the prompt, not new features | Fri 23 Oct | Pending |
| Build | MVP finished: summaries, dose flags, recall card, review screen | Tue 27 Oct | Pending |
| Tests | Run T1 to T5, record actual numbers, Pass/Fail | 29 Oct | Pending |
| Results | Results note + go / fix / stop decision, review with Hitesh | 30 Oct | Pending |

## Optional

Two 10-minute calls with any GP, showing a mock recall card, to learn whether doctors actually
want this. Interviews are still needed to validate the real-world problem.

## Open items to settle together

- Retention (90 d / 7 d): agree or counter.
- S3 to S12 are listed in Hitesh's plan doc; copy them into the table above so one file is enough.
- Where the code lives (this repo, `DocAssistant`) and the stack: not decided in the docs yet.
