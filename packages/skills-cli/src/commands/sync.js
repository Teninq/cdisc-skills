"use strict";

const { run: runInstall } = require("./install");

function run(options = {}) {
  runInstall(options);
}

module.exports = { run };
