Build 208 production publication uses the exact signed APK, its pinned native content catalog and immutable GitHub data files. No publication command rebuilds the APK or changes Java classes, native libraries, startup assets, cache or saves.

Patch 5's Frida updater compares logical `PATCH_VERSION=5` with `patch_version.json.version`, then passes the manifest's `url` and string-array `changelog` to its existing update dialog. Android versionCode199 alone does not drive that prompt. The build208 script uses logical version208 and the production routes:

- `https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest/download/patch_version.json`
- `https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest`

Both `url` and `apk_url` name the exact GitHub build208 APK. `version` and `versionCode` are208; `asset_version` is208. The user-provided update message is `added all the global story events and event battles.` Known issues retain the exact strings `Overdrive skills crash the game.` and `dark visions crash the game`.

The native downloader reads the catalog embedded in each APK. It does not need a mutable latest asset pointer to discover the208 files. Older APKs retain their immutable pack URLs; the stable beta203 asset manifest remains unchanged. The old production `base_manifest_url` and `content_manifest_url` remain legacy references. The208 updater additionally advertises current `event_manifest_url` and `content_catalog_url`, with aliases inside the208 APK release. No old release asset is deleted or overwritten.

Run all commands from `S:/FFBE JP Data Export/build/v208-production` after reviewing the source. They require the existing publisher credentials only for explicit remote operations.

1. `node publication/publish_assets.mjs --stage` requires a passed final download plan, banner/order plan hashes, and independent transport qualification. It creates/reuses one exact immutable208 data prerelease with `make_latest=false`, uploads only its pack/catalog/manifest allowlist, and verifies full public hashes plus first/middle/last pack ranges. Production remains Patch5.
2. `node publication/prepare_site.mjs` is local only. It requires the exact signed208 qualification and verified asset receipt, writes metadata/page bytes and seals publisher source pins. The production HTML changes only the Android card, Android/iOS version band and a historical Patch5 notes label. All previous links, iOS and Windows content remain.
3. `node publication/publish_release.mjs --stage` uploads only the qualified APK and fixed metadata aliases to its exact208 prerelease, still `make_latest=false`. It verifies full APK SHA-256 and first/middle/last ranges, all small metadata, and unchanged production guards.
4. Root tests the exact candidate APK in BlueStacks. `device/BLUESTACKS_V208_REVIEW.json` must say `passed:true`, versionCode208 and the same APK size/SHA. Physical phone testing remains pending. A failed or missing report cannot promote the release.
5. `node publication/publish_release.mjs --promote` validates the signed APK, all plans/receipts/source pins, exact BlueStacks report, current protected files and mutable route predecessors before mutation. It adds final release/emulator evidence, promotes only this APK release to nonprerelease/latest, waits for the canonical latest updater, updates the guarded CDN updater and beta APK updater, waits for their canonical public bytes, then updates only the production download index. It records full activation evidence and rechecks old base/content/Vortex assets, direct old Patch5 updater, main source SHA and the stable beta203 asset manifest.

`publication/config.json` lists concrete final plan and receipt paths. Missing or differing inputs fail before publication. Main branch source changes, settings/credential writes, GitHub asset deletion/replacement and unrelated hosting uploads are not admitted by the208 helper. The old Patch5 release and all historical beta releases remain rollback references.

Current state: source preparation only; no208 publication has been executed by this agent. Final APK, independent signed/transport qualification, BlueStacks evidence and production activation are required before marking208 live. These scripts do not claim a physical-phone test, save-migration validation or repaired Overdrive/Dark Visions gameplay.
