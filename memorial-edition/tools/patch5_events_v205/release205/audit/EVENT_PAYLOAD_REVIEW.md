# Patch5 event-only payload

The payload starts from literal production Patch5. Every original decoded master row stays unchanged and in its original order. Corrected203 contributes only previously absent IDs; its changes to five original books, 24 original maps and 190 original entries are discarded.

The menu adds 3 categories, 863 books, 1,850 maps and 7,999 stage/scene entries. Of the new books, 835 have battles and require explicit empty-array markers in the existing Patch5 party map; the remaining 28 contain scenes only. The original party classifier and hooks need no change.

The removed Greetings aggregation had 10 maps and 18 entries. Every one of those entries has an identical scene signature already retained under an original Patch5 book. Its unused icon is omitted. All retained new rows have closed parent links and consistent category fields. Patch5's pre-existing dormant map/book gaps remain unchanged and are recorded separately in the plan.

The payload contains 500 event dependency files: 15 masters, 199 CPK archives and 286 audio banks. Only three playback masters, the icon master and the banner CPK require newly derived bytes. The other 495 files reuse exact hash-pinned corrected203 bytes. Every scene/audio filename has a literal reference in the merged masters except two native monster companion archives, which have their own event/member proof.

The banner CPK preserves all 214 literal Patch5 members byte for byte and appends 347 filenames referenced by the new book/category icons. It omits 676 unused newly introduced image members. The monster companion proof independently preserves all 1,524 and 132 original Patch5 members in monster2c and monster2d; only 3 and 21 required new members are appended.

The side-story manifest retains all 1,370 original paths and adds 487 paths. All actual Patch5 master hashes remain accepted, including the three masters originally delivered through the base downloader. The complete manifest is bundled metadata and is excluded from the 500 download rows.

Machine-readable outputs are `EVENT_PLAN.json`, `EVENT_BANNER_PRESERVATION.json` and `EVENT_COMPANION_ASSET_PROOF.json`. The plan includes exact source pins, file hashes, original and added IDs, row counts, duplicate-scene evidence, parent checks and the 835 party markers. Payload preparation performs no APK build, native/runtime edit, device operation or remote write.
