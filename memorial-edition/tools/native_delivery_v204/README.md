# Native delivery APK 204

This directory retains the frozen Patch 5 foundation, APK 204 builder/runtime and host fixtures. Java runtime, tests and signed builder inputs match the tested release workspace; `SOURCE_SNAPSHOT.json` records each source hash. The historical 203 source directory remains unchanged.

Read [the release workflow](documents/NATIVE_RELEASE_WORKFLOW.md), [startup compatibility contract](documents/STARTUP_COMPATIBILITY.md) and [physical-phone checklist](documents/PHONE_TEST_CHECKLIST.md) before a later build.

The user authorized exactly 162 Patch 5-identical startup assets at original APK paths, with a signed inventory. All remaining corrected 203 content uses the existing immutable GitHub per-file graph. APK 204 keeps the package/signer and updates over installed 203. Production remains Patch 5.

`build_config.release204.json`, `host_test_config.release204.json` and `run_tests.release204.py` preserve the exact tested configuration/runner bytes. The default builder uses this canonical source and a separate build output directory. The canonical host runner has one path adaptation: `MetadataTest-actual204` reads `actual_stage` from `host_test_config.json`, with the original `ROOT.parent` fallback. Its config explicitly names the signed 204 payload workspace and a separate host output directory. Input APK, payload and original provenance workspace paths remain explicit local dependencies. For later work, copy/configure a new source/output directory and preserve prior signed APKs, inputs and reports.

The full frozen host suite passed 4,461 assertions; the integrated guard passed 34 regression tests. The signed APK is 145,575,080 bytes, SHA-256 `cfb96d5dd90625b56f2f8fe8c512be08b45186a2d4624f80f22658dc3b209385`. Exact signed qualification, build, source/content audits and publication receipts are retained under `release204`. The pinned release guard and its fixtures are in `guard`.

APK 204 is published at [the beta site](https://ffbe.luminest.io/downloads/beta/). Source-copy checks, host fixtures and public download verification do not prove physical Android startup, actual save migration or native ELF 16 KB compatibility. APK 203 was reported to crash after startup download on Galaxy Z Fold 8/Android 17 without a supplied log. APK 204 phone results remain pending.
