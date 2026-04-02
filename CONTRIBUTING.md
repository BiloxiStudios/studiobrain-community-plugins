# Contributing a Community Plugin

This guide walks you through submitting your plugin to the StudioBrain community registry.

## Prerequisites

Before submitting, make sure you have:

- A working StudioBrain plugin built as a WASM bundle (`.wasm` file)
- The bundle hosted at a stable, public URL (GitHub Releases is recommended)
- A public source repository for your plugin
- A permissive open-source license (MIT, Apache 2.0, BSD, ISC, etc.)

## Step 1: Build your plugin

Use the [StudioBrain Plugin SDK](https://github.com/BiloxiStudios/studiobrain-core) to scaffold and build your plugin:

```bash
# Install the SDK CLI (once available)
pip install studiobrain-plugin-sdk

# Scaffold a new plugin
sb-plugin init my-plugin-name

# Build the WASM bundle
sb-plugin build --release
# Output: dist/my-plugin-name.wasm
```

## Step 2: Host your WASM bundle

Upload the `.wasm` file to a stable, publicly accessible URL. GitHub Releases is the recommended approach:

```bash
gh release create v1.0.0 dist/my-plugin-name.wasm \
  --repo your-org/your-plugin-repo \
  --title "v1.0.0" \
  --notes "Initial release"
```

The release asset URL will be in the format:
```
https://github.com/your-org/your-plugin-repo/releases/download/v1.0.0/my-plugin-name.wasm
```

Use this URL as `wasm_bundle_url` in your registry entry.

## Step 3: Fork this repository

```bash
gh repo fork BiloxiStudios/studiobrain-community-plugins --clone
cd studiobrain-community-plugins
```

## Step 4: Add your plugin entry to index.json

Open `index.json` and add a new object to the `plugins` array. Every field is required:

```json
{
  "id": "your-org-my-plugin-name",
  "name": "My Plugin Name",
  "version": "1.0.0",
  "description": "A short description of what your plugin does (max 200 characters)",
  "author": "Your Name or Org",
  "repo_url": "https://github.com/your-org/your-plugin-repo",
  "wasm_bundle_url": "https://github.com/your-org/your-plugin-repo/releases/download/v1.0.0/my-plugin.wasm",
  "platforms": ["core", "desktop", "cloud"],
  "runtime": "wasm",
  "category": "utility",
  "tags": ["tag1", "tag2"],
  "min_version": "0.1.0",
  "license": "MIT"
}
```

### Field reference

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier. Use `author-plugin-slug` format. No spaces. |
| `name` | string | Human-readable display name. |
| `version` | string | Semver version of this entry (must match your WASM bundle). |
| `description` | string | Short description. Max 200 characters. |
| `author` | string | Your name, GitHub username, or organization name. |
| `repo_url` | string | URL to the plugin's source repository. |
| `wasm_bundle_url` | string | Direct URL to the `.wasm` file. Empty string if not yet published. |
| `platforms` | array | Supported platforms: any combination of `"core"`, `"desktop"`, `"cloud"`. |
| `runtime` | string | Must be `"wasm"` — only WASM plugins are accepted in the community registry. |
| `category` | string | One of: `"example"`, `"utility"`, `"importer"`, `"exporter"`, `"ui"`, `"workflow"`. |
| `tags` | array | Searchable tags. Keep to 5 or fewer. |
| `min_version` | string | Minimum StudioBrain version required. Semver string. |
| `license` | string | SPDX license identifier (e.g., `"MIT"`, `"Apache-2.0"`). |

### ID naming rules

- Must be globally unique across the registry
- Lowercase letters, numbers, and hyphens only
- Recommended format: `{author}-{plugin-slug}` (e.g., `acmestudio-asset-renamer`)
- No spaces, underscores, or special characters

## Step 5: Validate locally (optional but recommended)

```bash
# Install ajv-cli for local validation
npm install -g ajv-cli

# Validate index.json against schema
ajv validate -s schema/plugin-entry.json -d index.json
```

Or simply let CI validate when you open the PR.

## Step 6: Open a pull request

```bash
git checkout -b add-my-plugin-name
git add index.json
git commit -m "Add my-plugin-name by your-org"
git push origin add-my-plugin-name

gh pr create \
  --title "Add: my-plugin-name" \
  --body "Plugin submission for my-plugin-name.

**What it does:** Brief description
**Source:** https://github.com/your-org/your-plugin-repo
**License:** MIT"
```

## Review process

1. CI validates your `index.json` entry against the schema automatically
2. A maintainer reviews the plugin source code and WASM bundle
3. We check for obvious security concerns (capability declarations, no obfuscated code)
4. If approved, your entry is merged and immediately available in the registry

Reviews typically take 3-5 business days.

## Updating a plugin

To update an existing entry (new version, changed URL, etc.):

1. Fork the repository
2. Update your plugin's entry in `index.json` — bump the `version` field to match your new WASM bundle
3. Open a PR with the changes

Maintainers will fast-track updates from existing verified authors.

## Removing a plugin

If you need to remove your plugin from the registry, open a PR that removes your entry from `index.json`. Include a brief reason in the PR description.

## Questions?

Open an issue in this repository or join the [StudioBrain Discord](https://studiobrain.ai/community).
