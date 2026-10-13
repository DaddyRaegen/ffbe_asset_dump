# Patch 5 startup comparison for v204

The exact published Patch 5 candidate is `FFBE-Memorial-EN-Patch-5-Units-Cards.apk`, 145,144,781 bytes, SHA-256 `534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208`. Its local bytes match the published pin in the retained production build report. That report records an exact release-clone native ARM emulator test; it does not record a physical-phone test.

## Safe bundled baseline

All 162 current v203 root records marked `phase=boot` are present in the actual production Patch 5 APK and frozen v201 APK with identical SHA-256 and byte count. Together they are 106,756,081 raw bytes. Their original APK paths are `assets/<logical_path>`. `PROPOSED_BUNDLED_STARTUP_ALLOWLIST.json` records every exact identity and original path.

This is the complete production core/startup set, excluding executable/profile/bootstrap metadata and production's old `side_stories/manifest.tsv`. It includes 4 Android audio files, 4 vendor bin files, 2 Bishamon shader packs, 4 core CPKs, 2 fonts, 23 HTML resources, 4 memory-room files, 117 plate-pack files and 2 shaders. It is a conservative safe baseline, not a proven strict minimum.

Do not copy the old production side-story manifest over the current corrected v203 manifest. The current graph's `side_stories/manifest.tsv` has 200,695 bytes and SHA-256 `c6fbf98a241a85fb0c2393c0ebd3061e84d01d6757c5488c35dab8f06f470aa0`. Keep the 501 current game-phase root records and 1,411 additional content records on their existing immutable per-file GitHub transport, and retain original 3,127 base descriptors.

## Actual production startup order

Selected classes were disassembled directly from the pinned signed APK into `patch5-smali/`, rather than assuming earlier source was still current.

1. `Lapis.<clinit>` loads the unchanged native `game` library before the activity starts. (`patch5-smali/com/square_enix/ffbejpn/Lapis.smali`, line 41.)
2. `Lapis.onCreate` invokes `FridaBootstrap.bootstrap(context)`, then the original `Cocos2dxActivity.onCreate`. It has no `GameAssets.bootReady` gate or separate startup-download redirect. (`Lapis.smali`, lines 471–476.)
3. Production `FridaBootstrap` copies its signed script from APK assets, extracts bundled plate artwork to its private plate directory, and loads the gadget. Its historical optional plate-network refresh also remains in production; copying that entire old method would reintroduce unrelated legacy networking. Prefer the reviewed signed-runtime setup with explicit bundled-asset behavior.
4. Native `AppDelegate.applicationDidFinishLaunching` initializes CRI and creates `StartupScene` before the regular on-demand download scene. The retained native disassembly shows CRI initialization at `0x15779f0` and construction of `StartupScene` at `0x1577a3c`.
5. Native startup/resource consumers use core CPK, font, audio, shaders and HTML paths through the normal packaged Android asset path, Cocos `FileUtilsAndroid` and CRI path lookup. Startup and initial-download scene resources exist in the APK already.
6. Native `LapisJNI.checkUnAvailableOnDemandResources` calls `O1.e.r -> ContentDownloader.checkAssets`; its existing progress/total/download callbacks remain `O1.e.l/m/n/o/p/s/t`, and `O1.e.v -> ContentDownloader.startDownload`. Both production and v203 preserve these callback interfaces.

The original native disassembly in the retained audit is applicable because all eight native files, including both `libgame.so` ABIs, are byte-identical across the actual production Patch 5, frozen v201 and signed v203 APKs. Cocos and CRI code is integrated into `libgame.so`; no separate Cocos/CRI library is present. See `PATCH5_V201_V203_NATIVE_ABIS.json` for actual hashes.

## v203 changes that bundling alone cannot fix

Actual v203 DEX was independently disassembled into `v203-smali/`.

- `Lapis.<clinit>` is suppressed; native library loading is deferred into gated `onCreate`.
- Lapis and Cocos activity callbacks use `GameAssets.bootReady` / `gameNativeStarted`; the initial Cocos `onCreate` redirects to `GameAssetsBoot` until external startup data is ready.
- `GameAssetsBoot` downloads the 162 boot files, builds symlink-backed filesystem views, then launches Lapis again.
- `native_game_assets.js` requires `active-root.txt`, prepends external `cpk/`, `font/`, `android/` and root paths to Cocos search paths, purges its path cache, and redirects the CRI ACF argument.
- `GameAssets.open`, `openFd`, `typeface` and `webURL` first call `rootFile`. For root-catalog names, this requires a verified external object and prevents fallback to packaged bytes even if the file has been re-added to the APK.
- The old eager story-index preparation in `O1.e` was deliberately removed and preparation deferred until current downloaded game content is ready. Restoring the entire old production `O1.e` would bring that early dependency back.

For v204, bundled startup paths need a deliberate APK-first trusted allowlist, their native startup path must work independently of the external root marker, and startup must not depend on the separate download activity. Preserve the latest graph identities and deferred game-phase index setup. Keep the external per-file resolver and native callback progress for remaining game assets.

The observed post-download crash has no crash trace in this comparison. Native library byte changes are ruled out; the new Java lifecycle, external startup path and Frida search-path integration are concrete differences to remove from packaged startup. This comparison does not establish the exact crashing instruction or a successful v204 phone launch.

## Evidence produced

- `PATCH5_ASSETS.json`: every production APK asset path, raw/compressed size and hash.
- `V201_ASSETS.json`: every frozen v201 APK asset path, size and hash.
- `V203_ASSETS.json`: every actual signed v203 APK asset path, size and hash.
- `PATCH5_V203_COMPARISON.json`: every production asset compared against the current v203 root graph, plus summary.
- `PROPOSED_BUNDLED_STARTUP_ALLOWLIST.json`: the exact 162 current graph files suitable for bundling.
- `PATCH5_V201_V203_NATIVE_ABIS.json`: all native file identities across all three APKs.
- `patch5-smali/` and `v203-smali/`: selected actual DEX startup/downloader classes.

No runtime/build/guard source, immutable APK, remote host or device was modified by this audit.
