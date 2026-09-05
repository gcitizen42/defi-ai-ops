# Market Ops Lab Market UI

Local UI for exploring public Arcus market data. It proxies public REST endpoints only and does not read local secrets or place trades.

## Requirements

- Node.js 18+

## Run

```bash
npm install
npm start
```

Then open `http://localhost:4173`.

Use `PORT` to run on another port:

```bash
PORT=4174 npm start
```
