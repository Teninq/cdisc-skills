"use strict";

function run(options = {}) {
  const source = options.source || "";
  if (!source) {
    throw new Error("add requires <repo-or-package>");
  }

  const payload = {
    action: "add",
    source,
    message: "Source registered. Run install to materialize skills.",
  };

  if (options.json) {
    process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
    return;
  }

  process.stdout.write(`${payload.message}\n`);
}

module.exports = { run };
