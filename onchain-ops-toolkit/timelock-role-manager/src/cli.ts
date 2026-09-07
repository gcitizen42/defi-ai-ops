#!/usr/bin/env node
import 'dotenv/config'
import fs from 'node:fs/promises'
import path from 'node:path'
import { parseConfig } from './config.js'
import { buildRotationPlan } from './planner.js'

function argument(name: string): string | undefined {
  const index = process.argv.indexOf(name)
  return index >= 0 ? process.argv[index + 1] : undefined
}

async function main(): Promise<void> {
  const configPath = process.argv[2]
  if (!configPath || configPath.startsWith('--')) {
    throw new Error('Usage: npm run start --workspace timelock-role-manager -- CONFIG.json [--out generated]')
  }
  const config = parseConfig(JSON.parse(await fs.readFile(configPath, 'utf8')))
  const rpcUrl = process.env[config.rpcEnv]
  if (!rpcUrl || rpcUrl.includes('your-ethereum-rpc')) {
    throw new Error(`Set the archive-capable RPC URL in ${config.rpcEnv}.`)
  }

  const outputDir = argument('--out') ?? 'generated'
  const plan = await buildRotationPlan(config, rpcUrl)
  await fs.mkdir(outputDir, { recursive: true })
  await Promise.all([
    fs.writeFile(path.join(outputDir, 'plan.json'), `${JSON.stringify(plan, null, 2)}\n`),
    fs.writeFile(path.join(outputDir, 'schedule.json'), `${JSON.stringify(plan.scheduleBatch, null, 2)}\n`),
    fs.writeFile(path.join(outputDir, 'execute.json'), `${JSON.stringify(plan.executeBatch, null, 2)}\n`)
  ])

  console.log(`Operation: ${plan.operationId}`)
  console.log(`Actions: ${plan.actions.length}`)
  console.log(`Minimum delay: ${plan.minimumDelaySeconds} seconds`)
  console.log(`Plan: ${path.join(outputDir, 'plan.json')}`)
  console.log(`Schedule batch: ${path.join(outputDir, 'schedule.json')}`)
  console.log(`Execute batch: ${path.join(outputDir, 'execute.json')}`)
  for (const warning of plan.warnings) console.warn(`Warning: ${warning}`)
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error)
  process.exitCode = 1
})
