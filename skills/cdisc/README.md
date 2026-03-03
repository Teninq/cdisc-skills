# cdisc skill

This directory follows the universal skills package layout:

- `SKILL.md`: skill entry point with frontmatter (`name`, `description`)
- `metadata.json`: machine-readable metadata for indexing and validation
- `references/`: supporting domain guidance used by the skill

Use the repository CLI for install and validation:

- `npx superpowers-skills install --target claude`
- `npx superpowers-skills validate --target claude`
