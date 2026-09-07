import { describe, expect, it } from 'vitest'
import { makeSafeBatch, safeBatchChecksum, type SafeBatch } from '../src/safe-batch.js'

describe('Safe batch output', () => {
  it('creates a raw calldata transaction for the configured Safe and chain', () => {
    const batch = makeSafeBatch(
      1,
      '0x0000000000000000000000000000000000000001',
      '0x0000000000000000000000000000000000000002',
      '0x1234',
      'Schedule rotation',
      'Review first',
      123
    )
    expect(batch.chainId).toBe('1')
    expect(batch.createdAt).toBe(123)
    expect(batch.meta.createdFromSafeAddress).toBe('0x0000000000000000000000000000000000000001')
    expect(batch.meta.checksum).toBe(safeBatchChecksum(batch))
    expect(batch.meta.checksum).toMatch(/^0x[0-9a-f]{64}$/)
    expect(batch.transactions[0]).toMatchObject({
      to: '0x0000000000000000000000000000000000000002',
      value: '0',
      data: '0x1234'
    })
    expect(batch.transactions[0]).not.toHaveProperty('contractMethod')
  })

  it('matches the Safe Transaction Builder checksum fixture', () => {
    const address = '0x49d4450977E2c95362C13D3a31a09311E0Ea26A6'
    const fixture = {
      version: '1.0',
      chainId: '4',
      createdAt: 1646321521061,
      meta: {
        name: 'test batch file',
        txBuilderVersion: '1.4.0',
        checksum: '',
        createdFromSafeAddress: '0xDF8a1Ce35c9a6ACE153B4e0767942f1E2291a1Aa',
        createdFromOwnerAddress: address
      },
      transactions: [
        {
          to: address,
          value: '0',
          contractMethod: {
            inputs: [{ internalType: 'address', name: 'paramAddress', type: 'address' }],
            name: 'testAddress',
            payable: false
          },
          contractInputsValues: { paramAddress: address }
        },
        {
          to: address,
          value: '0',
          contractMethod: {
            inputs: [{ internalType: 'bool', name: 'paramBool', type: 'bool' }],
            name: 'testBool',
            payable: false
          },
          contractInputsValues: { paramAddress: '', paramBool: 'false' }
        },
        {
          to: address,
          value: '2000000000000000000',
          data: '0x42f4579000000000000000000000000049d4450977e2c95362c13d3a31a09311e0ea26a6'
        }
      ]
    } as unknown as SafeBatch

    expect(safeBatchChecksum(fixture)).toBe('0x86c81826dbf7e8a37612153294cc85fdf5c81998dd0a44b86d945502a7eace7c')
  })
})
