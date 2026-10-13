// Same native engine and on-demand UI, backed by individually verified files.
// This code ships in the signed APK. No downloaded code or Android APK asset mount.
(function () {
    'use strict';
    const marker = '/data/data/com.square_enix.ffbejpn/files/game_assets/active-root.txt';
    let root;
    try {
        root = File.readAllText(marker).trim();
        if (!/^\/data\/(?:data\/com\.square_enix\.ffbejpn|user\/\d+\/com\.square_enix\.ffbejpn)\/files\/game_assets\/[a-f0-9]{64}\/tree\/$/.test(root)) throw new Error('Invalid game asset root');
    } catch (error) { throw new Error('Verified startup data is required before native startup: ' + error); }
    const game = Process.getModuleByName('libgame.so');
    function symbol(name) {
        let address = game.findExportByName(name);
        if (address) return address;
        for (const module of Process.enumerateModules()) {
            address = module.findExportByName(name);
            if (address) return address;
        }
        throw new Error('Required native symbol unavailable: ' + name);
    }
    const instance = new NativeFunction(game.getExportByName('_ZN7cocos2d9FileUtils11getInstanceEv'), 'pointer', []);
    const add = new NativeFunction(game.getExportByName('_ZN7cocos2d9FileUtils13addSearchPathERKNSt6__ndk112basic_stringIcNS1_11char_traitsIcEENS1_9allocatorIcEEEEb'), 'void', ['pointer', 'pointer', 'uint8']);
    const constructor = new NativeFunction(symbol('_ZNSt6__ndk112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEEC2IDnEEPKc'), 'void', ['pointer', 'pointer']);
    const purge = new NativeFunction(game.getExportByName('_ZN7cocos2d9FileUtils18purgeCachedEntriesEv'), 'void', ['pointer']);
    const installed = new Set();
    const strings = [];
    // Basename resolution for original core CPK/font/audio callers, preserving root paths.
    for (const suffix of ['cpk/', 'font/', 'android/', '']) {
        const object = Memory.alloc(3 * Process.pointerSize);
        constructor(object, Memory.allocUtf8String(root + suffix));
        strings.push(object); // One process-lifetime string per search path.
    }
    function install(fileUtils) {
        const key = fileUtils.toString();
        if (fileUtils.isNull() || installed.has(key)) return;
        for (const string of strings) add(fileUtils, string, 1);
        purge(fileUtils);
        installed.add(key);
    }
    // init may be reached by Director before AppDelegate's first explicit FileUtils call.
    Interceptor.attach(game.getExportByName('_ZN7cocos2d16FileUtilsAndroid4initEv'), {
        onEnter(args) { this.fileUtils = args[0]; },
        onLeave(result) { if (!result.isNull()) install(this.fileUtils); }
    });
    Interceptor.attach(game.getExportByName('_ZN11AppDelegate29applicationDidFinishLaunchingEv'), {
        onEnter() { install(instance()); }
    });
    // CRI's ACF initializer receives the string returned by CommonUtils::getResourcePath.
    // Use the same verified filesystem tree if that legacy path remains relative.
    const acf = game.findExportByName('criAtomEx_RegisterAcfFile');
    if (acf) Interceptor.attach(acf, {
        onEnter(args) {
            let name;
            try { name = args[1].readUtf8String(); } catch (_) { return; }
            if (name === 'android/Lapis_sound.acf' || name === 'assets/android/Lapis_sound.acf') {
                this.path = Memory.allocUtf8String(root + 'android/Lapis_sound.acf');
                args[1] = this.path;
            }
        }
    });
    // Existing plate hooks consume the verified source artwork directly.
    globalThis.FFBE_GAME_ASSET_ROOT = root;
}());
