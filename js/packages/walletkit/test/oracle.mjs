import { Core, RELAYER_EVENTS } from "@walletconnect/core";
import { SignClient } from "@walletconnect/sign-client";
import { WalletKit } from "../src/index.ts";
import { Wallet as CryptoWallet } from "@ethersproject/wallet";

const TEST_METADATA = {
  name: "Oracle",
  description: "Oracle",
  url: "https://example.org",
  icons: [],
};

function logRelayer(core, label) {
  // Log raw relayer events so we can see tags + payload shapes the official SDK uses.
  core.relayer.on(RELAYER_EVENTS.message, (event) => {
    const { topic, message } = event;
    console.log(`[${label}] relayer_message topic=${topic} msgLen=${(message || "").length}`);
  });
  core.relayer.on(RELAYER_EVENTS.publish, (event) => {
    // NOTE: publish event in core includes request/opts in v2; log best-effort
    console.log(`[${label}] relayer_publish`, JSON.stringify(event).slice(0, 1200));
  });
}

async function main() {
  const projectId = process.env.WC_PROJECT_ID;
  if (!projectId) {
    console.error("Set WC_PROJECT_ID in container env (any valid projectId).");
    process.exit(2);
  }
  const relayUrl = process.env.WC_RELAY_URL;

  const walletEth = CryptoWallet.createRandom();

  const dapp = await SignClient.init({
    projectId,
    relayUrl,
    name: "Dapp",
    metadata: TEST_METADATA,
  });

  const walletCore = new Core({ projectId, relayUrl });
  const walletkit = await WalletKit.init({
    core: walletCore,
    name: "wallet",
    metadata: TEST_METADATA,
    signConfig: { disableRequestQueue: true },
  });

  logRelayer(dapp.core, "DAPP");
  logRelayer(walletkit.core, "WALLET");

  walletkit.on("session_proposal", async (proposal) => {
    console.log("[WALLET] session_proposal", JSON.stringify({ id: proposal.id }).slice(0, 300));
    await walletkit.approveSession({ id: proposal.id, namespaces: proposal.params.requiredNamespaces });
  });

  walletkit.on("session_authenticate", async (payload) => {
    console.log("[WALLET] session_authenticate", JSON.stringify({ id: payload.id }).slice(0, 300));
    // minimal approve: sign chain[0]
    const chain = payload.params.authPayload.chains[0];
    const iss = `${chain}:${walletEth.address}`;
    const message = walletkit.formatAuthMessage({ request: payload.params.authPayload, iss });
    const sig = await walletEth.signMessage(message);
    const auth = {
      h: { t: "caip122" },
      p: { ...payload.params.authPayload, iss: `did:pkh:${iss}` },
      s: { t: "eip191", s: sig },
    };
    await walletkit.approveSessionAuthenticate({ id: payload.id, auths: [auth] });
  });

  // Use authenticate flow (matches the reference tests under "Sign 2.5")
  const { uri, response } = await dapp.authenticate({
    chains: ["eip155:1", "eip155:2"],
    domain: "localhost",
    nonce: "1",
    uri: "aud",
    methods: ["personal_sign"],
    resources: [],
  });
  if (!uri) throw new Error("No URI from dapp.authenticate");

  await walletkit.pair({ uri });
  // Wait for dapp side response to complete (it should resolve if auth approved)
  try {
    await response();
    console.log("[DAPP] authenticate response resolved");
  } catch (e) {
    console.log("[DAPP] authenticate response errored", e?.message || e);
  }

  // Give a bit of time for exchanges + prints
  await new Promise((r) => setTimeout(r, 5000));
  await dapp.disconnect({ topic: Object.values(dapp.session.getAll() || {})[0]?.topic, reason: { code: 6000, message: "done" } }).catch(() => {});
  process.exit(0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});


