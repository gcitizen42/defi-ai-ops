#!/usr/bin/env node
import 'dotenv/config'
import { DEPLOYMENT_BLOCK, scanWalletRegistry } from './registry.js'

function argument(name: string): string | undefined {
  const index = process.argv.indexOf(name)
  return index >= 0 ? process.argv[index + 1] : undefined
}

function blockArgument(name: string, fallback?: number): number | undefined {
  const value = argument(name)
  if (!value || value === 'latest') return fallback
  const parsed = Number(value)
  if (!Number.isSafeInteger(parsed) || parsed < 0) throw new Error(`${name} must be a block number or latest.`)
  return parsed
}

async function main(): Promise<void> {
  const rpcUrl = process.env.ETHEREUM_RPC_URL
  if (!rpcUrl || rpcUrl.includes('your-ethereum-rpc')) {
    throw new Error('Set ETHEREUM_RPC_URL in tbtc-wallet-registry/.env.')
  }

  const state = argument('--state') ?? 'live'
  if (!['live', 'all'].includes(state)) throw new Error('--state must be live or all.')
  const result = await scanWalletRegistry(
    rpcUrl,
    blockArgument('--from-block', DEPLOYMENT_BLOCK),
    blockArgument('--to-block'),
    state === 'all'
  )
  console.log(`${JSON.stringify({ generatedAt: new Date().toISOString(), stateFilter: state, ...result }, null, 2)}\n`)
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error)
  process.exitCode = 1
})
