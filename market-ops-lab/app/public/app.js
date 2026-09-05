const state = {
  env: "mainnet",
  markets: [],
  mids: {},
  selected: null,
  socket: null,
  candles: [],
  wsUrl: "wss://api.arcus.xyz/v1/ws",
};

const el = {
  status: document.querySelector("#status"),
  env: document.querySelector("#env"),
  refresh: document.querySelector("#refresh"),
  search: document.querySelector("#search"),
  category: document.querySelector("#category"),
  marketStatus: document.querySelector("#marketStatus"),
  summary: document.querySelector("#summary"),
  marketList: document.querySelector("#marketList"),
  selectedName: document.querySelector("#selectedName"),
  selectedMeta: document.querySelector("#selectedMeta"),
  copySymbol: document.querySelector("#copySymbol"),
  markPrice: document.querySelector("#markPrice"),
  oraclePrice: document.querySelector("#oraclePrice"),
  volume24h: document.querySelector("#volume24h"),
  openInterest: document.querySelector("#openInterest"),
  chart: document.querySelector("#chart"),
  chartInfo: document.querySelector("#chartInfo"),
  bids: document.querySelector("#bids"),
  asks: document.querySelector("#asks"),
  bookInfo: document.querySelector("#bookInfo"),
  restSnapshot: document.querySelector("#restSnapshot"),
};

function fmt(value) {
  if (value === undefined || value === null || value === "") return "-";
  const n = Number(value);
  if (!Number.isFinite(n)) return String(value);
  if (Math.abs(n) >= 1000000) return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
  if (Math.abs(n) >= 1) return n.toLocaleString(undefined, { maximumFractionDigits: 4 });
  return n.toLocaleString(undefined, { maximumSignificantDigits: 6 });
}

