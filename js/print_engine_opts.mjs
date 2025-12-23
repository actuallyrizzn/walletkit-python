import { ENGINE_RPC_OPTS } from "@walletconnect/sign-client";

const pick = (x) => ({ ttl: x.ttl, tag: x.tag, prompt: x.prompt });

console.log(
  JSON.stringify(
    {
      wc_sessionPropose: {
        req: pick(ENGINE_RPC_OPTS.wc_sessionPropose.req),
        res: pick(ENGINE_RPC_OPTS.wc_sessionPropose.res),
      },
      wc_sessionSettle: {
        req: pick(ENGINE_RPC_OPTS.wc_sessionSettle.req),
        res: pick(ENGINE_RPC_OPTS.wc_sessionSettle.res),
      },
      wc_sessionAuthenticate: {
        req: pick(ENGINE_RPC_OPTS.wc_sessionAuthenticate.req),
        res: pick(ENGINE_RPC_OPTS.wc_sessionAuthenticate.res),
      },
    },
    null,
    2,
  ),
);


