import { getProvider, getWalletRegistry } from "./config.ts"
import { Interface, Log } from "ethers"

const args = Object.fromEntries(process.argv.slice(2).map(s => {
  const [k,v] = s.replace(/^--/,"").split("="); return [k, v ?? true]
}))
const REG = args.registry as string | undefined
const POLL_INTERVAL = args.interval ? Number(args.interval) : 10000

async function main() {
  const provider = getProvider()
  const reg = getWalletRegistry(REG)
  const iface: Interface = reg.interface
  const address = reg.target as string

  console.log(`Listening (polling) on WalletRegistry ${address} every ${POLL_INTERVAL}ms ...`)

  let fromBlock = await provider.getBlockNumber()

  setInterval(async () => {
    try {
      const latest = await provider.getBlockNumber()
      if (latest <= fromBlock) return
      const toBlock = latest

      const logs: Log[] = await provider.getLogs({ address, fromBlock: fromBlock + 1, toBlock })
      for (const log of logs) {
        try {
          const parsed = iface.parseLog(log)
          switch (parsed.name) {
            case "DkgResultSubmitted": {
              const [resultHash, seed, result] = parsed.args as any
              console.log("[DkgResultSubmitted]", { block: log.blockNumber, tx: log.transactionHash, resultHash,
                submitterMemberIndex: result.submitterMemberIndex?.toString?.(), members: result.members?.length })
              break
            }
            case "DkgResultApproved": {
              const [resultHash, approver] = parsed.args as any
              console.log("[DkgResultApproved]", { block: log.blockNumber, tx: log.transactionHash, resultHash, approver })
              break
            }
            case "DkgResultChallenged": {
              const [resultHash, challenger, reason] = parsed.args as any
              console.log("[DkgResultChallenged]", { block: log.blockNumber, tx: log.transactionHash, resultHash, challenger, reason })
              break
            }
            case "WalletRegistered": {
              const [walletPubKey, members] = parsed.args as any
              console.log("[WalletRegistered]", { block: log.blockNumber, tx: log.transactionHash, walletPubKey, membersCount: members.length })
              break
            }
          }
        } catch {}
      }

      fromBlock = toBlock
    } catch (e) {
      console.error("poll error", e)
    }
  }, POLL_INTERVAL)

  process.stdin.resume()
}

main().catch(e => { console.error(e); process.exit(1) })
