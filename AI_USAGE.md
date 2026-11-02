# AI Tools Usage --- Financial Data PII Scrubber

## Tools Used

1.  **ChatGPT (OpenAI)**\
    Used for project planning, understanding requirements, discussing
    architecture and implementation choices, troubleshooting errors,
    reviewing documentation, and preparing submission materials.

2.  **OpenCode with an Ollama Cloud-hosted model**\
    Used as the coding assistant/agent for repository inspection and
    development tasks. The model was accessed through Ollama Cloud via
    OpenCode.

3.  **Groq API**\
    Used by the application for AI-powered financial-statement analysis
    and document-grounded chat, as required by the assignment. Only
    scrubbed document content should be sent to the external AI service.

## How the Tools Were Used

-   ChatGPT supported planning, debugging discussions, code review
    guidance, and documentation.
-   OpenCode with the Ollama Cloud model supported coding and
    repository-level development work.
-   Groq provided the application's AI inference service for analysis
    and chat.

## Accuracy and Evidence

This document lists the tools and purposes reported for this project. It
is not a verbatim transcript of conversations or proof that a particular
feature passed testing. Any required prompts, conversation transcripts,
API responses, and test results should be supplied from actual records.
Do not present reconstructed prompts or illustrative output as original
evidence.

## Privacy Note

Before publishing the repository or submission ZIP, remove API keys,
`.env` files, private credentials, and unredacted financial data. Keep
only the scrubbed sample outputs required for submission.
