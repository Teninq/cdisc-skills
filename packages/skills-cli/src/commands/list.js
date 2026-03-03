"use strict";

const fs = require("node:fs");
const path = require("node:path");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function run(options = {}) {
  const repoRoot = options.repoRoot || path.resolve(__dirname, "..", "..", "..", "..");
  const indexPath = path.join(repoRoot, "skills", "INDEX.json");
  const data = readJson(indexPath);

  if (options.json) {
    process.stdout.write(`${JSON.stringify(data, null, 2)}\n`);
    return;
  }

  for (const skill of data.skills) {
    process.stdout.write(`- ${skill.name} (${skill.entry})\n`);
  }
}

module.exports = { run };
