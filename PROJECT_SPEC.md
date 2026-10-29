# PROJECT_SPEC — Technical Task: Financial Data PII Scrubber

> Source: `INSTRUCTIONS.pdf` (transcribed for reference). Execution governed by
> `Financial_Data_PII_Scrubber_Today_Planner.md`. If the two conflict, the planner's
> privacy rules take precedence.

## Deadline

The source document states two conflicting deadlines:
- "Wednesday, 5 August 2026, 11:59 PM (PKT)" (body text)
- "Friday, 30 October 2026, 11:59 PM (PKT)" (footer)

**Assumed actual deadline: Friday, 30 October 2026, 11:59 PM PKT** (planner target).

## Background

We are building a personal-finance application that analyzes users' bank and wallet
statements using an LLM API. Before any statement text leaves the user's machine, all
sensitive identifiers must be stripped out locally. The task is to build that scrubbing
tool.

## The Task

Build a FastAPI service that scrubs raw financial statements (provided in the attached
`data/` folder — a mix of PDF, DOCX, CSV, and TXT files) so they are safe to send to an
external LLM API. The system has these parts:

1. **Scrubbing engine** — must be able to process EVERY file in a data folder
   (regardless of format, without hardcoding filenames) and produce the scrubbed result
   as ONE single combined string, with a clear per-file header
   (e.g. `---- File: <name> ----`) separating each file's content.
2. **FastAPI API** exposing the scrubber. Endpoint design is up to the implementer; it is
   assessed on architecture thinking. Justify the design in `NOTES.md`.
3. **PostgreSQL persistence** — the scrubbed data must be stored in a PostgreSQL
   database. The schema is the implementer's decision; justify it in `NOTES.md`.
4. **Simple frontend** that drives the API, so the whole flow can be demonstrated end to
   end. Either plain HTML/CSS/vanilla JavaScript or Streamlit/Gradio — no React/Vue/Angular.
