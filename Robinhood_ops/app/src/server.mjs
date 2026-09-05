import http from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize, sep } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const publicDir = normalize(join(__dirname, "..", "public"));
const port = Number(process.env.PORT || 4173);

const envs = {
  mainnet: {
    rest: "https://api.arcus.xyz",
    ws: "wss://api.arcus.xyz/v1/ws",
  },
  testnet: {
    rest: "https://api.testnet.arcus.xyz",
    ws: "wss://api.testnet.arcus.xyz/v1/ws",
  },
};

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
};

function sendJson(res, status, body) {
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  });
  res.end(JSON.stringify(body));
}

function getEnv(url) {
  const envName = url.searchParams.get("env") || "mainnet";
  return envs[envName] ? envName : "mainnet";
}

async function proxyJson(res, targetUrl) {
  const response = await fetch(targetUrl, {
    headers: { accept: "application/json" },
  });
  const text = await response.text();
  res.writeHead(response.status, {
    "content-type": response.headers.get("content-type") || "application/json",
    "cache-control": "no-store",
  });
  res.end(text);
}

async function handleApi(req, res, url) {
  const envName = getEnv(url);
  const base = envs[envName].rest;

  if (url.pathname === "/api/config") {
    return sendJson(res, 200, {
      env: envName,
      environments: envs,
      docs: "https://docs.arcus.xyz/api-reference/introduction",
    });
  }

  if (url.pathname === "/api/markets") {
    return proxyJson(res, `${base}/v1/markets`);
  }

  if (url.pathname === "/api/mids") {
    return proxyJson(res, `${base}/v1/mids`);
  }

  if (url.pathname === "/api/candles") {
    const market = url.searchParams.get("market") || "BTC-USD";
    const timeframe = url.searchParams.get("timeframe") || "1m";
    const countback = url.searchParams.get("countback") || "120";
    const to = url.searchParams.get("to") || String(Date.now() * 1000);
    const qs = new URLSearchParams({ market, timeframe, to, countback });
    return proxyJson(res, `${base}/v1/candles?${qs.toString()}`);
  }

  return sendJson(res, 404, { error: "Unknown API route" });
}

async function serveStatic(res, pathname) {
  const cleanPath = pathname === "/" ? "/index.html" : pathname;
  const filePath = normalize(join(publicDir, cleanPath));
  if (filePath !== publicDir && !filePath.startsWith(`${publicDir}${sep}`)) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }

  try {
    const body = await readFile(filePath);
    res.writeHead(200, {
      "content-type": mimeTypes[extname(filePath)] || "application/octet-stream",
      "cache-control": "no-store",
    });
    res.end(body);
  } catch {
    res.writeHead(404);
    res.end("Not found");
  }
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url || "/", `http://${req.headers.host}`);
  try {
    if (url.pathname.startsWith("/api/")) {
      await handleApi(req, res, url);
      return;
    }
    await serveStatic(res, url.pathname);
  } catch (error) {
    sendJson(res, 500, { error: error.message || "Internal server error" });
  }
});

server.listen(port, () => {
  console.log(`Robinhood Ops Arcus base app running at http://localhost:${port}`);
});
