# Cross-platform Rules

- Use Python 3 and `pathlib` for scripts.
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
