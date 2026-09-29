# GL / JP asset recovery

Recovered from the supplied local GL and JP dump on September 29, 2026 UTC (September 28 local time), against commit `5f7e66f462cbf70fbd7039099097cda0df335ac7`.

**31,049 source files added, totaling 1,164,107,864 bytes (1.16 GB).** Existing asset files were not replaced or deleted. Of these additions, 24,028 belong to the four priority categories and 7,021 extend the existing item, equipment, emblem, ability, and related categories.

| Priority | New sprite IDs / images | Source files added |
| --- | ---: | ---: |
| Units | 866 unit forms | 15,326 |
| Battle backgrounds | 681 image names absent from the old repository | 3,034 |
| Monsters | 747 monster sprite IDs | 4,280 |
| Vision cards | 212 vision-card sprite IDs | 1,388 |

Unit and monster totals include icons, illustrations, animation CSVs, texture pages, and auxiliary assets. Background additions comprise 379 JPEGs, 1,389 PNGs, and 1,266 SSBP files. The 681 image-name count groups files by basename across image formats; it is not a count of distinct playable battle scenes. Vision-card additions include 720 animation CSVs, including missing companions for older cards already in the repository.

## Verification

- Indexed all 14,332 CPK archives in the supplied dump: 517,535 archive members, with no indexing errors.
- Verified every imported file against its recorded SHA-256 and byte length; decoded every imported image. No file-validation errors or remaining selected filename gaps.
- All 866 new unit forms, 747 new monster IDs, and 212 new vision-card IDs have their frame data and idle/card animation sequence. Those sequences reference valid frame indices.
- Recovered 38 legacy files stored as plaintext inside otherwise encrypted JP archives. Regression checks cover both encrypted and plaintext members; a second run adds zero files.
- BFFrameAnimator 2.1.2 rendered samples for unit `100040107` (16 frames), monster `10002901` (4 frames), and vision card `100006601` (53 frames). The older renderer reported three improper frames for the unit sample; these derived previews were not imported.

## Original animation-data limitations

The source data contains 588 references extending beyond the selected atlas boundaries across 45 unit forms, 4 monsters, and 5 vision cards. The warnings are preserved in [summary.json](summary.json). For the checked idle/card sequences, these references are unused except for six references in monster `3045310`; that monster's source atlas/sequence may render incompletely. Its only matching source in this dump is the JP `monster3g.cpk` archive. The import retains the original assets without inventing or altering missing pixels.

## Scope and provenance

The import fills every missing filename found in the priority and existing repository categories. It preserves existing filenames rather than updating their contents, and does not claim every regional revision or all assets from the game's lifetime. When multiple sources offer a new filename, selection prefers HD, then JP, then the highest numbered GL archive version. [source-manifest.csv](source-manifest.csv) records the actual source chosen for every addition.

The much larger optional collection outside existing categories was inventoried but not imported: 128,905 destinations, approximately 15.19 GB of archive-member data, covering maps, effects, event art, UI, localized assets, and their companions. Loose-file sizes are additional. Audio, video, master data, and general story text remain in the source dump and are outside this visual-asset import.

The legacy `data.json`, `lastUpdated.json`, and existing GIFs are unchanged. New catalogs identify available assets by ID without guessing character names. See [the import instructions](../../tools/README.md) for repeatable recovery and animation-tool usage.
