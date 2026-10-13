# Reviewed Patch5 event port

The new source module starts from the literal production Patch5 script and recreates the frozen201 reference byte for byte. Its input pin is `31a87e1c3deff7f22d692f5a35d476db76b3d0f6639eb0c487fda9b91fb02b44`; output is `da4112ae429c2cf8ea4d392a9d2c677f1177a1a5ecf0d3881391eb6a693dc0fd` (209,183 bytes). The production APK's Android versionCode is **199**; its JavaScript PATCH_VERSION is **5**.

The complete semantic delta is: intermediate PATCH_VERSION 5 → 6; **831 added imported-book markers** (85 → 916 books); and imported playback detection for book IDs 1,000,000 through 1,999,999. Every added marker is an empty JavaScript array, allowing imported events to use normal saved parties. The existing 85 book party lists and all 2,177 entry party lists are unchanged. No hooks, native symbols, Java invocation signatures, movie behavior, or other script logic differ.

Frozen201 also introduced 541 blank lines and normalized all newlines to CRLF. The port reproduces that cosmetic history to make its output equal the immutable reference SHA. The masked compact diff and JSON report account for every script difference without duplicating the large unchanged map.

`source/patch5_event_script.py` is self-contained, reads no external data, rejects any other input hash, refuses party overwrites and checks the output hash. The changed-input check passed. The parent builder owns final version204, beta updater routing, inherited movie-network removal and the asset adapter. This port performs no APK assembly, publication, install or runtime test.
