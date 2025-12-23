import u from "@walletconnect/utils";

const keys = Object.keys(u)
  .filter((k) => /key|sym|shared|x25519|hkdf/i.test(k))
  .sort();
console.log(keys.join("\n"));


