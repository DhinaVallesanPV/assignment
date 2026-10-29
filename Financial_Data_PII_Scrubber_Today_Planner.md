# Financial Data PII Scrubber — Thursday Execution Planner

**Execution date:** Thursday, 29 October 2026  
**Target:** A working, demonstrable application by tonight, with Friday reserved for validation, documentation completion, recording, packaging, and submission.  
**Deadline:** Friday, 30 October 2026, 11:59 PM PKT.

## 1. Mission and operating model

Build the assignment in small, verifiable phases. Do not attempt to generate the entire application in one pass.

- **Project owner / technical lead:** Approves decisions, prioritizes work, reviews evidence, and decides whether a phase is accepted.
- **OpenCode:** Inspects the repository, proposes focused plans, implements the approved task, runs checks, and reports actual results.
- **ChatGPT:** Used separately by the project owner for architecture review, debugging, prompt planning, and documentation guidance. Keep approved decisions in this project specification so tools do not invent conflicting designs.

**Definition of success tonight:** The main end-to-end path works: files are processed locally → PII is scrubbed → one combined output is produced → scrubbed data is persisted in PostgreSQL → Groq analysis works → chat answers questions against the scrubbed data. All claims must be supported by actual verification.

The schedule below is a timebox, not permission to skip security or correctness. If work runs late, cut visual polish and optional features first.

## 2. Critical privacy and implementation rules

1. **Raw financial statement contents must remain local.** Do not read, summarize, upload, attach, log, or transmit supplied statement contents through a cloud-backed coding model or any external service. Use filenames, source code, and synthetic examples for agent-assisted development.
2. The application's extraction and scrubbing must execute locally. Only the resulting scrubbed text may be sent to Groq, after local checks. Do not send raw files or raw extracted text to Groq.
3. Configure `.gitignore` before processing data. Exclude `.env`, supplied statement files, private outputs, caches, and other sensitive artifacts from version control. Never publish raw data or an output that has not been verified safe to share.
4. Do not hardcode input filenames, bank names, or one country's formats. Discover supported files dynamically and use configurable recognizers/rules.
5. Preserve analytical meaning: person names, merchant names (including names that resemble URLs), dates, times, amounts, balances, currencies, transaction types, and descriptions. Replace identifiers without deleting the surrounding useful text.
6. Use real PostgreSQL. SQLite is not an acceptable substitute.
7. Do not claim a test passed unless it was actually executed. Report `PASS`, `FAIL`, or `NOT VERIFIED` with evidence.
8. Inspect before editing. Make the smallest coherent change. Do not rewrite unrelated working code or add unnecessary frameworks.
9. Do not put API keys in frontend code. Keep secrets in environment variables.
10. Keep the real task data out of ChatGPT/OpenCode prompts and transcripts. AI transcripts and `prompts.txt` must be genuine records; never fabricate missing records.

## 3. Recommended project structure

Adapt to the existing workspace after inspecting it; do not blindly overwrite existing files.

```text
financial-pii-scrubber/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── api/
│   │   ├── scrub.py
│   │   ├── analysis.py
│   │   └── chat.py
│   ├── services/
│   │   ├── file_extractor.py
│   │   ├── pii_scrubber.py
│   │   ├── scrub_pipeline.py
│   │   ├── financial_parser.py
│   │   └── groq_service.py
│   └── static/
│       ├── index.html
│       ├── styles.css
│       └── app.js
├── data/                    # Local input; never commit
├── output/                  # Local output; review before sharing
├── tests/                   # Synthetic test data only
├── sql/schema.sql
├── transcripts/              # Full genuine AI conversations
├── PROJECT_SPEC.md
├── README.md
├── NOTES.md
├── prompts.txt               # Actual prompts only, chronological order
├── requirements.txt
├── .env.example
└── .gitignore
```

## 4. Time management and priorities

Use the following target schedule. If the actual start time is later, preserve the order and shorten optional work—not privacy checks or core validation.

