# CDISC Skills — Developer Context for Claude Code

This repo uses the [agent-skills](https://github.com/vercel-labs/agent-skills) universal format.

## Key directories

- `skills/cdisc/` — the CDISC skill (SKILL.md + metadata.json)
- `adapters/` — platform install config (one adapter.json per target)
- `packages/skills-build/` — build and validation scripts
- `packages/skills-cli/` — npx-installable CLI
- `schema/` — JSON schemas for skills and adapters
- `scripts/` — Python CLI tool for CDISC Library API queries

## Common tasks

**Rebuild the skills index:**
```bash
node packages/skills-build/src/build-index.js
```

**Validate all skills and adapters:**
```bash
node packages/skills-build/src/validate-skills.js
```

**Test CLI locally:**
```bash
node packages/skills-cli/bin/skills.js list
node packages/skills-cli/bin/skills.js install --target claude
```

**Run Python tests:**
```bash
python -m pytest
```

## Adding a new skill

1. Create `skills/<name>/SKILL.md` — the skill instructions (platform-agnostic)
2. Create `skills/<name>/metadata.json` — name, description, version, tags
3. Run `node packages/skills-build/src/build-index.js` to update `skills/INDEX.json`
4. Run `node packages/skills-build/src/validate-skills.js` to verify

## Platform adapters

Each adapter in `adapters/<target>/adapter.json` tells the CLI how to install skills for that platform (install path, link strategy, discovery pattern). The skills themselves are unchanged per platform.
