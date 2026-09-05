const state = { env: "mainnet", markets: [], mids: {} };
const el = {
  env: document.querySelector("#env"),
  filter: document.querySelector("#filter"),
  refresh: document.querySelector("#refresh"),
  status: document.querySelector("#status"),
  markets: document.querySelector("#markets"),
};

async function getJson(path) {
  const separator = path.includes("?") ? "&" : "?";
  const response = await fetch(`${path}${separator}env=${state.env}`);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

function format(value) {
  if (value === undefined || value === null || value === "") return "-";
  const n = Number(value);
  if (!Number.isFinite(n)) return String(value);
  if (Math.abs(n) >= 1000) return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return n.toLocaleString(undefined, { maximumSignificantDigits: 8 });
}

function render() {
  const query = el.filter.value.trim().toUpperCase();
  const markets = state.markets.filter((market) => {
    const name = `${market.market || ""} ${market.baseAsset || ""} ${market.fullAssetName || ""}`.toUpperCase();
    return !query || name.includes(query);
  });

  el.markets.innerHTML = markets.map((market) => {
    const symbol = market.market || market.ticker || market.id || "Unknown";
    const mid = state.mids[symbol] ?? state.mids[market.marketId];
    return `<article class="market">
      <h2>${symbol}</h2>
      <dl>
        <dt>Status</dt><dd>${market.status || "-"}</dd>
        <dt>Type</dt><dd>${market.type || market.category || "-"}</dd>
        <dt>Base</dt><dd>${market.baseAsset || "-"}</dd>
        <dt>Mid</dt><dd>${format(mid)}</dd>
      </dl>
    </article>`;
  }).join("");
}

async function load() {
  el.status.textContent = `Loading ${state.env} market data...`;
  try {
    const [markets, mids] = await Promise.all([getJson("/api/markets"), getJson("/api/mids")]);
    state.markets = Array.isArray(markets) ? markets : markets.markets || [];
    state.mids = mids || {};
    el.status.textContent = `${state.env}: ${state.markets.length} markets loaded`;
    render();
  } catch (error) {
    el.status.textContent = `Load failed: ${error.message}`;
  }
}

el.env.addEventListener("change", () => { state.env = el.env.value; load(); });
el.filter.addEventListener("input", render);
el.refresh.addEventListener("click", load);
load();
