"use strict";

const claude = require("./claude");
const cursor = require("./cursor");
const opencode = require("./opencode");
const codex = require("./codex");
const generic = require("./generic");

const platformMap = {
  [claude.target]: claude,
  [cursor.target]: cursor,
  [opencode.target]: opencode,
  [codex.target]: codex,
  [generic.target]: generic,
};

function getPlatform(target) {
  const platform = platformMap[target];
  if (!platform) {
    throw new Error(`Unknown target '${target}'. Expected one of: ${Object.keys(platformMap).join(", ")}`);
  }
  return platform;
}

function listTargets() {
  return Object.keys(platformMap).sort();
}

module.exports = {
  getPlatform,
  listTargets,
};
