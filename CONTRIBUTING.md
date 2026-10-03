# Contributing

Contributions are welcome! Open an issue first for large changes, so we can agree on the approach.

## Development setup

You need [uv](https://docs.astral.sh/uv/) and Node.js (used by the prettier hook).

```bash
script/setup
source .venv/bin/activate
pytest --cov
prek run --all-files
```

`script/setup` installs git hooks: the checks run on every commit and fix most issues themselves (formatting, import order).

To try your changes in Home Assistant, copy `custom_components/mawaqit` into the `custom_components` folder of a test configuration and restart Home Assistant.

## Workflow

`main` is the only long-lived branch. HACS users never get it directly: they install releases (see below), so `main` can contain unreleased work.

1. Create a branch from `main` (a fork for external contributors).
2. Open a pull request to `main` and fill in the template.
3. Set a label: it decides where the change appears in the release notes.

   | Label | Release notes section |
   | --- | --- |
   | `breaking-change` | Breaking changes (users must change something) |
   | `enhancement` | New features |
   | `bug` | Bug fixes |
   | `dependencies` | Dependencies |
   | `skip-changelog` | Not listed (CI, docs, refactoring) |

4. CI must pass:
   - `lint`: the prek hooks, including mypy.
   - `pytest (latest HA)` and `pytest (HA 2025.3.0)`: tests on the newest and the oldest supported Home Assistant, with 100% coverage.
   - `hassfest` and `HACS`: Home Assistant and HACS validation.
5. A member of [@mawaqit/home-assistant](https://github.com/orgs/mawaqit/teams/home-assistant) approves it. Every comment must be resolved, and a new push needs a new approval.
6. The pull request is squash merged: its title becomes the commit message on `main`, so keep it clear (`Add Imsak sensor`, not `fix stuff`). The branch is deleted automatically.

Dependabot opens weekly pull requests for Python dependencies and GitHub Actions. It skips `tests/requirements_min_ha.txt`, which pins the oldest supported Home Assistant: update it by hand when `hacs.json` changes.

## Releases

Releases are made from `main` by the Release workflow, see [RELEASING.md](RELEASING.md). HACS offers each published GitHub release to users, and pre-releases only to users who enabled beta versions.
