import { keccak256, toUtf8Bytes } from 'ethers'

type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue }

export type SafeBatch = {
  version: '1.0'
  chainId: string
  createdAt: number
  meta: {
    name: string
    description: string
    txBuilderVersion: '1.0.0'
    createdFromSafeAddress: string
    createdFromOwnerAddress: ''
    checksum: string
  }
  transactions: Array<{
    to: string
    value: '0'
    data: string
  }>
}

function serialize(value: JsonValue): string {
  if (Array.isArray(value)) return `[${value.map(serialize).join(',')}]`
  if (typeof value === 'object' && value !== null) {
    const keys = Object.keys(value).sort()
    return `{${JSON.stringify(keys)}${keys.map((key) => `${serialize(value[key])},`).join('')}}`
  }
  return JSON.stringify(value)
}

export function safeBatchChecksum(batch: SafeBatch): string {
  const { checksum: _checksum, ...meta } = batch.meta
  const checksummed = { ...batch, meta: { ...meta, name: null } } as unknown as JsonValue
  return keccak256(toUtf8Bytes(serialize(checksummed)))
}

export function makeSafeBatch(
  chainId: number,
  safeAddress: string,
  timelockAddress: string,
  data: string,
  name: string,
  description: string,
  createdAt = Date.now()
): SafeBatch {
  const batch: SafeBatch = {
    version: '1.0',
    chainId: String(chainId),
    createdAt,
    meta: {
      name,
      description,
      txBuilderVersion: '1.0.0',
      createdFromSafeAddress: safeAddress,
      createdFromOwnerAddress: '',
      checksum: ''
    },
    transactions: [
      {
        to: timelockAddress,
        value: '0',
        data
      }
    ]
  }
  batch.meta.checksum = safeBatchChecksum(batch)
  return batch
}
