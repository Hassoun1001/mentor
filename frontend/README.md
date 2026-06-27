# Mentor — Frontend

Vite + React 18 + TypeScript (strict) + Tailwind + TanStack Query + Zod.

```bash
npm install
npm run dev          # → http://localhost:5173 (proxies /api to :8000)
npm run typecheck
npm run lint
npm run build
```

## Layout

```
src/
├── api/              Typed HTTP client (Zod-validated responses)
├── components/       Reusable UI primitives (Field, Metric, Tooltip, TopNav)
├── lib/              Number/money/percent formatters
├── pages/            Top-level screens (currently: RiskCalculatorPage)
├── App.tsx           Page router shell
└── main.tsx          React + QueryClient bootstrap
```

## Design language

The plan asks for "a calm, uncluttered interface in both light and dark
modes." The default theme is dark — a deep teal palette set in
`tailwind.config.js` (`mentor.bg`, `mentor.panel`, `mentor.accent`).
Numbers are monospace so columns align across metrics; headings are serif
to echo the print-style product spec.

Every metric label is a `<Tooltip>` — hover or focus to see the mentor's
plain-language explanation, computed from the same vocabulary as the
backend domain.

## Money & decimals on the wire

The API ships decimals as JSON strings to avoid float precision loss.
The Zod schemas in `api/risk.ts` keep them as strings; `lib/format.ts`
parses them only at the moment of display. Never store API decimals in
`number` state.