async function getJson(path) {
  const res = await fetch(`${path}${path.includes("?") ? "&" : "?"}env=${state.env}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

function renderSummary() {
  const total = state.markets.length;
  const online = state.markets.filter((m) => m.status === "ONLINE").length;
  const categories = Object.entries(
    state.markets.reduce((acc, market) => {
      acc[market.category || "UNKNOWN"] = (acc[market.category || "UNKNOWN"] || 0) + 1;
      return acc;
    }, {}),
  ).sort(([a], [b]) => a.localeCompare(b));

  el.summary.innerHTML = [
    `<div>Total<strong>${total}</strong></div>`,
    `<div>Online<strong>${online}</strong></div>`,
    ...categories.map(([category, count]) => `<div>${category}<strong>${count}</strong></div>`),
  ].join("");
}

function renderCategoryOptions() {
  const current = el.category.value;
  const categories = [...new Set(state.markets.map((m) => m.category).filter(Boolean))].sort();
  el.category.innerHTML = `<option value="">All categories</option>${categories
    .map((category) => `<option value="${category}">${category}</option>`)
    .join("")}`;
  el.category.value = categories.includes(current) ? current : "";
}

function marketMatches(market) {
  const q = el.search.value.trim().toLowerCase();
  const category = el.category.value;
  const status = el.marketStatus.value;
  const text = `${market.marketDisplayName} ${market.fullAssetName} ${market.baseAsset} ${market.category}`.toLowerCase();
  return (!q || text.includes(q)) && (!category || market.category === category) && (!status || market.status === status);
}

function renderMarketList() {
  const markets = state.markets.filter(marketMatches);
  el.marketList.innerHTML = markets
    .map((market) => {
      const isActive = state.selected?.marketDisplayName === market.marketDisplayName;
      const statusClass = market.status === "ONLINE" ? "badge" : "badge offline";
      return `<button class="market-row ${isActive ? "active" : ""}" type="button" data-market="${market.marketDisplayName}">
        <div class="line">
          <strong>${market.marketDisplayName}</strong>
          <span class="${statusClass}">${market.status}</span>
        </div>
        <p>${market.fullAssetName || market.baseAsset} · ${market.category || "UNKNOWN"} · mid ${fmt(state.mids[market.marketDisplayName])}</p>
      </button>`;
    })
    .join("");
}

function setSelected(market) {
  state.selected = market;
  state.candles = [];
  el.selectedName.textContent = market.marketDisplayName;
  el.selectedMeta.textContent = `${market.fullAssetName || market.baseAsset} · ${market.type || "-"} · ${market.category || "-"}`;
  el.markPrice.textContent = fmt(market.markPrice || state.mids[market.marketDisplayName]);
  el.oraclePrice.textContent = fmt(market.oraclePrice);
  el.volume24h.textContent = fmt(market.volume24hNotional || market.volume24h);
  el.openInterest.textContent = fmt(market.openInterest);
  el.restSnapshot.textContent = JSON.stringify(market, null, 2);
  el.bids.innerHTML = "";
  el.asks.innerHTML = "";
  el.bookInfo.textContent = "Connecting to L2 order book...";
  el.chartInfo.textContent = "Loading REST candles...";
  renderMarketList();
  loadRestCandles(market.marketDisplayName);
  connectMarketSocket(market.marketDisplayName);
}

async function loadMarkets() {
  el.status.textContent = `Loading ${state.env} market universe...`;
  const config = await getJson("/api/config");
  state.wsUrl = config.environments[state.env].ws;
  const [markets, mids] = await Promise.all([getJson("/api/markets"), getJson("/api/mids")]);
  state.markets = markets.markets || [];
  state.mids = mids.mids || {};
  renderCategoryOptions();
  renderSummary();
  renderMarketList();
  el.status.textContent = `${state.env}: ${state.markets.length} markets, ${state.markets.filter((m) => m.status === "ONLINE").length} online`;
  const previous = state.selected && state.markets.find((m) => m.marketDisplayName === state.selected.marketDisplayName);
  setSelected(previous || state.markets.find((m) => m.status === "ONLINE") || state.markets[0]);
}

async function loadRestCandles(market) {
  try {
    const data = await getJson(`/api/candles?market=${encodeURIComponent(market)}&timeframe=1m&countback=120`);
    state.candles = data.candles || [];
    drawChart();
    el.chartInfo.textContent = `${state.candles.length} REST candles loaded`;
  } catch (error) {
    el.chartInfo.textContent = `REST candles unavailable: ${error.message}`;
    drawChart();
  }
}

function connectMarketSocket(market) {
  if (state.socket) state.socket.close();
  const ws = new WebSocket(state.wsUrl);
  state.socket = ws;

  ws.addEventListener("open", () => {
    ws.send(JSON.stringify({ type: "subscribe", channel: "l2Orderbook", id: market, nLevels: 12 }));
    ws.send(JSON.stringify({ type: "subscribe", channel: "candles", id: `${market}/1m` }));
  });

  ws.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    if (msg.channel === "l2Orderbook" && msg.id === market) {
      renderBook(msg.contents || {});
    }
    if (msg.channel === "candles" && msg.id === `${market}/1m`) {
      updateCandles(msg.contents || {});
    }
  });

  ws.addEventListener("close", () => {
    if (state.socket === ws) el.bookInfo.textContent = "WebSocket closed";
  });

  ws.addEventListener("error", () => {
    el.bookInfo.textContent = "WebSocket error";
  });
}

function renderBook(book) {
  const bids = book.bids || [];
  const asks = book.asks || [];
  el.bids.innerHTML = bids.map(([price, size]) => `<tr><td class="bid-price">${fmt(price)}</td><td>${fmt(size)}</td></tr>`).join("");
  el.asks.innerHTML = asks.map(([price, size]) => `<tr><td class="ask-price">${fmt(price)}</td><td>${fmt(size)}</td></tr>`).join("");
  const ts = book.timestamp ? new Date(Number(book.timestamp) / 1000).toLocaleTimeString() : new Date().toLocaleTimeString();
  el.bookInfo.textContent = `${bids.length} bids / ${asks.length} asks · ${ts}`;
}

function updateCandles(contents) {
  if (contents.isSnapshot && Array.isArray(contents.candles)) {
    state.candles = contents.candles;
  } else if (contents.openTime) {
    const index = state.candles.findIndex((c) => c.openTime === contents.openTime);
    if (index >= 0) state.candles[index] = contents;
    else state.candles.push(contents);
    state.candles = state.candles.slice(-200);
  }
  drawChart();
  el.chartInfo.textContent = `${state.candles.length} live candles`;
}

function drawChart() {
  const canvas = el.chart;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#11171b";
  ctx.fillRect(0, 0, width, height);

  const candles = state.candles.filter((c) => Number.isFinite(Number(c.close))).slice(-120);
  if (!candles.length) {
    ctx.fillStyle = "#9eadb5";
    ctx.fillText("No candle data yet", 18, 32);
    return;
  }

  const prices = candles.flatMap((c) => [Number(c.high || c.close), Number(c.low || c.close)]);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const span = max - min || 1;
  const pad = 18;
  const candleWidth = Math.max(2, (width - pad * 2) / candles.length);

  ctx.strokeStyle = "#303a41";
  ctx.lineWidth = 1;
  for (let i = 0; i < 4; i += 1) {
    const y = pad + ((height - pad * 2) * i) / 3;
    ctx.beginPath();
    ctx.moveTo(pad, y);
    ctx.lineTo(width - pad, y);
    ctx.stroke();
  }

  candles.forEach((candle, index) => {
    const open = Number(candle.open);
    const close = Number(candle.close);
    const high = Number(candle.high || close);
    const low = Number(candle.low || close);
    const x = pad + index * candleWidth + candleWidth / 2;
    const y = (price) => height - pad - ((price - min) / span) * (height - pad * 2);
    const up = close >= open;
    ctx.strokeStyle = up ? "#7ddc89" : "#f07c7c";
    ctx.fillStyle = ctx.strokeStyle;
    ctx.beginPath();
    ctx.moveTo(x, y(high));
    ctx.lineTo(x, y(low));
    ctx.stroke();
    const bodyTop = y(Math.max(open, close));
    const bodyHeight = Math.max(1, Math.abs(y(open) - y(close)));
    ctx.fillRect(x - candleWidth * 0.32, bodyTop, candleWidth * 0.64, bodyHeight);
  });

  ctx.fillStyle = "#9eadb5";
  ctx.fillText(fmt(max), 18, 18);
  ctx.fillText(fmt(min), 18, height - 8);
}

el.refresh.addEventListener("click", loadMarkets);
el.env.addEventListener("change", () => {
  state.env = el.env.value;
  loadMarkets();
});
el.search.addEventListener("input", renderMarketList);
el.category.addEventListener("change", renderMarketList);
el.marketStatus.addEventListener("change", renderMarketList);
el.marketList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-market]");
  if (!button) return;
  const market = state.markets.find((m) => m.marketDisplayName === button.dataset.market);
  if (market) setSelected(market);
});
el.copySymbol.addEventListener("click", () => {
  if (state.selected) navigator.clipboard.writeText(state.selected.marketDisplayName);
});

loadMarkets().catch((error) => {
  el.status.textContent = `Failed to load Arcus markets: ${error.message}`;
});
