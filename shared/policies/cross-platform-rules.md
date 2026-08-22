# Cross-platform Rules

- Use Python 3 and `pathlib` for scripts.
- When running a Superleads script, prefer the current host's host-provided runtime interpreter (宿主自带 runtime 解释器); fall back to a system interpreter only when the host runtime is unavailable. Missing dependencies do not authorize runtime installation, temporary dependency directories, `PYTHONPATH`, or interpreter hunting: 不得借用其他应用程序的 Python 环境、虚拟环境或解释器. If neither can run the required deterministic step, record the capability gap and downgrade the deliverable without exposing these internal details.
- Interpreter selection, dependency availability, module names, and installation status are internal execution details and must not appear in user-visible output. Switch interpreters silently; if the work cannot complete, state the affected delivery tier or missing capability in business language without module names or installation commands.
- Do not hard-code Windows, macOS, Linux, WSL, or user-specific paths.
- Use JSON as the script interchange format.
- Default workbook export to XLSX when `openpyxl` is available; fall back to UTF-8-SIG CSV files without installing global dependencies.
- Never require a global package install for the basic path.
- Keep unavailable tool results as explicit capability gaps and downgrade output rather than inventing evidence.
- Preserve original text for translations and keep derived observations linked to originals.
- When recorded, `platform` identifies the Agent host as one canonical ID:
  lowercase ASCII letters, digits, and underscores only, with no whitespace,
  case variant, or hyphen. Generic host IDs such as `hermes`, `claude`,
  `chatgpt_desktop`, and `workbuddy` remain valid. A concrete executable is
  never a platform. For
  Codex CLI, `curl`, `wget`, and `python_requests` may be recorded only as
  source-reading tools under an explicit, read-only public HTTP(S) capability
  contract; they do not imply search access or bypass source evidence rules.
