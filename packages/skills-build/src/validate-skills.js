#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");

function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    throw new Error(`Failed to read JSON at ${filePath}: ${error.message}`);
  }
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function validateIndex(index) {
  assert(typeof index === "object" && index, "skills/INDEX.json must be an object");
  assert(typeof index.schemaVersion === "string" && index.schemaVersion.length > 0, "INDEX schemaVersion missing");
  assert(typeof index.generatedAt === "string" && index.generatedAt.length > 0, "INDEX generatedAt missing");
  assert(Array.isArray(index.skills), "INDEX skills must be an array");

  for (const skill of index.skills) {
    assert(typeof skill.name === "string" && skill.name.length > 0, "INDEX entry missing name");
    assert(typeof skill.path === "string" && skill.path.length > 0, `INDEX ${skill.name} missing path`);
    assert(typeof skill.entry === "string" && skill.entry.length > 0, `INDEX ${skill.name} missing entry`);
    assert(typeof skill.metadata === "string" && skill.metadata.length > 0, `INDEX ${skill.name} missing metadata`);
  }
}

function validateMetadata(repoRoot, index) {
  for (const skill of index.skills) {
    const metadataPath = path.join(repoRoot, skill.metadata);
    const entryPath = path.join(repoRoot, skill.entry);

    assert(fs.existsSync(metadataPath), `Missing metadata file: ${skill.metadata}`);
    assert(fs.existsSync(entryPath), `Missing entry file: ${skill.entry}`);

    const metadata = readJson(metadataPath);
    assert(metadata.name === skill.name, `Metadata name mismatch in ${skill.metadata}`);
    assert(typeof metadata.version === "string" && metadata.version.length > 0, `Missing version in ${skill.metadata}`);
    assert(Array.isArray(metadata.compatibleTargets), `Missing compatibleTargets in ${skill.metadata}`);
  }
}

function validateAdapters(repoRoot) {
  const adaptersRoot = path.join(repoRoot, "adapters");
  if (!fs.existsSync(adaptersRoot)) {
    return;
  }

  const targetDirs = fs.readdirSync(adaptersRoot, { withFileTypes: true }).filter((entry) => entry.isDirectory());
  for (const target of targetDirs) {
    const adapterPath = path.join(adaptersRoot, target.name, "adapter.json");
    assert(fs.existsSync(adapterPath), `Missing adapter manifest: adapters/${target.name}/adapter.json`);
    const adapter = readJson(adapterPath);
    assert(adapter.target === target.name, `Adapter target mismatch in ${adapterPath}`);
  }
}

function run(options = {}) {
  const repoRoot = options.repoRoot || path.resolve(__dirname, "..", "..", "..");
  try {
    const indexPath = path.join(repoRoot, "skills", "INDEX.json");
    assert(fs.existsSync(indexPath), "skills/INDEX.json is missing");

    const index = readJson(indexPath);
    validateIndex(index);
    validateMetadata(repoRoot, index);
    validateAdapters(repoRoot);

    const message = "Skills validation passed.";
    if (!options.silent) {
      process.stdout.write(`${message}\n`);
    }
    return { ok: true, message };
  } catch (error) {
    const message = error.message;
    if (!options.silent) {
      process.stderr.write(`${message}\n`);
    }
    if (options.throwOnError) {
      throw error;
    }
    return { ok: false, message };
  }
}

function main() {
  const result = run();
  if (!result.ok) {
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { run };
