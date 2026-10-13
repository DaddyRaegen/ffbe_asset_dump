# Memorial Edition source archive

Read `README.md` before changing this subtree. The version directories preserve
historical source, tests, configurations, and workflows. Their original absolute
paths and sealed inputs are provenance; use an explicit new configuration and a
fresh output directory for future builds instead of running historical defaults.

Keep the copied source/configuration bytes and source seals intact. Put a new
implementation in a new version or workspace, with new qualification evidence.
The inherited v205 instructions are retained under `docs/history/`; they describe
that release, not the current production state. The v208 workflow is under
`tools/production_v208/documents/PRODUCTION_WORKFLOW.md`.

Commit source, tests, authored documentation, and reviewed small configuration
or fixture files. Keep APKs, CPKs, packs, payloads, generated artwork, reports,
receipts, caches, and signing material out of source control. Retain existing
local archives; do not delete or overwrite them during housekeeping.

Source organization does not authorize running publishers, rebuilding a signed
APK, promoting a release, changing any production/beta updater or CDN route, or
interacting with installed app data. Release work requires the applicable scope
and exact-build qualification. Physical phone testing remains separate evidence.

Run safe source/host checks in a new temporary workspace. Do not run archived
`run_tests.py` or `run_guard_regression.py` defaults when they would overwrite
historical output. Never uninstall the app or clear saves/caches for validation.
