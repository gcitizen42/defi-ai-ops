import { mkdirSync, writeFileSync } from "fs"
import { join } from "path"
import { getProvider, getWalletRegistry, OUT_DIR } from "./config.ts"

const args = Object.fromEntries(process.argv.slice(2).map(s => {
  const [k, v] = s.replace(/^--/, "").split("=")
  return [k, v ?? true]
}))

const FROM = Number(args.from)
const TO = Number(args.to)
const REG = args.registry as string | undefined
const BATCH = args.batch ? Number(args.batch) : 2000

if (!Number.isFinite(FROM)) throw new Error("--from block required")
if (!Number.isFinite(TO)) throw new Error("--to block required")
if (FROM > TO) throw new Error("--from must be <= --to")
if (!Number.isFinite(BATCH) || BATCH <= 0) throw new Error("--batch must be positive")

async function main() {
  const provider = getProvider()
  const reg = getWalletRegistry(REG)
  const iface = reg.interface
  const address = reg.target as string

  console.log(`Scanning WalletRegistry ${address} from block ${FROM} to ${TO} in batches of ${BATCH}`)

  const historyDir = join(OUT_DIR, "history")
  mkdirSync(historyDir, { recursive: true })

  const entries: Array<Record<string, unknown>> = []
  const csvRows: string[] = ["event,block,tx,data"]

  let start = FROM
  while (start <= TO) {
    const end = Math.min(start + BATCH - 1, TO)
    console.log(`Fetching logs ${start}-${end}`)
    const logs = await provider.getLogs({ address, fromBlock: start, toBlock: end })

    for (const log of logs) {
      try {
        const parsed = iface.parseLog(log)
        let data: Record<string, unknown> = {}
        switch (parsed.name) {
          case "DkgResultSubmitted": {
            const [resultHash, seed, result] = parsed.args as any
            data = {
              resultHash,
              seed: seed?.toString?.(),
              submitterMemberIndex: result?.submitterMemberIndex?.toString?.(),
              membersCount: result?.members?.length
            }
            break
          }
          case "DkgResultApproved": {
            const [resultHash, approver] = parsed.args as any
            data = { resultHash, approver }
            break
          }
          case "DkgResultChallenged": {
            const [resultHash, challenger, reason] = parsed.args as any
            data = { resultHash, challenger, reason: reason?.toString?.() }
            break
          }
          case "WalletRegistered": {
            const [walletPubKey, members] = parsed.args as any
            data = { walletPubKey, membersCount: members?.length }
            break
          }
          default:
            data = Object.fromEntries(parsed.args.map((value: unknown, index: number) => [index, value]))
        }

        const entry = {
          event: parsed.name,
          blockNumber: log.blockNumber,
          transactionHash: log.transactionHash,
          data
        }
        entries.push(entry)
        csvRows.push(`${parsed.name},${log.blockNumber},${log.transactionHash},"${JSON.stringify(data).replace(/"/g, '""')}"`)
      } catch (error) {
        console.warn("Failed to parse log", error)
      }
    }

    start = end + 1
  }

  const baseName = `history_${FROM}_${TO}`
  const jsonPath = join(historyDir, `${baseName}.json`)
  const csvPath = join(historyDir, `${baseName}.csv`)

  writeFileSync(jsonPath, JSON.stringify(entries, null, 2))
  writeFileSync(csvPath, csvRows.join("\n"))

  console.log(`Wrote ${entries.length} entries to ${jsonPath}`)
  console.log(`Wrote CSV to ${csvPath}`)
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
