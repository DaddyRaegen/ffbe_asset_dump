# FFBE Memorial release requirements: Patch 5 events, APK 205

The latest October 4, 2026 user direction is literal production Patch 5 plus all qualified missing events and required asset downloads only, with **“NOTHING EXTRA.”** This supersedes the 203/204 runtime and whole-graph correction for APK 205. [The exact earlier requirements](tools/patch5_events_v205/documents/HISTORICAL_RELEASE_REQUIREMENTS_through_v204.md), historical sources, signed APKs, reports and receipts remain unchanged.

Read [the 205 workflow](tools/patch5_events_v205/documents/PATCH5_EVENTS_RELEASE_WORKFLOW.md), [known limits and evidence](tools/patch5_events_v205/documents/KNOWN_LIMITS.md) and [Kev's checklist](tools/patch5_events_v205/documents/PHONE_TEST_CHECKLIST.md). Current work root: `S:/FFBE JP Data Export/build/v205-patch5-events`.

APK 205 is [published on beta](https://ffbe.luminest.io/downloads/beta/releases/patch5-events-v205-e5cd923909292166/FFBE-Memorial-EN-Patch-5-Events-v205.apk), 145,206,221 bytes, SHA-256 `e5cd92390929216666cebdbb9055d1f216cf2001c20dc4f8fe63225101dbf039`. `publication/activation-receipt.json` records successful activation at `2026-10-04T21:23:40.532Z` with immutable event release `beta-content-v205-bc652c2ce823875b`; production remains Patch 5. Phone/runtime/gameplay/save results remain pending.

## Exact foundation and permitted delta

- Use literal production `FFBE-Memorial-EN-Patch-5-Units-Cards.apk`, 145,144,781 bytes, SHA-256 `534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208`, source versionCode 199. Frozen 201/203/204 are not executable foundations for 205.
- Preserve Patch 5 startup assets/paths, movies/movie networking, native libraries, downloader/cache/resume/callbacks, lifecycle, UI, roster and unrelated features/hooks. Add no APK members; preserve all 170 original asset members. There is no new bootstrap inventory, startup gate, whole-graph OTA adapter or PatchUpdater replacement.
- Preserve every original decoded event/dependency master record and its order. Append only qualified new IDs from the pinned corrected 203 event source. Preserve original archive/banner members byte for byte; add only required event dependencies. Do not reclassify original books, rewrite existing banners or merge regional identities by number/title alone.
- The exact delta adds 863 books: 835 battle and 28 scene-only, plus three categories, 1,850 maps and 7,999 stage/scene entries. Total book IDs are 1,045 = 182 + 863, exactly the literal Patch 5/corrected 203 union. Duplicate Greetings aggregation 1550000 was already absent from corrected 203; its 18 scenes remain under original books. No unique scene is discarded.
- Keep all 85 original book and 2,177 entry party policies. Add 835 explicit empty-array book markers through existing Patch 5 behavior. Keep the classifier/hooks and scene-only policies unchanged.
- Limit the DEX edit to sealed nested scene path predicates in `O1/ExtraContent$Entry` and `O1/SideStoryTables`, plus nested parent-directory creation in the latter. Only pinned `r2_scene_jp/gl/<16-hex>/<safe-name>.cpk` paths are added. Preserve startup/downloader methods. The Frida delta is the party map and three release/beta update constants only.
- Increment versionCode and the existing notification counter to 205. Keep package `com.square_enix.ffbejpn` and signing certificate SHA-256 `21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee`, so 205 updates over installed 203/204. Never uninstall or clear data to bypass an upgrade problem.

## Asset delivery and channels

The original Patch 5 eight-field content catalog and three/four-field side metadata remain the contract. Preserve all 1,411 original catalog rows/order except exact event paths approved by `EVENT_PLAN.json`; append missing rows only. Keep all 1,370 original side paths. Bind every one of the 500 qualified dependencies to matching hash/size metadata and immutable GitHub ranges. Preserve unchanged descriptor fields and packs. Missing/changed event files use the existing native screen; retain valid cache, partial transfers and saves.

Host assets on existing `luminest-llc/ffbe-memorial-downloads`. Reuse byte-identical qualified locations; new derived bytes use new hash-qualified packs on a beta prerelease with `make_latest=false`. Never replace/delete old packs. Use the saved account without credential/service/settings changes or fees. Keep credentials away from redirected public hosts and out of files/logs.

Standing beta upload authorization covers reviewed event assets, the exact qualified APK and beta page/update metadata. It does not authorize source/code pushes or production promotion. Preserve `DaddyRaegen/ffbe_asset_dump` history, asset `main`, production Patch 5/latest and production page/updaters. Beta notification uses `https://raw.githubusercontent.com/luminest-llc/ffbe-memorial-downloads/beta/channels/beta/patch_version.json`; never production `releases/latest`. Preserve Vortex and prior beta rollback links. No full-site deployment.

Stage/qualify exact assets and signed APK before beta activation. Planned links are unpublished until verified receipts exist. Verify each new pack/APK by complete GET hash/size and first/middle/last ranges; state reused-pack verification separately. Historical 203/204 manifests and receipts remain preserved. APK 205 does not require their complete `game_asset_manifest` graph or bootstrap inventory.

## Qualification and honest limits

Run the exact 205 guard/regressions against literal Patch 5, the signed candidate, event plan, catalog and sealed two-class receipt. Independently check the five changed members; unchanged assets/native/resources and DEX classes; all original rows/order; added parents; all 500 source-pinned payloads; banner/companion member preservation; and actual 205 catalog admission/cache/partial fixtures. Old reports do not qualify new bytes.

Only `AndroidManifest.xml`, `classes.dex`, `assets/frida_script.js`, `assets/content_delivery.tsv` and `assets/side_stories/manifest.tsv` may differ within the scope above.

Qualified missing events are source-backed archived routes/dependencies admitted by the plan. They do not establish every event ever released, server rewards/rankings/exploration, GL combat parity or physical playability. Runtime/gameplay/save migration and phone results remain pending. ZIP 16 KB alignment does not establish native ELF page compatibility. Preserve exact source-gap evidence. Movies retain original Patch 5 behavior; the 203/204 12/123 movie graph count is not a 205 claim. Optional animations, new units, UI changes and unrelated runtime redesign are outside scope.

## Kev's physical-phone checkpoint

Standing October 3 instruction (`Sentinel_c86dc0dd2974819180496cd2e691b3b6`): offer every published APK to Kev with verified live link, exact version/bytes/SHA, known limits and short checklist tied to that hash. Every later APK needs a new offer.

Keep the checkpoint pending until Kev supplies 205 results. Publication/static/host/emulator checks or another APK's results do not establish 205 startup, gameplay or saves. Record device/Android version, exact build and failures. Ask Kev to install over the existing package, verify saves, startup/resume, missing event downloads, JP Memories/normal/archive battles, banners and Unit Library. Do not ask for uninstall or clear-data workarounds.

Record publication/offer/results in the handoff and `PHONE_TEST_CHECKPOINT.json`. Before verified publication use `APK_published=false` and `physical_phone_test=pending_publication`; label planned links unpublished. This checkpoint does not authorize agent installation, device-file reads, battles or cache/save changes. Production promotion remains a separate user decision after review.
