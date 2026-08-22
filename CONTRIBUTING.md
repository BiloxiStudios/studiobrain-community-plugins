# Contributing to the StudioBrain Community Registry

This repo is the public submission home for community work. It is still named
`studiobrain-community-plugins` on GitHub; treat it as `studiobrain-community`
(rename is planned).

There are **two different submission paths**. Pick one.

| You are submitting | Edit this file | Schema |
| --- | --- | --- |
| A WASM-component plugin | [`plugins/index.json`](plugins/index.json) | [`schema/plugin-entry.json`](schema/plugin-entry.json) |
| Catalog data (templates, rules, skills, layouts, packs, providers, abilities, flows, canvas) | [`catalog/index.json`](catalog/index.json) | [`schema/catalog-entry.json`](schema/catalog-entry.json) |

Do **not** add entries to root `index.json`. That file is a pointer only.

Official first-party templates, rules, skills, layouts, packs, and provider YAML
stay in [`studiobrain-templates`](https://github.com/BiloxiStudios/studiobrain-templates).
Do **not** open a PR there for community data.

We **never deploy community plugins as Cloudflare Workers**. A merged plugin
entry is an index pointer + checksum, not a Worker deploy.

---

## Submit a plugin

### Prerequisites

- A StudioBrain plugin built as a **WASM component** (`.wasm`)
- The bundle hosted at a stable public HTTPS URL (GitHub Releases recommended)
- A public source repository
- A permissive open-source license (MIT, Apache 2.0, BSD, ISC, etc.)
- The SHA-256 of the exact bytes at `wasm_bundle_url`

### 1. Build

Use the [StudioBrain Plugin SDK](https://github.com/BiloxiStudios/studiobrain-core)
to scaffold and build a WASM component. Community plugins must declare
`"runtime": "wasm-component"`.

The `hello-world-community` example may still use `"runtime": "wasm"` as a
placeholder. New submissions may not.

### 2. Host the WASM bundle

Upload the `.wasm` file to a stable public URL:

```bash
gh release create v1.0.0 dist/my-plugin-name.wasm \
  --repo your-org/your-plugin-repo \
  --title "v1.0.0" \
  --notes "Initial release"
```

Checksum the published file:

```bash
sha256sum dist/my-plugin-name.wasm
```

### 3. Fork and add an entry

```bash
gh repo fork BiloxiStudios/studiobrain-community-plugins --clone
cd studiobrain-community-plugins
```

Add an object to the `plugins` array in `plugins/index.json`:

```json
{
  "id": "your-org-my-plugin-name",
  "name": "My Plugin Name",
  "version": "1.0.0",
  "description": "A short description of what your plugin does (max 200 characters)",
  "author": "Your Name or Org",
  "repo_url": "https://github.com/your-org/your-plugin-repo",
  "wasm_bundle_url": "https://github.com/your-org/your-plugin-repo/releases/download/v1.0.0/my-plugin.wasm",
  "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "manifest_url": "https://github.com/your-org/your-plugin-repo/releases/download/v1.0.0/plugin.json",
  "environments": ["desktop", "mobile"],
  "network": "none",
  "platforms": ["core", "desktop"],
  "runtime": "wasm-component",
  "category": "utility",
  "tags": ["tag1", "tag2"],
  "min_version": "0.1.0",
  "license": "MIT"
}
```

| Field | Description |
| --- | --- |
| `id` | Unique `author-plugin-slug`. Lowercase, digits, hyphens. |
| `wasm_bundle_url` | Direct HTTPS URL to the `.wasm` file. |
| `sha256` | 64 lowercase hex chars of those bytes. Required when the URL is set. |
| `manifest_url` | HTTPS URL to `plugin.json`. Required when the WASM URL is set. |
| `environments` | `desktop`, `mobile`, and/or `cloud` (cloud = panel / author backend, not our Worker). |
| `network` | `none` or `local`. `local` is allowed only when `environments` is exactly `["desktop"]`. |
| `runtime` | Must be `wasm-component`. |
| `category` | `example`, `utility`, `importer`, `exporter`, `ui`, or `workflow`. |

Do not put secrets in the index entry. Use plugin settings for user-provided credentials.

CI also rejects `network:local` unless the listing is desktop-only.

### 4. Open a plugin PR

```bash
git checkout -b add-my-plugin-name
git add plugins/index.json
git commit -m "Add my-plugin-name by your-org"
git push origin add-my-plugin-name
```

CI validates schema, unique IDs, `wasm-component` runtime, HTTPS WASM URL,
`sha256`, `manifest_url`, no secrets, and `network:local` only when
`environments` is exactly `["desktop"]`. Catalog CI is cheaper (schema + HTTPS
URL + checksum field).

---

## Submit catalog data

Use this path for community **data**, not executable plugins.

Kinds (each is its own array in `catalog/index.json`):

`templates` · `rules` · `skills` · `layouts` · `packs` · `providers` · `abilities` · `flows` · `canvas`

Official copies of these kinds belong in `studiobrain-templates`. Community
forks, genre packs, and third-party providers belong here.

### Entry shape

Every catalog entry needs these fields (`schema/catalog-entry.json`):

```json
{
  "id": "your-org-my-template",
  "kind": "template",
  "version": "1.0.0",
  "download_url": "https://github.com/your-org/my-template/releases/download/v1.0.0/character.md",
  "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "author": "Your Name or Org"
}
```

`kind` must match the array you append to (`template` → `templates`, `flow` →
`flows`, and so on). Extra metadata fields are allowed. Catalog CI is cheaper
than plugin CI: it checks schema, HTTPS `download_url`, and checksum field
format. It does not download or execute the artifact.

### Open a catalog PR

```bash
git checkout -b add-my-template
git add catalog/index.json
git commit -m "Add my-template catalog entry"
git push origin add-my-template
```

---

## Review process

1. CI validates the touched index against the matching schema
2. A maintainer reviews the source and the hosted artifact
3. Plugin reviews check capability declarations and obvious security issues
4. Catalog reviews check license, uniqueness, and that official templates-repo
   content was not copied here as a bypass
5. On merge, `publish-r2.yml` uploads:
   - `community/plugins/_index.json`
   - `community/catalog/_index.json`

Reviews typically take 3-5 business days.

## Updating or removing an entry

Fork, edit **your** object in `plugins/index.json` or `catalog/index.json`
(bump `version` when the artifact changes), and open a PR. To remove an entry,
delete that object and say why in the PR body.

## Local validation

```bash
pip install jsonschema
python3 scripts/validate_entries.py
python3 scripts/check_duplicates.py
python3 scripts/check_wasm_runtime.py
```

## Questions?

Open an issue in this repository or join the [StudioBrain Discord](https://studiobrain.ai/community).
