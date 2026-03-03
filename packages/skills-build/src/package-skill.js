#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");

function main() {
  const repoRoot = path.resolve(__dirname, "..", "..", "..");
  const distDir = path.join(repoRoot, "dist", "skills");

  if (!fs.existsSync(distDir)) {
    process.stderr.write("dist/skills does not exist. Run build first.\n");
    process.exit(1);
  }

  const packagedSkills = fs
    .readdirSync(distDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();

  process.stdout.write(`Packaging check complete for ${packagedSkills.length} skill(s).\n`);
  process.stdout.write(`${JSON.stringify({ skills: packagedSkills }, null, 2)}\n`);
}

main();
