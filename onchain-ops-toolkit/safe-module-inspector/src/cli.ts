#!/usr/bin/env node
import 'dotenv/config'
import fs from 'node:fs/promises'
import path from 'node:path'
import { ethers } from 'ethers'
import { CHAINS, type ChainConfig } from './chains.js'
import { classifyModule, riskRank, type ModuleClassification } from './module-classifier.js'

type SafeInfo = {
  address: string
  threshold: number
  owners: string[]
  modules: string[]
}

type Finding = {
  chain: ChainConfig
  safe: SafeInfo
  modules: ModuleClassification[]
}

function argument(name: string): string | undefined {
  const index = process.argv.indexOf(name)
  return index >= 0 ? process.argv[index + 1] : undefined
}

function csv(value?: string): string[] {
  return value?.split(',').map((item) => item.trim()).filter(Boolean) ?? []
}

function selectedChains(): ChainConfig[] {
  const requested = csv(argument('--chains') ?? process.env.CHAIN_FILTER).map((value) => value.toLowerCase())
  if (requested.length === 0) return CHAINS
  const selected = CHAINS.filter(
    (chain) => requested.includes(chain.shortName) || requested.includes(chain.name.toLowerCase())
  )
  if (selected.length !== requested.length) {
    const matched = new Set(selected.flatMap((chain) => [chain.shortName, chain.name.toLowerCase()]))
    const unknown = requested.filter((value) => !matched.has(value))
    if (unknown.length > 0) throw new Error(`Unknown chain filter: ${unknown.join(', ')}`)
  }
  return selected
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { headers: { accept: 'application/json' } })
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)
  return (await response.json()) as T
}

async function safesByOwner(chain: ChainConfig, owner: string): Promise<string[]> {
  const result = await fetchJson<{ safes: string[] }>(
    `${chain.transactionServiceUrl}/api/v1/owners/${owner}/safes/`
  )
  return result.safes.map(ethers.getAddress)
}

async function safeInfo(chain: ChainConfig, address: string): Promise<SafeInfo> {
  const result = await fetchJson<SafeInfo>(`${chain.transactionServiceUrl}/api/v1/safes/${address}/`)
  return {
    address: ethers.getAddress(result.address ?? address),
    threshold: Number(result.threshold),
    owners: result.owners.map(ethers.getAddress),
    modules: (result.modules ?? []).map(ethers.getAddress)
  }
}

function markdown(owner: string, findings: Finding[], errors: string[]): string {
  const lines = [
    '# Safe Module Inspection',
    '',
    `- Generated: \`${new Date().toISOString()}\``,
    `- Owner: \`${owner}\``,
    `- Safes found: \`${findings.length}\``,
    '',
    'This report is read-only. Enabled modules can expand a Safe\'s execution permissions.',
    ''
  ]

  for (const finding of findings) {
    lines.push(`## ${finding.chain.name}: ${finding.safe.address}`, '')
    lines.push(`- Threshold: \`${finding.safe.threshold}/${finding.safe.owners.length}\``)
    lines.push(`- Explorer: ${finding.chain.explorerUrl}/address/${finding.safe.address}`)
    lines.push(`- Enabled modules: \`${finding.modules.length}\``, '')
    if (finding.modules.length === 0) {
      lines.push('No enabled modules reported by the Safe Transaction Service.', '')
      continue
    }
    lines.push('| Risk | Module | Classification | Notes |', '| --- | --- | --- | --- |')
    for (const module of [...finding.modules].sort((a, b) => riskRank(b.risk) - riskRank(a.risk))) {
      const notes = module.reasons.join(' ').replaceAll('|', '\\|')
      lines.push(`| ${module.risk.toUpperCase()} | [\`${module.moduleAddress}\`](${module.explorerUrl}) | ${module.label} | ${notes} |`)
    }
    lines.push('')
  }

  if (errors.length > 0) lines.push('## Scan Errors', '', ...errors.map((error) => `- ${error}`), '')
  return `${lines.join('\n')}\n`
}

async function main(): Promise<void> {
  const ownerInput = argument('--owner') ?? process.env.OWNER_ADDRESS
  if (!ownerInput || ownerInput.includes('YOUR_')) {
    throw new Error('Set OWNER_ADDRESS in .env or pass --owner 0xADDRESS.')
  }
  const owner = ethers.getAddress(ownerInput)
  const extras = csv(process.env.EXTRA_SAFE_ADDRESSES).map(ethers.getAddress)
  const findings: Finding[] = []
  const errors: string[] = []

  for (const chain of selectedChains()) {
    let provider: ethers.JsonRpcProvider | undefined
    try {
      const rpcUrl = process.env[chain.rpcEnv]
      provider = rpcUrl ? new ethers.JsonRpcProvider(rpcUrl, Number(chain.chainId)) : undefined
      const discovered = await safesByOwner(chain, owner)
      const addresses = [...new Set([...discovered, ...extras])]
      for (const address of addresses) {
        const safe = await safeInfo(chain, address)
        const modules = []
        for (const moduleAddress of safe.modules) {
          modules.push(await classifyModule(chain, moduleAddress, provider))
        }
        findings.push({ chain, safe, modules })
        console.error(`${chain.name}: ${safe.address} (${modules.length} module${modules.length === 1 ? '' : 's'})`)
      }
    } catch (error) {
      errors.push(`${chain.name}: ${error instanceof Error ? error.message : String(error)}`)
    } finally {
      provider?.destroy()
    }
  }

  const reportDir = process.env.REPORT_DIR ?? 'reports'
  await fs.mkdir(reportDir, { recursive: true })
  const stamp = new Date().toISOString().replace(/[:.]/g, '-')
  const jsonPath = path.join(reportDir, `safe-modules-${stamp}.json`)
  const markdownPath = path.join(reportDir, `safe-modules-${stamp}.md`)
  const data = {
    generatedAt: new Date().toISOString(),
    owner,
    findings: findings.map(({ chain, ...finding }) => ({
      chain: { name: chain.name, shortName: chain.shortName, chainId: chain.chainId.toString() },
      ...finding
    })),
    errors
  }
  await fs.writeFile(jsonPath, `${JSON.stringify(data, null, 2)}\n`)
  await fs.writeFile(markdownPath, markdown(owner, findings, errors))
  console.log(`JSON report: ${jsonPath}`)
  console.log(`Markdown report: ${markdownPath}`)
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error)
  process.exitCode = 1
})
