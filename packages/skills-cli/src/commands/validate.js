"use strict";

const { run: runBuildValidate } = require("../../../../packages/skills-build/src/validate-skills");

function run(options = {}) {
  const result = runBuildValidate({ silent: true, throwOnError: false });
  const payload = {
    action: "validate",
    target: options.target || "claude",
    ok: result.ok,
    message: result.message,
  };

  if (options.json) {
    process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
    return;
  }

  process.stdout.write(`${payload.message}\n`);
}

module.exports = { run };
