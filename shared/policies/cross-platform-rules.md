# Cross-platform Rules

- Use Python 3 and `pathlib` for scripts.
- When running a Superleads script, prefer the host-provided runtime interpreter; fall back to a system interpreter only when the host runtime is unavailable. The host runtime normally includes dependencies declared in `requirements.txt`, while a system interpreter often does not. If neither can run the required deterministic step, record the capability gap and downgrade the deliverable; do not modify the user's system environment, install packages globally, or tell the user to do so.
- Interpreter selection, dependency availability, module names, and installation status are internal execution details and must not appear in user-visible output. Switch interpreters silently; if the work cannot complete, state the affected delivery tier or missing capability in business language without module names or installation commands.
- Do not hard-code Windows, macOS, Linux, WSL, or user-specific paths.
- Use JSON as the script interchange format.
- Default workbook export to XLSX when `openpyxl` is available; fall back to UTF-8-SIG CSV files without installing global dependencies.
- Never require a global package install for the basic path.
- Keep unavailable tool results as explicit capability gaps and downgrade output rather than inventing evidence.
- Preserve original text for translations and keep derived observations linked to originals.
- When recorded, `platform` identifies the Agent host as one canonical ID:
  lowercase ASCII letters, digits, and underscores only, with no whitespace,
  case variant, or hyphen. Generic host IDs such as `hermes`, `claude`, and
  `workbuddy` remain valid. A concrete executable is never a platform. For
  Codex CLI, `curl`, `wget`, and `python_requests` may be recorded only as
  source-reading tools under an explicit, read-only public HTTP(S) capability
  contract; they do not imply search access or bypass source evidence rules.
