import fs from "node:fs";
import { formatMessage } from "@walletconnect/utils";

const file = process.argv[2];
if (!file) {
  console.error("Usage: node js/compare_authmsg.mjs <authmsg_capture.json>");
  process.exit(2);
}

const cap = JSON.parse(fs.readFileSync(file, "utf-8"));
const request = cap.request;
const iss = cap.iss;
const py = cap.python_message;

// WalletConnect canonical signature: formatMessage(requestParams, iss)
// where iss is e.g. "did:pkh:eip155:1:0x..." OR "eip155:1:0x..."
const msg = formatMessage(request, iss);

console.log("=== JS formatMessage ===");
console.log(msg);
console.log("\n=== Python format_auth_message ===");
console.log(py);
console.log("\n=== Equal? ===");
console.log(msg === py);


