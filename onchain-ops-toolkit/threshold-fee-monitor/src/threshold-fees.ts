import { ethers } from 'ethers'
import { monthWindows } from './report.js'

export const TBTC_BRIDGE = '0x5e4861a80B55f035D899f66772117F00FA0E8e7B'
const DEPLOYMENT_BLOCK = 17_392_800
const EVENT = 'RedemptionRequested(bytes20,bytes,address,uint64,uint64,uint64)'
const TOPIC = ethers.id(EVENT)
const INTERFACE = new ethers.Interface([
  'event RedemptionRequested(bytes20 indexed walletPubKeyHash, bytes redeemerOutputScript, address indexed redeemer, uint64 requestedAmount, uint64 treasuryFee, uint64 txMaxFee)'
])

async function blockAtOrAfter(
  provider: ethers.Provider,
  unixSeconds: number,
  latestBlock: number
): Promise<number> {
  const latest = await provider.getBlock(latestBlock)
  if (!latest) throw new Error(`Could not load block ${latestBlock}.`)
  if (unixSeconds > latest.timestamp) return latestBlock + 1

  let low = DEPLOYMENT_BLOCK
  let high = latestBlock
  while (low < high) {
    const middle = Math.floor((low + high) / 2)
    const block = await provider.getBlock(middle)
    if (!block) throw new Error(`Could not load block ${middle}.`)
    if (block.timestamp < unixSeconds) low = middle + 1
    else high = middle
  }
  return low
}

async function logsInChunks(
  provider: ethers.Provider,
  fromBlock: number,
  toBlock: number,
  step = 90_000
): Promise<ethers.Log[]> {
  const logs: ethers.Log[] = []
  for (let from = fromBlock; from <= toBlock; from += step) {
    logs.push(
      ...(await provider.getLogs({
        address: TBTC_BRIDGE,
        topics: [TOPIC],
        fromBlock: from,
        toBlock: Math.min(from + step - 1, toBlock)
      }))
    )
  }
  return logs
}

export function sumTreasuryFees(logs: readonly ethers.Log[]): bigint {
  return logs.reduce((total, log) => {
    try {
      const decoded = INTERFACE.decodeEventLog('RedemptionRequested', log.data, log.topics)
      return total + (decoded.treasuryFee as bigint)
    } catch {
      return total
    }
  }, 0n)
}

export async function queryTreasuryFees(
  rpcUrl: string,
  fromIso: string,
  toIso: string
): Promise<Record<string, bigint>> {
  const provider = new ethers.JsonRpcProvider(rpcUrl, 1)
  try {
    const latestBlock = await provider.getBlockNumber()
    const monthly: Record<string, bigint> = {}
    for (const window of monthWindows(fromIso, toIso)) {
      const fromBlock = await blockAtOrAfter(provider, window.start.valueOf() / 1000, latestBlock)
      const toBlock = (await blockAtOrAfter(provider, window.end.valueOf() / 1000, latestBlock)) - 1
      const logs = fromBlock <= toBlock ? await logsInChunks(provider, fromBlock, toBlock) : []
      monthly[window.label] = sumTreasuryFees(logs)
      console.error(`${window.label}: ${logs.length} redemption request${logs.length === 1 ? '' : 's'}`)
    }
    return monthly
  } finally {
    provider.destroy()
  }
}
