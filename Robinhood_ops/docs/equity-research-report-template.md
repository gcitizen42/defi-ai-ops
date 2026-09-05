# Equity Research Report Template

Date stored: 2026-09-03

## Purpose

Use this prompt when we need a beginner-friendly public-source equity research report for a company or ticker. This is useful for the trading control center when evaluating tokenized equities, related-market context, or stock-linked perps.

## Prompt

```text
Act as a senior equity research analyst at a top-tier firm. Write a clear, beginner-friendly research report on [COMPANY / TICKER].

Include these sections:
- Company overview and business model
- Revenue streams and how the company makes money
- Last 3-5 years of financial performance plus the most recent quarter
- Industry landscape and market position
- Key growth drivers
- Main risks
- Management assessment
- Simple key metrics table (revenue, growth, margins, cash, debt)

Use only recent public sources (10-K, 10-Q, earnings releases, investor presentations, reputable news). Cite sources with dates. Clearly separate facts from assumptions. Do not give a buy, sell, or hold recommendation.
```

## Control Center Use

Use this for:

- Arcus tokenized equity context;
- stock-linked perps context;
- related-market analysis for assets like MSTR, COIN, NVDA, AMD, QQQ, SPY;
- pre-trade fundamental background;
- longer-horizon thesis checks.

Do not use it as a standalone trade signal. It should feed the `Research Agent` and `Risk Agent`, while execution still depends on market data, volatility, liquidity, and stop/target feasibility.

