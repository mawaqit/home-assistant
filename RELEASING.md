# Releasing

HACS installs GitHub releases, never the `main` branch. `main` always carries a development version (`X.Y.Z.devN`) so installs from the branch are recognisable in bug reports.

1. Open a PR bumping `version` in `custom_components/mawaqit/manifest.json` to the release version: `4.1.0`, or `4.1.0b1` for a beta.
2. Once merged, run the **Release** workflow from the Actions tab on `main` (tick "Pre-release" for a beta). It creates a draft release `v<version>` with generated notes and `mawaqit.zip` attached.
3. Review the notes, then publish. They are grouped by PR label (`.github/release.yml`), so label every PR before merging it: `breaking-change`, `enhancement`, `bug`, `translations`, `documentation`, `dependencies`, `ci`, or `skip-changelog` to leave it out. Pre-releases only reach HACS users who enabled beta versions.
4. Open a PR bumping `version` to the next development version (`4.2.0.dev0`).

Do not create releases by hand: published `v*` tags cannot be moved or deleted, so a tag that does not match the manifest cannot be fixed.
