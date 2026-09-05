export type ChainConfig = {
  name: string
  shortName: string
  chainId: bigint
  transactionServiceUrl: string
  rpcEnv: string
  explorerUrl: string
}

export const CHAINS: ChainConfig[] = [
  chain('Ethereum', 'ethereum', 1n, 'mainnet', 'ETHEREUM_RPC_URL', 'https://etherscan.io'),
  chain('Gnosis Chain', 'gnosis', 100n, 'gnosis-chain', 'GNOSIS_RPC_URL', 'https://gnosisscan.io'),
  chain('Polygon', 'polygon', 137n, 'polygon', 'POLYGON_RPC_URL', 'https://polygonscan.com'),
  chain('Arbitrum', 'arbitrum', 42161n, 'arbitrum', 'ARBITRUM_RPC_URL', 'https://arbiscan.io'),
  chain('Optimism', 'optimism', 10n, 'optimism', 'OPTIMISM_RPC_URL', 'https://optimistic.etherscan.io'),
  chain('Base', 'base', 8453n, 'base', 'BASE_RPC_URL', 'https://basescan.org'),
  chain('Avalanche', 'avalanche', 43114n, 'avalanche', 'AVALANCHE_RPC_URL', 'https://snowtrace.io'),
  chain('BNB Smart Chain', 'bsc', 56n, 'bsc', 'BSC_RPC_URL', 'https://bscscan.com'),
  chain('Linea', 'linea', 59144n, 'linea', 'LINEA_RPC_URL', 'https://lineascan.build'),
  chain('Scroll', 'scroll', 534352n, 'scroll', 'SCROLL_RPC_URL', 'https://scrollscan.com'),
  chain('zkSync Era', 'zksync', 324n, 'zksync', 'ZKSYNC_RPC_URL', 'https://explorer.zksync.io')
]

function chain(
  name: string,
  shortName: string,
  chainId: bigint,
  serviceName: string,
  rpcEnv: string,
  explorerUrl: string
): ChainConfig {
  return {
    name,
    shortName,
    chainId,
    transactionServiceUrl: `https://safe-transaction-${serviceName}.safe.global`,
    rpcEnv,
    explorerUrl
  }
}
