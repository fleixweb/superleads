# Changelog

All notable changes to this project are documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Superleads Versioning

- **MAJOR**: changes schema fields, verification gates, or removes states. These can break an in-use research graph and must include migration instructions.
- **MINOR**: adds capabilities without breaking existing research graphs.
- **PATCH**: fixes bugs or changes copy.

## [0.1.2] - 2026-07-20

### Fixed

- Register the optional Codex update notice through the plugin manifest and use plugin-root paths, so it can run from any user project on macOS, Linux, and Windows.
- Keep technical installation documentation and remote update checks on the GitHub default `master` branch.

## [0.1.1] - 2026-07-20

### Added

- Optional Codex SessionStart update notice with one anonymous public manifest GET, a 3-second timeout, opt-out environment variables, and silent failure.

### Fixed

- Align marketplace documentation and update checks with the GitHub default `master` branch.

## [0.1.0] - 2026-07-20

### Added

- Initial public distribution metadata for Codex and Claude Code.
- Self-hosted marketplace manifests and an optional, silent update notice.
- PolyForm Noncommercial 1.0.0 license.
