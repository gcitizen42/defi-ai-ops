// Unified DKG CLI:
//   - History scan using provider.getLogs (works on RPCs with eth_newFilter disabled)
//   - Live polling using provider.getLogs (no filters API)
//   - Optional per-member leaderboard
//
// Usage:
//   RPC_URL=<https url> npm run dkg -- history \
//     --registry=0x46d52E41C2F300BC82217Ce22b920c34995204eb \
//     --from=20929658 --to=23557658 --batch=4000 --out=out --leaderboard
//
//   RPC_URL=<https url> npm run dkg -- live \
//     --registry=0x46d52E41C2F300BC82217Ce22b920c34995204eb \
//     [--interval=5000] [--confirmations=1]
//
// Output files (history):
//   out/dkg_results_summary.json  (per-round details)
//   out/dkg_results_summary.csv   (overview per round)
//   out/member_stats.{json,csv}   (if --leaderboard)

import "dotenv/config";
import { JsonRpcProvider, Interface, Log } from "ethers";
import fs from "node:fs/promises";
import path from "node:path";

type Args = Record<string, string | boolean>;
const argv = process.argv.slice(2);
const cmdArg = argv[0]?.startsWith("--") ? "" : (argv.shift() ?? "");
const args: Args = Object.fromEntries(
  argv.map((p) => {
    const [k, v] = p.startsWith("--")
      ? p.replace(/^--/, "").split("=")
      : [p, true];
    return [k, v ?? true];
  })
);

const cmd = cmdArg.toLowerCase();

function req(k: string): string {
  const v = (args[k] as string) ?? "";
  if (!v) throw new Error(`Missing --${k}`);
  return v;
}
function optNum(k: string, d: number): number {
  const v = args[k];
  if (v === undefined || v === true) return d;
  const n = Number(v);
  return Number.isFinite(n) ? n : d;
}
function optStr(k: string, d: string): string {
  const v = args[k];
  if (v === undefined || v === true) return d;
  return String(v);
}
function has(k: string): boolean {
  const v = args[k];
  if (v === undefined) return false;
  if (v === true) return true;
  if (typeof v === "string") {
    const normalized = v.toLowerCase();
    return normalized !== "false" && normalized !== "0" && normalized !== "";
  }
  return Boolean(v);
}

// Only the event we need
const walletRegistryAbi = [
  {
    type: "event",
    name: "DkgResultSubmitted",
    inputs: [
      { name: "resultHash", type: "bytes32", indexed: true },
      { name: "seed", type: "uint256", indexed: false },
      {
        name: "result",
        type: "tuple",
        indexed: false,
        components: [
          { name: "submitterMemberIndex", type: "uint256" },
          { name: "groupPubKey", type: "bytes" },
          { name: "misbehavedMembersIndices", type: "uint8[]" },
          { name: "signatures", type: "bytes" },
          { name: "signingMembersIndices", type: "uint256[]" },
          { name: "members", type: "uint32[]" },
          { name: "membersHash", type: "bytes32" },
        ],
      },
    ],
    anonymous: false,
  },
] as const;

const TOPIC_DKG =
  "0x8e7fd4293d7db11807147d8890c287fad3396fbb09a4e92273fc7856076c153a";
const iface = new Interface(walletRegistryAbi);

const RPC_URL = process.env.RPC_URL;
let provider: JsonRpcProvider | undefined;

function getProvider(): JsonRpcProvider {
  if (!RPC_URL) {
    throw new Error("RPC_URL env var is required (https RPC endpoint).");
  }
  if (!provider) {
    provider = new JsonRpcProvider(RPC_URL);
  }
  return provider;
}

type Round = {
  block: number;
  tx: string;
  logIndex: number;
  resultHash: string;
  groupPubKey: string;
  submitterMemberIndex: number;
  seed: string;
  members: number[];
  signers: number[];
  misbehaved: number[];
  absent: number[];
};

