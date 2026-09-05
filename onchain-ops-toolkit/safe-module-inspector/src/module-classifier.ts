import { ethers } from 'ethers'
import type { ChainConfig } from './chains.js'

export type ModuleRisk = 'critical' | 'high' | 'medium' | 'info'

export type ModuleClassification = {
  moduleAddress: string
  risk: ModuleRisk
  label: string
  reasons: string[]
  explorerUrl: string
  bytecodeSize?: number
  implementationAddress?: string
}

type SelectorProfile = {
  label: string
  risk: ModuleRisk
  signatures: string[]
  minimumMatches: number
}

const SELECTOR_PROFILES: SelectorProfile[] = [
  {
    label: 'Zodiac Delay candidate',
    risk: 'high',
    minimumMatches: 3,
    signatures: ['avatar()', 'target()', 'txCooldown()', 'txExpiration()', 'setTxCooldown(uint256)']
  },
  {
    label: 'Zodiac Roles candidate',
    risk: 'high',
    minimumMatches: 3,
    signatures: [
      'avatar()',
      'target()',
      'assignRoles(address,bytes32[],bool[])',
      'execTransactionWithRole(address,uint256,bytes,uint8,bytes32,bool)',
      'scopeTarget(bytes32,address)'
    ]
  },
  {
    label: 'Zodiac module candidate',
    risk: 'medium',
    minimumMatches: 2,
    signatures: ['avatar()', 'target()', 'setAvatar(address)', 'setTarget(address)']
  },
  {
    label: 'Safe-compatible module candidate',
    risk: 'medium',
    minimumMatches: 1,
    signatures: [
      'execTransactionFromModule(address,uint256,bytes,uint8)',
      'execTransactionFromModuleReturnData(address,uint256,bytes,uint8)'
    ]
  }
]

const EIP1967_IMPLEMENTATION_SLOT = '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc'
const EIP1167_PREFIX = '0x363d3d373d3d3d363d73'
const EIP1167_SUFFIX = '5af43d82803e903d91602b57fd5bf3'

export function riskRank(risk: ModuleRisk): number {
  return { critical: 4, high: 3, medium: 2, info: 1 }[risk]
}

export function extractMinimalProxyImplementation(bytecode: string): string | undefined {
  const code = bytecode.toLowerCase()
  if (!code.startsWith(EIP1167_PREFIX) || !code.endsWith(EIP1167_SUFFIX)) return undefined
  try {
    return ethers.getAddress(`0x${code.slice(EIP1167_PREFIX.length, EIP1167_PREFIX.length + 40)}`)
  } catch {
    return undefined
  }
}

function addressFromStorage(word: string): string | undefined {
  const raw = word.toLowerCase().replace(/^0x/, '').padStart(64, '0').slice(24)
  if (!/[1-9a-f]/.test(raw)) return undefined
  try {
    return ethers.getAddress(`0x${raw}`)
  } catch {
    return undefined
  }
}

function selector(signature: string): string {
  return ethers.id(signature).slice(2, 10).toLowerCase()
}

function applyProfiles(bytecode: string, currentRisk: ModuleRisk): { label: string; risk: ModuleRisk; reasons: string[] } {
  let label = 'Unknown module'
  let risk = currentRisk
  const reasons: string[] = []
  const code = bytecode.toLowerCase()

  for (const profile of SELECTOR_PROFILES) {
    const matches = profile.signatures.filter((signature) => code.includes(selector(signature)))
    if (matches.length < profile.minimumMatches) continue
    if (label === 'Unknown module' || riskRank(profile.risk) > riskRank(risk)) label = profile.label
    if (riskRank(profile.risk) > riskRank(risk)) risk = profile.risk
    reasons.push(`Matched ${matches.join(', ')}.`)
  }

  return { label, risk, reasons }
}

async function implementationAddress(
  provider: ethers.Provider,
  moduleAddress: string,
  bytecode: string
): Promise<string | undefined> {
  const minimalProxy = extractMinimalProxyImplementation(bytecode)
  if (minimalProxy) return minimalProxy

  try {
    const stored = addressFromStorage(await provider.getStorage(moduleAddress, EIP1967_IMPLEMENTATION_SLOT))
    if (stored && (await provider.getCode(stored)) !== '0x') return stored
  } catch {
    // Proxy detection is best-effort because module implementations vary.
  }
  return undefined
}

export async function classifyModule(
  chain: ChainConfig,
  moduleAddress: string,
  provider?: ethers.Provider
): Promise<ModuleClassification> {
  const explorerUrl = `${chain.explorerUrl}/address/${moduleAddress}`
  if (!provider) {
    return {
      moduleAddress,
      risk: 'medium',
      label: 'Unclassified module',
      reasons: ['Configure the chain RPC URL to inspect bytecode and proxy patterns.'],
      explorerUrl
    }
  }

  try {
    const bytecode = await provider.getCode(moduleAddress)
    if (bytecode === '0x') {
      return {
        moduleAddress,
        risk: 'critical',
        label: 'Address without contract bytecode',
        reasons: ['The enabled module address has no contract bytecode on this chain.'],
        explorerUrl,
        bytecodeSize: 0
      }
    }

    const direct = applyProfiles(bytecode, 'medium')
    const proxyImplementation = await implementationAddress(provider, moduleAddress, bytecode)
    let label = direct.label
    let risk = direct.risk
    const reasons = [`Contract bytecode present (${(bytecode.length - 2) / 2} bytes).`, ...direct.reasons]

    if (proxyImplementation) {
      reasons.push(`Proxy implementation candidate: ${proxyImplementation}.`)
      const implementationCode = await provider.getCode(proxyImplementation)
      const implementationProfile = applyProfiles(implementationCode, risk)
      if (implementationProfile.label !== 'Unknown module') label = implementationProfile.label
      if (riskRank(implementationProfile.risk) > riskRank(risk)) risk = implementationProfile.risk
      reasons.push(...implementationProfile.reasons)
    }

    reasons.push('Review permissions and configuration before treating this module as trusted.')
    return {
      moduleAddress,
      risk,
      label,
      reasons,
      explorerUrl,
      bytecodeSize: (bytecode.length - 2) / 2,
      implementationAddress: proxyImplementation
    }
  } catch (error) {
    return {
      moduleAddress,
      risk: 'medium',
      label: 'Lookup failed',
      reasons: [error instanceof Error ? error.message : String(error)],
      explorerUrl
    }
  }
}
