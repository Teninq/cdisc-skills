---
name: cdisc
description: >-
  CDISC clinical data standards assistant. Queries SDTM/ADaM/CDASH/CT
  standard definitions from the CDISC Library API, and assists with clinical
  data programming. Triggers: user mentions CDISC, SDTM, ADaM, CDASH,
  controlled terminology, clinical trial data standards, domain variables,
  codelist, define.xml, or similar terms.
allowed-tools:
  - Bash
  - Read
---

# CDISC Standards Assistant

## Overview

You have two capabilities:

1. **Standard Queries** — Query the CDISC Library API for standard definitions (SDTM, ADaM, CDASH, Controlled Terminology) using the CLI tool.
2. **Programming Guidance** — Help write clinical data code (SAS, R, Python) using the reference guide and queried definitions.

## Prerequisites

- **Python 3.9+** must be available on the system.
- **CDISC API Key** — The user must have a CDISC Library API key set as the `CDISC_API_KEY` environment variable, or pass it via `--api-key`.

If the API key is not configured, instruct the user:
> Set your CDISC Library API key: `export CDISC_API_KEY="your-key-here"`
> Get a free key at https://www.cdisc.org/cdisc-library

## CLI Tool Reference

The query tool is located relative to this skill file:

```
{skill_directory}/../../scripts/cdisc_query.py
```

To find the absolute path, use the directory of this SKILL.md file and resolve `../../scripts/cdisc_query.py`.

### Subcommands

| Subcommand | Required Args | Description |
|------------|--------------|-------------|
| `products` | (none) | List all CDISC standards and their published versions |
| `sdtm-domains` | `--version` | List SDTM domains for a version |
| `sdtm-variables` | `--version --domain` | List variables for an SDTM domain |
| `sdtm-variable` | `--version --domain --variable` | Get a specific SDTM variable definition |
| `adam-structures` | `--version` | List ADaM data structures for a version |
| `adam-variable` | `--version --structure --variable` | Get a specific ADaM variable definition |
| `cdash-domains` | `--version` | List CDASH domains for a version |
| `cdash-fields` | `--version --domain` | List fields for a CDASH domain |
| `ct-packages` | (none) | List controlled terminology packages |
| `codelist` | `--package --codelist` | Get a codelist definition |
| `codelist-terms` | `--package --codelist` | List terms in a codelist |

### Version Format

Versions can use dots or dashes — both `3.4` and `3-4` are accepted. The tool auto-converts dots to dashes.

### Example Invocations

```bash
# Discover available standards and versions
python scripts/cdisc_query.py products

# List all SDTM-IG 3.4 domains
python scripts/cdisc_query.py sdtm-domains --version 3.4

# Get variables for the AE domain in SDTM 3.4
python scripts/cdisc_query.py sdtm-variables --version 3.4 --domain AE

# Get the full definition of AETERM
python scripts/cdisc_query.py sdtm-variable --version 3.4 --domain AE --variable AETERM

# List ADaM IG 1.3 data structures
python scripts/cdisc_query.py adam-structures --version 1.3

# Get a specific ADaM variable
python scripts/cdisc_query.py adam-variable --version 1.3 --structure ADSL --variable USUBJID

# List CDASH 2.0 domains
python scripts/cdisc_query.py cdash-domains --version 2.0

# List controlled terminology packages
python scripts/cdisc_query.py ct-packages

# Get a codelist definition
python scripts/cdisc_query.py codelist --package sdtmct-2024-03-29 --codelist C66781

# Get terms in a codelist
python scripts/cdisc_query.py codelist-terms --package sdtmct-2024-03-29 --codelist C66781
```

## Interpreting Results

- All output is **JSON**.
- Lists may be **truncated** — look for `"_truncated": true` and `"total_count"` in the last element.
- Top-level list responses are wrapped: `{"items": [...], "total_returned": N, "has_more": bool}`.
- HAL metadata (`_links`, `ordinal`) is automatically stripped from responses.

## Workflow Guidance

1. **Discover versions first** — If the user does not specify a version, run `products` to find available versions, then ask which one to use.
2. **Version comparison** — To compare two versions (e.g., SDTM 3.2 vs 3.4), query domains for both versions and diff the results.
3. **Always query definitions before generating code** — Do not rely on memory for variable names, types, or codelists. Query the API to get the authoritative definition.
4. **Domain and variable names are case-insensitive** — The tool auto-uppercases domain and variable arguments.

## Programming Reference

For CDISC data model knowledge and code patterns, refer to:

```
{skill_directory}/references/programming-guide.md
```

Read this file when you need to:
- Understand SDTM observation class hierarchy
- Know standard variable prefixes and key identifiers
- Generate SAS/R/Python code for clinical data tasks
- Understand ADaM derivation patterns
- Work with controlled terminology bindings
