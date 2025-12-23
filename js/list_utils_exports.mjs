import u from "@walletconnect/utils";

const keys = Object.keys(u).sort();
console.log(keys.filter((k) => k.toLowerCase().includes("format")).join("\n"));


