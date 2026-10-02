# Recovering assets from a local FFBE dump

Requires Python 3.10 or later and Pillow (`python -m pip install -r tools/requirements.txt`). Encrypted JP archives also require a local copy of `DataExtractor.exe`, `CriPakTools.exe`, and the accompanying native DLLs. These third-party binaries are not included in this repository.

The importer reads the source dump without changing it. It inventories archive members, compares filenames against the current Git commit, and adds missing assets. Existing repository files are never replaced. New unit, monster, battle-background, and vision-card assets use the established folders; vision-card CSVs use `vc_animated_csv`. Reviewed unit-ID collisions use server-specific folders and pinned source archives (see below).

Example in PowerShell, from the repository root:

```powershell
python tools/recover_assets.py inventory --dump 'T:\Projects\ffbe\dump' --repo . --work .recovery-work
python tools/recover_assets.py recover --dump 'T:\Projects\ffbe\dump' --repo . --work .recovery-work --extractor 'PATH\TO\EXTRACTOR' --phase priority
python tools/recover_assets.py recover --dump 'T:\Projects\ffbe\dump' --repo . --work .recovery-work --extractor 'PATH\TO\EXTRACTOR' --phase additional --existing-folders-only
python tools/validate_recovery.py --repo . --work .recovery-work
```

Use an absolute path for `--extractor`. The directory must contain the executable and its dependencies. Windows is required when using this external extractor. GL archives and the inventory reader use Python directly.

Keep the work directory between runs: it stores the baseline, inventory, per-archive cache, and recovery manifest. Reruns resume from that manifest. Run validation after recovery to detect missing, altered, or invalid output. Start a new work directory for a new baseline. `--phase all` selects both phases. Omitting `--existing-folders-only` in the additional phase imports a much larger `additional/` collection; review its size before doing so.

## Selection and preservation

- Matching filenames retain the existing repository copy. New filenames prefer an HD source, then JP, then the highest numbered GL archive version; ties are deterministic. This is filename gap recovery, not replacement of older files or an archive of every regional revision.
- Confirmed unit-ID collisions are an exception to filename ranking: `catalog/unit_identity_decisions.json` pins one coherent archive per regional form. Only those archive members enter `regional_units/{gl|jp}/{original_id}/{category}/`. Ordinary GL archives can contain the JP unit at a colliding ID, so the server directory alone is insufficient evidence. New archive versions require a reviewed policy update and an explicit provenance migration.
- Names outside established categories retain their region, localization, and source category under `additional/` when that optional scope is selected.
- Visual assets include PNG/JPEG images and their CSV, SSBP, BMB, model, map, font, and related companion files. Audio, video, master data, executable tools, and general story text are outside this import scope.
- Some JP archives mix encrypted files with plaintext legacy members. If the external tool's output fails validation, the importer checks the original member bytes before rejecting the file.
- Images are decoded, animation CSVs are checked, and every addition gets a SHA-256 hash and source path. Source animation references outside their texture boundaries are reported without altering the original files.

The source manifest identifies each imported file and its archive. Catalogs list unit forms, monster IDs, and vision cards with links to sprite sheets and animation data. The old `data.json` remains a legacy name lookup, so it does not name every newly recovered ID.

## Animation tools

[BFFrameAnimator](https://github.com/BluuArc/BFFrameAnimator) and [FFBE Sprite Sheet Assembler](https://github.com/dsxragnarok/FFBE-sprite-sheet-assembler) consume the recovered PNG/CSV inputs. Gather files for one ID into the input folder expected by the tool. For units, use `unit_animated` and `unit_animated_csv`; for monsters, use `monster_animated` and `monster_animated_csv`; vision cards use `vc_vignette_animated` and `vc_animated_csv`. Vision cards name their sequence `vc_cgs_<id>.csv` rather than an idle-specific filename.

The recovery preserves source assets. It does not regenerate the existing `animated_gifs` collection.

## Regional unit identities

`catalog/unit_master.json` is a form registry. Unaffected forms keep their original
numeric string as `master_id`. The eleven reviewed collision IDs use
`unit:GL:<original_id>` and `unit:JP:<original_id>`. Do not perform arithmetic on a
master ID or use it as a native filename. Resolve `(server, original_id)` through
the `identities` list and use the explicit `assets` paths. Native base/unit IDs
are retained separately as `source_unit_id`; different form IDs are not merged.

The source snapshot contains only normalized game identity fields and source
hashes, with no decryption keys. Raw GL and JP SSID tables establish regional
membership. An identity-matched translated JP SSID table supplies JP English
names, and the GL datamine supplies checked GL localization. The translated
Memorial payload also imports 420 GL-only forms; it cannot establish JP membership.

Rebuild and validate the checked-in master registry:

```powershell
python tools/build_unit_master.py --repo . --annotate-legacy
python tools/validate_unit_identities.py --repo .
python -m unittest discover -s tools -p "test_*.py"
```

To verify original source hashes too, add `--dump 'T:\Projects\ffbe\dump'` to the
identity validator. That additionally reads the SSID/datamine paths recorded in
the source snapshot. Omit the flag when those private local source paths are
unavailable; restored assets and all registry invariants are still checked.

To reproduce the 22 repaired bundles directly from the original archives:

```powershell
python tools/recover_unit_collisions.py --repo . --dump 'T:\Projects\ffbe\dump' --work .recovery-work/identities --extractor 'PATH\TO\EXTRACTOR'
python tools/build_unit_master.py --repo . --annotate-legacy
python tools/validate_unit_identities.py --repo . --dump 'T:\Projects\ffbe\dump'
```

The repair keeps native archive member names, records source and output SHA-256,
and refuses to replace an existing regional file with different bytes. A rerun
with the same inputs preserves the outputs. All texture pages and companion
files for a form come from its pinned archive.

After updating this importer, rerun `inventory` before any ordinary `recover`.
Pre-policy inventories are rejected rather than allowed to collapse IDs again.
Inventory metadata fingerprints the collision/source policy and inventory bytes;
resume checks verify published or work-directory regional provenance and file
hashes. `validate_recovery.py` preserves ambiguity annotations and rebuilds the
master list using the published identity evidence.

The 21 assets without raw identity metadata and 126 untranslated JP forms remain
explicitly unresolved/native-named. See `coverage` in the master list. This
repository change does not rebuild the separate FFR picker/cache or asset-viewer
index; those consumers must adopt the mapping before showing both identities.