function decodeRound(log: Log): Round | null {
  try {
    const parsed = iface.parseLog(log);
    if (parsed?.name !== "DkgResultSubmitted") return null;

    const resultHash = parsed.args.resultHash as string;
    const seed = parsed.args.seed.toString();
    const r = parsed.args.result;

    const submitterMemberIndex = Number(r.submitterMemberIndex);
    const groupPubKey = r.groupPubKey as string;
    const members: number[] = (r.members as bigint[]).map(Number);
    const signIdx: number[] = (r.signingMembersIndices as bigint[]).map(Number);
    const misIdx: number[] = (r.misbehavedMembersIndices as number[]).map(Number);

    // Map 1-based indices to actual member ids (members array)
    const toMemberId = (i: number) => members[i - 1];

    const signers = [...new Set(signIdx.map(toMemberId))].filter(
      (x) => x !== undefined
    );
    const misbehaved = [...new Set(misIdx.map(toMemberId))].filter(
      (x) => x !== undefined
    );
    const absent = members.filter(
      (m) => !signers.includes(m) && !misbehaved.includes(m)
    );

    return {
      block: Number(log.blockNumber),
      tx: log.transactionHash,
      logIndex: Number(log.logIndex),
      resultHash,
      groupPubKey,
      submitterMemberIndex,
      seed,
      members,
      signers,
      misbehaved,
      absent,
    };
  } catch {
    // swallow malformed/unknown logs; avoid BUFFER_OVERRUN or null-name parse explosions
    return null;
  }
}

async function ensureDir(dir: string) {
  await fs.mkdir(dir, { recursive: true }).catch(() => {});
}

