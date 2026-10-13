This separate qualifier checks the v205 release against the literal production
Patch 5 APK. It does not apply the superseded 203/204 runtime or asset policies.

Run `patch5_event_guard.py` with `--baseline-apk`, `--apk`, `--payload`,
`--event-plan`, `--smali-receipt`, and a fresh `--output` JSON path. Tool and
frozen source defaults point to the retained local FFBE project. The output's
sibling timestamped `_work` directory contains the real Android signature,
alignment, package and full DEX disassembly evidence. Each run creates a fresh
work directory and records its path in the qualification report.

The qualifier accepts exactly five changed APK members: the binary manifest's
versionCode integer, classes.dex, the original event party map and three update
constants in frida_script.js, content_delivery.tsv, and side_stories/manifest.tsv.
All 170 original asset members, original resources, native libraries and every
other compressed ZIP payload are preserved. All DEX classes remain present;
only the exact path predicates and nested parent directory creation in two
sealed original classes may change. DEX descriptors identify classes so Windows
filename collision suffixes cannot imply a class change. Label offsets and equivalent
const-string/jumbo or goto width encodings are normalized and reported.

The payload comparison independently decodes all 15 event/dependency tables,
preserves every full original record in order, and derives additions from the
pinned source tables. New parent references must close. The 18 omitted
Greetings scene records must have exact original signatures. Catalog metadata
must match all 500 admitted event payload files; each transport pins an immutable
GitHub release. Original metadata outside these files remains literal Patch 5.
The event artwork archive retains all 214 original raw members and adds only
347 required icon filenames. Two monster companion archives retain their 1,656
original members and append 24 members proven necessary by the pinned dependency
ledger. The rest of the event payload keeps the exact admitted source bytes.

`test_patch5_event_guard.py` contains focused positive and mutation tests,
including the independently assembled two-class reference and real production
binary manifest. Run `python -B -m unittest -v test_patch5_event_guard` here.
Successful static qualification does not claim device gameplay or runtime tests.
