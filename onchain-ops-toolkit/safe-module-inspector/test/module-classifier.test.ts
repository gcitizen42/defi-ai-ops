import { describe, expect, it } from 'vitest'
import { extractMinimalProxyImplementation, riskRank } from '../src/module-classifier.js'

describe('module classifier helpers', () => {
  it('orders risk levels', () => {
    expect(riskRank('critical')).toBeGreaterThan(riskRank('high'))
    expect(riskRank('high')).toBeGreaterThan(riskRank('medium'))
    expect(riskRank('medium')).toBeGreaterThan(riskRank('info'))
  })

  it('extracts an EIP-1167 implementation address', () => {
    const implementation = '1234567890abcdef1234567890abcdef12345678'
    const bytecode = `0x363d3d373d3d3d363d73${implementation}5af43d82803e903d91602b57fd5bf3`
    expect(extractMinimalProxyImplementation(bytecode)?.toLowerCase()).toBe(`0x${implementation}`)
  })

  it('ignores unrelated bytecode', () => {
    expect(extractMinimalProxyImplementation('0x60006000')).toBeUndefined()
  })
})
