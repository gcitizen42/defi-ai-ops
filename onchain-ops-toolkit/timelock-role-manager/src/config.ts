import { ethers } from 'ethers'

export const MANAGED_ROLES = ['proposers', 'executors', 'cancellers'] as const
export type ManagedRole = (typeof MANAGED_ROLES)[number]

export type RoleManagerConfig = {
  chainId: number
  timelockAddress: string
  safeAddress: string
  expectedMinDelaySeconds: number
  salt: string
  rpcEnv: string
  roles: Partial<Record<ManagedRole, string[]>>
  allowOpenExecutor: boolean
  allowExternalAdmin: boolean
}

function integer(value: unknown, name: string, minimum: number): number {
  if (!Number.isSafeInteger(value) || Number(value) < minimum) {
    throw new Error(`${name} must be an integer greater than or equal to ${minimum}.`)
  }
  return Number(value)
}

function address(value: unknown, name: string): string {
  if (typeof value !== 'string') throw new Error(`${name} must be an EVM address.`)
  try {
    return ethers.getAddress(value)
  } catch {
    throw new Error(`${name} must be an EVM address.`)
  }
}

function addresses(value: unknown, name: ManagedRole, allowZero: boolean): string[] {
  if (!Array.isArray(value) || value.length === 0) {
    throw new Error(`roles.${name} must contain at least one address.`)
  }
  const normalized = value.map((item, index) => address(item, `roles.${name}[${index}]`))
  if (new Set(normalized.map((item) => item.toLowerCase())).size !== normalized.length) {
    throw new Error(`roles.${name} contains duplicate addresses.`)
  }
  if (!allowZero && normalized.includes(ethers.ZeroAddress)) {
    throw new Error(`roles.${name} cannot contain the zero address.`)
  }
  return normalized
}

export function parseConfig(input: unknown): RoleManagerConfig {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('Config must be a JSON object.')
  const raw = input as Record<string, unknown>
  const rawRoles = raw.roles
  if (!rawRoles || typeof rawRoles !== 'object' || Array.isArray(rawRoles)) {
    throw new Error('roles must be a JSON object.')
  }

  const roleObject = rawRoles as Record<string, unknown>
  const unknownRoles = Object.keys(roleObject).filter(
    (name) => !MANAGED_ROLES.includes(name as ManagedRole)
  )
  if (unknownRoles.length > 0) {
    throw new Error(`Unsupported role groups: ${unknownRoles.join(', ')}. Admin roles are intentionally blocked.`)
  }
  if (Object.keys(roleObject).length === 0) throw new Error('Configure at least one role group.')
  if (('proposers' in roleObject) !== ('cancellers' in roleObject)) {
    throw new Error('Rotate proposers and cancellers together by providing both role groups.')
  }

  const allowOpenExecutor = raw.allowOpenExecutor === true
  const roles: Partial<Record<ManagedRole, string[]>> = {}
  for (const name of MANAGED_ROLES) {
    if (name in roleObject) roles[name] = addresses(roleObject[name], name, name === 'executors' && allowOpenExecutor)
  }
  if (roles.executors?.includes(ethers.ZeroAddress) && !allowOpenExecutor) {
    throw new Error('Set allowOpenExecutor to true before assigning the zero address as executor.')
  }

  const timelockAddress = address(raw.timelockAddress, 'timelockAddress')
  const safeAddress = address(raw.safeAddress, 'safeAddress')
  if (timelockAddress === safeAddress) throw new Error('timelockAddress and safeAddress must be different.')
  if (typeof raw.salt !== 'string' || raw.salt.trim().length < 8) {
    throw new Error('salt must be a unique descriptive string with at least 8 characters.')
  }

  return {
    chainId: integer(raw.chainId, 'chainId', 1),
    timelockAddress,
    safeAddress,
    expectedMinDelaySeconds: integer(raw.expectedMinDelaySeconds, 'expectedMinDelaySeconds', 0),
    salt: raw.salt.trim(),
    rpcEnv: typeof raw.rpcEnv === 'string' && raw.rpcEnv.trim() ? raw.rpcEnv.trim() : 'ETHEREUM_RPC_URL',
    roles,
    allowOpenExecutor,
    allowExternalAdmin: raw.allowExternalAdmin === true
  }
}
