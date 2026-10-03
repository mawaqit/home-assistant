# Instructions for AI agents

MAWAQIT custom integration for Home Assistant, installed through HACS.

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the GitHub workflow and [RELEASING.md](RELEASING.md) for releases.

## Layout

- `custom_components/mawaqit/`: the integration. `migration.py` migrates config entries created by v3 and older.
- `tests/`: pytest suite using `pytest-homeassistant-custom-component`.
- `script/setup`: development environment setup.

## Commands

- `script/setup`: creates `.venv` and installs the git hooks. Activate the venv before anything else.
- `pytest --cov`: runs the tests. Coverage must stay at 100%.
- `prek run --all-files`: runs ruff, codespell, zizmor, yamllint, prettier and mypy. Run it before every commit.

## Rules

- Follow the Home Assistant integration conventions; the linters use Home Assistant's settings.
- Supported Home Assistant versions: from the one in `hacs.json` to the latest, and CI tests both ends. The oldest runs Python 3.13 and has no `probatio`, hence `voluptuous` and `from __future__ import annotations` where forward references need it. No Python 3.14-only syntax.
- User-facing strings live in `translations/en.json`; add every new key to all the other files of `translations/`.
- Never hardcode entity IDs in the integration: they depend on the user's language.
- Every change comes with tests.
- Do not change existing entity unique IDs, or the config entry version, without a migration.
- Keep comments short; comment non-obvious constraints only.

## AI policy

A human must review, understand and be able to explain every change before it is submitted. Do not open issues or pull requests, or post comments, without the user's review.
