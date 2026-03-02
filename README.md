# CDISC Claude Code Plugin

A Claude Code plugin for querying CDISC clinical data standards (SDTM, ADaM, CDASH, Controlled Terminology) directly from the CDISC Library API.

## Installation

### Via Claude Code Plugin System

```bash
claude plugin add <git-url>
```

### Manual Installation

Clone the repository into your Claude Code plugins directory:

```bash
git clone <git-url> ~/.claude/plugins/cdisc-plugin
```

## API Key Setup

This plugin requires a CDISC Library API key.

1. **Obtain a key** — Register for free at [cdisc.org/cdisc-library](https://www.cdisc.org/cdisc-library).
2. **Set the environment variable:**

```bash
export CDISC_API_KEY="your-api-key-here"
```

Add this to your shell profile (`~/.zshrc`, `~/.bashrc`, etc.) for persistence.

Alternatively, pass the key directly when using the CLI tool:

```bash
python scripts/cdisc_query.py --api-key "your-key" products
```

## Verify Installation

After installing, ask Claude Code:

> "Show me the available CDISC standards and versions"

Claude should invoke the CDISC skill and return a list of standards from the API.

## Usage Examples

Once the plugin is installed and the API key is set, ask Claude naturally:

- "What domains are available in SDTM-IG 3.4?"
- "Show me the AE domain variables in SDTM 3.4"
- "What is the definition of AETERM in SDTM?"
- "Compare SDTM 3.2 and 3.4 domains"
- "List the ADaM data structures in version 1.3"
- "Show me the AGEU codelist terms"
- "Write SAS code to create an ADAE dataset"

## Plugin Architecture

This plugin is designed to host multiple skills. Currently available:

| Skill | Description |
|-------|-------------|
| `cdisc` | CDISC Library API queries and clinical data programming assistance |

Future skills will be added to the `skills/` directory. Each skill has its own `SKILL.md` entry point and supporting reference files.

## CLI Tool

The underlying query tool can also be used standalone:

```bash
python scripts/cdisc_query.py --help
python scripts/cdisc_query.py products
python scripts/cdisc_query.py sdtm-domains --version 3.4
python scripts/cdisc_query.py sdtm-variable --version 3.4 --domain AE --variable AETERM
```

All output is JSON. The tool has zero external dependencies (Python 3.9+ stdlib only).

## Requirements

- Python 3.9+
- CDISC Library API key

## License

MIT
