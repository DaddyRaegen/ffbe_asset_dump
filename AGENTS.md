# Asset dump and Memorial source

The asset directories, `catalog/`, `data.json`, and `tools/` are the raw asset
preservation project. Preserve native filenames, regional identities, original
asset bytes, source receipts, and explicit metadata gaps.

Memorial patch source, host tests, and release documentation belong under
`memorial-edition/`. Read its `AGENTS.md` and `README.md` for that work. Do not mix
APKs, generated payloads, signing material, caches, or release packs into asset
or source commits.

The installed production app uses the separate Memorial download repository and
CDN. Repository cleanup does not authorize building, signing, publishing,
promoting a release, changing hosted files, or interacting with device data.

For asset tooling changes, run the tests documented in `tools/README.md`.
