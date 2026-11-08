# AI Prompt Versions & Guidelines

## Engine: Google Gemini API (`gemini-3.8-flash`)

### Security Rules for AI Triage
1. **Zero External Access:** The Gemini model is supplied only with sanitized, truncated structured data. It has no web access or tool invocation privileges during triage.
2. **Untrusted Data Sanitization:** All user-controlled fields (e.g., HTTP response headers, title tags, banner snippets) are escaped and enclosed in strict XML boundary tags (`<untrusted_evidence>...</untrusted_evidence>`).
3. **Structured Output Enforcement:** Models return responses adhering strictly to `Pydantic` JSON schemas (`TriageResult` and `ScanSummary`).

### Supported Languages
- English (`en`)
- Hinglish (`hi-Latn`): Romanized Hindi and English conversational blend designed for Indian business owners.
