# Cross-platform Rules

- Use Python 3 and `pathlib` for scripts.
- Do not hard-code Windows, macOS, Linux, WSL, or user-specific paths.
- Use JSON as the script interchange format.
- Default workbook export to XLSX when `openpyxl` is available; fall back to UTF-8-SIG CSV files without installing global dependencies.
- Never require a global package install for the basic path.
- Keep unavailable tool results as explicit capability gaps and downgrade output rather than inventing evidence.
- Preserve original text for translations and keep derived observations linked to originals.
