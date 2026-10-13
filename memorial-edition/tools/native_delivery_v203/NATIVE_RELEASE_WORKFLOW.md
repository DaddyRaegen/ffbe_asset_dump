# Native delivery build and qualification

The canonical requirements are the repository's `RELEASE_REQUIREMENTS.md` and
`tools/release_guard/README.md`. They apply to later patches. This pipeline stages
a signed APK; it has no install, publication, code push, cache clearing or save
mutation step.

`build_native_apk.py --config build_config.json` starts from the frozen signed
v201 executable baseline, verifies its SHA, overlays the checked native downloader
sources, adjusts the original binary Android manifest to version 203, removes all
game data from APK assets, preserves Android/native resources, and signs with the
existing project keystore. Passwords are read through the existing project
mechanism and passed to the signer only in environment variables.

The v202 custom ZIP bootstrap is never an input. The signed APK includes only
the executable/profile allowlist and five delivery metadata files. Every game
resource stays in the per-file external graph. A signed baseline JSON lets the
runtime compare future per-file revisions. Preserve both original APK ABIs; ZIP
alignment is a separate result from native ELF 16 KB compatibility.

`qualify_native_release.py --config qualification_config.json` runs the actual
signed APK guard, its regression tests, the downloader/cache/resume/transition
host fixtures, decoded source event ledger, banner byte identities, and every
locally packed asset byte. It must complete successfully for each new build.
It verifies exact APK and manifest hashes before and after qualification. No
old passing report is reused as evidence for changed code.

Configurations use explicit local paths for the existing project Android tools,
frozen executable baseline, native sources, manifest/catalogs, retained evidence
workspace and fresh output directory. Copy the supplied examples and change those
paths for the next release. Keep historical inputs immutable. Event/banner source
checks require the original catalog/provenance workspace and supported project
decoding tools; do not invent a synthetic fixture to bypass missing evidence.

The Java startup activity downloads only the files needed before the native
download screen can draw. It uses the existing `ContentDownloader` and
`ResumableTransfer`; the rest uses the original unavailable-file/progress/start
callbacks. Native Cocos/CRI reads use verified filesystem objects and search
paths, with explicit Java font/audio/video/web adapters. It does not mount a ZIP
into Android resources. Runtime qualification remains pending.

The separate `publish_beta_assets.mjs` tool accepts a frozen, hash-bound asset
plan. `--check` is local, `--preflight` is read-only network inspection, and
`--publish` changes the exact asset repository beta release/pointer paths. It
never publishes an APK, moves production main/latest, or pushes code. A passing
local guard is not authorization to publish. The present asset upload was blocked
by automatic approval review and is awaiting explicit approval.

APK 203 is staged for review. The public beta APK remains v202, and its updater
notification stays disabled in the proposed beta pointer until a separately
reviewed APK is available. Device install/battle/save testing is not authorized.

## Kev's physical-phone release checkpoint

Standing user instruction, October 3, 2026 (`Sentinel_c86dc0dd2974819180496cd2e691b3b6`): every published APK must be offered to Kev for a physical-phone test. Publishing or passing static/host checks does not establish runtime validation.

- After every APK publication, give Kev the verified beta/download link, exact version, byte size, SHA-256, known limits and a short phone-test checklist. Keep the offer tied to that exact APK hash. A later APK requires a new test offer.
- Record the checkpoint as `pending` until Kev supplies results for that build. Never mark physical-phone/runtime/save behavior as passed from publication, a download check, emulator/host fixtures or another APK's results. Record device/Android version and reported failures when available.
- Ask Kev to install over the existing package, verify retained saves, exercise startup/resume, JP Memories, normal/archived event battles, banners and Unit Library, then report crashes, missing assets and long loading. Do not ask for uninstall or clear-data workarounds.
- Production promotion remains a separate decision and authorization after review of Kev's results. Publication alone never promotes production.
- This checkpoint does not authorize the agent to install, start battles, read device data, clear caches/saves or perform device tests. Kev performs the physical-phone test; existing agent runtime permissions remain unchanged.

Record publication/offer/test state in the release handoff and `PHONE_TEST_CHECKPOINT.json`. While publication is blocked, keep `APK_published=false` and `physical_phone_test=pending_publication`; do not present a planned APK URL as live.
