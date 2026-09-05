#!/usr/bin/env node
import 'dotenv/config'
import { monthWindows, summariseYears } from './report.js'
import { queryTreasuryFees } from './threshold-fees.js'

async function main(): Promise<void> {
  const from = process.argv[2] ?? '2024-01-01'
  const to = process.argv[3] ?? new Date().toISOString().slice(0, 10)
  monthWindows(from, to)

  const rpcUrl = process.env.ETHEREUM_RPC_URL
  if (!rpcUrl || rpcUrl.includes('your-ethereum-rpc')) {
    throw new Error('Set ETHEREUM_RPC_URL in threshold-fee-monitor/.env.')
  }

  const monthly = await queryTreasuryFees(rpcUrl, from, to)
  const yearly = summariseYears(monthly)

  console.log('# Threshold Treasury Fees')
  console.log(`\nRange: ${from} to ${to} (end date excluded)`)
  console.log('\n## Monthly (satoshis)')
  for (const [month, value] of Object.entries(monthly)) console.log(`${month}: ${value}`)
  console.log('\n## Yearly (satoshis)')
  for (const [year, value] of Object.entries(yearly)) console.log(`${year}: ${value}`)
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error)
  process.exitCode = 1
})
