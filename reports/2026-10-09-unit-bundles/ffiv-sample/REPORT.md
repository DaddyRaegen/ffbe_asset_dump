# FFIV sample icon ZIP audit

Audited 2026-10-09 without changing the supplied ZIP. The two Markdown files inside the archive were inspected as reference data; their contents did not authorize work or override the user's request.

Source: `T:\Downloads\Suno\ICONS_04_FFIV_Sample_Pack.zip`

Size: 1,928,676 bytes

SHA-256: `f23b622f7371b4ba6e4c2baff2e9f608d87d414e83831b03f5a36acca8f13033`

## Image dimensions and quality

| Category | Files | Dimensions | Format | File-size range |
|---|---:|---|---|---:|
| Large icons | 108 | 128 × 128 pixels, every file | PNG, RGBA | 9,328–13,640 bytes |
| Ability icons | 107 | 64 × 64 pixels, every file | PNG, RGBA | 5,241–6,223 bytes |

All 215 PNGs pass ZIP CRC, PNG structural verification and complete image decoding. Every image has both fully transparent and partially transparent pixels. No broken or blank image was found. PNG encoding is lossless; this does not prove that earlier resizing or editing was lossless.

Representative images were inspected visually at their native sizes and in a nearest-neighbor enlarged contact sheet. They are finished, framed portrait icons with readable pixel art and transparent outer areas. Large icons have a silver diamond frame; ability icons have a compact portrait badge. Their artwork is visibly low-resolution pixel art with some smoothed/composited edges, so the 128 × 128 canvas should not be described as newly detailed high-resolution artwork. The ability icons have a different composition; they are not simply an exact half-size copy of the large icons. No JPEG block artifacts or obvious broken transparency were seen in the inspected samples.

There are only **43 distinct pixel images in each size**. Many files reuse identical artwork across rarity/alternate forms. Shared artwork between forms can be legitimate, but **the pack does not preserve all variant-specific portraits**. Three comparisons against the repository's corresponding native `unit_icons/unit_icon_<id>.png` establish this:

| Two supplied IDs/labels | Repository native icons | Supplied ZIP icons |
|---|---|---|
| Kain `204000203` / Noble Dragoon Kain `204003607` | Both 56 × 38; different pixels and visibly different portraits | Identical pixels to each other in both sizes |
| Rosa `204000304` / White Mage of Benediction Rosa `204003307` | Both 56 × 38; different pixels and visibly different portraits | Identical pixels to each other in both sizes |
| Pure Summoner Rydia `204001505` / Eidolon Whisperer Rydia `204003407` | Both 56 × 38; different pixels and visibly different portraits | Identical pixels to each other in both sizes |

These are technically valid image files, but their names imply distinctions that their artwork does not retain. Preserve the ID-level records; do not use the ZIP duplicates as evidence that the native forms are interchangeable. The side-by-side comparison is in `native-comparison.png`, with image hashes in `native-comparison.json`. Native portraits are shown at 4×, ZIP large icons at 1× and ZIP ability icons at 2× using nearest-neighbor previews. A larger output canvas and visibly pixelated artwork are evident; the precise source, scale factor and resampling method used to create the ZIP cannot be proven from these comparisons.

## Filename and set checks

The two consistent patterns are:

```text
ICON-Large_04-FFIV_<character-and-variant>_<unit-form-id>.png
ICON_Ability_04-FFIV_<character-and-variant>_<unit-form-id>.png
```

The filenames contain 37 distinct character/variant labels. Names are readable; spaces and `&` are valid filename characters but must be escaped or URL-encoded when used by scripts or links. Parse the final numeric suffix rather than splitting every underscore, because `Cecil-Red Wings_Dark` and `_Light` contain underscores inside their labels. These are editorial display filenames, not the repository's raw `unit_icon_<id>.png` naming scheme.

Three concrete exceptions need attention:

1. **Rydia filename typo:** the large icon is named `ICON-Large_04-FFIV_Rydia-Eidolon Whisperer_2040034017.png`. Its 10-digit suffix should be reviewed as `204003417`: that is the ID in the ability filename, the supplied icon list and the repository's master registry. The supplied ZIP was not renamed.
2. **Edward pair missing:** `ICON-Large_04-FFIV_Edward_204000602.png` exists, but there is no corresponding ability icon and this large filename is omitted from `Iconlist_04_FFIV.md`. The repository has a sprite/CSV asset-only entry for `204000602` with no raw unit metadata. The user-supplied filename is evidence for an editorial Edward label, not evidence of a raw regional/rarity record.
3. **Rubicante ID unsupported:** both sizes contain Rubicante `204001804`, but the current registry and native `unit_icons` files have no such ID. JP Rubicante starts at `204001805`; GL has `401001504`. Do not silently merge or rename these based on the suffix. Other supplied Rubicante IDs are present in the registry.

After correcting the Rydia filename reference, all size pairs match except Edward `204000602`. The unsupported Rubicante ID is present in both sizes, so a pair-only check would miss that issue.

## Regional identity note from the supplied README

The README asks why four fiends also appear under `401001...` IDs. Current source-backed registry entries distinguish regional records: Barbariccia uses GL `401001405` and JP `204001904`/`204001905`; Rubicante has GL `401001504` and JP `204001805`; Cagnazzo has GL `401001604` plus `204002104`; Scarmiglione has GL `401001903` plus `204002003`. These are different records even where names and artwork overlap. Do not deduplicate them by character name or image hash.

## Reproducible audit outputs

- `audit_zip.py`: read-only source inspection and contained extraction.
- `audit.json`: aggregate results, discrepancies and duplicate-image groups.
- `image-inventory.csv` / `.json`: every image, dimensions, hashes, mode and alpha counts.
- `sample-contact-sheet.png`: 12 representative large icons enlarged for inspection; the original PNGs remain under `images/`.
- `native-comparison.png` / `.json`: three pairs of ZIP portraits compared with the six corresponding native repository icons, plus pixel hashes.

This audit covers the supplied icons. It does not establish that sprite sheets, animation CSVs, illustrations or source metadata are complete; those require the separate unit-bundle audit.
