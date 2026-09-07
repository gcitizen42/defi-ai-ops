import { describe, expect, it } from 'vitest'
import { buildRoleActions, makeRoleState, memberDiff } from '../src/role-plan.js'

const A = '0x0000000000000000000000000000000000000001'
const B = '0x0000000000000000000000000000000000000002'
const C = '0x0000000000000000000000000000000000000003'
const ROLE = `0x${'11'.repeat(32)}`
const ADMIN = `0x${'22'.repeat(32)}`

describe('role diff planner', () => {
  it('calculates the minimal member diff', () => {
    expect(memberDiff([A, B], [B, C])).toEqual({ grants: [C], revokes: [A] })
  })

  it('orders every grant before every revoke', () => {
    const executor = makeRoleState('executors', ROLE, ADMIN, [A], [B])
    const canceller = makeRoleState('cancellers', ROLE, ADMIN, [B], [C])
    expect(buildRoleActions([executor, canceller]).map(({ action, account }) => [action, account])).toEqual([
      ['grantRole', B],
      ['grantRole', C],
      ['revokeRole', A],
      ['revokeRole', B]
    ])
  })

  it('preserves an omitted role group', () => {
    const state = makeRoleState('proposers', ROLE, ADMIN, [A, B])
    expect(state.changed).toBe(false)
    expect(state.desiredMembers).toEqual([A, B])
  })
})