function toCSV(rows: any[], header?: string[]): string {
  if (!rows.length) return (header || []).join(",") + "\n";
  const cols = header || Object.keys(rows[0]);
  const esc = (v: any) => {
    const s =
      v == null
        ? ""
        : Array.isArray(v)
        ? v.join("|")
        : typeof v === "object"
        ? JSON.stringify(v)
        : String(v);
    return s.includes(",") || s.includes("\n") ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [cols.join(","), ...rows.map((r) => cols.map((c) => esc(r[c])).join(","))].join(
    "\n"
  );
}

type RoundRow = {
  block: number;
  tx: string;
  resultHash: string;
  members: number;
  signers: number;
  misbehaved: number;
  absent: number;
};

async function history() {
  const registry = req("registry").toLowerCase();
  const fromBlock = Number(req("from"));
  const toBlock = Number(req("to"));
  const batch = optNum("batch", 4000);
  const outBase = optStr("out", "out");
  const provider = getProvider();

  if (!Number.isFinite(fromBlock) || !Number.isFinite(toBlock)) {
    throw new Error("--from and --to must be valid numbers");
  }
  if (fromBlock > toBlock) {
    throw new Error("--from cannot be greater than --to");
  }
  if (!Number.isFinite(batch) || batch <= 0) {
    throw new Error("--batch must be a positive number");
  }

  const outDir = path.resolve(outBase);
  await ensureDir(outDir);

  console.log(
    `Scanning ${registry} from ${fromBlock} to ${toBlock} in batches of ${batch}`
  );

  const rounds: Round[] = [];

  for (let start = fromBlock; start <= toBlock; start += batch) {
    const end = Math.min(start + batch - 1, toBlock);
    console.log(`getLogs ${start}-${end}`);

    const logs = await provider.getLogs({
      address: registry,
      fromBlock: start,
      toBlock: end,
      topics: [TOPIC_DKG],
    });

    for (const log of logs) {
      const round = decodeRound(log);
      if (!round) continue;
      console.log(
        `[${round.block}] ${round.resultHash} members=${round.members.length} signers=${round.signers.length} mis=${round.misbehaved.length} absent=${round.absent.length}`
      );
      rounds.push(round);
    }
  }

  await fs.writeFile(
    path.join(outDir, "dkg_results_summary.json"),
    JSON.stringify(rounds, null, 2),
    "utf8"
  );

  const csvRows: RoundRow[] = rounds.map((r) => ({
    block: r.block,
    tx: r.tx,
    resultHash: r.resultHash,
    members: r.members.length,
    signers: r.signers.length,
    misbehaved: r.misbehaved.length,
    absent: r.absent.length,
  }));
  await fs.writeFile(
    path.join(outDir, "dkg_results_summary.csv"),
    toCSV(csvRows, ["block", "tx", "resultHash", "members", "signers", "misbehaved", "absent"]),
    "utf8"
  );

  if (has("leaderboard")) {
    const stats = new Map<
      number,
      { seen: number; signed: number; mis: number; absent: number }
    >();
    for (const r of rounds) {
      for (const m of r.members) {
        if (!stats.has(m)) stats.set(m, { seen: 0, signed: 0, mis: 0, absent: 0 });
        stats.get(m)!.seen++;
      }
      for (const m of r.signers) stats.get(m)!.signed++;
      for (const m of r.misbehaved) stats.get(m)!.mis++;
      for (const m of r.absent) stats.get(m)!.absent++;
    }
    const table = [...stats.entries()]
      .map(([member, s]) => ({
        member,
        rounds: s.seen,
        signed: s.signed,
        misbehaved: s.mis,
        absent: s.absent,
        signRate: s.seen ? (s.signed / s.seen).toFixed(4) : "0",
        misRate: s.seen ? (s.mis / s.seen).toFixed(4) : "0",
        absentRate: s.seen ? (s.absent / s.seen).toFixed(4) : "0",
      }))
      .sort((a, b) => Number(b.signRate) - Number(a.signRate));

    await fs.writeFile(
      path.join(outDir, "member_stats.json"),
      JSON.stringify(table, null, 2),
      "utf8"
    );
    await fs.writeFile(
      path.join(outDir, "member_stats.csv"),
      toCSV(table, [
        "member",
        "rounds",
        "signed",
        "misbehaved",
        "absent",
        "signRate",
        "misRate",
        "absentRate",
      ]),
      "utf8"
    );
    console.log(`Wrote leaderboard to ${path.join(outDir, "member_stats.{json,csv}")}`);
  }

  console.log(
    `Wrote outputs to ${outDir}/dkg_results_summary.{json,csv}. Rounds: ${rounds.length}`
  );
}

async function live() {
  const registry = req("registry").toLowerCase();
  const pollMs = optNum("interval", 5000);
  const confs = optNum("confirmations", 1);
  const provider = getProvider();

  if (!Number.isFinite(pollMs) || pollMs <= 0) {
    throw new Error("--interval must be a positive number of milliseconds");
  }
  if (!Number.isFinite(confs) || confs < 0) {
    throw new Error("--confirmations must be zero or greater");
  }

  console.log(`Polling DkgResultSubmitted on ${registry} (every ${pollMs} ms).`);
  let last = 0;

  let running = false;

  async function tick() {
    if (running) return;
    running = true;
    try {
      const head = await provider.getBlockNumber();
      if (last === 0) last = Math.max(head - confs - 1, 0);
      const fromBlock = last + 1;
      const toBlock = head - confs;
      if (toBlock < fromBlock) return;

      const logs = await provider.getLogs({
        address: registry,
        fromBlock,
        toBlock,
        topics: [TOPIC_DKG],
      });

      for (const log of logs) {
        const round = decodeRound(log);
        if (!round) continue;
        console.log(
          `[DkgResultSubmitted @${round.block}] resultHash=${round.resultHash} members=${round.members.length} signers=${round.signers.length} mis=${round.misbehaved.length} absent=${round.absent.length}`
        );
      }

      last = toBlock;
    } finally {
      running = false;
    }
  }

  const handleError = (e: unknown) => console.error("tick error:", e);
  tick().catch(handleError);
  setInterval(() => {
    tick().catch(handleError);
  }, pollMs);
}

(async () => {
  try {
    if (cmd === "history") return await history();
    if (cmd === "live") return await live();
    console.log(
      `Usage:
  npm run dkg -- history --registry=<addr> --from=<block> --to=<block> [--batch=4000] [--out=out] [--leaderboard]
  npm run dkg -- live    --registry=<addr> [--interval=5000] [--confirmations=1]

Env:
  RPC_URL=https://...`
    );
  } catch (e: any) {
    console.error(e?.message || e);
    process.exit(1);
  }
})();
