# Literal Patch 5 download and startup review

The minimal runtime extension is two classes and three methods. Patch 5 already has the required GitHub packed-range, checksum and resume implementation. Its native download screen already combines missing base files with missing extra event content. Add only the exact missing-event catalog/manifest rows and the narrowly required JP/GL scene path support; retain all other Patch 5 runtime classes and original data routes.

The actual source APK is `T:/Projects/FFBE Patch/localization-rounds/2026-09-29-units-cards-ios/dist/FFBE-Memorial-EN-Patch-5-Units-Cards.apk`, SHA-256 `534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208`. The fresh review disassembly comes directly from that pinned APK using `T:/Projects/FFBE Patch/tools/bin/baksmali.jar`, with default options. `PATCH5_ORIGINAL_DOWNLOADER.json` records the APK/Dex/class/metadata seals. Readable historical Java is supporting evidence; the shipped DEX is the authority.

## Original initialization and native callbacks

1. `Lapis.<clinit>` loads `libgame` before the activity's `onCreate` runs. Raw bundled Patch 5 assets are therefore available before Frida hooks. Keep this original order and its original asset entries/compression.
2. `Lapis.onCreate` calls `FridaBootstrap.bootstrap(Context)` before the Cocos superclass `onCreate`. The original bootstrap extracts `frida_script.js`, extracts the bundled plate pack when needed, retains its existing optional plate-manifest check, and loads `frida-gadget`. It is retained unchanged.
3. `Cocos2dxActivity.onCreate` keeps the original activity/task-root checks, `onLoadNativeLibraries`, Cocos context/handler setup, `Cocos2dxHelper.init`, native GL-context attributes, `init`, and video/web/view helper setup. Its native/library/GL lifecycle stays unchanged.
4. After that superclass call, `Lapis.onCreate` assigns the current activity, performs its existing platform setup, creates `O1.e`, assigns `Lapis.n`, and calls `e.u()` to initialize the original base asset directory. `O1.e`'s constructor retains `StoryPortTables.prepareIndexes` and `SideStoryTables.prepareIndexes`.
5. Native code obtains that `O1.e` object through the unchanged `Lapis.getLapisAssetManager` interface. Its existing callbacks are unchanged:

| O1.e method | Original delegated behavior |
| --- | --- |
| `r()` | `ContentDownloader.checkAssets()` |
| `v()` | `ContentDownloader.startDownload()` |
| `o()` / `n()` / `p()` | Checking / downloading / needs-download state |
| `l()` / `m()` | Downloaded file count / bytes |
| `s()` / `t()` | Total file count / bytes |
| `u()` | `CdnDownloader.initLocalDir()` |
| `k(name)` | Base local resolver, then MemoryRoomTitles, EncyclopediaTables, BattleTables, StoryPortTables and SideStoryTables overrides |

`ContentDownloader.checkAssets` calls `ExtraContent.missing`, then the original `CdnDownloader.checkAssets`, and presents their combined counts/bytes. Its existing worker uses the original shared pause/resume attempt and extra-content batches alongside base downloads. Only after both missing sets are empty does it repeat story/side-story index preparation and mark completion. All existing retry/dialog/progress callbacks remain literal Patch 5. This is a static callback/initialization trace; no device timing or native UI behavior was tested.

## Already-shipped delivery behavior

The actual Patch 5 APK contains 1,411 pinned extra rows: 1,370 side stories, 18 story ports, 14 battle and 9 encyclopedia rows. Its 3,127 original base rows already use GitHub. The full 203 extra catalog has exactly the same 1,411 paths: 1,398 byte-identical rows and 13 changed payload hash/size rows. A wholesale 203 catalog/runtime replacement is unnecessary for the new scope. Keep every old base and unaffected extra row byte-identical; add only the missing-event dependency closure and the necessary event table/manifest revisions.

`ExtraContent` already parses an eight-field APK-pinned catalog with hash, plain size, URL, logical offset, wire size, compression and logical source size. It deduplicates identical hashes, reuses existing verified cache aliases, retains compressed `.part` files, fetches only the requested packed slice, unpacks method 0/8 bytes, verifies SHA-256/size, commits the file and removes its completed partial. `ResumableTransfer` already parses `#ffbe-range=start:size:total`, follows approved GitHub release redirects, checks exact returned ranges/lengths and resumes at the saved physical byte. No new transport helper or OTA graph admission is needed.

Preserve `ExtraContent.open`'s original bundled-first semantics. Preserve the original base `assetpacks/<pack>/199/199/assets/<name>` cache and the original `side_stories/<hash>/<name>`, story/battle/encyclopedia resolver paths. SideStoryTables keeps original expected-source/accepted-hash/variant behavior, including preserving unknown original sources and its existing missing-DAT fallback. Missing event rows must have correct original-source admission metadata; a downloaded file alone does not override an incompatible source.

The original Frida movie branch, curl prefetch, LBDialog, updater, plate check/extraction and all original callbacks remain outside the runtime edit. The new scope does not authorize importing 203/204 replacements for those branches, GameAssets, GameAssetsBoot, BundledAssets, MovieAssets, new lifecycle deferral or compatible-graph OTA.

## Exact code delta and tests

`source/patch_event_paths.py` exports `patch_smali(base_smali_dir)` and refuses any class that differs from the sealed literal Patch 5 originals, aside from CRLF/LF normalization. It writes only:

| Class/method | Exact change |
| --- | --- |
| `ExtraContent$Entry.<init>` | Original flat namespaces, plus `side_stories/r2_scene_(jp|gl)/<16 lower-case hex>/<safe filename>.cpk` |
| `SideStoryTables.load` | Original flat manifest names, plus the same relative JP/GL scene CPK form |
| `SideStoryTables.choose` | The same narrow name predicate; create `target.getParentFile()` using spare local v9, leaving original dir/temp/cache paths intact |

The helper retains original class seals and exact before/after edit blocks in its receipt. All other methods in these two classes are text-identical before assembly. The root builder/independent final qualifier must compare the complete DEX and all other APK members against Patch 5; this review decoded only the relevant 22-class subset.

`MINIMAL_EXTENSION_TESTS.json` records 196 passing host assertions: original transfer 15, GitHub 64, base cache 57, extra-content 35, packed extra-content 6, and new narrow nested-path/preserved-behavior 19. It also records eight sealed-class/method checks, equivalent isolated readable-Java compilation and successful assembly/re-disassembly of the two modified smali classes using the retained APK tool's assembler. The new fixture covers JP/GL paths, malformed/traversing paths, exact nested alias copies, original cache reuse, unknown-source fallback, bundled-first reads and missing-DAT fallback. All networking was an in-memory fake HTTPS handler.

No compiled reference Java enters the APK. No original source/APK, remote state, device files or actual saves were changed. Host and static checks do not prove physical startup, native symlinks, gameplay, save migration or native ELF 16 KB compatibility.
