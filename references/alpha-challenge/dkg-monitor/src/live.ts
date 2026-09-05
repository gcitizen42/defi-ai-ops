import { WebSocketProvider } from "ethers"
import { getWalletRegistry } from "./config.ts"

const args = Object.fromEntries(process.argv.slice(2).map(s => {
  const [k,v] = s.replace(/^--/,"").split("="); return [k, v ?? true]
}))
const REG = args.registry as string | undefined
const WS_URL = process.env.WS_URL

if (!WS_URL) {
  console.error("WS_URL not set. Use polling fallback: npm run live:poll -- --registry=0x...")
  process.exit(1)
}

async function main() {
  const provider = new WebSocketProvider(WS_URL)
  const reg = getWalletRegistry(REG).connect(provider)

  console.log(`Listening (WebSocket) on WalletRegistry ${reg.target} ...`)

  reg.on(reg.filters.DkgResultSubmitted(), (resultHash, seed, result, event) => {
    console.log("[DkgResultSubmitted]", {
      block: event.blockNumber, tx: event.transactionHash, resultHash,
      submitterMemberIndex: result.submitterMemberIndex?.toString?.(),
      members: result.members?.length
    })
  })
  reg.on(reg.filters.DkgResultApproved(), (resultHash, approver, event) => {
    console.log("[DkgResultApproved]", { block: event.blockNumber, tx: event.transactionHash, resultHash, approver })
  })
  reg.on(reg.filters.DkgResultChallenged(), (resultHash, challenger, reason, event) => {
    console.log("[DkgResultChallenged]", { block: event.blockNumber, tx: event.transactionHash, resultHash, challenger, reason })
  })
  reg.on(reg.filters.WalletRegistered(), (walletPubKey, members, event) => {
    console.log("[WalletRegistered]", { block: event.blockNumber, tx: event.transactionHash, walletPubKey, membersCount: members.length })
  })

  process.stdin.resume()
}

main().catch(e => { console.error(e); process.exit(1) })
