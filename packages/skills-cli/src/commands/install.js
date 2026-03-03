"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { getPlatform } = require("../platforms");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function expandHome(input) {
  if (!input.startsWith("~")) {
    return input;
  }
  const home = process.env.USERPROFILE || process.env.HOME;
  return path.join(home, input.slice(1));
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function copyDir(sourceDir, targetDir) {
  ensureDir(targetDir);
  const entries = fs.readdirSync(sourceDir, { withFileTypes: true });

  for (const entry of entries) {
    const src = path.join(sourceDir, entry.name);
    const dst = path.join(targetDir, entry.name);

    if (entry.isDirectory()) {
      copyDir(src, dst);
      continue;
    }

    fs.copyFileSync(src, dst);
  }
}

function run(options = {}) {
  const target = options.target || "claude";
  const platform = getPlatform(target);
  const repoRoot = options.repoRoot || path.resolve(__dirname, "..", "..", "..", "..");
  const index = readJson(path.join(repoRoot, "skills", "INDEX.json"));

  const baseDir = expandHome(options.configDir || platform.defaultDir);
  ensureDir(baseDir);

  const installed = [];
  for (const skill of index.skills) {
    const src = path.join(repoRoot, skill.path);
    const dst = path.join(baseDir, skill.name);
    copyDir(src, dst);
    installed.push({ name: skill.name, path: dst });
  }

  const payload = { action: "install", target, baseDir, installed };
  if (options.json) {
    process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
    return;
  }

  process.stdout.write(`Installed ${installed.length} skill(s) to ${baseDir}\n`);
}

module.exports = { run };