| Target time | Phase | Required outcome | Priority |
|---|---|---|---|
| 1:30–2:00 PM | 0. Workspace and safeguards | Project structure, assignment spec, `.gitignore`, input ZIP extracted locally | Critical |
| 2:00–2:30 PM | 1. Inspect and plan | Approved architecture, dependencies, modules, schema, acceptance criteria | Critical |
| 2:30–4:00 PM | 2. Extract and scrub | Dynamic discovery; PDF/DOCX/CSV/TXT extraction; combined output; first scrubber version | Critical |
| 4:00–4:30 PM | 3. Core accuracy check | Synthetic tests for identifiers, false positives, and preservation of meaning | Critical |
| 4:30–5:45 PM | 4. API and PostgreSQL | Upload/scrub, persist, retrieve; real PostgreSQL verified | Critical |
| 5:45–6:45 PM | 5. Frontend | Upload, scrubbed-output view, analysis view, chat UI | High |
| 6:45–8:00 PM | 6. Groq | Analysis and follow-up chat; only scrubbed content sent | High |
| 8:00–9:00 PM | 7. Integration | End-to-end flow, database check, chat grounding, critical bug fixes | Critical |
| 9:00–10:00 PM | 8. Documentation and AI records | README, NOTES, actual prompts, complete transcripts | Critical |
| 10:00–11:00 PM | 9. Demo and release preparation | Demo recording, repository audit, ZIP prepared | High |

**Timebox rules:**
- At the end of each phase, spend at most five minutes reviewing the agent's report and deciding whether to accept it or issue a focused correction.
- If a task exceeds its timebox by 15 minutes, stop adding features. Ask the agent for a root-cause diagnosis and the smallest viable fix.
- If Groq is blocked by credentials or service availability, finish and verify the local engine/API/database first, then return to Groq. Do not falsely report the LLM stage as working.
- If time is short, reduce UI polish, charts, and optional abstractions. Never skip local scrubbing, persistence, privacy checks, required documentation, or a truthful status report.
- Commit after each verified phase so a later change can be reverted safely.

## 5. Phase instructions

### Phase 0 — Workspace and privacy safeguards (1:30–2:00 PM)

**Tasks**
1. Inspect existing files and tools without opening or summarizing statement contents.
2. Create/confirm the project structure and save the full assignment in `PROJECT_SPEC.md`.
3. Extract the provided archive locally into `data/` if not already extracted.
4. Add `.gitignore` entries for `.env`, `data/`, private outputs, caches, virtual environments, and generated sensitive files.
5. Create `.env.example` with placeholder values only. Never create a real secret in tracked files.

**Acceptance criteria**
- Project structure is clear.
- The input files are available locally.
- Raw data and secrets are excluded from Git.
- No external AI service has received raw data.

### Phase 1 — Inspect and architecture plan (2:00–2:30 PM)

OpenCode must inspect the workspace and return a plan before coding. Prefer a modular FastAPI app with a separate local scrubbing service, SQLAlchemy/PostgreSQL persistence, plain HTML/CSS/JavaScript, and a Groq service.

**API proposal**
- `POST /api/scrub`: accept multiple uploaded files, scrub locally, combine output, persist scrubbed result.
- `GET /api/documents/{id}`: retrieve scrubbed text and processing status.
- `POST /api/documents/{id}/analysis`: generate and save analysis.
- `POST /api/chat`: answer a question about a selected document/conversation.
- `GET /api/conversations/{id}`: retrieve conversation history.
- `GET /health`: health check.

**Database proposal**
- `documents`: scrubbed combined text, file count, status, timestamps.
- `analyses`: document foreign key, model, structured analysis, timestamp.
- `conversations`: document foreign key and timestamps.
- `chat_messages`: conversation foreign key, role, content, timestamp.

Do not store raw statement text. Document any deviations and their reasons.

**Acceptance criteria**
- Plan and dependencies are reviewed before implementation.
- API and schema choices are recorded.
- OpenCode waits for approval before starting Phase 2.

### Phase 2 — File extraction and local scrubber (2:30–4:00 PM)

