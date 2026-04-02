# StudioBrain Community Plugins

This repository is the official registry for community-submitted plugins for [StudioBrain](https://studiobrain.ai). Community plugins are distributed as WebAssembly (WASM) bundles and work across all StudioBrain editions (core, desktop, cloud).

## How Community Plugins Work

StudioBrain loads plugins at runtime from the registry index. Each plugin entry in `index.json` points to a WASM bundle hosted in the plugin author's own repository. The core runtime downloads, sandboxes, and executes the WASM bundle — no server-side code is ever trusted or executed.

### What community plugins can do

- Add custom entity types and field renderers
- Register asset importers and exporters
- Provide custom UI panels via the plugin host API
- Define workflow steps and automation triggers

### What community plugins cannot do

- Access the filesystem directly (all I/O goes through the plugin host API)
- Make arbitrary network requests (requires declared capabilities)
- Run native code — WASM only, no native addons

## Submission Process

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full step-by-step guide.

At a high level:

1. Build your plugin as a WASM bundle using the StudioBrain Plugin SDK
2. Host the bundle somewhere publicly accessible (GitHub Releases, CDN, etc.)
3. Fork this repository
4. Add your plugin entry to `index.json` following the schema in `schema/plugin-entry.json`
5. Open a pull request — CI will validate your entry automatically
6. A maintainer will review and merge

## Requirements

- Plugin must be open source (MIT, Apache 2.0, or similar permissive license)
- WASM bundle must be publicly hosted with a stable URL
- Plugin must target `min_version` of StudioBrain 0.1.0 or later
- Plugin ID must be globally unique (namespaced as `author-slug-plugin-name` is recommended)

## Registry Index

`index.json` contains all registered community plugins. It is updated automatically when PRs are merged. Do not edit it manually outside of the plugin submission PR workflow.

## License

The registry infrastructure (this repository) is licensed under MIT. Individual plugins retain their own licenses as declared in each entry's `license` field.

## Creating the GitHub repository

When you are ready to push this to GitHub, run the following from `/opt/studiobrain-dev/community-plugins/`:

```bash
gh repo create BiloxiStudios/studiobrain-community-plugins \
  --public \
  --description "Official community plugin registry for StudioBrain — WASM plugins submitted via PR" \
  --homepage "https://studiobrain.ai" \
  --source . \
  --remote origin \
  --push
```

This will:
1. Create the public repo under the BiloxiStudios org
2. Set it as the `origin` remote
3. Push the initial commit

After creation, enable branch protection on `main` (require PR + passing CI before merge).
