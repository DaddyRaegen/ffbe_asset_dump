# APK 204 physical-phone checkpoint

APK 203 was reported to fail after its startup download on Galaxy Z Fold 8 running Android 17. No crash log was supplied. APK 204 is a new test target; its physical startup/runtime/save results remain pending.

Published test target: [APK 204](https://ffbe.luminest.io/downloads/beta/releases/startup-fix-v204-cfb96d5dd90625b5/FFBE-Memorial-EN-Startup-Fix-v204.apk), 145,575,080 bytes. SHA-256: `cfb96d5dd90625b56f2f8fe8c512be08b45186a2d4624f80f22658dc3b209385`. Public download identity is verified; phone testing remains pending. Record device model, Android version, installed APK hash/version and each reported result in the release checkpoint.

1. Install 204 over the existing FFBE package. Confirm existing saves/settings remain; do not uninstall or clear data.
2. Open the game. Important startup files should be available from the APK without a startup network download. Report any immediate crash or repeated startup prompt; capture a crash message/log if available.
3. Check that the original native game download screen fetches only missing/changed remaining files. Interrupt and resume once; report repeated transfers, missing assets or long loading.
4. Close and reopen. Confirm completed content is reused and the game reaches its normal starting screen.
5. Open JP Memories, Archived Event Battles and Normal Events. Check the restored/moved events, banners and quest visibility; report exact affected names. Kev may test a battle and report the outcome.
6. Open Unit Library and several units. Report pauses, missing names/art or crashes. Check a known available movie if desired; CG coverage remains incomplete.
7. Reopen and confirm saves/settings again. Report device/Android details, errors and results tied to this exact 204 APK hash.

Known limits remain: 675 restored banners with 189 explicit fallback/source gaps; 12/123 selected CG names graph-backed, 91 unqualified local candidates and 20 absent. Native ELF 16 KB compatibility, actual saves and physical runtime are unverified. Host tests and publication do not establish these results or authorize production promotion.

Keep the checkpoint pending until Kev supplies 204 results. This checklist does not authorize the agent to install, inspect device files, start battles, uninstall, or clear caches/saves. Every later APK requires a new offer tied to its own hash.
