# Source organization and production delivery

On October 12, 2026, the previously untracked Memorial tooling was moved from
`tools/<version>` to `memorial-edition/tools/<version>`. Raw asset folders, catalog
paths, asset importer code, and tracked asset bytes stay at their existing paths.
The original v205 root instructions are preserved in `docs/history` with explicit
historical filenames. The root instructions now distinguish asset preservation
from Memorial release work.

The source selection contains 287 original files, 2,060,008 bytes: code, tests,
authored documentation, ten small configurations, a small v207 fixture, and three
source/test pin records. All 287 original file hashes were checked after the move.
The 1,707 generated release files were retained locally and excluded from the
commit; their combined size is 777,784,029 bytes. Nothing was deleted.

## Production baseline checked

The locally retained production APK matches the published GitHub release:

| Property | Verified value |
| --- | --- |
| Version | Global Events v208 |
| APK bytes | 145,206,221 |
| APK SHA-256 | `9d21fc8b61c9900eaacb1c2ddef2cabcad1e97d2dc720be16ac09b06fc0086b4` |
| GitHub release | `production-v208-9d21fc8b61c9900e`, ID `403364176` |
| Download repository | `luminest-llc/ffbe-memorial-downloads` |
| Movie route | `https://cdn.luminest.io/ffbe/movies/` |
| GitHub/CDN updater SHA-256 | `f504224839185dfacf906bb6ed6110b8d7e21304eb1877ebf3a2b76b555e86b9` |

The APK's embedded base and content catalogs pin packs in `content-v1`,
`content-20260929`, `beta-content-v203-295644c91db31636`,
`beta-content-v206-ac96f646eaa91996`, and `content-v208-d76ed937ddeb7ddd`.
The inspected APK contains no reference to `DaddyRaegen/ffbe_asset_dump` or the
Memorial tooling paths being moved. The production download page and updater
manifests were read without mutation.

This operation changes the source repository layout only. It does not build,
sign, upload, promote, or install an APK; change a hosted pack/catalog/updater;
deploy a website; or touch device caches and saves.

## Preserving historical code

Historical source/configuration bytes and their SHA pins remain unchanged.
`.gitattributes` disables text normalization for these snapshots so the committed
blob bytes preserve their original line endings. Existing absolute paths in
build configs, handoff scripts, and source seals are retained as provenance.
They must be overridden in a fresh workspace for a later build.

The excluded local release artifacts retain their version-folder layout because
several host fixtures load sibling source/plans. `.gitignore` excludes their
binary payloads and generated records. Future generated outputs should also be
kept in a separate workspace or an ignored `local-archives/` directory.

## Organization validation

All 188 Memorial guard/transport regression tests and all 65 asset-tooling tests
passed using the relocated source. All 92 Python files parsed, all 14 selected
JSON files decoded, and all 38 JavaScript modules/scripts passed syntax checks.
The staged Git blobs of all 287 original source files match their recorded hashes.
Every excluded release artifact is ignored and no release binary is staged.

Read-only production checks after the move matched the baseline APK and embedded
catalogs, GitHub/CDN updater bytes, website/download links, latest release identity,
and release asset hashes. No hosted content was modified. These checks verify a
source-only organization; they are not a new phone gameplay test.
