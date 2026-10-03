# Instructions for AI agents

MAWAQIT custom integration for Home Assistant, installed through HACS. The same integration is being added to Home Assistant core ([home-assistant/core#167919](https://github.com/home-assistant/core/pull/167919), code on the `mawaqit-integration` branch of [mawaqit/ha-core-integration](https://github.com/mawaqit/ha-core-integration)). Keep this repository as close as possible to that code.

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the GitHub workflow and [RELEASING.md](RELEASING.md) for releases.

## Layout

- `custom_components/mawaqit/`: the integration.
- `tests/`: pytest suite using `pytest-homeassistant-custom-component`.
- `script/`: development scripts.

## Commands

- `script/setup`: creates `.venv` and installs the git hooks. Activate the venv before anything else.
- `pytest --cov`: runs the tests. Coverage must stay at 100%.
- `prek run --all-files`: runs ruff, codespell, zizmor, yamllint, prettier, mypy and the translation check. Run it before every commit.
- `python3 -m script.translations`: regenerates `translations/en.json` from `strings.json`. Run it after editing `strings.json`; tests read `en.json`.

## Rules

- Follow the Home Assistant core conventions; the linters use core's settings.
- Supported Home Assistant versions: from the one in `hacs.json` to the latest. CI tests both ends. The oldest runs Python 3.13, so no Python 3.14-only syntax (unparenthesized `except A, B:`, unquoted forward references without `from __future__ import annotations`).
- Every user-facing string goes in `strings.json` and in every file of `translations/`; the translation check fails on missing or unknown keys.
- Never hardcode entity IDs in the integration: they depend on the user's language.
- Every change comes with tests.
- Do not change existing entity unique IDs, or the config entry version, without a migration.
- Keep comments short; comment non-obvious constraints only.

## Differences with the core integration

Changes made in core should be copied here by hand. These differences are intentional and must be kept:

- `config_flow.py`: `import voluptuous as vol` instead of `probatio` (older Home Assistant releases have no `probatio`), and `MINOR_VERSION = 2`.
- `types.py`: `from __future__ import annotations`, for Python 3.13.
- `__init__.py` and `migration.py`: migration of config entries created by the legacy (v3) custom integration.
- `manifest.json`: `documentation`, `issue_tracker` and `version`; no `quality_scale`.
- `translations/`: every language is maintained here; core gets them from Lokalise.
- Tests import from `custom_components.mawaqit` and `pytest_homeassistant_custom_component.common`, enable custom integrations in `conftest.py`, and `test_migration.py` only exists here.

Changes that are not specific to HACS should also be proposed to core.

## AI policy

A human must review, understand and be able to explain every change before it is submitted. Do not open issues or pull requests, or post comments, without the user's review.
