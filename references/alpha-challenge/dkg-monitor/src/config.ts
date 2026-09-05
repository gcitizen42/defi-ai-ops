import "dotenv/config"
import { JsonRpcProvider, Contract } from "ethers"
import { readFileSync } from "fs"
import { fileURLToPath } from "url"
import { dirname, join } from "path"

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const abiPath = join(__dirname, "abi", "WalletRegistry.min.abi.json")
const abi = JSON.parse(readFileSync(abiPath, "utf-8"))

export const RPC_URL = process.env.RPC_URL!
if (!RPC_URL) throw new Error("RPC_URL is required in .env")

export const OUT_DIR = process.env.OUT_DIR || "out"

export function getProvider() {
  return new JsonRpcProvider(RPC_URL)
}

export function getWalletRegistry(address?: string) {
  const addr = address || process.env.WALLET_REGISTRY_ADDRESS
  if (!addr) throw new Error("WalletRegistry address missing. Set WALLET_REGISTRY_ADDRESS in .env or pass --registry 0x...")
  return new Contract(addr, abi)
}
