# Base-unit lookup and unit series

The repository's `data.json` is now a complete sourced base-unit lookup with
regional form identities and series metadata. All 1,043 original numeric keys and
their display names, acquisition types and rarity fields are preserved, including
the original missing rarity field. The file expands to 1,895 numeric base IDs and
contains 6,823 regional form links. It does not flatten sprite forms into base rows
or replace native numeric keys with master-key strings.

The [eleven form conflicts](CONFLICTS.md) remain separated by stable `unit:GL:...`
and `unit:JP:...` master IDs. Kaito, Godrea and Emperor Foo keep their existing GL
base keys `401008505`, `401008605`, `401008705`, with their conflicting seven-star
forms linked underneath. The other eight conflicting base IDs have no single
top-level master ID; their named GL and JP identities and asset paths are nested.
For example, `data.json["401014207"]` contains GL Master Machinist Abigail and JP
Dark Knight Duane, with the correct separate regional assets.

## Series source and normalization

Assignments join each original regional SSID `game_id` to that region's
`F_GAME_TITLE_MST` (`91D3CfxA.dat`). The GL Ver69 table has 84 rows; JP Ver99 has 79.
Their union contains 89 codes. Existing GL game-title localization is retained
where available. Complete source paths, SHA-256 hashes, raw labels, regional codes
and normalization notes are in [`series_sources.json`](../../catalog/series_sources.json).

| Source game code | Normalized series | Specific title retained when different |
| --- | --- | --- |
| 11001 | FFBE | Final Fantasy Brave Exvius |
| 10016 | FFXVI | Final Fantasy XVI |
| 20028 | Kingdom Hearts | Kingdom Hearts |
| 20033 | Kingdom Hearts | Kingdom Hearts III |
| 20034 | Kingdom Hearts | Kingdom Hearts Dark Road |
| 20032 | Fullmetal Alchemist | Source title retained |

Numbered Final Fantasy subseries remain distinct. Direct sequels/spinoffs group
with their numbered subseries while preserving `game_title`. Every regional form
retains its original game code and source provenance. Six shared forms use
different regional codes for Ariana Grande or Katy Perry; regional lookup resolves
these correctly. No assignment uses a unit-name guess or numeric unit-ID prefix.

## Coverage and verification

All 6,823 sourced regional forms and all 1,895 base rows have supported series
assignments; no used game codes are unmapped. Twenty-one asset-only master entries
lack raw unit identity metadata and retain `series: null`. They do not become
invented base-unit rows. The 126 previously untranslated JP unit names remain
native-named, with series assigned from their actual game codes.

Three series labels retain their verified Japanese source text: `リコドキッ！`
(code 20026), `南国少年パプワくん` (20050), and `魔法陣グルグル` (20051). These cover
22 regional forms. The series is known; an English label is not supplied without
localization evidence. Unused game-title rows may also retain native text.

[`validation.json`](validation.json) records exact coverage, legacy-field
preservation, unique aliases, and resolved asset paths. Regression tests cover
native/base ID separation, all collision links, series code differences, missing
metadata/code zero, custom-field preservation and deterministic rebuilds. Existing
asset validation continues to verify all 352 repaired assets and their sources.

## Consumer scope

The documented consumer contract is repository name lookup; no executable reader
of this exact file was found in the inspected local projects. Numeric keys and
existing fields are preserved for unknown external readers. New readers should
follow `identities[].forms[].assets`; a numeric ID alone remains ambiguous at a
regional collision. The preserved original is
[`legacy_unit_lookup.json`](../../catalog/legacy_unit_lookup.json).

The separate asset viewer's `public/data.json` has a different `{assets,totalImages,stats}`
schema and was not replaced. Separate FFR caches, APKs and hosted indexes are not
migrated by this change. Those consumers need an explicit integration with the
master/lookup schema. No assets or original dump files are changed in this update.
