import fs from "node:fs";
import process from "node:process";
import { decrypt } from "@walletconnect/utils";

function usage() {
  console.error("Usage: node js/decode_capture.mjs <capture.jsonl>");
  process.exit(2);
}

const file = process.argv[2];
if (!file) usage();

const lines = fs.readFileSync(file, "utf-8").split(/\r?\n/).filter(Boolean);
for (const line of lines) {
  const rec = JSON.parse(line);
  const kind = rec.kind;
  const encoded = rec.encoded;
  const symKey = rec.sym_key;
  if (!encoded || !symKey) {
    console.log(`[SKIP] ${kind} missing encoded/sym_key`);
    continue;
  }
  try {
    // WalletConnect uses base64url encoding on the wire by default.
    const msg = decrypt({ symKey, encoded, encoding: "base64url" });
    const json = JSON.parse(msg);
    console.log(`[OK] ${kind} topic=${rec.pairing_topic || rec.session_topic || rec.response_topic || "?"}`);
    console.log(JSON.stringify(json).slice(0, 1200));
  } catch (e) {
    console.log(`[FAIL] ${kind} err=${e?.message || e}`);
  }
}


