# Complete unit bundles and FFIV sample audit

The repository already contained the recovered priority filenames, but its ordinary
unit records exposed only a sheet, CGG and idle sequence. This update links the
complete available inputs, repairs mixed source revisions, and includes asset-only
characters in the main lookup.

## Actual asset repairs

Seventeen unit bundles now match one complete source archive each. **67 existing
files were replaced together: 51 PNGs and 16 CGG tables.** Their accompanying
animation CSVs now refer to the correct frame tables and textures.

| Forms | Source bundle | Replaced files |
| --- | --- | ---: |
| Nikujaga Vision `256000301` | JP `unit8.cpk` | 4 |
| Alpha Weltall `331001117` | JP `unit22.cpk` | 3 |
| Twelve door forms `903001101/102` through `903001601/602` | JP `unit9.cpk` | 48 |
| Super Trust Moogle forms `906000103/104/105` | JP `unit9.cpk` | 12 |

Nikujaga and the material units had newer JP sequences paired with shorter older
frame tables. Alpha Weltall had a German GL atlas and mixed image revisions with
JP frame data. Complete source sets resolve these inconsistencies without guessing
frame indices or editing artwork.

The three `repair-*.json` files record source archive SHA-256, all 273 current bundle
file hashes, and the previous/replacement hashes. `repair-validation.json` verifies
the archive hashes, all current files, complete PNG decoding, and the previous Git
contents. Sixteen old checkout CSVs differed from Git only by CRLF versus LF;
that distinction is explicitly recorded. Previous substantive contents remain in
Git commit `45b111dac51f7cd7ad1485248b299cdbe970d222` and local work backups.

## Complete and correctly paired links

The catalog now exposes **53,677 previously omitted companion links** across
3,942 ordinary forms. All 3,964 master forms retain explicit primary paths and gain
the available sheets, CGGs, animation sequences, illustrations, icons and companions.
`animation_sets` separates 3,964 main, 80 overdrive, three effect and one limit-effect
families. These sets identify which CGG and texture pages each sequence consumes.
The 22 reviewed GL/JP collision bundles remain separate and hash-verified.

The fresh inventory read **34,736 source files, 14,332 archives and 517,535 members**
with zero errors. It found no additional missing unit, monster, battle-background
or vision-card destinations. The 128,905 optional `additional/` destinations remain
outside this focused update. Thus filename absence was not the current unit problem;
incomplete links and mixed revisions were.

## Characters without metadata

`data.json` now includes **1,916 rows**: 1,895 sourced base-unit records plus 21
explicit `lookup_kind: "asset_form"` records. The latter link all 335 available
files without inventing a base ID, region, series, acquisition type or rarity.
Edward `204000602` uses the supplied ZIP filename as a display label with ZIP/hash
provenance; its canonical identity remains unknown. All 1,043 legacy lookup rows
retain their display fields. Exact IDs are in `incorporated-forms.json`.

## Validation and original-source limitations

The final all-form check covers **4,048 animation sets, 49,523 active CGS files and
489,817 steps**, with no invalid active frame references. Lookup validation resolves
65,855 distinct existing asset paths. Independent integration checks confirm that
all frame tables and active sequences belong to exactly one appropriate set.
All 65 regression tests pass; the recorded output is in `tests.txt`.

Eleven source-invalid sequences across nine forms remain in `asset_files` for
archival completeness but are excluded from active lists. They affect Tronn
`100001101/102`, Abel `100006303/304/305`, Drace `212001404`, the unresolved form
`211000203`, and Cupid Luna `302001203/204`. Available alternatives, including
fresh JP extraction for Abel and Drace, do not supply valid replacements.

There are also 259 active texture-rectangle warnings across 21 forms. These match
original source bundles, so they remain visible as clipping warnings rather than
being silently redrawn. Gilgamesh (WOTV FFBE) `339000127`, for example, references
an out-of-atlas part during its limit sequence. These checks establish file and
frame compatibility; they do not promise that every source animation renders
without clipping. `catalog/unit_animation_notes.json` pins the affected inputs by
hash; stale exceptions fail validation if the inputs change.

`note-source-byte-check.json` records 368 source-CSV line endings restored in Git so
the published input bytes match those pinned hashes. Their numeric content is
unchanged. The old September recovery manifest remains a historical receipt;
these repair receipts supersede its hashes only for explicitly repaired files.

## Download and supplied ZIP

[`identity-and-metadata-gaps.zip`](../../unit_bundles/identity-and-metadata-gaps.zip)
contains **60 forms and 960 original files**: the 22 collision forms, 21 asset-only
forms, and 17 repaired bundles. Its manifest includes all SHA-256 hashes, correct
animation groups and source limitations. Each form has its own folder under
`gl`, `jp`, `shared`, or `unresolved`; native filenames are preserved. The source
does not provide an icon or illustration for asset-only ID `9990196`.

The pack is 6,444,686 bytes, SHA-256
`39e0728c5fbceadc1dcaca0f18bd7f7deca046c8cf886bea7e97e40a1cd3f1a9`.
Its ZIP CRC and all 960 contained asset hashes were verified.

The supplied FFIV ZIP is unchanged. It contains 108 large 128×128 PNGs and 107
ability 64×64 PNGs, all valid RGBA with transparency. However, distinct character
variants sometimes reuse incorrect portraits. Its Rydia filename has an extra
digit, Edward lacks an ability counterpart, and one Rubicante ID has no supporting
native record. See the [full image/naming audit](ffiv-sample/REPORT.md), inventory
and native-image comparison for exact findings.
