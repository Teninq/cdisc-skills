# CDISC Skills — Agent Context

This repository contains the CDISC skills package in the [agent-skills](https://github.com/vercel-labs/agent-skills) universal format.

## What this repo does

Provides AI agent skills for querying CDISC clinical data standards (SDTM, ADaM, CDASH, Controlled Terminology) from the CDISC Library API. Skills are distributed via `npx superpowers-skills install`.

## Repository structure

```
skills/cdisc/SKILL.md         ← skill instructions (readable by any agent)
skills/cdisc/metadata.json    ← machine-readable metadata
skills/INDEX.json             ← generated index of all skills
adapters/*/adapter.json       ← per-platform install config
packages/skills-cli/          ← npx CLI for installing skills
packages/skills-build/        ← build and validation tooling
schema/                       ← JSON schemas
scripts/                      ← Python CDISC Library API tool
```

## Skills are platform-agnostic

The `SKILL.md` files contain instructions that any LLM agent can read and follow. Platform differences (where skills are installed, how they are discovered) are handled by the CLI using `adapters/<target>/adapter.json`.

## Development commands

```bash
# Validate
node packages/skills-build/src/validate-skills.js

# Install to Claude
node packages/skills-cli/bin/skills.js install --target claude

# List available skills
node packages/skills-cli/bin/skills.js list

# Run tests
python -m pytest
```
