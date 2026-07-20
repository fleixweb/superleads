#!/usr/bin/env node
// Optional Codex update notice. Delete hooks.json to disable it.
// This performs one public GET, writes nothing, and exits silently on failure.

import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const VERSION_RE = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;
const REMOTE_MANIFEST =
  "https://raw.githubusercontent.com/fleixweb/superleads/master/.codex-plugin/plugin.json";
const DISABLED_VALUES = new Set(["1", "true", "yes", "on"]);

function isDisabled(name) {
  return DISABLED_VALUES.has((process.env[name] || "").trim().toLowerCase());
}

function readVersion(jsonPath) {
  const version = JSON.parse(readFileSync(jsonPath, "utf8")).version;
  return typeof version === "string" && VERSION_RE.test(version) ? version : null;
}

function isNewer(remote, local) {
  const remoteParts = remote.split(".").map(Number);
  const localParts = local.split(".").map(Number);

  for (let index = 0; index < remoteParts.length; index += 1) {
    if (remoteParts[index] !== localParts[index]) {
      return remoteParts[index] > localParts[index];
    }
  }
  return false;
}

function fetchManifest() {
  return execFileSync(
    "curl",
    ["--fail", "--silent", "--show-error", "--max-time", "3", REMOTE_MANIFEST],
    {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      timeout: 3500,
      windowsHide: true,
    },
  );
}

async function main() {
  if (isDisabled("SUPERLEADS_DISABLE_UPDATE_CHECK") || isDisabled("DISABLE_TELEMETRY")) {
    return;
  }

  const scriptDir = path.dirname(fileURLToPath(import.meta.url));
  const localVersion = readVersion(path.resolve(scriptDir, "..", ".codex-plugin", "plugin.json"));
  if (!localVersion) {
    return;
  }

  const remoteVersion = readVersionFromText(fetchManifest());
  if (remoteVersion && isNewer(remoteVersion, localVersion)) {
    process.stdout.write(`Superleads ${remoteVersion} 可用（你在 ${localVersion}）-> 见 CHANGELOG\n`);
  }
}

function readVersionFromText(text) {
  const version = JSON.parse(text).version;
  return typeof version === "string" && VERSION_RE.test(version) ? version : null;
}

main().catch(() => {});
