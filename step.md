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

## Architecture (Hitesh's diagram)

Three layers, fictional data only:
- **Web app:** 1 pick transcript (from `test_data`), 3 review screen (flags, edit, approve), 5 search patient (shows recall card).
- **Backend API:** 2a summary service, 2b dose and medicine checker (rules), 4 approve and save, 6 recall card service (DB lookup).
- **Model and data:** LLM (temperature 0, pinned model, returns JSON summary), audit log (model version, prompts, edits, approvals), patients and visits DB.
- **Test only (dotted):** `test_data` folder (20 transcripts + expected summaries, 5 code-mixed) and a test harness (T1 to T5) that runs the pipeline and scores Pass/Fail.

Diagram file: `Patient_History_Assistant_Architecture.svg`.

## Two-week build plan (19 to 30 Oct 2026)

Check-in with test numbers to Hitesh every Fri 23 and Fri 30 Oct.

### Week 1: data, summary service, first T1 run

| Day | Story | Done when (test) |
|-----|-------|------------------|
| Mon 19 Oct | **S1** 20 synthetic transcripts + expected summaries; 5 code-mixed; 10 with one planted error (5 wrong medicine names, 5 wrong doses) | Count script shows 20 transcripts, 20 expected summaries, 5 code-mixed, 10 planted errors listed with IDs |
| Tue 20 Oct | **S2** 20 fictional patients, each with a prior approved visit. Tables: patients, visits, summaries, audit log | Seed script on an empty DB loads 20 patients + 20 visits; 0 rows with a real name or phone |
| Wed 21 Oct | **S3** Transcript to structured summary (symptoms, duration, history, medicines with dose and frequency). Model pinned, temperature 0 | 20/20 outputs pass JSON schema; second run gives same medicines and doses on >= 18/20 |
| Thu 22 Oct | **S4** Scoring script for T1 | Perfect file scores 20/20; copy with one dose removed scores 19/20 |
| Fri 23 Oct | **S5** First T1 result + one prompt fix | Before/after scores and changed prompt written in the results sheet. **Gate:** < 14/20 after the fix means Mon 26 Oct goes to prompt and schema work, not new features |

### Week 2: checks, screens, tests, results

| Day | Story | Done when (test) |
|-----|-------|------------------|
| Mon 26 Oct | **S6** Flag wrong or doubtful medicine names and doses | 10/10 planted errors flagged; at most 2 of 10 clean transcripts falsely flagged |
| Mon 26 Oct | **S9** Search patient, show recall card (visit date, main complaint, medicines with doses, follow-up advice) | 20/20 cards open for the right patient; 4/4 fields correct on every card |
| Tue 27 Oct | **S7** Review screen showing summary and flags | Approve with an unhandled flag is blocked; after fix or dismiss, Approve works |
| Tue 27 Oct | **S8** Approve and save; every action in audit log. **Build done by end of day** | Approve 15 of 20, leave 5: 15 saved, 0 unapproved saved, audit log has 20/20 entries with time and action |
| Wed 28 Oct | **S10** Timing sessions with 3 role-playing doctors; run T1 to T3 on final build | Median recall-card lookup < 15 s and >= 2x faster than reading the transcript; approval < 30 s |
| Thu 29 Oct | **S11** Run T4 and T5, then re-run all T1 to T5 on the final build | Each test shows Pass/Fail with its number; nothing changed after this run |
| Fri 30 Oct | **S12** Results note (max 1 page) + review with Hitesh | Each test number against its target, plus a go / fix / stop call |

### Rules and risks

- Mock data only: no real names, phones or recordings.
- Model and prompt pinned, temperature 0, so runs can be repeated.
- Nothing is saved until the doctor approves; audit log records every action.
- If the build slips, drop search polish, not the tests.
- Week 1 gate: if T1 < 14/20 after the first prompt fix, Mon 26 Oct goes to prompt and schema work and the dose checker (S6) moves to Tue.

### Before the plan (hypothesis doc housekeeping)

| Task | Status |
|------|--------|
| Accept or reject Hitesh's ~25 suggestions in the hypothesis doc (incl. 90 d / 7 d retention); reply "Done" on the Ideas task | **Open** |
| Send Hitesh the transcript count when S1 is ready | **Open** |

## Optional

Two 10-minute calls with any GP, showing a mock recall card, to learn whether doctors actually
want this. Interviews are still needed to validate the real-world problem.

## Open items to settle together

- Retention (90 d / 7 d): agree or counter.
- Where the code lives (this repo, `DocAssistant`) and the stack: not decided in the docs yet.
