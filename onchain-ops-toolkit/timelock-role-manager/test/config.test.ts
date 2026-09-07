import { describe, expect, it } from 'vitest'
import { parseConfig } from '../src/config.js'

const base = {
  chainId: 1,
  timelockAddress: '0x0000000000000000000000000000000000000001',
  safeAddress: '0x0000000000000000000000000000000000000002',
  expectedMinDelaySeconds: 86400,
  salt: 'rotation-example-1',
  roles: { executors: ['0x0000000000000000000000000000000000000003'] }
}

describe('role manager config', () => {
  it('normalizes a valid executor rotation', () => {
    expect(parseConfig(base).roles.executors).toEqual(['0x0000000000000000000000000000000000000003'])
  })

  it('requires proposer and canceller rotations together', () => {
    expect(() => parseConfig({ ...base, roles: { proposers: base.roles.executors } })).toThrow(
      'Rotate proposers and cancellers together'
    )
  })

  it('blocks admin role input', () => {
    expect(() => parseConfig({ ...base, roles: { admins: base.roles.executors } })).toThrow(
      'Admin roles are intentionally blocked'
    )
  })

  it('requires explicit acknowledgement for an open executor', () => {
    expect(() => parseConfig({ ...base, roles: { executors: ['0x0000000000000000000000000000000000000000'] } })).toThrow(
      'zero address'
    )
  })

  it('accepts an explicitly acknowledged open executor', () => {
    const config = parseConfig({
      ...base,
      allowOpenExecutor: true,
      roles: { executors: ['0x0000000000000000000000000000000000000000'] }
    })
    expect(config.roles.executors).toEqual(['0x0000000000000000000000000000000000000000'])
  })
})
