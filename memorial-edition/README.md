# FFBE Memorial Edition

This folder holds the Memorial Android patch tooling, host tests, and authored
release documentation. The game artwork, animation catalogs, and asset recovery
tools remain in their existing folders at the repository root.

## Source layout

| Directory | Contents |
| --- | --- |
| `tools/native_delivery_v203` | Native asset delivery overlays, builders, host tests, and pinned configurations. |
| `tools/native_delivery_v204` | Startup delivery correction, frozen overlays/tests, and its release guard. |
| `tools/patch5_events_v205` | Event import/build tools, transport checks, and the minimal Patch 5 guard. |
| `tools/event_cleanup_v206` | Event cleanup and banner preparation tools with finite-change tests. |
| `tools/download_spacing_v207` | Download counter formatting tools and regression tests. |
| `tools/production_v208` | Production banner/order preparation, qualification, and publication source snapshots. |
| `tools/release_guard` | Shared historical native-delivery guard and its regression tests. |
| `docs/history` | The original v205 repository instructions and release requirements. |

Source files inside `release204`, `release205`, and later release folders retain
their original relative layout. Their names identify historical snapshots;
they do not mean that a signed APK or the generated release payload is checked in.
The archive source and configuration bytes are preserved, including line endings.

## Where the production app gets its files

The published English Global Events v208 APK carries its download catalogs inside
the APK: `assets/base_delivery.tsv`, `assets/content_delivery.tsv`, and
`assets/side_stories/manifest.tsv`. Those catalogs point to immutable release packs
in [luminest-llc/ffbe-memorial-downloads](https://github.com/luminest-llc/ffbe-memorial-downloads),
with individual paths, sizes, hashes, and byte ranges. Movies use
`https://cdn.luminest.io/ffbe/movies/`.

The APK's production update check uses the latest release of that separate
download repository. The download page at `https://ffbe.luminest.io/downloads/`
also points to the published APK there. Neither the APK's catalogs nor its updater
reference this repository's Memorial source folders.

Moving these local source folders therefore does not redirect the installed app's
downloads. The October 12, 2026 organization preserves the raw asset paths,
published APK, release packs, download catalogs, updater manifests, and website.
The checked production identity is v208, 145,206,221 bytes, SHA-256
`9d21fc8b61c9900eaacb1c2ddef2cabcad1e97d2dc720be16ac09b06fc0086b4`.
See [the delivery and organization record](docs/SOURCE_ORGANIZATION.md).

## Local artifacts and historical paths

APKs, CPKs, download packs, generated payloads/artwork, build output, reports, and
publication receipts are ignored. Existing local copies remain alongside their
historical source where fixtures rely on that layout. They are not part of the
source checkout and must be supplied separately when a release-specific test
requires them. Signing material and publisher credentials are not included.

Archived builders and handoff scripts retain the original absolute work paths
and configuration pins. Some defaults refer to the former repository location
or the original `build/v20x-*` workspace. These are historical inputs, not portable
launch commands. For a future build, copy the needed source into a fresh workspace
and provide a new explicit configuration with the correct source, payload,
baseline APK, and output paths. Do not change a historical seal to disguise a new
input, or run an archived publisher as a cleanup check.

## Safe validation

The raw asset tooling tests remain documented in `../tools/README.md`. The shared
Memorial guard tests run from `tools/release_guard`:

```powershell
python -B -m unittest -v test_release_guard test_bootstrap_inventory
```

These tests use synthetic interfaces and retained frozen v201/v202 APKs. Set
`FFBE_FROZEN_V201_APK` and `FFBE_FROZEN_V202_APK` if those external fixtures are in
different locations. Use a writable temporary directory for `TEMP` and `TMP`.
They do not install the app or change hosted data.

The v205 guard also requires the original Patch 5 Smali inspection. Its transport
test imports the audit and guard modules together. The v206 integration fixtures
require the excluded cleanup plan and source payload; v207 requires its baseline
APK. Supply these original fixtures explicitly in a test harness. The archived
test runners can write to old output paths and should not be run unchanged.

Python syntax parsing and `node --check` validate source without executing builds,
publishers, or device scripts. Host and source checks do not establish phone
gameplay, save migration, or native ELF compatibility.