**Tasks**
1. Dynamically discover all supported files; do not hardcode names.
2. Extract text from PDF, DOCX, CSV, and TXT. Handle unreadable or unsupported files explicitly.
3. Return one combined string with a header such as `---- File: example.pdf ----` for every processed file.
4. Implement configurable, layered PII detection. Use deterministic patterns for structured identifiers and suitable local recognizers for less structured entities. Avoid relying on one regex or one tool to guarantee complete detection.
5. Replace bank account numbers, IBANs, card numbers (while allowing explicitly permitted masked last-four formats), national IDs, emails, phones, payment handles, routing identifiers, long reference IDs, and home/customer addresses.
6. Preserve person and merchant names, merchant-like URLs such as `Netflix.com`, dates, amounts, balances, currencies, and transaction descriptions.
7. Add a local command-line entry point that writes `output/scrubbed_output.txt`.

**Synthetic tests**
- Known identifiers are replaced.
- `Netflix.com` and other merchant-like names are retained.
- Masked card values such as `xxxx1234` remain when permitted.
- Dates, currency symbols, amounts, balances, and useful descriptions survive.
- Identifiers embedded inside descriptions are replaced without deleting the whole transaction.
- Different filenames and multiple files are handled.
- Empty, unreadable, or malformed files produce clear outcomes.

**Acceptance criteria**
- The engine returns one combined string with per-file headers.
- Tests use synthetic data only.
- Limitations and unhandled cases are reported honestly.

### Phase 3 — Scrubber review (4:00–4:30 PM)

Review synthetic test outcomes and the code. Check for both missed identifiers and false positives. Avoid printing real raw or sensitive statement text to logs or AI conversations.

Then run the supplied data through the local program. Review the result locally and do not paste its contents into an AI assistant. Include the combined output in the submission only after verifying it is safe to share under the task's privacy constraints.

**Acceptance criteria**
- Actual execution result is known.
- Problems are logged as issue descriptions without exposing PII.
- No unsupported claim of perfect detection is made.

### Phase 4 — FastAPI and PostgreSQL (4:30–5:45 PM)

**Tasks**
1. Add configuration and SQLAlchemy database connection.
2. Create schema/models and initialization instructions.
3. Implement upload/scrub and document retrieval.
4. Persist scrubbed output and metadata only.
5. Add clear request validation, safe error handling, and health endpoint.
6. Test using synthetic uploads and query PostgreSQL directly to prove persistence.

**Acceptance criteria**
- API starts using documented commands.
- Real PostgreSQL is connected.
- A scrubbed record can be written and retrieved.
- No raw statement text is stored.
- Database errors do not leak secrets or statement contents.

### Phase 5 — Minimal frontend (5:45–6:45 PM)

Build one plain HTML/CSS/JavaScript page with:
1. Multi-file upload.
2. Processing state and errors.
3. Combined scrubbed-output display.
4. Analysis results.
5. Chat input and conversation history.

Use the backend API; do not duplicate scrubbing logic in JavaScript. Keep the Groq API key on the server.

**Acceptance criteria**
- A user can start the flow from the frontend.
- Scrubbed output and API errors are visible.
- The interface remains minimal; visual polish is secondary.

### Phase 6 — Groq analysis and chat (6:45–8:00 PM)

**Analysis**
- Select a currently available Groq model after checking capability, context size, speed, cost, and access.
- Send only scrubbed text after local validation.
- Ask for spending categories, merchant frequency, recurring patterns, and notable insights.
- Prefer structured JSON output and validate it server-side.

**Chat**
- Accept a document/conversation ID and user question.
- Retrieve the associated scrubbed text and bounded conversation history from PostgreSQL.
- Keep the system prompt separate from user-supplied statement content.
- Treat transaction descriptions as untrusted data, not instructions.
- Use Python to calculate exact totals/counts from parsed transactions wherever reliable; use the LLM to explain results.
- If records cannot be parsed or the answer is unsupported, say so rather than inventing figures.
- Store chat messages and model responses in the database.

**Acceptance criteria**
- Actual Groq call succeeds with a configured key.
- The request contains scrubbed content only.
- At least one analysis and two grounded questions are demonstrated.
- An unsupported question is handled honestly.
- If Groq is not verified, clearly report it as `FAIL` or `NOT VERIFIED`.

### Phase 7 — End-to-end integration (8:00–9:00 PM)

