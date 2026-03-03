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

function validateMetadataShape(metadata, metadataPath) {
  assert(typeof metadata === "object" && metadata, `Metadata must be an object: ${metadataPath}`);
  assert(typeof metadata.name === "string" && metadata.name.length > 0, `Metadata name missing: ${metadataPath}`);
  assert(typeof metadata.version === "string" && metadata.version.length > 0, `Metadata version missing: ${metadataPath}`);
}

function listSkillDirs(skillsDir) {
  if (!fs.existsSync(skillsDir)) {
    return [];
  }

  return fs
    .readdirSync(skillsDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
}

function buildIndex(repoRoot) {
  const skillsDir = path.join(repoRoot, "skills");
  const skillNames = listSkillDirs(skillsDir);

  const skills = skillNames
    .map((name) => {
      const skillPath = path.join(skillsDir, name);
      const metadataPath = path.join(skillPath, "metadata.json");
      const entryPath = path.join(skillPath, "SKILL.md");
      if (!fs.existsSync(metadataPath) || !fs.existsSync(entryPath)) {
        return null;
      }
      const metadata = readJson(metadataPath);
      validateMetadataShape(metadata, metadataPath);
      return {
        name: metadata.name,
        path: `skills/${name}`,
        entry: `skills/${name}/SKILL.md`,
        metadata: `skills/${name}/metadata.json`,
      };
    })
    .filter(Boolean);

  return {
    schemaVersion: "1.0.0",
    generatedAt: new Date().toISOString(),
    skills,
  };
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function writeJson(filePath, data) {
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
}

function copyDir(sourceDir, destDir) {
  ensureDir(destDir);
  const entries = fs.readdirSync(sourceDir, { withFileTypes: true });

  for (const entry of entries) {
    const src = path.join(sourceDir, entry.name);
    const dst = path.join(destDir, entry.name);

    if (entry.isDirectory()) {
      copyDir(src, dst);
      continue;
    }

    fs.copyFileSync(src, dst);
  }
}

function buildDist(repoRoot, indexData) {
  const distDir = path.join(repoRoot, "dist");
  const distSkillsDir = path.join(distDir, "skills");

  ensureDir(distSkillsDir);
  writeJson(path.join(distDir, "skills-index.json"), indexData);

  for (const skill of indexData.skills) {
    const src = path.join(repoRoot, skill.path);
    const dst = path.join(distSkillsDir, skill.name);
    copyDir(src, dst);
  }
}

function main() {
  try {
    const repoRoot = path.resolve(__dirname, "..", "..", "..");
    const indexData = buildIndex(repoRoot);

    writeJson(path.join(repoRoot, "skills", "INDEX.json"), indexData);
    buildDist(repoRoot, indexData);

    process.stdout.write(`Built ${indexData.skills.length} skills.\n`);
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exit(1);
  }
}

main();
