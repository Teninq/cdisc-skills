# CDISC Skills (Universal Agent Format)

A universal skills package for querying CDISC clinical data standards (SDTM, ADaM, CDASH, Controlled Terminology) directly from the CDISC Library API. Works with any AI agent that supports the [agent-skills](https://github.com/vercel-labs/agent-skills) format.

## Installation

### Recommended (npx)

```bash
npx superpowers-skills install --target claude
```

Other targets:

```bash
npx superpowers-skills install --target cursor
npx superpowers-skills install --target opencode
npx superpowers-skills install --target codex
npx superpowers-skills install --target generic
```

`install` is idempotent — safe to re-run to self-heal.

### Uninstall

Delete the target directory installed by your adapter. For Claude:

```bash
rm -rf ~/.claude/skills/cdisc
```

## Repository Layout

This repository follows the [agent-skills](https://github.com/vercel-labs/agent-skills) universal layout:

```
skills/
  cdisc/
    SKILL.md          ← skill entry point (platform-agnostic)
    metadata.json     ← machine-readable metadata
skills/INDEX.json     ← generated index
adapters/
  claude/adapter.json
  cursor/adapter.json
  opencode/adapter.json
  codex/adapter.json
packages/
  skills-build/       ← build + validate tools
  skills-cli/         ← npx CLI
schema/               ← JSON schemas
```

## Development

### Build and validate

```bash
node packages/skills-build/src/build-index.js
node packages/skills-build/src/validate-skills.js
```

Or via npm:

```bash
npm run validate:skills
```

### CLI (local)

```bash
node packages/skills-cli/bin/skills.js list
node packages/skills-cli/bin/skills.js install --target claude
node packages/skills-cli/bin/skills.js validate --target claude
node packages/skills-cli/bin/skills.js sync --target claude
```

JSON output for automation:

```bash
node packages/skills-cli/bin/skills.js install --target claude --json
```

### Run tests

```bash
python -m pytest
```

## API Key Setup

This skill requires a CDISC Library API key.

1. **Obtain a key** — Register for free at [cdisc.org/cdisc-library](https://www.cdisc.org/cdisc-library).
2. **Set the environment variable:**

```bash
export CDISC_API_KEY="your-api-key-here"
```

Add this to your shell profile (`~/.zshrc`, `~/.bashrc`, etc.) for persistence.

## Usage

Once installed and the API key is set, ask your agent:

- "What domains are available in SDTM-IG 3.4?"
- "Show me the AE domain variables in SDTM 3.4"
- "What is the definition of AETERM in SDTM?"
- "Compare SDTM 3.2 and 3.4 domains"
- "List the ADaM data structures in version 1.3"
- "Show me the AGEU codelist terms"
- "Write SAS code to create an ADAE dataset"

## Available Skills

| Skill | Description |
|-------|-------------|
| `cdisc` | CDISC Library API queries and clinical data programming assistance |

## CLI Tool (standalone)

The underlying query tool can also be used standalone:

```bash
python scripts/cdisc_query.py --help
python scripts/cdisc_query.py products
python scripts/cdisc_query.py sdtm-domains --version 3.4
python scripts/cdisc_query.py sdtm-variable --version 3.4 --domain AE --variable AETERM
```

All output is JSON. Zero external dependencies (Python 3.9+ stdlib only).

## Requirements

- Node.js 18+ (for CLI)
- Python 3.9+ (for query tool)
- CDISC Library API key

## License

MIT
