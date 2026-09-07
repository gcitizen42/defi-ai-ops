import { ethers } from 'ethers'
import { MANAGED_ROLES, type ManagedRole, type RoleManagerConfig } from './config.js'
import { buildRoleActions, makeRoleState, ROLE_METHODS, type RoleState } from './role-plan.js'
import { makeSafeBatch } from './safe-batch.js'

const TIMELOCK_ABI = [
  'function PROPOSER_ROLE() view returns (bytes32)',
  'function EXECUTOR_ROLE() view returns (bytes32)',
  'function CANCELLER_ROLE() view returns (bytes32)',
  'function getRoleAdmin(bytes32 role) view returns (bytes32)',
  'function hasRole(bytes32 role, address account) view returns (bool)',
  'function getMinDelay() view returns (uint256)',
  'function hashOperationBatch(address[] targets, uint256[] values, bytes[] payloads, bytes32 predecessor, bytes32 salt) view returns (bytes32)',
  'function isOperation(bytes32 id) view returns (bool)',
  'function scheduleBatch(address[] targets, uint256[] values, bytes[] payloads, bytes32 predecessor, bytes32 salt, uint256 delay)',
  'function executeBatch(address[] targets, uint256[] values, bytes[] payloads, bytes32 predecessor, bytes32 salt)',
  'event RoleGranted(bytes32 indexed role, address indexed account, address indexed sender)',
  'event RoleRevoked(bytes32 indexed role, address indexed account, address indexed sender)'
]

const SAFE_ABI = [
  'function getOwners() view returns (address[])',
  'function getThreshold() view returns (uint256)'
]

type ContractLike = ethers.Contract & Record<string, (...args: unknown[]) => Promise<unknown>>

export type RotationPlan = {
  generatedAt: string
  chainId: number
  latestBlock: number
  deploymentBlock: number
  timelockAddress: string
  safe: { address: string; owners: string[]; threshold: number }
  minimumDelaySeconds: string
  saltText: string
  salt: string
  operationId: string
  roles: RoleState[]
  adminMembers: Record<string, string[]>
  checks: {
    timelockIsSelfAdmin: boolean
    safeCanSchedule: boolean
    safeCanExecute: boolean
    safeCanCancel: boolean
    executorIsOpen: boolean
    scheduleCallSimulated: boolean
  }
  warnings: string[]
  actions: ReturnType<typeof buildRoleActions>
  scheduleBatch: ReturnType<typeof makeSafeBatch>
  executeBatch: ReturnType<typeof makeSafeBatch>
}

async function findDeploymentBlock(
  provider: ethers.Provider,
  address: string,
  latestBlock: number
): Promise<number> {
  if ((await provider.getCode(address, latestBlock)) === '0x') throw new Error('No contract found at timelockAddress.')
  let low = 0
  let high = latestBlock
  try {
    while (low < high) {
      const middle = Math.floor((low + high) / 2)
      if ((await provider.getCode(address, middle)) === '0x') low = middle + 1
      else high = middle
    }
  } catch (error) {
    throw new Error(`Could not verify the Timelock deployment block. Use an archive-capable RPC. ${String(error)}`)
  }
  return low
}

async function discoverRoleMembers(
  provider: ethers.Provider,
  timelockAddress: string,
  roleHashes: string[],
  fromBlock: number,
  toBlock: number
): Promise<Map<string, string[]>> {
  const iface = new ethers.Interface(TIMELOCK_ABI)
  const granted = ethers.id('RoleGranted(bytes32,address,address)')
  const revoked = ethers.id('RoleRevoked(bytes32,address,address)')
  const candidates = new Map<string, Set<string>>()
  for (const roleHash of roleHashes) candidates.set(roleHash.toLowerCase(), new Set())

  for (let from = fromBlock; from <= toBlock; from += 90_000) {
    const end = Math.min(from + 89_999, toBlock)
    console.error(`Reading role events ${from}-${end}`)
    const logs = await provider.getLogs({
      address: timelockAddress,
      topics: [[granted, revoked], roleHashes],
      fromBlock: from,
      toBlock: end
    })
    for (const log of logs) {
      const parsed = iface.parseLog(log)
      if (!parsed) continue
      const roleHash = String(parsed.args.role).toLowerCase()
      candidates.get(roleHash)?.add(ethers.getAddress(String(parsed.args.account)))
    }
  }

  const contract = new ethers.Contract(timelockAddress, TIMELOCK_ABI, provider) as ContractLike
  const members = new Map<string, string[]>()
  for (const [roleHash, accounts] of candidates) {
    const active: string[] = []
    for (const account of accounts) {
      if (await contract.hasRole(roleHash, account)) active.push(account)
    }
    members.set(roleHash, active.sort((left, right) => left.localeCompare(right)))
  }
  return members
}

