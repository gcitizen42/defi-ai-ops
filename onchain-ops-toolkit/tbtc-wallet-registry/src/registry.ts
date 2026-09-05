import { Buffer } from 'node:buffer'
import * as bitcoin from 'bitcoinjs-lib'
import { ethers } from 'ethers'

export const TBTC_BRIDGE = '0x5e4861a80B55f035D899f66772117F00FA0E8e7B'
export const DEPLOYMENT_BLOCK = 17_392_800
const LIVE_STATE = 1
const EVENT_TOPIC = ethers.id('NewWalletRegistered(bytes32,bytes20)')
const ABI = [
  'function wallets(bytes20) view returns (bytes32 ecdsaWalletID, bytes32 mainUtxoHash, uint64 pendingRedemptionsValue, uint32 createdAt, uint32 movingFundsRequestedAt, uint32 closingStartedAt, uint32 pendingMovedFundsSweepRequestsCount, uint8 state, bytes32 movingFundsTargetWalletsCommitmentHash)'
]

const STATE_NAMES = ['uninitialized', 'live', 'moving-funds', 'closing', 'closed', 'terminated'] as const

export type WalletRecord = {
  walletPublicKeyHash: string
  bitcoinAddress: string
  ecdsaWalletId: string
  state: string
  createdAt: string | null
  ageDays: number | null
  hasMainUtxo: boolean
  pendingRedemptionsSats: string
  pendingMovedFundsSweeps: number
}

export function walletStateName(state: number): string {
  return STATE_NAMES[state] ?? `unknown-${state}`
}

export function walletHashFromTopic(topic: string): string {
  if (!/^0x[0-9a-fA-F]{64}$/.test(topic)) throw new Error(`Invalid wallet topic: ${topic}`)
  return `0x${topic.slice(-40).toLowerCase()}`
}

export function bitcoinAddressFromWalletHash(hash: string): string {
  if (!/^0x[0-9a-fA-F]{40}$/.test(hash)) throw new Error(`Invalid wallet public key hash: ${hash}`)
  const result = bitcoin.payments.p2wpkh({
    hash: Buffer.from(hash.slice(2), 'hex'),
    network: bitcoin.networks.bitcoin
  }).address
  if (!result) throw new Error(`Could not encode wallet public key hash: ${hash}`)
  return result
}

async function registrationLogs(
  provider: ethers.Provider,
  fromBlock: number,
  toBlock: number,
  step = 90_000
): Promise<ethers.Log[]> {
  const logs: ethers.Log[] = []
  for (let from = fromBlock; from <= toBlock; from += step) {
    const end = Math.min(from + step - 1, toBlock)
    console.error(`Scanning blocks ${from}-${end}`)
    logs.push(
      ...(await provider.getLogs({
        address: TBTC_BRIDGE,
        topics: [EVENT_TOPIC],
        fromBlock: from,
        toBlock: end
      }))
    )
  }
  return logs
}

export async function scanWalletRegistry(
  rpcUrl: string,
  fromBlock = DEPLOYMENT_BLOCK,
  requestedToBlock?: number,
  includeAllStates = false
): Promise<{ fromBlock: number; toBlock: number; wallets: WalletRecord[] }> {
  const provider = new ethers.JsonRpcProvider(rpcUrl, 1)
  try {
    const latest = await provider.getBlockNumber()
    const toBlock = requestedToBlock === undefined ? latest : Math.min(requestedToBlock, latest)
    if (fromBlock < DEPLOYMENT_BLOCK || fromBlock > toBlock) {
      throw new Error(`Block range must be between ${DEPLOYMENT_BLOCK} and ${latest}.`)
    }

    const logs = await registrationLogs(provider, fromBlock, toBlock)
    const walletHashes = [...new Set(logs.map((log) => walletHashFromTopic(log.topics[2])))]
    const bridge = new ethers.Contract(TBTC_BRIDGE, ABI, provider)
    const wallets: WalletRecord[] = []

    for (let offset = 0; offset < walletHashes.length; offset += 5) {
      const batch = walletHashes.slice(offset, offset + 5)
      const records = await Promise.all(
        batch.map(async (hash): Promise<WalletRecord | undefined> => {
          const wallet = await bridge.wallets(hash)
          const state = Number(wallet.state)
          if (!includeAllStates && state !== LIVE_STATE) return undefined
          const createdAtSeconds = Number(wallet.createdAt)
          const createdAt = createdAtSeconds > 0 ? new Date(createdAtSeconds * 1000) : undefined
          return {
            walletPublicKeyHash: hash,
            bitcoinAddress: bitcoinAddressFromWalletHash(hash),
            ecdsaWalletId: String(wallet.ecdsaWalletID),
            state: walletStateName(state),
            createdAt: createdAt?.toISOString() ?? null,
            ageDays: createdAt ? Math.floor((Date.now() - createdAt.valueOf()) / 86_400_000) : null,
            hasMainUtxo: String(wallet.mainUtxoHash) !== ethers.ZeroHash,
            pendingRedemptionsSats: (wallet.pendingRedemptionsValue as bigint).toString(),
            pendingMovedFundsSweeps: Number(wallet.pendingMovedFundsSweepRequestsCount)
          }
        })
      )
      wallets.push(...records.filter((record): record is WalletRecord => record !== undefined))
    }

    wallets.sort((left, right) => (right.createdAt ?? '').localeCompare(left.createdAt ?? ''))
    return { fromBlock, toBlock, wallets }
  } finally {
    provider.destroy()
  }
}