5. **AI analysis stage using the Groq API** — after scrubbing, the SCRUBBED data is sent
   to a Groq-hosted LLM to produce an analysis useful for an AI budgeting app (e.g.
   spending by category, top merchants, notable insights — exact output is the
   implementer's design). Groq has a free tier: <https://console.groq.com>.
6. **Chat feature** — through the frontend, the user can chat with the LLM about the
   analysis and the scrubbed data (follow-up questions like "how much did I spend on
   food?" or "which merchant did I pay most often?"). Answers must stay grounded in the
   actual data. Conversation history/context handling is the implementer's design;
   document it in `NOTES.md`.

## What must be REMOVED (replaced with placeholders like `<IBAN>`, `<PHONE>`, `<ACCOUNT_ID>`)

- Bank account numbers and IBANs (all countries)
- Credit/debit card numbers (full or partial beyond a masked last-4 like `xxxx1234`,
  which may stay)
- National identity numbers (CNIC, SSN, SIN, UK National Insurance number, etc.)
- Email addresses and phone numbers (any format, any country)
- Payment handles / wallet IDs (e.g. `someone@easywallet`, UPI IDs)
- Bank routing identifiers (routing numbers, sort codes, SWIFT/BIC, IFSC, transit numbers)
- Long numeric reference/trace/transaction IDs
- Home/customer addresses

## What must be KEPT (it carries analytical value)

- Person names (account holder and counterparties)
- Merchant names (e.g. Foodpanda, Netflix.com, TESCO STORES) — including ones that look
  like URLs
- Dates, times, amounts, balances, currencies
- Transaction types and descriptions (minus the identifiers inside them)

The hard part is exactly this balance: remove every identifier without destroying the
transaction's meaning. A scrubber that deletes Netflix.com as a "URL" or mangles half a
description is as much a failure as one that leaks an IBAN.

## Requirements

1. Python. Any libraries; choice of approach and tooling is part of the evaluation.
2. Scrubbing must run fully locally. RAW data must never be sent to any external API or
   online service — that is the entire purpose of the tool. The ONLY thing allowed to
   leave the machine is the scrubbed output, sent to the Groq API in the analysis stage.
   If the scrubber leaks PII into that call, that is a failure of the core task.
3. Folder in, one string out. The scrubbing engine handles every file in a data folder
   (PDF, DOCX, CSV, TXT — do not hardcode filenames) and produces a single combined
   scrubbed string with per-file headers. It will be run on an unseen folder containing
   statements in similar formats from other banks/countries.
4. FastAPI + PostgreSQL + simple frontend. PostgreSQL must be a real database (local
   install or Docker), not SQLite renamed.
5. Include a short `README.md`: how to install dependencies, set up the database, and run
   the API + frontend, plus 3–5 sentences on the approach and known limitations. The
   system must be runnable from the README alone.
6. The LLM analysis stage must be documented in `NOTES.md` — all four points required:
   - **Model choice:** which Groq model, and why (capability, context window, speed,
     cost — show reasoning).
   - **System prompt design:** the prompt itself and the reasoning behind its structure.
   - **Hallucination & accuracy handling:** how the model is kept from inventing
     transactions/amounts, and how its numbers are verified against the actual data.
   - **Guardrails:** what guardrails were implemented (e.g. output validation, grounding
     checks, refusal handling) and — importantly — how they were tested.
7. Include a written `NOTES.md` (max 1 page — conciseness is part of the exercise)
   documenting R&D and thought process: what was researched, which approaches/libraries
   were considered and rejected (and why), how the final solution was reached, API design
   and DB schema justifications, the four LLM points above, and what would be improved
   with more time. This is required — the video alone is not enough.

## AI Tool Policy

AI tools may be used (ChatGPT, Claude, Copilot, Cursor, etc.). Transparency is mandatory:

1. Full transcript(s) of every AI conversation used for this task (exported file or
   complete copy-paste, not screenshots of fragments).
2. Name of each tool/model used.
3. A separate file (`prompts.txt`) containing only the prompts, in order, without the AI's
   responses.

Submissions that clearly used AI without including these will not be considered. Using AI
is not penalized — how it is driven is part of the assessment.

## Deliverables

Single `.zip` replied to the task email + public GitHub repo link.

1. All source code (scrubbing engine, FastAPI app, frontend, DB schema/SQL)
2. `README.md` (setup incl. database, usage, approach, limitations)
2b. `NOTES.md` — written R&D + thought process (research done, approaches
    considered/rejected, reasoning, API + DB justifications, the four LLM points: model
    choice, system prompt, hallucination handling, guardrails + testing, future
    improvements)
3. The single combined scrubbed output for the provided `data/` folder
4. AI transcripts + tool names (if AI used)
5. `prompts.txt` — prompts only (if AI used)
6. Demo video demonstrating every feature end to end (file in the zip, or a
   Loom/Drive link in the reply)
7. Link to a public GitHub repository with the full solution (same contents as the zip,
   minus the video) — in the reply email and README

## The Video

The video must demonstrate EVERYTHING working — every feature, end to end, through the
frontend: submit the provided data via the FE → API scrubs it → show the scrubbed output →
show the stored rows in PostgreSQL (e.g. a quick `psql` or pgAdmin query on screen) → show
the Groq analysis result → ask the chat a couple of questions about the data and show its
grounded answers. A feature not shown working in the video will be treated as not working.
Then explain: approach and why, API/DB design decisions, research/R&D, and one thing to
improve with more time. Both the video and `NOTES.md` are required; the video complements
the notes, it does not replace them.

## How We Evaluate

- **Correctness** — no leaked identifiers in the output (diffed against a reference)
- **Precision** — no over-scrubbing; merchants, names, amounts, dates survive intact
- **Generalization** — behavior on unseen statements in similar formats
- **Code quality** — readable, runnable from the README alone
- **Architecture** — API endpoint design and PostgreSQL schema, with justifications in
  `NOTES.md`
- **LLM engineering** — model choice, prompt design, hallucination/accuracy handling, and
  guardrail testing (the four `NOTES.md` points)
- **Communication** — the video, README, and `NOTES.md` explain the *why*, not just the
  *what*; written R&D notes are weighed heavily
- **AI usage** — quality of prompts and judgment, if AI was used