function membersFor(map: Map<string, string[]>, roleHash: string): string[] {
  return map.get(roleHash.toLowerCase()) ?? []
}

export async function buildRotationPlan(config: RoleManagerConfig, rpcUrl: string): Promise<RotationPlan> {
  const provider = new ethers.JsonRpcProvider(rpcUrl)
  try {
    const network = await provider.getNetwork()
    if (network.chainId !== BigInt(config.chainId)) {
      throw new Error(`RPC chain ID ${network.chainId} does not match configured chain ID ${config.chainId}.`)
    }

    const latestBlock = await provider.getBlockNumber()
    const deploymentBlock = await findDeploymentBlock(provider, config.timelockAddress, latestBlock)
    if ((await provider.getCode(config.safeAddress, latestBlock)) === '0x') {
      throw new Error('No contract found at safeAddress.')
    }

    const safe = new ethers.Contract(config.safeAddress, SAFE_ABI, provider) as ContractLike
    let owners: string[]
    let threshold: number
    try {
      owners = ((await safe.getOwners()) as string[]).map(ethers.getAddress)
      threshold = Number(await safe.getThreshold())
    } catch {
      throw new Error('safeAddress does not expose the expected Safe owner and threshold interface.')
    }
    if (owners.length === 0 || threshold < 1 || threshold > owners.length) {
      throw new Error('The Safe owner or threshold state is invalid.')
    }

    const timelock = new ethers.Contract(config.timelockAddress, TIMELOCK_ABI, provider) as ContractLike
    const roleHashes = {} as Record<ManagedRole, string>
    const adminHashes = {} as Record<ManagedRole, string>
    for (const name of MANAGED_ROLES) {
      roleHashes[name] = String(await timelock[ROLE_METHODS[name]]())
      adminHashes[name] = String(await timelock.getRoleAdmin(roleHashes[name]))
    }

    const allHashes = [...new Set([...Object.values(roleHashes), ...Object.values(adminHashes)])]
    const roleMembers = await discoverRoleMembers(
      provider,
      config.timelockAddress,
      allHashes,
      deploymentBlock,
      latestBlock
    )
    const roles = MANAGED_ROLES.map((name) =>
      makeRoleState(
        name,
        roleHashes[name],
        adminHashes[name],
        membersFor(roleMembers, roleHashes[name]),
        config.roles[name]
      )
    )
    const actions = buildRoleActions(roles)
    if (actions.length === 0) throw new Error('The desired role state already matches the current on-chain state.')

    for (const role of roles) {
      if (role.desiredMembers.length === 0) throw new Error(`Rotation would leave ${role.name} empty.`)
      if (role.name !== 'executors' && role.desiredMembers.includes(ethers.ZeroAddress)) {
        throw new Error(`The zero address cannot satisfy ${role.name}.`)
      }
    }

    const adminMembers: Record<string, string[]> = {}
    const externalAdmins = new Set<string>()
    for (const adminHash of new Set(Object.values(adminHashes))) {
      const members = membersFor(roleMembers, adminHash)
      adminMembers[adminHash] = members
      if (!members.some((member) => member === config.timelockAddress)) {
        throw new Error(`Timelock is not a member of required admin role ${adminHash}.`)
      }
      for (const member of members) {
        if (member !== config.timelockAddress) externalAdmins.add(member)
      }
    }
    if (externalAdmins.size > 0 && !config.allowExternalAdmin) {
      throw new Error(
        `External Timelock admins detected: ${[...externalAdmins].join(', ')}. Review them and set allowExternalAdmin to true only if intentional.`
      )
    }

    const minimumDelay = BigInt(String(await timelock.getMinDelay()))
    if (minimumDelay !== BigInt(config.expectedMinDelaySeconds)) {
      throw new Error(
        `On-chain minimum delay ${minimumDelay} does not match expectedMinDelaySeconds ${config.expectedMinDelaySeconds}.`
      )
    }

    const safeCanSchedule = Boolean(await timelock.hasRole(roleHashes.proposers, config.safeAddress))
    const executorIsOpen = Boolean(await timelock.hasRole(roleHashes.executors, ethers.ZeroAddress))
    const safeCanExecute = executorIsOpen || Boolean(await timelock.hasRole(roleHashes.executors, config.safeAddress))
    const safeCanCancel = Boolean(await timelock.hasRole(roleHashes.cancellers, config.safeAddress))
    if (!safeCanSchedule) throw new Error('The configured Safe does not currently have PROPOSER_ROLE.')
    if (!safeCanExecute) throw new Error('The configured Safe cannot execute and EXECUTOR_ROLE is not open.')

    const targets = actions.map(() => config.timelockAddress)
    const values = actions.map(() => 0n)
    const payloads = actions.map((action) => action.data)
    const predecessor = ethers.ZeroHash
    const salt = ethers.id(config.salt)
    const operationId = String(
      await timelock.hashOperationBatch(targets, values, payloads, predecessor, salt)
    )
    if (await timelock.isOperation(operationId)) {
      throw new Error(`Operation ${operationId} already exists on the Timelock.`)
    }

    const iface = new ethers.Interface(TIMELOCK_ABI)
    const scheduleData = iface.encodeFunctionData('scheduleBatch', [
      targets,
      values,
      payloads,
      predecessor,
      salt,
      minimumDelay
    ])
    const executeData = iface.encodeFunctionData('executeBatch', [targets, values, payloads, predecessor, salt])
    try {
      await provider.call({ from: config.safeAddress, to: config.timelockAddress, data: scheduleData })
    } catch (error) {
      throw new Error(`Read-only schedule simulation reverted: ${String(error)}`)
    }

    const warnings: string[] = []
    if (!safeCanCancel) warnings.push('The configured Safe cannot cancel pending operations.')
    if (executorIsOpen) warnings.push('EXECUTOR_ROLE is open to the zero address, so anyone can execute ready operations.')
    if (externalAdmins.size > 0) warnings.push(`External admin access acknowledged for ${[...externalAdmins].join(', ')}.`)

    const createdAt = Date.now()
    return {
      generatedAt: new Date(createdAt).toISOString(),
      chainId: config.chainId,
      latestBlock,
      deploymentBlock,
      timelockAddress: config.timelockAddress,
      safe: { address: config.safeAddress, owners, threshold },
      minimumDelaySeconds: minimumDelay.toString(),
      saltText: config.salt,
      salt,
      operationId,
      roles,
      adminMembers,
      checks: {
        timelockIsSelfAdmin: true,
        safeCanSchedule,
        safeCanExecute,
        safeCanCancel,
        executorIsOpen,
        scheduleCallSimulated: true
      },
      warnings,
      actions,
      scheduleBatch: makeSafeBatch(
        config.chainId,
        config.safeAddress,
        config.timelockAddress,
        scheduleData,
        'Schedule Timelock role rotation',
        `Schedule atomic role rotation ${operationId}`,
        createdAt
      ),
      executeBatch: makeSafeBatch(
        config.chainId,
        config.safeAddress,
        config.timelockAddress,
        executeData,
        'Execute Timelock role rotation',
        `Execute atomic role rotation ${operationId} after the minimum delay`,
        createdAt
      )
    }
  } finally {
    provider.destroy()
  }
}
