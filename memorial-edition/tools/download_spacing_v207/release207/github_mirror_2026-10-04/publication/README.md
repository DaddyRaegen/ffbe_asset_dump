# Build 207 GitHub mirror page

This folder changes only the current beta download button: GitHub becomes the primary 207 download and the existing Luminest URL remains a mirror. It retains every other page byte, all eight older build links, the original checksum/release/checklist URLs and the pending phone-test wording.

Run `node publication/prepare_page.mjs`, then `node publication/review_page_local.mjs` locally. These commands make no network requests. The exact previous published 207 page and receipt are pinned under `publication/frozen207`.

The root publisher owns the GitHub APK upload and canonical beta updater change. It must first write `publication/github-apk-receipt.json` with successful exact APK full-download/hash/size verification and three verified range receipts. The receipt must identify the fixed 207 prerelease, its release ID, `prerelease:true`, and `make_latest:false`.

Only after that verification and canonical updater readback may root run `node publication/publish_page.mjs`. The script checks that both beta updater URLs point to the exact GitHub 207 APK, checks production main/latest, six protected public files and the stable 203 manifest pointer, and writes only the guarded `downloads/beta/index.html`. It performs no APK, asset, release-metadata, GitHub release or updater writes. No APK download retest or asset-pack test is part of this page publication.

Historical 207 files and receipts remain unchanged. Phone/runtime/save checks remain pending for the same signed APK.
