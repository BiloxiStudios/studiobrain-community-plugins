# StudioBrain Community Registry

Public submission home for community **plugins** and community **catalog data**.
The GitHub repo is still named `studiobrain-community-plugins`; it is treated as
`studiobrain-community` (rename is a follow-up).

This is **one repo, two indexes**:

| Index | File | What it lists |
| --- | --- | --- |
| Plugins | [`plugins/index.json`](plugins/index.json) | WASM-component plugins hosted by their authors |
| Catalog | [`catalog/index.json`](catalog/index.json) | Community templates, rules, skills, layouts, packs, providers, abilities, flows, canvas |

Root [`index.json`](index.json) is a thin pointer to those two files. Do not add
new entries there.

## What belongs where

**Submit a plugin here** when you have a sandboxed WASM component (WIT /
`wasm-component` runtime). Authors host the `.wasm` file; this registry only
stores the pointer, `sha256`, and metadata.

**Submit catalog data here** when you have community templates, rules, skills,
layouts, packs, providers, abilities, flows, or canvas files. Official first-party
data stays in [`studiobrain-templates`](https://github.com/BiloxiStudios/studiobrain-templates).
Do **not** open PRs for community data against `studiobrain-templates`.

## What we never do

- **We never deploy community plugins as Cloudflare Workers.** Community WASM
  is not bundled into Workers, Durable Objects, or Dynamic Worker Loader isolates.
  Cloud may list an entry from the R2 index; it does not ship your plugin as a Worker.
- We never host first-party / signed official plugins here. Those live in the
  private `studiobrain-plugins` repo.
- We never treat GitHub raw as the runtime source of truth. Clients read the
  published R2 copies:
  - `community/plugins/_index.json`
  - `community/catalog/_index.json`

## How plugins work

StudioBrain loads community plugins at runtime from the plugin index. Each entry
points at a WASM **component** hosted in the author's own repository. Desktop and
self-host runtimes download, sandbox, and execute that bundle. Capability grants
and a consent prompt are required.

Community plugins cannot:

- Access the filesystem directly (all I/O goes through the host API)
- Make arbitrary network requests (requires declared capabilities)
- Run native code — WASM component only, no native addons, no Python

## How to submit

See [CONTRIBUTING.md](CONTRIBUTING.md). Plugin submissions and catalog-data
submissions are different sections with different schemas.

## Requirements

- Plugin must be open source (MIT, Apache 2.0, or similar permissive license)
- Plugin runtime must be `wasm-component` (`wasm` is allowed only on the
  `hello-world-community` placeholder)
- WASM bundle must be publicly hosted with a stable HTTPS URL and a `sha256`
- Catalog entries need `id`, `kind`, `version`, `download_url`, `sha256`, `author`
- IDs must be globally unique across both indexes

## License

The registry infrastructure (this repository) is licensed under MIT. Individual
plugins and catalog artifacts retain their own licenses as declared on each entry.
