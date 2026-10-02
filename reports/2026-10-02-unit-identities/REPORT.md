# GL / JP unit identity repair

Eleven native form IDs identify different units in GL and JP. The previous
filename-only recovery preferred JP for missing filenames, so GL counterparts
were omitted. In particular, the existing `401014207` sheet, CGG and idle files
still match the September recovery's JP hashes: this case was omission through
ID conflation, not evidence of an overwrite of earlier GL files.

Both identities now have stable master IDs and complete regional bundles. The
352 original files (5,335,884 bytes) were freshly extracted from seven pinned
archives. All old flat assets remain byte-for-byte unchanged. Their eleven legacy
catalog rows are marked ambiguous and link to the authoritative master list.

## Verified mappings

For every ID below, the GL master ID is `unit:GL:<ID>` and JP is `unit:JP:<ID>`.
Names in the JP column come from the identity-checked translated JP DAT.

| Native form IDs | GL identity | JP identity |
| --- | --- | --- |
| 401008507 | Kaito | Yoshikiri |
| 401008607 | Godrea | Starlight Elena |
| 401008707 | Emperor Foo | Ibara |
| 401014207, 401014217 | Master Machinist Abigail | Dark Knight Duane |
| 401014307, 401014317 | Curse of Immunity Melissa | Eternal Radiance Elena |
| 401014507, 401014517 | Dark Knight Duane | Hyoh & Panthera Ultimus |
| 401014607, 401014617 | Ruin Explorer Nora | Richt |

Shared regional forms keep their numeric master IDs, including Louise
`401011607/617`, Storm Seeker Esther `401012807/817`, and Blade of Vengeance Ibara
`401014407/417`. Their CSV rigs agree despite regional mechanics, names, or image
revisions; name or byte differences alone do not justify splitting identities.
All 83 noncollision raw-name differences are recorded as reviewed shared forms.
Different numeric forms remain separate, even when they depict the same character.

## Sources and identification

- GL: `FFBE_GL/.../mst/Ver402_SsidX62G.dat`, 3,311 forms.
- JP: `FFBE_JP/.../mst/Ver1355_SsidX62G.dat`, 3,512 forms.
- Translated JP: `build/memorial-vortex/payload/SsidX62G.dat`, 3,806 rows.
- GL localized names: existing wiki datamine `datamine/data/gl/units.json`,
  exactly the same 3,311 form IDs as the raw GL table.

The DATs were decoded using the existing `tools/devui/ffbe_live.py` AES-CBC recipe
and external key/field-name metadata. No keys are included here. Full source paths,
SHA-256 hashes, normalized identity fields and reviewed decisions are in
[`unit_identity_sources.json`](../../catalog/unit_identity_sources.json) and
[`unit_identity_decisions.json`](../../catalog/unit_identity_decisions.json).

The translated payload contains 420 GL-only IDs absent from raw JP, and omits 126
raw JP forms. Membership therefore comes from raw regional tables. English names
are accepted only when native unit ID, game ID, sex, character reference, shift
flag, trust master and super trust master match the raw JP record. All 3,386
overlapping records pass this identity check. Old `english_patch/swapped/SsidX62G.txt`
has stale GL names at conflicting JP IDs and was not used as JP naming authority.

The GL dump itself also carries JP bundles. GL `Ver1/Ver2_unit27_common.cpk` contains
Duane at Abigail's IDs, byte-identical to JP `unit27.cpk` across all 16 members per
form. Actual GL Abigail comes from `Ver51_unit3_sg_common.cpk`. Its attack animation
lasts 258 ticks, consistent with its GL DAT's final hit at tick 181; the carried
Duane animation lasts only 133 ticks. Thus source selection pins whole reviewed
archives and never fills one form's companions from another regional identity.

## Validation and coverage

[`validation.json`](validation.json) records a passing validation of:

- 3,964 unique master IDs and 6,823 unique `(server, original_id)` aliases.
- 22 regional collision bundles, all 352 file hashes/lengths and decoded images.
- 264 animation sequences, 2,595 frame references, and 30,839 texture-part bounds.
- All seven original CPK hashes and four identity-source file hashes.
- Every restored file agrees with an independent source/cached-decryption audit.

[`asset-manifest.json`](asset-manifest.json) records every original member, source
archive hash, restored hash and legacy comparison. 185 restored files match the
old flat file; 167 differ. Differing bytes are preserved in separate regional
paths and never overwrite an original source or legacy asset.

The master list covers all 3,953 legacy sprite IDs, plus the eleven required
splits. Raw tables cover 3,932 native IDs: 2,891 shared, 420 GL-only and 621 JP-only.
There are no missing primary assets among the mapped legacy rows. Twenty-one
legacy sprite IDs lack raw-table identity records and remain `unresolved_asset_only`.
Another 126 JP forms have no translated name and retain their native names. Exact
IDs and all rejected name aliases are available in the master list's `coverage`.

The schema retains native filenames and form/base IDs for consumer compatibility.
Master IDs are opaque strings, not replacement game IDs. The separate FFR cache
and picker currently combine numeric IDs and read other asset roots; they require
a separate mapping migration/rebuild to benefit from this repair. No FFR project,
APK, hosting site or GitHub remote is changed by this commit.
