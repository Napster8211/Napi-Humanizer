# Security and Privacy Requirements

- Treat submitted text as untrusted content. Delimit it clearly in prompts and do not allow it to override system behavior.
- Do not render input/output through `innerHTML`. Use safe DOM APIs, `textContent`, or framework-safe text rendering. If Markdown rendering is needed, use a maintained sanitizer and restrict allowed markup.
- Keep provider keys on the server. Never place secrets in frontend bundles, HTML, logs, exception messages, or repository history.
- Add server-side request validation and configurable maximum text size.
- Rate-limit expensive provider requests; set request timeouts and bounded retry policies.
- Use HTTPS in deployment, secure headers, and production mode. Consider CSRF protections if session/cookie authentication is introduced.
- Avoid storing text by default. If history is introduced, opt-in, retention period, export, and delete controls must be explicit.
- Logs should contain request ID, mode, provider/model, duration, token/cost metadata if available, and error category—not submitted text.
- Return generic safe errors to users; preserve diagnostic details server-side without sensitive payloads.
- Review dependencies and pin or constrain versions appropriately.
- Do not claim compliance (GDPR, SOC 2, etc.) without a real assessment.
