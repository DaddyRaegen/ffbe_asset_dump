# Startup runtime review and bundled-source implementation

The exact v203 physical crash cause remains unproven without a phone stack or log. The static source shows a delivery gap that the authorized APK startup bundle addresses: downloading 162 files into a private filesystem tree does not make those bytes visible through every native Android AssetManager consumer.

## Evidence

The retained native audit identifies direct `AAssetManager_open` consumers in CRI, Cocos FileUtils and experimental AudioEngineImpl, plus direct `AAssetManager_openDir` consumers in PUMaterialCache. v203 only installs Cocos search paths and intercepts one CRI ACF path. Java font/audio/video/WebView adapters do not intercept arbitrary native AssetManager calls.

The actual decoded v203 `Lapis.onCreate` calls `System.loadLibrary("game")` at line 781, then `FridaBootstrap.bootstrap` at line 785. Native ELF constructors/JNI initialization therefore cannot depend on hooks installed by that later Frida script. The retained `NATIVE_ASSET_CALLERS.json`, `RESOURCE_STARTUP.asm` and decoded APK sources are the evidence; no device run or native responsiveness is claimed.

Before this change, `ExtraContent.available` accepted only verified private cache files, and `GameAssets.rootFile` threw for a cataloged root missing in that cache. Simply embedding core assets would still leave them in the download queue and would not make Java adapters use them.

## Implemented owned files

- `source/java/O1/BundledAssets.java` validates the signed inventory's schema, package, certificate, APK/asset versions, exact manifest hash, declared paths, namespace, byte sizes and asset hashes. The inventory set must equal every signed baseline root/boot record; fixture counts may vary. APK204 and later require the inventory. Only exact FileNotFoundException absence on legacy APK203 permits the old strict external mode.
- `source/java/O1/ExtraContent.java` unwraps reflective AssetManager exceptions so absence cannot swallow malformed metadata or source failures. It verifies each declared raw APK stream, atomically seeds the existing per-file object cache, and retains the existing hash index. It preserves remote partials and unrelated save files. Bundled cache corruption, including same-size corruption, repairs from the admitted APK bytes without HTTP.
- `source/java/O1/GameAssets.java` admits the bundle after validating the signed baseline and before selecting cached revisions or checking missing files. Every Java adapter still reads the verified filesystem source. Owned bundled tree aliases can be repaired after atomic cache replacement; other collisions still fail closed. Future graphs cannot remove or change a bundled startup path's hash/size; such changes require a newer APK. A stale bundle never qualifies a changed hash.
- `source/tests/BundledStartupTest.java` tests the complete local startup path with fake HTTPS and isolated files. It leaves the existing native lifecycle/downloader behavior intact.

The parent builder must keep the admitted 162 raw startup assets at their original APK paths, preserving their exact qualified production bytes. Those real APK paths satisfy early native AssetManager reads. It must also embed the complete signed inventory and baseline metadata. Existing boot preparation publishes the filesystem marker before Frida starts, preserving script compatibility, with no startup network transfer when the admitted bundle is complete.

## Verification

All copied Java sources and fixtures compile for Java 8 against the existing Android API jar.

The focused suite passed **43 checks**, covering both AtomicFile backup/base and modern `.new` commit styles: first boot with zero HTTPS, no duplicate boot queue, verified Java reads, original raw APK reads, preservation of fixture saves/partials, same-size cache repair, incremental GitHub downloads for nonbootstrap assets, future bundled-core rejection, stale-source rejection, and malformed/missing/tampered inventory/source failures.

The existing NativeDeliveryTest passed **25 cache/transition checks**, confirming legacy APK203 fixtures without inventory retain the external delivery behavior. Host hardlinks simulate Android symlinks; these results do not establish native Android runtime, actual saves, or the physical crash fix.

The parent should register BundledStartupTest with the fixture-output path in the canonical host runner, then run the full signed-APK/inventory guard, asset byte/catalog checks and existing host suites against the final build. No device install, battle, save/cache clearing, network publication or remote mutation occurred in this delegated implementation.
