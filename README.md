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
In the `data.json` file, search for the name of the unit you're looking for. Copy the associated **Unit ID** and search the repository for that ID.
`data.json` is a legacy name lookup and does not name every recovered unit. The [unit catalog](catalog/units.json), [monster catalog](catalog/monsters.json), and [vision-card catalog](catalog/vision_cards.json) list available sprite IDs and their matching animation inputs.

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