Run the complete journey from the frontend:
1. Upload files.
2. Scrub locally.
3. Display combined output.
4. Confirm persistence in PostgreSQL.
5. Generate Groq analysis.
6. Ask follow-up chat questions.
7. Confirm history retrieval.

Inspect the code path that builds Groq requests. Use synthetic canary identifiers to verify the scrubber removes them and that the external request is assembled from scrubbed output—not raw input. Do not use a real secret as a test canary.

Fix critical integration defects only. Keep a known-good Git commit.

### Phase 8 — Documentation and AI records (9:00–10:00 PM)

**README.md**
- Prerequisites and dependency installation.
- PostgreSQL setup and schema initialization.
- `.env` configuration using `.env.example` as a template.
- Commands to run API and frontend.
- End-to-end usage.
- Three to five sentences on approach and known limitations.

**NOTES.md — maximum one page**
- Research and approaches considered/rejected, with reasons.
- API and database design justifications.
- Actual Groq model choice and capability/context/speed/cost reasoning.
- Actual system prompt and why it is structured that way.
- Hallucination prevention and numerical verification.
- Implemented guardrails and how they were actually tested.
- Known limitations and one or more future improvements.

**AI policy**
- Save full, genuine transcripts of every AI conversation used for the task, with tool/model names.
- `prompts.txt` must contain only the actual prompts in chronological order, without responses.
- Do not fabricate transcripts or reconstruct missing content as if it were original.
- Do not include supplied raw financial statements in prompts, transcripts, public repository, or AI service uploads.

### Phase 9 — Demo and release preparation (10:00–11:00 PM)

Prepare the demo in this order:
1. Show the frontend and upload the files.
2. Show the combined scrubbed output and file headers.
3. Show relevant PII replacement and preserved financial meaning without exposing unnecessary sensitive details.
4. Query PostgreSQL on screen to show persisted scrubbed rows.
5. Run Groq analysis.
6. Ask two questions and show grounded answers.
7. Explain architecture choices, research/trade-offs, limitations, and one future improvement.

Before packaging:
- Verify `.env`, secrets, raw inputs, and unsafe outputs are excluded from the public GitHub repository.
- Confirm the output file is included only if it is safe to share and required for submission.
- Confirm README instructions match actual commands.
- Create the ZIP with all required source, documentation, output, genuine transcripts, and prompts file; exclude the video from the repository copy if following the assignment instructions.
- Confirm the public repository URL and ZIP are valid.
- Reserve Friday for final validation and submission, not initial implementation.

## 6. Required reporting format after each task

At the end of each phase, report:

1. **Status:** `PASS`, `FAIL`, or `NOT VERIFIED`.
2. **Files inspected and changed.**
3. **Design/implementation decisions.**
4. **Commands actually executed.**
5. **Test results and evidence.**
6. **Known defects and limitations.**
7. **Privacy implications or risks.**
8. **Recommended next task.**

Do not begin the next phase until the project owner reviews the report and approves it.

## 7. Release acceptance checklist

- [ ] Application runs using README instructions.
- [ ] PDF, DOCX, CSV, and TXT files are dynamically discovered and processed.
- [ ] Combined output includes a header for each file.
- [ ] Synthetic PII tests check both removal and preservation.
- [ ] Supplied data is scrubbed locally and output is reviewed locally.
- [ ] PostgreSQL persistence and retrieval are demonstrated.
- [ ] Groq receives scrubbed data only.
- [ ] Analysis is generated and persisted.
- [ ] Chat answers are grounded; unsupported questions are handled honestly.
- [ ] README.md and one-page NOTES.md are complete.
- [ ] Full genuine AI transcripts and chronological prompts.txt are included.
- [ ] Public repository has no secrets, raw statements, or unsafe output.
- [ ] Demo shows the entire flow and explains key engineering decisions.
- [ ] ZIP and public GitHub repository are ready for submission.

## 8. Final instruction to the coding agent

Start with **Phase 0 only**. Inspect the existing workspace without reading statement contents, establish privacy protections, and report the current state. Then prepare the Phase 1 plan and wait for approval. Do not attempt to build all phases in one run.
