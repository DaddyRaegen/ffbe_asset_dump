# Final Fantasy Brave Exvius Data Dump
![GitHub repo size](https://img.shields.io/github/repo-size/DaddyRaegen/ffbe_asset_dump)

A repo of Final Fantasy Brave Exvius in game assets

## How to find units
Use [the master unit list](catalog/unit_master.json) for names, regional identity,
and explicit asset paths. Eleven native form IDs belong to different GL and JP
units. For example, `unit:GL:401014207` is **Master Machinist Abigail**, while
`unit:JP:401014207` is **Dark Knight Duane**. These master IDs are opaque lookup
keys; use `assets.sprite_sheet`, `assets.frame_data`, and `assets.idle_animation`
instead of inserting them into filenames. Original numeric IDs and filenames
remain available as provenance.

The corresponding [regional bundles](regional_units) restore both identities.
Existing flat files are retained for compatibility; collision rows in the old
catalog are explicitly marked `ambiguous_legacy_id`. Numeric lookup alone is
ambiguous for those rows. See the [identity repair report](reports/2026-10-02-unit-identities/REPORT.md)
for all mappings, evidence, validation, and remaining metadata gaps.

### Legacy lookup
[`data.json`](data.json) keeps numeric **base-unit** keys and the original names,
acquisition types and rarity labels. It now covers 1,895 sourced base IDs. Each
entry includes `series`, regional `identities`, and their `forms` with native IDs,
master IDs and explicit asset paths. A colliding numeric base has `master_id: null`
and two named regional identities; choose a server and form before loading assets.
`canonical_name` contains the source-backed name while legacy display names remain
unchanged. New acquisition types are `unknown` rather than guessed. The lookup
also includes 21 `lookup_kind: "asset_form"` entries for assets without source
metadata, for 1,916 total rows. These are individual sprite forms with explicit
asset links, not inferred base-unit or regional records.

Series come from each regional SSID row's `game_id` and the regional game-title
master: for example **FFBE**, **FFXVI**, **Kingdom Hearts**, and **Fullmetal Alchemist**.
Specific titles such as Kingdom Hearts III remain in `game_title`. Every form keeps
the original game code and series provenance. See [all eleven conflicts](reports/2026-10-02-unit-series/CONFLICTS.md)
and the [lookup/series report](reports/2026-10-02-unit-series/REPORT.md).

The [unit catalog](catalog/units.json), [monster catalog](catalog/monsters.json),
and [vision-card catalog](catalog/vision_cards.json) list available sprite IDs and
animation inputs. The master list additionally preserves 21 asset-only IDs whose
identity and series are unknown. They are also available in `data.json` as
explicit asset forms. Edward `204000602` has the display label supplied in the
FFIV sample ZIP, with filename provenance; its canonical identity stays unknown.

### Complete unit files

Every master form now exposes all available `sprite_sheets`, `frame_data_files`,
`animation_csvs`, `illustrations`, `icons`, and `companion_files`, plus the complete
`asset_files` list. The singular `sprite_sheet`, `frame_data`, `idle_animation`,
`illustration`, and `icon` paths identify the primary files. Use the regional
master entry for colliding IDs so sheets and CSVs belong to the same identity.
Use `animation_sets` to pair main, overdrive, and effect sequences with their
specific frame table and texture pages. Known unusable source sequences remain
archived in `asset_files` but are excluded from active animation lists; clipping
limitations are recorded in `source_warnings`.

The [60-form unit pack](unit_bundles/identity-and-metadata-gaps.zip) contains all
960 available files for the 22 regional conflict forms, 21 asset-only forms,
and 17 repaired bundles,
with native filenames and a SHA-256 manifest. See the
[bundle audit](reports/2026-10-09-unit-bundles/REPORT.md) for coverage and source
limits, and the [FFIV ZIP audit](reports/2026-10-09-unit-bundles/ffiv-sample/REPORT.md)
for image sizes, naming issues, and reused variant artwork.

`lastUpdated.json` records the latest asset maintenance date. Its `last_unit`
string is a retained historical label, not a claim about the newest game release.

## GL / JP asset recovery

The September 2026 recovery adds 31,049 files from a local GL/JP dump, including 866 unit forms, 747 monster sprite IDs, 212 vision-card sprite IDs, and 681 background image names absent from the previous repository. Existing assets are preserved.

See the [recovery report](reports/2026-09-29-recovery/REPORT.md) for category counts, validation, source limitations, and the [source manifest](reports/2026-09-29-recovery/source-manifest.csv). Vision-card animation data is in `vc_animated_csv`. Repeatable import instructions are in [tools/README.md](tools/README.md).

## How to convert the PNGs into animated sprites
* Note: Requires [nodejs](https://nodejs.org/en/)

Use the [FFBE Sprite Sheet Assembler](https://github.com/dsxragnarok/FFBE-sprite-sheet-assembler) tool by dsxragnarok.

Download the sprite sheet from the `unit_animated` folder and the corresponding .csv file from `unit_animated_csv`. Follow the instructions from the Sprite Sheet Assembler.


# Support FFBE Encyclopedia
Looking for other ways to support FFBE Encyclopedia?
- Help me port FFBE Encyclopedia to iOS! [GoFundMe](https://gofund.me/9a342f26)

  You can also see updates on the app on the GoFundMe page and on [Instagram](https://www.instagram.com/amethyst.nebula/)
