// Polkadot.js extension helpers — optional wallet connect for demo (finalize uses backend signer)

const WS_URL = process.env.NEXT_PUBLIC_PORTALDOT_WS || "ws://127.0.0.1:9944";

export type ExtensionConnectResult =
  | { ok: true; address: string; accounts: { address: string; name?: string }[] }
  | { ok: false; code: "no_extension" | "denied" | "no_accounts"; message: string };

export async function connectExtension(appName = "Sentinel Treasury"): Promise<ExtensionConnectResult> {
  if (typeof window === "undefined") {
    return { ok: false, code: "no_extension", message: "Extension connect runs in the browser only." };
  }

  const { web3Enable, web3Accounts, isWeb3Injected } = await import("@polkadot/extension-dapp");

  if (!isWeb3Injected) {
    return {
      ok: false,
      code: "no_extension",
      message:
        "Polkadot.js extension not detected. Install it from https://polkadot.js.org/extension/ then refresh.",
    };
  }

  const extensions = await web3Enable(appName);
  if (extensions.length === 0) {
    return {
      ok: false,
      code: "denied",
      message: "Extension access denied. Click the Polkadot.js icon and allow this site, then retry.",
    };
  }

  const accounts = await web3Accounts();
  if (accounts.length === 0) {
    return {
      ok: false,
      code: "no_accounts",
      message:
        "No accounts in Polkadot.js. Open the extension → + → Create new account (or import //Bob dev seed for demo).",
    };
  }

  return {
    ok: true,
    address: accounts[0].address,
    accounts: accounts.map((a) => ({ address: a.address, name: a.meta.name })),
  };
}

export async function getApi() {
  const { ApiPromise, WsProvider } = await import("@polkadot/api");
  const provider = new WsProvider(WS_URL);
  return ApiPromise.create({ provider });
}

export { WS_URL };
