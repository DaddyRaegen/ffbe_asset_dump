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
unchanged. New acquisition types are `unknown` rather than guessed.

Series come from each regional SSID row's `game_id` and the regional game-title
master: for example **FFBE**, **FFXVI**, **Kingdom Hearts**, and **Fullmetal Alchemist**.
Specific titles such as Kingdom Hearts III remain in `game_title`. Every form keeps
the original game code and series provenance. See [all eleven conflicts](reports/2026-10-02-unit-series/CONFLICTS.md)
and the [lookup/series report](reports/2026-10-02-unit-series/REPORT.md).

The [unit catalog](catalog/units.json), [monster catalog](catalog/monsters.json),
and [vision-card catalog](catalog/vision_cards.json) list available sprite IDs and
animation inputs. The master list additionally preserves 21 asset-only IDs whose
identity and series are unknown; they are not invented as base-unit records.

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
