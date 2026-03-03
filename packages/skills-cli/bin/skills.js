#!/usr/bin/env node
"use strict";

const { run: runAdd } = require("../src/commands/add");
const { run: runInstall } = require("../src/commands/install");
const { run: runList } = require("../src/commands/list");
const { run: runValidate } = require("../src/commands/validate");
const { run: runSync } = require("../src/commands/sync");

function parseArgs(argv) {
  const args = argv.slice(2);
  const command = args[0] || "help";
  const rest = args.slice(1);

  const options = { json: false };
  const positionals = [];

  for (let index = 0; index < rest.length; index += 1) {
    const token = rest[index];
    if (token === "--json") {
      options.json = true;
      continue;
    }
    if (token === "--target") {
      options.target = rest[index + 1];
      index += 1;
      continue;
    }
    if (token === "--config-dir") {
      options.configDir = rest[index + 1];
      index += 1;
      continue;
    }
    positionals.push(token);
  }

  return { command, options, positionals };
}

function printHelp() {
  process.stdout.write("superpowers-skills commands:\n");
  process.stdout.write("  add <repo-or-package> [--json]\n");
  process.stdout.write("  install [--target <target>] [--config-dir <dir>] [--json]\n");
  process.stdout.write("  list [--json]\n");
  process.stdout.write("  validate [--target <target>] [--json]\n");
  process.stdout.write("  sync [--target <target>] [--config-dir <dir>] [--json]\n");
}

function main() {
  try {
    const { command, options, positionals } = parseArgs(process.argv);

    if (command === "add") {
      runAdd({ ...options, source: positionals[0] });
      return;
    }
    if (command === "install") {
      runInstall(options);
      return;
    }
    if (command === "list") {
      runList(options);
      return;
    }
    if (command === "validate") {
      runValidate(options);
      return;
    }
    if (command === "sync") {
      runSync(options);
      return;
    }

    printHelp();
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exit(1);
  }
}

main();
