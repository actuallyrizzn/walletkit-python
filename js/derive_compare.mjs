import fs from "node:fs";
import { deriveSymKey, hashKey } from "@walletconnect/utils";

const file = process.argv[2];
if (!file) {
  console.error("Usage: node js/derive_compare.mjs <vector.json>");
  process.exit(2);
}

const v = JSON.parse(fs.readFileSync(file, "utf-8"));
const a = deriveSymKey(v.privateA, v.publicB);
const b = deriveSymKey(v.privateB, v.publicA);
console.log(
  JSON.stringify(
    {
      symKeyA: a,
      symKeyB: b,
      topicA: hashKey(a),
      topicB: hashKey(b),
      equal: a === b,
    },
    null,
    2,
  ),
);


