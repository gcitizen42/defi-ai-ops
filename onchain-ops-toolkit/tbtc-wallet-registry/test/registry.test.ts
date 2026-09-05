import { describe, expect, it } from 'vitest'
import { bitcoinAddressFromWalletHash, walletHashFromTopic, walletStateName } from '../src/registry.js'

describe('wallet registry helpers', () => {
  it('extracts a bytes20 wallet hash from an indexed topic', () => {
    expect(walletHashFromTopic(`0x${'0'.repeat(24)}${'ab'.repeat(20)}`)).toBe(`0x${'ab'.repeat(20)}`)
  })

  it('encodes a mainnet P2WPKH address', () => {
    expect(bitcoinAddressFromWalletHash(`0x${'11'.repeat(20)}`)).toMatch(/^bc1q/)
  })

  it('names known and unknown states', () => {
    expect(walletStateName(1)).toBe('live')
    expect(walletStateName(9)).toBe('unknown-9')
  })
})
