import { ethers } from 'ethers'
import type { ManagedRole } from './config.js'

export const ROLE_METHODS: Record<ManagedRole, 'PROPOSER_ROLE' | 'EXECUTOR_ROLE' | 'CANCELLER_ROLE'> = {
  proposers: 'PROPOSER_ROLE',
  executors: 'EXECUTOR_ROLE',
  cancellers: 'CANCELLER_ROLE'
}

export type RoleState = {
  name: ManagedRole
  roleHash: string
  adminRoleHash: string
  currentMembers: string[]
  desiredMembers: string[]
  grants: string[]
  revokes: string[]
  changed: boolean
}

export type RoleAction = {
  action: 'grantRole' | 'revokeRole'
  role: ManagedRole
  roleHash: string
  account: string
  data: string
}

function key(address: string): string {
  return address.toLowerCase()
}

export function memberDiff(current: string[], desired: string[]): { grants: string[]; revokes: string[] } {
  const currentKeys = new Set(current.map(key))
  const desiredKeys = new Set(desired.map(key))
  return {
    grants: desired.filter((member) => !currentKeys.has(key(member))),
    revokes: current.filter((member) => !desiredKeys.has(key(member)))
  }
}

export function makeRoleState(
  name: ManagedRole,
  roleHash: string,
  adminRoleHash: string,
  currentMembers: string[],
  configuredMembers?: string[]
): RoleState {
  const desiredMembers = configuredMembers ?? currentMembers
  const { grants, revokes } = memberDiff(currentMembers, desiredMembers)
  return {
    name,
    roleHash,
    adminRoleHash,
    currentMembers,
    desiredMembers,
    grants,
    revokes,
    changed: configuredMembers !== undefined && (grants.length > 0 || revokes.length > 0)
  }
}

export function buildRoleActions(states: RoleState[]): RoleAction[] {
  const accessControl = new ethers.Interface([
    'function grantRole(bytes32 role, address account)',
    'function revokeRole(bytes32 role, address account)'
  ])
  const grants = states.flatMap((state) =>
    state.grants.map((account): RoleAction => ({
      action: 'grantRole',
      role: state.name,
      roleHash: state.roleHash,
      account,
      data: accessControl.encodeFunctionData('grantRole', [state.roleHash, account])
    }))
  )
  const revokes = states.flatMap((state) =>
    state.revokes.map((account): RoleAction => ({
      action: 'revokeRole',
      role: state.name,
      roleHash: state.roleHash,
      account,
      data: accessControl.encodeFunctionData('revokeRole', [state.roleHash, account])
    }))
  )
  return [...grants, ...revokes]
}
