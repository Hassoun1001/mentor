/**
 * Themed SVG diagrams for the "Under the hood" lessons.
 *
 * Each figure is a small, static, vector illustration (no data fetching) that
 * scales via viewBox and themes with the app via `currentColor` + `text-mentor-*`
 * classes — the same approach as ReliabilityDiagram.tsx. A lesson references a
 * figure by `key`; unknown keys render nothing (defensive).
 */
import type { ReactNode } from 'react';

type Tone = 'fg' | 'muted' | 'border' | 'accent' | 'accentSoft' | 'warn' | 'danger';

const TONE: Record<Tone, string> = {
  fg: 'text-mentor-fg',
  muted: 'text-mentor-muted',
  border: 'text-mentor-border',
  accent: 'text-mentor-accent',
  accentSoft: 'text-mentor-accentSoft',
  warn: 'text-mentor-warn',
  danger: 'text-mentor-danger',
};

// ---- primitives ----------------------------------------------------------

function Box({
  x,
  y,
  w,
  h,
  tone = 'border',
  fill = false,
}: {
  x: number;
  y: number;
  w: number;
  h: number;
  tone?: Tone;
  fill?: boolean;
}) {
  return (
    <rect
      x={x}
      y={y}
      width={w}
      height={h}
      rx={7}
      className={TONE[tone]}
      stroke="currentColor"
      strokeWidth={1.4}
      fill={fill ? 'currentColor' : 'none'}
      fillOpacity={fill ? 0.08 : 1}
    />
  );
}

function T({
  x,
  y,
  tone = 'fg',
  size = 10,
  anchor = 'middle',
  bold = false,
  children,
}: {
  x: number;
  y: number;
  tone?: Tone;
  size?: number;
  anchor?: 'start' | 'middle' | 'end';
  bold?: boolean;
  children: ReactNode;
}) {
  return (
    <text
      x={x}
      y={y}
      textAnchor={anchor}
      fontSize={size}
      className={TONE[tone]}
      fill="currentColor"
      fontWeight={bold ? 600 : 400}
    >
      {children}
    </text>
  );
}

function Arrow({
  x1,
  y1,
  x2,
  y2,
  tone = 'muted',
  dashed = false,
}: {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  tone?: Tone;
  dashed?: boolean;
}) {
  const a = Math.atan2(y2 - y1, x2 - x1);
  const s = 5;
  const hx1 = x2 - s * Math.cos(a - Math.PI / 6);
  const hy1 = y2 - s * Math.sin(a - Math.PI / 6);
  const hx2 = x2 - s * Math.cos(a + Math.PI / 6);
  const hy2 = y2 - s * Math.sin(a + Math.PI / 6);
  return (
    <g className={TONE[tone]} stroke="currentColor" fill="currentColor">
      <line
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        strokeWidth={1.4}
        strokeDasharray={dashed ? '4 3' : undefined}
      />
      <polygon points={`${x2},${y2} ${hx1},${hy1} ${hx2},${hy2}`} stroke="none" />
    </g>
  );
}

function Svg({ children, vb = '0 0 440 210' }: { children: ReactNode; vb?: string }) {
  return (
    <svg viewBox={vb} className="w-full" role="img" preserveAspectRatio="xMidYMid meet">
      {children}
    </svg>
  );
}

// ---- figures -------------------------------------------------------------

function HonestThesis() {
  return (
    <Svg vb="0 0 440 200">
      <T x={110} y={22} bold>
        Predicting DIRECTION
      </T>
      {/* coin-flip baseline */}
      <line x1={20} y1={120} x2={200} y2={120} className={TONE.muted} stroke="currentColor" strokeDasharray="4 3" />
      <T x={20} y={134} tone="muted" size={8} anchor="start">
        50% — coin flip
      </T>
      <Box x={70} y={100} w={70} h={45} tone="danger" fill />
      <T x={105} y={127} tone="danger" bold size={13}>
        ~53%
      </T>
      <T x={110} y={165} tone="muted" size={8}>
        barely above chance
      </T>

      <line x1={220} y1={20} x2={220} y2={185} className={TONE.border} stroke="currentColor" />

      <T x={330} y={22} bold>
        Predicting the RANGE
      </T>
      {/* volatility clusters -> predictable */}
      <polyline
        points="250,150 268,120 286,150 304,90 322,150 340,70 358,150 376,60 394,150 412,80"
        className={TONE.accent}
        stroke="currentColor"
        strokeWidth={1.6}
        fill="none"
      />
      <T x={330} y={175} tone="accentSoft" size={9} bold>
        clusters → forecastable ✓
      </T>
    </Svg>
  );
}

function DataPipeline() {
  const sources: [string, string][] = [
    ['Prices', 'Twelve Data · Yahoo'],
    ['Rates · $ · VIX', 'FRED'],
    ['News mood', 'GDELT'],
  ];
  return (
    <Svg vb="0 0 460 210">
      {sources.map(([a, b], i) => {
        const y = 25 + i * 58;
        return (
          <g key={a}>
            <Box x={12} y={y} w={120} h={42} />
            <T x={72} y={y + 19} bold size={10}>
              {a}
            </T>
            <T x={72} y={y + 33} tone="muted" size={8}>
              {b}
            </T>
            <Arrow x1={132} y1={y + 21} x2={168} y2={105} />
          </g>
        );
      })}
      <Box x={170} y={86} w={90} h={40} tone="accent" />
      <T x={215} y={103} bold size={10}>
        Clean &
      </T>
      <T x={215} y={117} bold size={10}>
        align
      </T>
      <Arrow x1={260} y1={106} x2={296} y2={106} />
      <Box x={298} y={86} w={70} h={40} />
      <T x={333} y={110} bold size={10}>
        Features
      </T>
      <Arrow x1={368} y1={106} x2={404} y2={106} />
      <Box x={406} y={80} w={46} h={52} tone="accent" fill />
      <T x={429} y={102} bold size={9}>
        Models
      </T>
      <T x={429} y={118} tone="accentSoft" size={8}>
        forecast
      </T>
    </Svg>
  );
}

function FeatureFamilies() {
  const groups: [string, string[], Tone][] = [
    ['Price & indicators', ['returns, EMA gap', 'RSI, MACD, ATR', 'highs / lows'], 'fg'],
    ['News mood', ['GDELT tone', 'is it turning?'], 'accentSoft'],
    ['Macro drivers', ['US rates, 2s10s', 'dollar index, VIX'], 'accent'],
  ];
  return (
    <Svg vb="0 0 440 210">
      {groups.map(([title, items, tone], i) => {
        const y = 14 + i * 62;
        return (
          <g key={title}>
            <Box x={12} y={y} w={210} h={54} tone={tone} />
            <T x={22} y={y + 18} anchor="start" bold size={10} tone={tone}>
              {title}
            </T>
            {items.map((it, j) => (
              <T key={it} x={22} y={y + 33 + j * 12} anchor="start" tone="muted" size={8}>
                • {it}
              </T>
            ))}
            <Arrow x1={222} y1={y + 27} x2={330} y2={105} tone="muted" />
          </g>
        );
      })}
      <Box x={332} y={82} w={96} h={46} tone="accent" fill />
      <T x={380} y={102} bold>
        Model
      </T>
      <T x={380} y={118} tone="muted" size={8}>
        probability
      </T>
    </Svg>
  );
}

function PointInTime() {
  const nowX = 250;
  return (
    <Svg vb="0 0 440 170">
      {/* past shaded */}
      <rect x={20} y={55} width={nowX - 20} height={40} className={TONE.accent} fill="currentColor" fillOpacity={0.1} />
      <rect x={nowX} y={55} width={170} height={40} className={TONE.muted} fill="currentColor" fillOpacity={0.06} />
      <line x1={20} y1={95} x2={430} y2={95} className={TONE.border} stroke="currentColor" />
      {/* now line */}
      <line x1={nowX} y1={35} x2={nowX} y2={115} className={TONE.accent} stroke="currentColor" strokeWidth={1.6} />
      <T x={nowX} y={28} tone="accent" bold size={10}>
        now (t)
      </T>
      <circle cx={nowX} cy={95} r={4} className={TONE.accent} fill="currentColor" />
      {/* target in future */}
      <circle cx={410} cy={95} r={5} className={TONE.warn} fill="none" stroke="currentColor" strokeWidth={1.6} />
      <line x1={405} y1={90} x2={415} y2={100} className={TONE.warn} stroke="currentColor" />
      <line x1={415} y1={90} x2={405} y2={100} className={TONE.warn} stroke="currentColor" />
      <T x={410} y={128} tone="warn" size={9}>
        t + H
      </T>
      <T x={135} y={128} tone="accentSoft" size={9} bold>
        PAST — features built here
      </T>
      <T x={340} y={143} tone="muted" size={9} bold>
        FUTURE — the answer
      </T>
    </Svg>
  );
}

function DirectionModel() {
  const stages: [string, string, Tone][] = [
    ['Rule baseline', 'the yardstick', 'muted'],
    ['Boosted trees', 'reads features', 'fg'],
    ['Regime check', 'shrinks if odd', 'accent'],
  ];
  return (
    <Svg vb="0 0 460 180">
      {stages.map(([a, b, tone], i) => {
        const x = 12 + i * 130;
        return (
          <g key={a}>
            <Box x={x} y={60} w={110} h={48} tone={tone} />
            <T x={x + 55} y={82} bold size={10}>
              {a}
            </T>
            <T x={x + 55} y={97} tone="muted" size={8}>
              {b}
            </T>
            {i < 2 && <Arrow x1={x + 110} y1={84} x2={x + 130} y2={84} />}
          </g>
        );
      })}
      <Arrow x1={402} y1={84} x2={424} y2={84} tone="accent" />
      <T x={432} y={80} tone="accentSoft" bold size={11} anchor="middle">
        55%
      </T>
      <T x={432} y={95} tone="muted" size={7}>
        ± band
      </T>
      <T x={175} y={140} tone="warn" size={9} bold>
        the trees ship ONLY if they beat the rule out-of-sample
      </T>
    </Svg>
  );
}

function VolCone() {
  return (
    <Svg vb="0 0 440 190">
      <line x1={20} y1={95} x2={420} y2={95} className={TONE.border} stroke="currentColor" strokeDasharray="3 3" />
      {/* history line */}
      <polyline points="20,110 60,85 100,100 140,95" className={TONE.fg} stroke="currentColor" strokeWidth={1.6} fill="none" />
      <circle cx={140} cy={95} r={3} className={TONE.accent} fill="currentColor" />
      {/* 90% conformal band (wide) */}
      <polygon points="140,95 420,35 420,155" className={TONE.accentSoft} fill="currentColor" fillOpacity={0.1} />
      {/* 1 sigma band (narrow) */}
      <polygon points="140,95 420,68 420,122" className={TONE.accent} fill="currentColor" fillOpacity={0.2} />
      <line x1={140} y1={95} x2={420} y2={95} className={TONE.accent} stroke="currentColor" strokeDasharray="2 3" />
      <T x={300} y={60} tone="accentSoft" size={9}>
        ~90% coverage band
      </T>
      <T x={300} y={112} tone="accent" size={9} bold>
        ±1σ expected move
      </T>
      <T x={135} y={175} tone="muted" size={9}>
        today
      </T>
      <T x={400} y={175} tone="muted" size={9}>
        + H days
      </T>
    </Svg>
  );
}

function Reliability() {
  const S = 150;
  const P = 22;
  const x = (v: number) => P + v * (S - 2 * P);
  const y = (v: number) => S - P - v * (S - 2 * P);
  const raw: [number, number][] = [
    [0.15, 0.32],
    [0.35, 0.44],
    [0.55, 0.52],
    [0.75, 0.6],
    [0.9, 0.66],
  ];
  return (
    <Svg vb="0 0 320 170">
      <g transform="translate(6,8)">
        <rect x={P} y={P} width={S - 2 * P} height={S - 2 * P} className={TONE.border} stroke="currentColor" fill="none" />
        <line x1={x(0)} y1={y(0)} x2={x(1)} y2={y(1)} className={TONE.muted} stroke="currentColor" strokeDasharray="4 3" />
        {/* raw (off diagonal) */}
        <polyline points={raw.map(([a, b]) => `${x(a)},${y(b)}`).join(' ')} className={TONE.danger} stroke="currentColor" strokeWidth={1.5} fill="none" />
        {/* calibrated (on diagonal) */}
        <polyline points={raw.map(([a]) => `${x(a)},${y(a)}`).join(' ')} className={TONE.accent} stroke="currentColor" strokeWidth={1.5} fill="none" />
        <T x={S / 2} y={S - 4} tone="muted" size={8}>
          predicted
        </T>
      </g>
      <T x={205} y={40} anchor="start" tone="muted" size={9}>
        dashed = perfect
      </T>
      <T x={205} y={62} anchor="start" tone="danger" size={9}>
        — raw scores
      </T>
      <T x={205} y={84} anchor="start" tone="accent" size={9}>
        — calibrated
      </T>
      <T x={205} y={112} anchor="start" tone="fg" size={9} bold>
        ECE halved
      </T>
      <T x={205} y={128} anchor="start" tone="muted" size={8}>
        now 60% means 60%
      </T>
    </Svg>
  );
}

function LearningLoop() {
  const nodes: [string, number, number, Tone][] = [
    ['Predict', 220, 30, 'accent'],
    ['Resolve', 360, 105, 'fg'],
    ['Post-mortem', 220, 180, 'fg'],
    ['Champion vs\nchallenger', 80, 105, 'accentSoft'],
  ];
  return (
    <Svg vb="0 0 440 210">
      {nodes.map(([label, cx, cy, tone]) => (
        <g key={label}>
          <Box x={cx - 58} y={cy - 20} w={116} h={40} tone={tone} />
          {label.split('\n').map((ln, i) => (
            <T key={ln} x={cx} y={cy - 2 + i * 12} bold size={10} tone={tone}>
              {ln}
            </T>
          ))}
        </g>
      ))}
      <Arrow x1={278} y1={40} x2={330} y2={88} tone="muted" />
      <Arrow x1={330} y1={125} x2={278} y2={168} tone="muted" />
      <Arrow x1={162} y1={168} x2={110} y2={125} tone="muted" />
      <Arrow x1={110} y1={88} x2={162} y2={42} tone="muted" />
      <T x={220} y={112} tone="warn" size={8} bold>
        promote only
      </T>
      <T x={220} y={124} tone="warn" size={8} bold>
        if it wins
      </T>
    </Svg>
  );
}

function RiskSizing() {
  const steps: [string, string, Tone][] = [
    ['Expected move', '±X pips', 'accent'],
    ['Stop', '≈ 1.5× move', 'fg'],
    ['Size', 'risk% ÷ stop', 'fg'],
    ['Position', 'rounded down', 'accentSoft'],
  ];
  return (
    <Svg vb="0 0 470 150">
      {steps.map(([a, b, tone], i) => {
        const x = 10 + i * 116;
        return (
          <g key={a}>
            <Box x={x} y={45} w={98} h={46} tone={tone} />
            <T x={x + 49} y={66} bold size={10}>
              {a}
            </T>
            <T x={x + 49} y={81} tone="muted" size={8}>
              {b}
            </T>
            {i < 3 && <Arrow x1={x + 98} y1={68} x2={x + 116} y2={68} />}
          </g>
        );
      })}
      <T x={235} y={122} tone="muted" size={9}>
        the risk budget is a ceiling — never a target
      </T>
    </Svg>
  );
}

function Tipster() {
  const steps = ['Message', 'Parse', 'Price @ mention', 'Scorecard', 'Leaderboard'];
  return (
    <Svg vb="0 0 460 190">
      {steps.map((s, i) => {
        const x = 8 + i * 92;
        return (
          <g key={s}>
            <Box x={x} y={25} w={80} h={38} tone={i === 4 ? 'accent' : 'border'} />
            <T x={x + 40} y={48} size={9} bold>
              {s}
            </T>
            {i < 4 && <Arrow x1={x + 80} y1={44} x2={x + 100} y2={44} />}
          </g>
        );
      })}
      {/* follow-him equity curve (honest: declines) */}
      <T x={230} y={95} tone="muted" size={9}>
        "what if I'd followed him?" — the honest equity curve
      </T>
      <rect x={40} y={105} width={380} height={70} className={TONE.border} stroke="currentColor" fill="none" />
      <polyline
        points="45,120 100,128 150,124 210,140 270,150 330,160 415,168"
        className={TONE.danger}
        stroke="currentColor"
        strokeWidth={1.6}
        fill="none"
      />
      <T x={52} y={118} tone="muted" size={7} anchor="start">
        $10k
      </T>
    </Svg>
  );
}

// ---- figures: general curriculum ----------------------------------------

function PairRatio() {
  return (
    <Svg vb="0 0 440 180">
      <circle cx={120} cy={70} r={34} className={TONE.accent} stroke="currentColor" fill="currentColor" fillOpacity={0.12} />
      <T x={120} y={74} bold size={13} tone="accent">
        EUR
      </T>
      <T x={220} y={64} size={22} tone="muted">
        ÷
      </T>
      <circle cx={320} cy={70} r={34} className={TONE.fg} stroke="currentColor" fill="currentColor" fillOpacity={0.08} />
      <T x={320} y={74} bold size={13}>
        USD
      </T>
      <T x={220} y={140} size={11} bold>
        EUR/USD = how many dollars one euro costs
      </T>
      <T x={220} y={160} size={9} tone="muted">
        you trade the relationship, never one currency alone
      </T>
    </Svg>
  );
}

function Leverage() {
  return (
    <Svg vb="0 0 440 170">
      <Box x={20} y={60} w={90} h={48} />
      <T x={65} y={80} bold size={10}>
        $1,000
      </T>
      <T x={65} y={95} tone="muted" size={8}>
        your margin
      </T>
      <Arrow x1={112} y1={84} x2={168} y2={84} tone="accent" />
      <T x={140} y={74} tone="accent" size={9} bold>
        ×100
      </T>
      <Box x={172} y={45} w={150} h={78} tone="accent" fill />
      <T x={247} y={80} bold size={13} tone="accent">
        $100,000
      </T>
      <T x={247} y={98} tone="muted" size={8}>
        controlled exposure
      </T>
      <T x={220} y={150} tone="warn" size={9} bold>
        gains AND losses are magnified the same way
      </T>
    </Svg>
  );
}

function Spread() {
  const rows: [string, number, Tone][] = [
    ['1.0853  ask', 40, 'danger'],
    ['1.0852', 62, 'muted'],
    ['1.0851', 84, 'muted'],
    ['1.0850  bid', 106, 'accent'],
  ];
  return (
    <Svg vb="0 0 440 170">
      <rect x={150} y={34} width={140} height={84} className={TONE.warn} fill="currentColor" fillOpacity={0.1} />
      {rows.map(([label, y, tone]) => (
        <g key={label}>
          <line x1={150} y1={y} x2={290} y2={y} className={TONE.border} stroke="currentColor" />
          <T x={300} y={y + 3} anchor="start" size={9} tone={tone}>
            {label}
          </T>
        </g>
      ))}
      <T x={90} y={78} anchor="end" size={10} bold tone="warn">
        spread
      </T>
      <T x={220} y={150} size={9} bold>
        the bid–ask gap is a fee you pay on every round trip
      </T>
    </Svg>
  );
}

function RiskVsPredict() {
  return (
    <Svg vb="0 0 440 190">
      <line x1={20} y1={150} x2={420} y2={150} className={TONE.border} stroke="currentColor" />
      {/* reckless: 55% win, 10% risk -> ruin */}
      <polyline points="20,120 70,90 120,120 170,70 220,140 270,175 320,178 380,178" className={TONE.danger} stroke="currentColor" strokeWidth={1.6} fill="none" />
      <T x={330} y={172} anchor="start" size={9} tone="danger">
        55% win · 10% risk
      </T>
      {/* disciplined: 45% win, 1% risk -> grind up */}
      <polyline points="20,140 70,135 120,138 170,128 220,120 270,108 320,95 400,78" className={TONE.accent} stroke="currentColor" strokeWidth={1.6} fill="none" />
      <T x={300} y={70} anchor="start" size={9} tone="accent">
        45% win · 1% risk
      </T>
      <T x={220} y={24} size={11} bold>
        Sizing beats accuracy
      </T>
    </Svg>
  );
}

function DrawdownRecovery() {
  const rows: [string, number][] = [
    ['lose 10%', 11],
    ['lose 25%', 33],
    ['lose 50%', 100],
    ['lose 80%', 400],
  ];
  return (
    <Svg vb="0 0 440 190">
      <T x={220} y={20} size={11} bold>
        The gain needed just to get back to even
      </T>
      {rows.map(([label, gain], i) => {
        const y = 40 + i * 34;
        const w = Math.min(300, gain * 0.75);
        const tone: Tone = gain >= 100 ? 'danger' : gain >= 33 ? 'warn' : 'muted';
        return (
          <g key={label}>
            <T x={95} y={y + 15} anchor="end" size={9}>
              {label}
            </T>
            <rect x={105} y={y + 4} width={w} height={16} rx={3} className={TONE[tone]} fill="currentColor" fillOpacity={0.5} />
            <T x={110 + w} y={y + 16} anchor="start" size={9} bold tone={tone}>
              +{gain}%
            </T>
          </g>
        );
      })}
    </Svg>
  );
}

function SizeFormula() {
  return (
    <Svg vb="0 0 440 170">
      <Box x={12} y={40} w={100} h={44} tone="accent" />
      <T x={62} y={60} bold size={9}>
        risk $
      </T>
      <T x={62} y={74} tone="muted" size={8}>
        account × 1%
      </T>
      <T x={120} y={68} size={16} tone="muted">
        ÷
      </T>
      <Box x={140} y={40} w={130} h={44} />
      <T x={205} y={60} bold size={9}>
        stop distance
      </T>
      <T x={205} y={74} tone="muted" size={8}>
        × pip value
      </T>
      <T x={278} y={68} size={16} tone="muted">
        =
      </T>
      <Box x={298} y={40} w={80} h={44} tone="accentSoft" fill />
      <T x={338} y={66} bold size={12}>
        lots
      </T>
      <T x={220} y={125} tone="warn" size={9} bold>
        notice the target isn't in the formula — the stop is a fact, the target a hope
      </T>
    </Svg>
  );
}

function Guardrails() {
  const rows: [string, string, Tone][] = [
    ['Per-trade cap', 'one position', 'muted'],
    ['Open-risk cap', 'all trades combined', 'accent'],
    ['Daily loss limit', 'stop for the day', 'danger'],
  ];
  return (
    <Svg vb="0 0 440 175">
      {rows.map(([a, b, tone], i) => {
        const y = 25 + i * 45;
        return (
          <g key={a}>
            <Box x={70} y={y} w={300} h={34} tone={tone} />
            <T x={85} y={y + 22} anchor="start" bold size={10} tone={tone}>
              {a}
            </T>
            <T x={355} y={y + 22} anchor="end" size={8} tone="muted">
              {b}
            </T>
          </g>
        );
      })}
      <T x={220} y={168} tone="muted" size={9}>
        the daily loss limit is the one that stops revenge trading
      </T>
    </Svg>
  );
}

function TrendContext() {
  return (
    <Svg vb="0 0 440 175">
      <line x1={20} y1={140} x2={420} y2={40} className={TONE.accent} stroke="currentColor" strokeWidth={1.4} strokeDasharray="5 3" />
      <polyline points="20,150 70,138 120,142 170,118 220,124 270,96 320,102 370,72 410,60" className={TONE.fg} stroke="currentColor" strokeWidth={1.6} fill="none" />
      <circle cx={270} cy={96} r={16} className={TONE.warn} stroke="currentColor" fill="none" strokeWidth={1.4} />
      <T x={270} y={62} tone="warn" size={8}>
        "obvious" pattern
      </T>
      <T x={220} y={158} size={9} bold>
        use the chart for CONTEXT (trend, volatility) — the obvious setup is already priced
      </T>
    </Svg>
  );
}

function SrZones() {
  return (
    <Svg vb="0 0 440 175">
      <rect x={20} y={40} width={400} height={20} className={TONE.danger} fill="currentColor" fillOpacity={0.12} />
      <T x={30} y={54} anchor="start" size={8} tone="danger">
        resistance zone
      </T>
      <rect x={20} y={120} width={400} height={20} className={TONE.accent} fill="currentColor" fillOpacity={0.12} />
      <T x={30} y={134} anchor="start" size={8} tone="accent">
        support zone
      </T>
      <polyline points="20,130 70,60 120,125 170,55 230,128 300,62 360,124 410,70" className={TONE.fg} stroke="currentColor" strokeWidth={1.6} fill="none" />
      <T x={220} y={165} size={9} bold>
        levels are zones the market remembers — not exact lines
      </T>
    </Svg>
  );
}

function CandleAnatomy() {
  return (
    <Svg vb="0 0 440 190">
      {/* bullish candle */}
      <line x1={150} y1={30} x2={150} y2={60} className={TONE.accent} stroke="currentColor" strokeWidth={1.4} />
      <rect x={134} y={60} width={32} height={60} className={TONE.accent} stroke="currentColor" fill="currentColor" fillOpacity={0.15} />
      <line x1={150} y1={120} x2={150} y2={155} className={TONE.accent} stroke="currentColor" strokeWidth={1.4} />
      <T x={210} y={38} anchor="start" size={9}>
        high — top wick
      </T>
      <T x={210} y={68} anchor="start" size={9}>
        open / close = body
      </T>
      <T x={210} y={152} anchor="start" size={9}>
        low — bottom wick
      </T>
      <Arrow x1={205} y1={35} x2={158} y2={40} tone="muted" />
      <Arrow x1={205} y1={90} x2={170} y2={90} tone="muted" />
      <Arrow x1={205} y1={149} x2={158} y2={145} tone="muted" />
      <T x={220} y={180} size={9} bold>
        four numbers per bar — that's the whole signal
      </T>
    </Svg>
  );
}

function MaLag() {
  return (
    <Svg vb="0 0 440 170">
      <polyline points="20,120 60,90 100,110 140,70 180,95 220,55 260,80 300,45 340,70 380,35 415,55" className={TONE.fg} stroke="currentColor" strokeWidth={1.6} fill="none" />
      <polyline points="20,125 60,118 100,112 140,102 180,96 220,86 260,80 300,72 340,66 380,58 415,52" className={TONE.accent} stroke="currentColor" strokeWidth={1.8} fill="none" />
      <T x={100} y={150} anchor="start" size={9} tone="accent" bold>
        moving average — always a step behind
      </T>
      <T x={350} y={28} anchor="end" size={9} tone="muted">
        price
      </T>
      <T x={220} y={168} size={9}>
        great as a trend filter, useless as a turn signal
      </T>
    </Svg>
  );
}

function RsiRegime() {
  const S = 40;
  return (
    <Svg vb="0 0 440 190">
      {/* price trending up */}
      <polyline points="20,90 90,75 160,80 230,55 300,60 380,35" className={TONE.fg} stroke="currentColor" strokeWidth={1.6} fill="none" />
      <T x={30} y={30} anchor="start" size={9} tone="muted">
        price keeps trending up ↑
      </T>
      {/* rsi panel */}
      <rect x={20} y={115} width={400} height={55} className={TONE.border} stroke="currentColor" fill="none" />
      <line x1={20} y1={128} x2={420} y2={128} className={TONE.danger} stroke="currentColor" strokeDasharray="3 3" />
      <T x={425 - S} y={126} anchor="start" size={7} tone="danger">
        70
      </T>
      <polyline points="20,140 90,132 160,130 230,126 300,129 380,127" className={TONE.warn} stroke="currentColor" strokeWidth={1.5} fill="none" />
      <T x={220} y={186} size={9} bold>
        RSI can pin "overbought" for hours in a trend — it's not a sell button
      </T>
    </Svg>
  );
}

function AtrStop() {
  return (
    <Svg vb="0 0 440 180">
      <rect x={20} y={70} width={400} height={44} className={TONE.muted} fill="currentColor" fillOpacity={0.1} />
      <T x={30} y={65} anchor="start" size={8} tone="muted">
        normal noise band (±ATR)
      </T>
      <polyline points="20,95 70,80 120,100 170,88 220,104 270,84 320,98 370,86 415,92" className={TONE.fg} stroke="currentColor" strokeWidth={1.5} fill="none" />
      <line x1={20} y1={100} x2={420} y2={100} className={TONE.danger} stroke="currentColor" strokeDasharray="4 3" />
      <T x={425} y={103} anchor="end" size={8} tone="danger">
        too-tight stop — inside the noise ✗
      </T>
      <line x1={20} y1={140} x2={420} y2={140} className={TONE.accent} stroke="currentColor" />
      <T x={425} y={135} anchor="end" size={8} tone="accent">
        2–3× ATR stop — beyond the noise ✓
      </T>
    </Svg>
  );
}

function ExpectancyFormula() {
  return (
    <Svg vb="0 0 440 165">
      <T x={220} y={40} size={12} bold>
        (win% × avg win) − (loss% × avg loss)
      </T>
      <T x={220} y={72} size={12} tone="muted">
        (0.40 × 2R) − (0.60 × 1R)
      </T>
      <T x={220} y={104} size={16} bold tone="accent">
        = +0.2R per trade
      </T>
      <T x={220} y={140} size={9}>
        positive expectancy makes money over many trades — even at a 40% win rate
      </T>
    </Svg>
  );
}

function RRuler() {
  const ticks: [number, string, Tone][] = [
    [40, '−1R', 'danger'],
    [140, '0R', 'muted'],
    [240, '+1R', 'fg'],
    [340, '+2R', 'accent'],
    [420, '+3R', 'accentSoft'],
  ];
  return (
    <Svg vb="0 0 440 150">
      <line x1={30} y1={80} x2={425} y2={80} className={TONE.border} stroke="currentColor" strokeWidth={1.6} />
      {ticks.map(([x, label, tone]) => (
        <g key={label}>
          <line x1={x} y1={72} x2={x} y2={88} className={TONE[tone]} stroke="currentColor" strokeWidth={1.6} />
          <T x={x} y={64} size={10} bold tone={tone}>
            {label}
          </T>
        </g>
      ))}
      <T x={40} y={104} size={8} tone="danger">
        stop-out
      </T>
      <T x={220} y={132} size={9}>
        R = outcome ÷ initial risk — one ruler compares every trade and strategy
      </T>
    </Svg>
  );
}

function WinrateMyth() {
  const seq: [number, boolean][] = [
    [1, false],
    [2, false],
    [3, true],
    [4, false],
    [5, false],
    [6, true],
    [7, false],
    [8, false],
  ];
  return (
    <Svg vb="0 0 440 175">
      {seq.map(([n, win], i) => {
        const x = 30 + i * 48;
        const h = win ? 60 : 20;
        const tone: Tone = win ? 'accent' : 'danger';
        return (
          <g key={n}>
            <rect
              x={x}
              y={win ? 100 - h : 100}
              width={30}
              height={h}
              className={TONE[tone]}
              fill="currentColor"
              fillOpacity={0.5}
            />
            <T x={x + 15} y={130} size={8} tone={tone}>
              {win ? '+3R' : '−1R'}
            </T>
          </g>
        );
      })}
      <line x1={20} y1={100} x2={420} y2={100} className={TONE.border} stroke="currentColor" />
      <T x={220} y={158} size={9} bold>
        6 losses, 2 big wins → still +2R. A low win rate can be very profitable.
      </T>
    </Svg>
  );
}

function Lookahead() {
  const nowX = 250;
  return (
    <Svg vb="0 0 440 165">
      <line x1={20} y1={95} x2={420} y2={95} className={TONE.border} stroke="currentColor" />
      <line x1={nowX} y1={45} x2={nowX} y2={120} className={TONE.accent} stroke="currentColor" strokeWidth={1.5} />
      <T x={nowX} y={38} tone="accent" size={9} bold>
        decision at t
      </T>
      {/* forbidden peek from the future */}
      <Arrow x1={400} y1={70} x2={262} y2={88} tone="danger" />
      <line x1={315} y1={62} x2={345} y2={92} className={TONE.danger} stroke="currentColor" strokeWidth={2} />
      <line x1={345} y1={62} x2={315} y2={92} className={TONE.danger} stroke="currentColor" strokeWidth={2} />
      <T x={360} y={55} size={9} tone="danger" anchor="middle">
        no peeking!
      </T>
      <T x={130} y={125} tone="muted" size={8}>
        past (allowed)
      </T>
      <T x={340} y={125} tone="muted" size={8}>
        future (forbidden)
      </T>
      <T x={220} y={152} size={9} bold>
        using future data = a backtest that prints money and a live account that bleeds
      </T>
    </Svg>
  );
}

function Overfitting() {
  const dots = [
    [40, 120],
    [90, 80],
    [140, 110],
    [190, 70],
    [240, 100],
    [290, 60],
    [340, 95],
    [390, 55],
  ];
  return (
    <Svg vb="0 0 440 170">
      {/* overfit wiggly line hitting every dot */}
      <polyline points="40,120 90,80 140,110 190,70 240,100 290,60 340,95 390,55" className={TONE.danger} stroke="currentColor" strokeWidth={1.4} fill="none" />
      {/* smooth generalising line */}
      <line x1={40} y1={112} x2={390} y2={64} className={TONE.accent} stroke="currentColor" strokeWidth={1.6} />
      {dots.map(([x, y]) => (
        <circle key={`${x}`} cx={x} cy={y} r={3} className={TONE.muted} fill="currentColor" />
      ))}
      <T x={110} y={150} anchor="start" size={9} tone="danger">
        overfit: fits every training dot (and the noise)
      </T>
      <T x={220} y={165} size={9} tone="accent">
        simpler line generalises to next year
      </T>
    </Svg>
  );
}

function CostsEraseEdge() {
  return (
    <Svg vb="0 0 440 165">
      <T x={70} y={40} size={9}>
        gross edge
      </T>
      <rect x={70} y={48} width={300} height={22} rx={3} className={TONE.accent} fill="currentColor" fillOpacity={0.45} />
      <T x={70} y={95} size={9}>
        − spread − commission − slippage
      </T>
      <rect x={70} y={103} width={270} height={22} rx={3} className={TONE.danger} fill="currentColor" fillOpacity={0.35} />
      <T x={355} y={120} anchor="start" size={9} bold tone="warn">
        net ≈ 0
      </T>
      <T x={220} y={152} size={9} bold>
        if a strategy needs a frictionless backtest to work, it doesn't work
      </T>
    </Svg>
  );
}

function JournalVsMemory() {
  return (
    <Svg vb="0 0 440 175">
      <Box x={20} y={35} w={185} h={95} tone="danger" />
      <T x={112} y={55} bold size={10} tone="danger">
        Memory
      </T>
      <polyline points="35,110 70,70 105,105 140,60 185,50" className={TONE.danger} stroke="currentColor" strokeWidth={1.5} fill="none" strokeDasharray="3 3" />
      <T x={112} y={124} size={8} tone="muted">
        edits the losses away
      </T>
      <Box x={235} y={35} w={185} h={95} tone="accent" />
      <T x={327} y={55} bold size={10} tone="accent">
        Journal
      </T>
      {[0, 1, 2, 3].map((i) => (
        <line key={i} x1={252} y1={75 + i * 12} x2={405} y2={75 + i * 12} className={TONE.muted} stroke="currentColor" />
      ))}
      <T x={327} y={124} size={8} tone="muted">
        the row is what it is
      </T>
      <T x={220} y={160} size={9} bold>
        write the entry BEFORE the trade — the checklist forces it
      </T>
    </Svg>
  );
}

function TiltSpiral() {
  return (
    <Svg vb="0 0 440 175">
      <polyline points="30,60 90,90 150,55 210,110 270,45 330,130 380,40" className={TONE.danger} stroke="currentColor" strokeWidth={1.8} fill="none" />
      <T x={110} y={40} anchor="start" size={9} tone="danger">
        loss → bigger risk → bigger loss
      </T>
      <line x1={20} y1={145} x2={420} y2={145} className={TONE.accent} stroke="currentColor" strokeWidth={1.6} strokeDasharray="5 3" />
      <T x={220} y={162} size={9} bold tone="accent">
        daily loss limit = the circuit breaker that stops the spiral
      </T>
    </Svg>
  );
}

function ReviewTags() {
  const tags: [string, number, Tone][] = [
    ['moved stop', 6, 'danger'],
    ['FOMO entry', 5, 'warn'],
    ['no plan', 3, 'warn'],
    ['followed rules', 8, 'accent'],
  ];
  return (
    <Svg vb="0 0 440 175">
      <T x={220} y={26} size={11} bold>
        Patterns show up in your tags before your P&L
      </T>
      {tags.map(([label, n, tone], i) => {
        const y = 42 + i * 30;
        return (
          <g key={label}>
            <T x={150} y={y + 15} anchor="end" size={9}>
              {label}
            </T>
            <rect x={160} y={y + 4} width={n * 26} height={16} rx={3} className={TONE[tone]} fill="currentColor" fillOpacity={0.5} />
            <T x={166 + n * 26} y={y + 16} anchor="start" size={9} bold tone={tone}>
              ×{n}
            </T>
          </g>
        );
      })}
    </Svg>
  );
}

// ---- figures: methods & tools --------------------------------------------

function SchoolsOfAnalysis() {
  const lenses: [string, string, Tone][] = [
    ['Technical', 'price & patterns', 'fg'],
    ['Fundamental', 'rates, growth, flows', 'accent'],
    ['Quantitative', 'statistics & code', 'accentSoft'],
    ['Sentiment', 'positioning & mood', 'warn'],
  ];
  return (
    <Svg vb="0 0 440 185">
      <circle cx={220} cy={95} r={26} className={TONE.muted} stroke="currentColor" fill="currentColor" fillOpacity={0.08} />
      <T x={220} y={92} size={9} bold>
        one
      </T>
      <T x={220} y={104} size={9} bold>
        market
      </T>
      {lenses.map(([a, b, tone], i) => {
        const pos = [
          [90, 40],
          [350, 40],
          [90, 150],
          [350, 150],
        ][i] as [number, number];
        return (
          <g key={a}>
            <Box x={pos[0] - 70} y={pos[1] - 18} w={140} h={36} tone={tone} />
            <T x={pos[0]} y={pos[1] - 2} bold size={9} tone={tone}>
              {a}
            </T>
            <T x={pos[0]} y={pos[1] + 11} size={7} tone="muted">
              {b}
            </T>
            <Arrow x1={pos[0] < 220 ? pos[0] + 60 : pos[0] - 60} y1={pos[1] + (pos[1] < 95 ? 14 : -14)} x2={pos[0] < 220 ? 198 : 242} y2={pos[1] < 95 ? 82 : 108} tone="muted" />
          </g>
        );
      })}
    </Svg>
  );
}

function TopDown() {
  const steps: [string, number][] = [
    ['Monthly / weekly — the big trend', 300],
    ['Daily — the current context', 230],
    ['Setup — a location worth trading', 160],
    ['Trigger — the precise entry', 90],
  ];
  return (
    <Svg vb="0 0 440 185">
      {steps.map(([label, w], i) => {
        const y = 25 + i * 38;
        const x = 220 - w / 2;
        const tone: Tone = i === 3 ? 'accent' : 'muted';
        return (
          <g key={label}>
            <rect x={x} y={y} width={w} height={28} rx={4} className={TONE[tone]} stroke="currentColor" fill="currentColor" fillOpacity={0.08} />
            <T x={220} y={y + 18} size={9} tone={i === 3 ? 'accent' : 'fg'} bold={i === 3}>
              {label}
            </T>
            {i < 3 && <Arrow x1={220} y1={y + 28} x2={220} y2={y + 38} tone="muted" />}
          </g>
        );
      })}
      <T x={220} y={182} size={9}>
        zoom from the big picture down to the trigger — never the reverse
      </T>
    </Svg>
  );
}

function EdgePipeline() {
  const steps = ['Idea', 'Backtest', 'Forward test', 'Small live', 'Scale'];
  return (
    <Svg vb="0 0 460 170">
      {steps.map((s, i) => {
        const x = 8 + i * 92;
        const tone: Tone = i === 4 ? 'accent' : 'border';
        return (
          <g key={s}>
            <Box x={x} y={45} w={80} h={38} tone={tone} />
            <T x={x + 40} y={68} size={9} bold>
              {s}
            </T>
            {i < 4 && <Arrow x1={x + 80} y1={64} x2={x + 100} y2={64} />}
            {i > 0 && i < 4 && (
              <>
                <Arrow x1={x + 40} y1={83} x2={x + 40} y2={110} tone="danger" />
                <T x={x + 40} y={124} size={7} tone="danger">
                  fails? drop it
                </T>
              </>
            )}
          </g>
        );
      })}
      <T x={230} y={155} size={9} bold>
        an edge must survive each gate before real money — most ideas don't
      </T>
    </Svg>
  );
}

function PredictableVsNot() {
  const good = ['Trend / momentum', 'Volatility clustering', 'Mean reversion', 'Carry (rate diff)'];
  const bad = ['Chart patterns', 'News timing', 'Round numbers', 'Gut feel'];
  return (
    <Svg vb="0 0 440 190">
      <Box x={16} y={22} w={195} h={150} tone="accent" />
      <T x={113} y={42} bold size={10} tone="accent">
        Has real evidence
      </T>
      {good.map((g, i) => (
        <T key={g} x={30} y={66 + i * 24} anchor="start" size={9}>
          ✓ {g}
        </T>
      ))}
      <Box x={229} y={22} w={195} h={150} tone="danger" />
      <T x={326} y={42} bold size={10} tone="danger">
        Mostly noise
      </T>
      {bad.map((b, i) => (
        <T key={b} x={243} y={66 + i * 24} anchor="start" size={9} tone="muted">
          ✗ {b}
        </T>
      ))}
    </Svg>
  );
}

function Distributions() {
  const bars = [12, 26, 46, 70, 88, 70, 46, 26, 12];
  return (
    <Svg vb="0 0 440 175">
      {bars.map((h, i) => {
        const x = 60 + i * 36;
        const tone: Tone = i === 4 ? 'accent' : 'muted';
        return <rect key={i} x={x} y={120 - h} width={28} height={h} className={TONE[tone]} fill="currentColor" fillOpacity={0.4} />;
      })}
      <line x1={40} y1={120} x2={410} y2={120} className={TONE.border} stroke="currentColor" />
      <line x1={222} y1={20} x2={222} y2={128} className={TONE.accent} stroke="currentColor" strokeDasharray="4 3" />
      <T x={222} y={16} size={8} tone="accent">
        base rate
      </T>
      <T x={80} y={140} anchor="start" size={8} tone="danger">
        bad
      </T>
      <T x={380} y={140} anchor="end" size={8} tone="accent">
        great
      </T>
      <T x={220} y={162} size={9} bold>
        think in distributions and odds, not single certain outcomes
      </T>
    </Svg>
  );
}

function ChartsPlatforms() {
  return (
    <Svg vb="0 0 440 180">
      <rect x={20} y={20} width={400} height={140} rx={6} className={TONE.border} stroke="currentColor" fill="none" />
      {/* candles */}
      {[0, 1, 2, 3, 4, 5, 6].map((i) => {
        const x = 45 + i * 30;
        const up = i % 2 === 0;
        const tone: Tone = up ? 'accent' : 'danger';
        const top = 45 + (i % 3) * 8;
        const h = 24 + (i % 2) * 10;
        return (
          <g key={i}>
            <line x1={x} y1={top - 8} x2={x} y2={top + h + 8} className={TONE[tone]} stroke="currentColor" />
            <rect x={x - 6} y={top} width={12} height={h} className={TONE[tone]} stroke="currentColor" fill="currentColor" fillOpacity={0.2} />
          </g>
        );
      })}
      {/* indicator sub-panel */}
      <line x1={30} y1={125} x2={270} y2={125} className={TONE.border} stroke="currentColor" />
      <polyline points="35,140 75,132 115,138 155,128 195,134 260,126" className={TONE.warn} stroke="currentColor" strokeWidth={1.4} fill="none" />
      <T x={345} y={60} anchor="start" size={9} bold>
        TradingView
      </T>
      <T x={345} y={78} anchor="start" size={8} tone="muted">
        MT4 / MT5
      </T>
      <T x={345} y={94} anchor="start" size={8} tone="muted">
        broker apps
      </T>
      <T x={345} y={118} anchor="start" size={8} tone="muted">
        drawing,
      </T>
      <T x={345} y={130} anchor="start" size={8} tone="muted">
        indicators,
      </T>
      <T x={345} y={142} anchor="start" size={8} tone="muted">
        alerts
      </T>
    </Svg>
  );
}

function DataCalendar() {
  const feeds: [string, string][] = [
    ['Economic calendar', 'ForexFactory'],
    ['Rates & macro', 'FRED'],
    ['Prices', 'Yahoo · Twelve Data'],
    ['News mood', 'GDELT'],
  ];
  return (
    <Svg vb="0 0 460 185">
      {feeds.map(([a, b], i) => {
        const y = 20 + i * 40;
        return (
          <g key={a}>
            <Box x={12} y={y} w={190} h={32} />
            <T x={24} y={y + 15} anchor="start" bold size={9}>
              {a}
            </T>
            <T x={24} y={y + 27} anchor="start" size={7} tone="muted">
              {b}
            </T>
            <Arrow x1={202} y1={y + 16} x2={300} y2={95} tone="muted" />
          </g>
        );
      })}
      <Box x={302} y={72} w={130} h={46} tone="accent" fill />
      <T x={367} y={92} bold size={10}>
        Your analysis
      </T>
      <T x={367} y={107} size={8} tone="muted">
        one clean picture
      </T>
    </Svg>
  );
}

function RiskTools() {
  const tools: [string, string, Tone][] = [
    ['Position-size calc', 'risk → lots', 'accent'],
    ['Trade journal', 'the record', 'fg'],
    ['Spreadsheet', 'expectancy, R', 'muted'],
  ];
  return (
    <Svg vb="0 0 440 165">
      {tools.map(([a, b, tone], i) => {
        const x = 20 + i * 140;
        return (
          <g key={a}>
            <Box x={x} y={40} w={120} h={60} tone={tone} />
            <T x={x + 60} y={66} bold size={10} tone={tone}>
              {a}
            </T>
            <T x={x + 60} y={84} size={8} tone="muted">
              {b}
            </T>
          </g>
        );
      })}
      <T x={220} y={135} size={9} bold>
        the boring tools protect the account — this app is your calc + journal
      </T>
    </Svg>
  );
}

function AutomationStack() {
  const steps: [string, string][] = [
    ['Screener', 'find candidates'],
    ['Alerts', 'wait, don’t stare'],
    ['Python / pandas', 'test & automate'],
  ];
  return (
    <Svg vb="0 0 460 160">
      {steps.map(([a, b], i) => {
        const x = 20 + i * 150;
        const tone: Tone = i === 2 ? 'accentSoft' : 'border';
        return (
          <g key={a}>
            <Box x={x} y={45} w={120} h={52} tone={tone} />
            <T x={x + 60} y={68} bold size={10}>
              {a}
            </T>
            <T x={x + 60} y={85} size={8} tone="muted">
              {b}
            </T>
            {i < 2 && <Arrow x1={x + 120} y1={71} x2={x + 170} y2={71} />}
          </g>
        );
      })}
      <T x={230} y={130} size={9}>
        automate the tedious parts — never the risk discipline
      </T>
    </Svg>
  );
}

function WeeklyRoutine() {
  const nodes: [string, number, number, Tone][] = [
    ['Plan', 220, 32, 'accent'],
    ['Trade', 350, 100, 'fg'],
    ['Journal', 220, 168, 'fg'],
    ['Review', 90, 100, 'accentSoft'],
  ];
  return (
    <Svg vb="0 0 440 200">
      {nodes.map(([label, cx, cy, tone]) => (
        <g key={label}>
          <Box x={cx - 50} y={cy - 18} w={100} h={36} tone={tone} />
          <T x={cx} y={cy + 4} bold size={11} tone={tone}>
            {label}
          </T>
        </g>
      ))}
      <Arrow x1={272} y1={40} x2={322} y2={84} tone="muted" />
      <Arrow x1={322} y1={118} x2={272} y2={160} tone="muted" />
      <Arrow x1={168} y1={160} x2={118} y2={118} tone="muted" />
      <Arrow x1={118} y1={84} x2={168} y2={42} tone="muted" />
      <T x={220} y={104} size={8} tone="muted">
        every week
      </T>
    </Svg>
  );
}

// ---- figures: chart terminology ------------------------------------------

function BullBear() {
  return (
    <Svg vb="0 0 440 180">
      {/* bullish */}
      <Arrow x1={70} y1={130} x2={130} y2={45} tone="accent" />
      <rect x={150} y={50} width={26} height={70} className={TONE.accent} stroke="currentColor" fill="currentColor" fillOpacity={0.2} />
      <line x1={163} y1={38} x2={163} y2={50} className={TONE.accent} stroke="currentColor" />
      <line x1={163} y1={120} x2={163} y2={132} className={TONE.accent} stroke="currentColor" />
      <T x={110} y={155} bold size={11} tone="accent">
        Bullish ↑
      </T>
      <T x={110} y={170} size={8} tone="muted">
        buyers in control
      </T>
      <line x1={220} y1={25} x2={220} y2={160} className={TONE.border} stroke="currentColor" />
      {/* bearish */}
      <Arrow x1={370} y1={45} x2={310} y2={130} tone="danger" />
      <rect x={264} y={55} width={26} height={70} className={TONE.danger} stroke="currentColor" fill="currentColor" fillOpacity={0.2} />
      <line x1={277} y1={43} x2={277} y2={55} className={TONE.danger} stroke="currentColor" />
      <line x1={277} y1={125} x2={277} y2={137} className={TONE.danger} stroke="currentColor" />
      <T x={330} y={155} bold size={11} tone="danger">
        Bearish ↓
      </T>
      <T x={330} y={170} size={8} tone="muted">
        sellers in control
      </T>
    </Svg>
  );
}

function TrendStructure() {
  return (
    <Svg vb="0 0 440 190">
      {/* uptrend: higher highs / higher lows, then a break */}
      <polyline
        points="20,150 70,100 110,125 160,70 200,95 250,45 300,72 340,120 400,150"
        className={TONE.fg}
        stroke="currentColor"
        strokeWidth={1.6}
        fill="none"
      />
      {/* swing highs */}
      <circle cx={70} cy={100} r={3} className={TONE.accent} fill="currentColor" />
      <circle cx={160} cy={70} r={3} className={TONE.accent} fill="currentColor" />
      <circle cx={250} cy={45} r={3} className={TONE.accent} fill="currentColor" />
      <T x={250} y={36} size={8} tone="accent">
        higher high
      </T>
      {/* swing lows */}
      <circle cx={110} cy={125} r={3} className={TONE.accentSoft} fill="currentColor" />
      <circle cx={200} cy={95} r={3} className={TONE.accentSoft} fill="currentColor" />
      <T x={200} y={112} size={8} tone="accentSoft">
        higher low
      </T>
      {/* break of structure */}
      <line x1={200} y1={95} x2={360} y2={95} className={TONE.danger} stroke="currentColor" strokeDasharray="4 3" />
      <circle cx={340} cy={120} r={4} className={TONE.danger} fill="none" stroke="currentColor" strokeWidth={1.6} />
      <T x={365} y={140} anchor="start" size={8} tone="danger">
        breaks the last
      </T>
      <T x={365} y={152} anchor="start" size={8} tone="danger">
        higher low →
      </T>
      <T x={365} y={164} anchor="start" size={8} tone="danger">
        trend in doubt
      </T>
      <T x={130} y={185} size={9} bold>
        an uptrend = higher highs AND higher lows, until the structure breaks
      </T>
    </Svg>
  );
}

function MovesInTrend() {
  return (
    <Svg vb="0 0 440 190">
      <line x1={20} y1={95} x2={250} y2={95} className={TONE.muted} stroke="currentColor" strokeDasharray="4 3" />
      <T x={60} y={88} size={8} tone="muted">
        resistance
      </T>
      <polyline
        points="20,120 60,100 100,110 150,96 200,105 245,70 290,92 330,60 360,110 410,150"
        className={TONE.fg}
        stroke="currentColor"
        strokeWidth={1.6}
        fill="none"
      />
      <circle cx={245} cy={70} r={4} className={TONE.accent} fill="none" stroke="currentColor" strokeWidth={1.5} />
      <T x={245} y={58} size={8} tone="accent">
        breakout
      </T>
      <circle cx={290} cy={92} r={4} className={TONE.accentSoft} fill="none" stroke="currentColor" strokeWidth={1.5} />
      <T x={300} y={92} anchor="start" size={8} tone="accentSoft">
        pullback (buy zone)
      </T>
      <circle cx={360} cy={110} r={4} className={TONE.danger} fill="none" stroke="currentColor" strokeWidth={1.5} />
      <T x={385} y={135} size={8} tone="danger">
        reversal
      </T>
      <T x={150} y={182} size={9} bold>
        breakout → pullback → continuation; a lower low warns of a reversal
      </T>
    </Svg>
  );
}

function CandleTypes() {
  return (
    <Svg vb="0 0 440 190">
      {/* doji */}
      <line x1={70} y1={40} x2={70} y2={130} className={TONE.muted} stroke="currentColor" />
      <rect x={58} y={82} width={24} height={6} className={TONE.muted} stroke="currentColor" fill="currentColor" fillOpacity={0.3} />
      <T x={70} y={150} size={9} bold>
        Doji
      </T>
      <T x={70} y={165} size={7} tone="muted">
        indecision
      </T>
      {/* bullish engulfing */}
      <rect x={168} y={70} width={16} height={28} className={TONE.danger} stroke="currentColor" fill="currentColor" fillOpacity={0.2} />
      <rect x={190} y={55} width={24} height={60} className={TONE.accent} stroke="currentColor" fill="currentColor" fillOpacity={0.25} />
      <T x={196} y={150} size={9} bold tone="accent">
        Engulfing
      </T>
      <T x={196} y={165} size={7} tone="muted">
        buyers take over
      </T>
      {/* pin bar / hammer */}
      <line x1={340} y1={55} x2={340} y2={135} className={TONE.accent} stroke="currentColor" />
      <rect x={329} y={55} width={22} height={18} className={TONE.accent} stroke="currentColor" fill="currentColor" fillOpacity={0.25} />
      <T x={340} y={150} size={9} bold>
        Pin bar
      </T>
      <T x={340} y={165} size={7} tone="muted">
        rejection of lows
      </T>
    </Svg>
  );
}

function Fibonacci() {
  const levels: [number, string, Tone][] = [
    [40, '0% (high)', 'muted'],
    [68, '23.6%', 'muted'],
    [86, '38.2%', 'accent'],
    [100, '50%', 'accent'],
    [114, '61.8%', 'accent'],
    [160, '100% (low)', 'muted'],
  ];
  return (
    <Svg vb="0 0 440 200">
      {/* common pullback zone band */}
      <rect x={60} y={86} width={330} height={28} className={TONE.accent} fill="currentColor" fillOpacity={0.08} />
      {levels.map(([y, label, tone]) => (
        <g key={label}>
          <line x1={60} y1={y} x2={360} y2={y} className={TONE[tone]} stroke="currentColor" strokeDasharray="3 3" />
          <T x={366} y={y + 3} anchor="start" size={8} tone={tone}>
            {label}
          </T>
        </g>
      ))}
      {/* swing up, then pullback into the zone, then continuation */}
      <polyline points="60,160 200,40 300,100 410,55" className={TONE.fg} stroke="currentColor" strokeWidth={1.6} fill="none" />
      <T x={210} y={190} size={9} bold>
        after a swing, price often pauses at 38–62% before continuing
      </T>
    </Svg>
  );
}

function TradeAnatomy() {
  return (
    <Svg vb="0 0 440 185">
      <line x1={150} y1={25} x2={150} y2={160} className={TONE.border} stroke="currentColor" />
      {/* take profit */}
      <line x1={120} y1={45} x2={330} y2={45} className={TONE.accent} stroke="currentColor" />
      <T x={335} y={49} anchor="start" size={9} tone="accent">
        take-profit  +60 pips (+2R)
      </T>
      {/* entry */}
      <line x1={120} y1={100} x2={330} y2={100} className={TONE.fg} stroke="currentColor" strokeWidth={1.5} />
      <circle cx={150} cy={100} r={4} className={TONE.fg} fill="currentColor" />
      <T x={335} y={104} anchor="start" size={9}>
        entry (go long)
      </T>
      {/* stop */}
      <line x1={120} y1={130} x2={330} y2={130} className={TONE.danger} stroke="currentColor" />
      <T x={335} y={134} anchor="start" size={9} tone="danger">
        stop-loss  −30 pips (−1R)
      </T>
      {/* R:R bracket */}
      <T x={95} y={75} anchor="end" size={8} tone="accent">
        reward
      </T>
      <T x={95} y={118} anchor="end" size={8} tone="danger">
        risk
      </T>
      <T x={220} y={178} size={9} bold>
        one picture ties it together: entry, stop, target, pips, and 2:1 R:R
      </T>
    </Svg>
  );
}

// ---- registry ------------------------------------------------------------

// ---- becoming-pro / using-mentor figures ---------------------------------

function OrderTypes() {
  return (
    <Svg vb="0 0 440 210">
      {/* price axis */}
      <line x1={60} y1={20} x2={60} y2={190} className={TONE.border} stroke="currentColor" />
      <line x1={40} y1={105} x2={420} y2={105} className={TONE.fg} stroke="currentColor" strokeWidth={1.8} />
      <T x={425} y={108} anchor="end" size={9} bold>
        current price
      </T>
      {/* buy limit below */}
      <line x1={70} y1={160} x2={230} y2={160} className={TONE.accentSoft} stroke="currentColor" strokeDasharray="5 3" strokeWidth={1.6} />
      <T x={75} y={153} anchor="start" size={9} tone="accentSoft" bold>
        BUY LIMIT — “fill me cheaper”
      </T>
      {/* buy stop above */}
      <line x1={70} y1={50} x2={230} y2={50} className={TONE.accent} stroke="currentColor" strokeDasharray="5 3" strokeWidth={1.6} />
      <T x={75} y={43} anchor="start" size={9} tone="accent" bold>
        BUY STOP — “enter on breakout”
      </T>
      {/* stop-loss for a long */}
      <line x1={250} y1={175} x2={420} y2={175} className={TONE.danger} stroke="currentColor" strokeWidth={1.6} />
      <T x={255} y={168} anchor="start" size={9} tone="danger" bold>
        STOP-LOSS — the exit that caps a long
      </T>
      {/* take profit */}
      <line x1={250} y1={35} x2={420} y2={35} className={TONE.accentSoft} stroke="currentColor" strokeWidth={1.6} />
      <T x={255} y={28} anchor="start" size={9} tone="accentSoft" bold>
        TAKE-PROFIT — the exit that banks it
      </T>
      <Arrow x1={140} y1={110} x2={140} y2={155} tone="muted" dashed />
      <Arrow x1={150} y1={100} x2={150} y2={55} tone="muted" dashed />
      <T x={220} y={202} size={9} tone="muted">
        market order = “now, at whatever it costs” — the other four wait at a price you chose
      </T>
    </Svg>
  );
}

function SessionsClock() {
  const bar = (x: number, w: number, y: number, tone: Tone, label: string) => (
    <g key={label}>
      <rect x={x} y={y} width={w} height={20} rx={5} className={TONE[tone]} stroke="currentColor" fill="currentColor" fillOpacity={0.14} />
      <T x={x + 6} y={y + 14} anchor="start" size={9} tone={tone} bold>
        {label}
      </T>
    </g>
  );
  return (
    <Svg vb="0 0 440 200">
      {/* UTC axis */}
      <line x1={20} y1={160} x2={420} y2={160} className={TONE.border} stroke="currentColor" />
      {[0, 4, 8, 12, 16, 20, 24].map((h) => (
        <g key={h}>
          <line x1={20 + (h / 24) * 400} y1={156} x2={20 + (h / 24) * 400} y2={164} className={TONE.muted} stroke="currentColor" />
          <T x={20 + (h / 24) * 400} y={177} size={8} tone="muted">
            {`${h}:00`}
          </T>
        </g>
      ))}
      {bar(20 + (21 / 24) * 400, 400 * (3 / 24), 30, 'muted', 'Sydney…')}
      {bar(20, 400 * (6 / 24), 30, 'muted', '…Sydney')}
      {bar(20, 400 * (9 / 24), 58, 'muted', 'Tokyo')}
      {bar(20 + (7 / 24) * 400, 400 * (9 / 24), 86, 'accent', 'London')}
      {bar(20 + (12 / 24) * 400, 400 * (9 / 24), 114, 'accent', 'New York')}
      {/* overlap highlight */}
      <rect x={20 + (12 / 24) * 400} y={82} width={400 * (4 / 24)} height={58} rx={6} className={TONE.accentSoft} stroke="currentColor" strokeDasharray="4 3" fill="currentColor" fillOpacity={0.1} />
      <T x={20 + (14 / 24) * 400} y={22} size={9} tone="accentSoft" bold>
        the overlap — EUR/USD’s busiest hours
      </T>
      <Arrow x1={20 + (14 / 24) * 400} y1={26} x2={20 + (14 / 24) * 400} y2={78} tone="accentSoft" dashed />
      <T x={220} y={196} size={9} tone="muted">
        open 24/5 — but liquidity follows the sun; trade where it is
      </T>
    </Svg>
  );
}

function SpreadAnatomy() {
  return (
    <Svg vb="0 0 440 190">
      <line x1={40} y1={95} x2={400} y2={95} className={TONE.border} stroke="currentColor" />
      {/* bid / ask levels */}
      <line x1={80} y1={130} x2={360} y2={130} className={TONE.danger} stroke="currentColor" strokeWidth={1.6} />
      <T x={70} y={134} anchor="end" size={10} tone="danger" bold>
        bid 1.1000
      </T>
      <T x={370} y={134} anchor="start" size={9} tone="muted">
        you SELL here
      </T>
      <line x1={80} y1={60} x2={360} y2={60} className={TONE.accent} stroke="currentColor" strokeWidth={1.6} />
      <T x={70} y={64} anchor="end" size={10} tone="accent" bold>
        ask 1.1001
      </T>
      <T x={370} y={64} anchor="start" size={9} tone="muted">
        you BUY here
      </T>
      {/* the gap */}
      <Arrow x1={220} y1={68} x2={220} y2={122} tone="warn" />
      <Arrow x1={220} y1={122} x2={220} y2={68} tone="warn" />
      <T x={232} y={99} anchor="start" size={10} tone="warn" bold>
        the spread — paid on entry, every trade
      </T>
      <T x={220} y={178} size={9} tone="muted">
        buy and instantly sell = one pip gone; ten trades a day = ten spreads a day
      </T>
    </Svg>
  );
}

function LeverageSeesaw() {
  return (
    <Svg vb="0 0 440 200">
      {/* pivot */}
      <polygon points="220,150 200,180 240,180" className={TONE.muted} fill="currentColor" stroke="none" />
      {/* beam */}
      <line x1={60} y1={110} x2={380} y2={170} className={TONE.fg} stroke="currentColor" strokeWidth={2.2} />
      <Box x={40} y={70} w={90} h={40} tone="accentSoft" fill />
      <T x={85} y={95} tone="accentSoft" bold>
        +10% gain
      </T>
      <Box x={330} y={150} w={90} h={40} tone="danger" fill />
      <T x={375} y={175} tone="danger" bold>
        −10% loss
      </T>
      <T x={220} y={30} bold size={11}>
        10× leverage moves BOTH ends of the seesaw
      </T>
      <T x={220} y={48} size={9} tone="muted">
        a routine 1% market move becomes 10% of your account — in either direction
      </T>
      <T x={220} y={196} size={9} tone="muted">
        pros pick the risk %, not the leverage — size comes from the stop, and the loan stays small
      </T>
    </Svg>
  );
}

function PlanPyramid() {
  const layer = (y: number, w: number, tone: Tone, label: string) => (
    <g key={label}>
      <rect x={220 - w / 2} y={y} width={w} height={30} rx={6} className={TONE[tone]} stroke="currentColor" fill="currentColor" fillOpacity={0.12} />
      <T x={220} y={y + 19} size={9.5} tone={tone} bold>
        {label}
      </T>
    </g>
  );
  return (
    <Svg vb="0 0 440 210">
      {layer(170, 380, 'danger', 'RISK RULES — max loss per trade / day / week')}
      {layer(136, 320, 'warn', 'MARKET & SCHEDULE — one pair, your sessions')}
      {layer(102, 260, 'accent', 'SETUPS — 2–3 written, testable patterns')}
      {layer(68, 200, 'accentSoft', 'EXECUTION — orders in before entry')}
      {layer(34, 140, 'fg', 'REVIEW — journal + weekly')}
      <T x={30} y={30} anchor="start" size={9} tone="muted">
        build from
      </T>
      <Arrow x1={45} y1={38} x2={45} y2={185} tone="muted" dashed />
      <T x={30} y={200} anchor="start" size={9} tone="muted">
        the bottom
      </T>
    </Svg>
  );
}

function DailyRoutineTimeline() {
  const seg = (x: number, w: number, tone: Tone, top: string, bottom: string) => (
    <g key={top}>
      <rect x={x} y={80} width={w} height={34} rx={7} className={TONE[tone]} stroke="currentColor" fill="currentColor" fillOpacity={0.12} />
      <T x={x + w / 2} y={74} size={9} tone={tone} bold>
        {top}
      </T>
      <T x={x + w / 2} y={101} size={8.5} tone="muted">
        {bottom}
      </T>
    </g>
  );
  return (
    <Svg vb="0 0 440 180">
      <line x1={20} y1={97} x2={425} y2={97} className={TONE.border} stroke="currentColor" />
      {seg(30, 100, 'accent', 'PREPARE · 15m', 'calendar · lean · plan')}
      {seg(150, 130, 'accentSoft', 'EXECUTE · 30–60m', 'setup? checklist → orders')}
      {seg(300, 80, 'warn', 'REVIEW · 10m', 'journal the day')}
      <T x={410} y={90} anchor="end" size={9} tone="muted" bold>
        …life
      </T>
      <T x={220} y={140} size={9} tone="muted">
        everything outside these windows is where impulse trades live — so the windows are the plan
      </T>
      <T x={220} y={160} size={9} tone="muted" bold>
        “no setup today” = a complete, successful trading day
      </T>
    </Svg>
  );
}

function AccountLadder() {
  const rung = (y: number, tone: Tone, label: string, exam: string) => (
    <g key={label}>
      <Box x={60} y={y} w={130} h={34} tone={tone} fill />
      <T x={125} y={y + 21} size={9.5} tone={tone} bold>
        {label}
      </T>
      <T x={205} y={y + 21} anchor="start" size={9} tone="muted">
        {exam}
      </T>
    </g>
  );
  return (
    <Svg vb="0 0 440 210">
      {rung(160, 'muted', 'DEMO', 'exam: 50 trades, zero rule breaks')}
      {rung(110, 'accent', 'TINY LIVE', 'exam: +expectancy with real feelings')}
      {rung(60, 'accentSoft', 'MEANINGFUL SIZE', 'raise after clean quarters; halve on 10% DD')}
      <Arrow x1={125} y1={158} x2={125} y2={148} tone="fg" />
      <Arrow x1={125} y1={108} x2={125} y2={98} tone="fg" />
      <T x={220} y={30} bold size={10.5}>
        each rung has an exit exam — consistency, never speed
      </T>
      <T x={220} y={200} size={9} tone="muted">
        skipping rungs is how accounts die young; sizing down after losses is what pros do
      </T>
    </Svg>
  );
}

function MentorDayFlow() {
  const step = (x: number, tone: Tone, label: string, sub: string) => (
    <g key={label}>
      <Box x={x} y={70} w={88} h={44} tone={tone} fill />
      <T x={x + 44} y={88} size={9.5} tone={tone} bold>
        {label}
      </T>
      <T x={x + 44} y={104} size={8} tone="muted">
        {sub}
      </T>
    </g>
  );
  return (
    <Svg vb="0 0 440 190">
      {step(15, 'accent', 'Dashboard', 'lean · news · pulse')}
      {step(125, 'accentSoft', 'Trade plan', 'ticket or stand-aside')}
      {step(235, 'warn', 'Broker', 'entry+stop+target')}
      {step(345, 'fg', 'Journal', 'grade yourself')}
      <Arrow x1={103} y1={92} x2={123} y2={92} tone="muted" />
      <Arrow x1={213} y1={92} x2={233} y2={92} tone="muted" />
      <Arrow x1={323} y1={92} x2={343} y2={92} tone="muted" />
      <T x={280} y={50} size={9} tone="muted">
        only if the plan says trade ↓
      </T>
      <T x={220} y={150} size={9} tone="muted">
        weekly: five minutes on the Loop page — is the engine healthy, what does its honest scoreboard say?
      </T>
      <T x={220} y={172} size={9} tone="muted" bold>
        total: under ten minutes a day, by design
      </T>
    </Svg>
  );
}

function TicketAnatomy() {
  const row = (y: number, tone: Tone, label: string, src: string) => (
    <g key={label}>
      <Box x={30} y={y} w={150} h={28} tone={tone} fill />
      <T x={40} y={y + 18} anchor="start" size={9} tone={tone} bold>
        {label}
      </T>
      <Arrow x1={185} y1={y + 14} x2={225} y2={y + 14} tone="muted" dashed />
      <T x={232} y={y + 18} anchor="start" size={9} tone="muted">
        {src}
      </T>
    </g>
  );
  return (
    <Svg vb="0 0 440 210">
      {row(18, 'accent', 'STANCE  long / short / aside', 'champion direction model')}
      {row(54, 'fg', 'ENTRY  latest price', 'no prediction — just the market')}
      {row(90, 'danger', 'STOP  1.5× expected move', 'volatility model (beyond noise)')}
      {row(126, 'accentSoft', 'TARGET  stop × R:R', 'your chosen asymmetry')}
      {row(162, 'warn', 'SIZE  lots', 'your account × risk % ÷ stop')}
      <T x={220} y={205} size={9} tone="muted">
        five lines, four different machines — and only the last one knows your account
      </T>
    </Svg>
  );
}

function DriftWatch() {
  return (
    <Svg vb="0 0 440 200">
      {/* axis */}
      <line x1={40} y1={160} x2={420} y2={160} className={TONE.border} stroke="currentColor" />
      <T x={40} y={175} anchor="start" size={8} tone="muted">
        time →
      </T>
      {/* champion proven level */}
      <line x1={40} y1={90} x2={420} y2={90} className={TONE.accentSoft} stroke="currentColor" strokeDasharray="5 3" />
      <T x={45} y={83} anchor="start" size={9} tone="accentSoft" bold>
        champion’s proven error + margin
      </T>
      {/* live rolling error line drifting up */}
      <polyline
        points="40,120 90,115 140,122 190,112 240,118 290,105 330,96 360,80 390,66"
        className={TONE.fg}
        stroke="currentColor"
        strokeWidth={1.8}
        fill="none"
      />
      <T x={70} y={140} anchor="start" size={9} tone="muted">
        live rolling error (last ~40 graded calls)
      </T>
      {/* crossing point */}
      <circle cx={345} cy={88} r={5} className={TONE.danger} fill="currentColor" />
      <Arrow x1={345} y1={80} x2={345} y2={40} tone="danger" />
      <T x={340} y={30} anchor="end" size={9.5} tone="danger" bold>
        drift! → retrain now (24h cooldown)
      </T>
    </Svg>
  );
}

function ProcessVsOutcome() {
  return (
    <Svg vb="0 0 440 200">
      <Box x={30} y={40} w={130} h={44} tone="accentSoft" fill />
      <T x={95} y={58} size={9.5} tone="accentSoft" bold>
        PROCESS
      </T>
      <T x={95} y={74} size={8.5} tone="muted">
        fully yours
      </T>
      <Box x={30} y={120} w={130} h={44} tone="warn" fill />
      <T x={95} y={138} size={9.5} tone="warn" bold>
        VARIANCE
      </T>
      <T x={95} y={154} size={8.5} tone="muted">
        nobody’s
      </T>
      <Arrow x1={165} y1={62} x2={255} y2={95} tone="muted" />
      <Arrow x1={165} y1={142} x2={255} y2={110} tone="muted" />
      <Box x={260} y={80} w={150} h={44} tone="fg" fill />
      <T x={335} y={98} size={9.5} bold>
        OUTCOME
      </T>
      <T x={335} y={114} size={8.5} tone="muted">
        this week’s P&L
      </T>
      <T x={220} y={190} size={9} tone="muted" bold>
        set goals on the box you control — score weeks by rules followed, not dollars printed
      </T>
    </Svg>
  );
}

// ---- learning renovation figures -----------------------------------------

function TrendTypes() {
  return (
    <Svg vb="0 0 460 170">
      {/* uptrend */}
      <polyline points="15,110 40,95 30,90 55,72 45,68 70,50 60,46 85,30" className={TONE.accentSoft} stroke="currentColor" strokeWidth={1.8} fill="none" />
      <T x={57} y={135} size={9} tone="accentSoft" bold>UPTREND</T>
      <T x={57} y={150} size={8} tone="muted">higher highs + lows</T>
      {/* downtrend */}
      <polyline points="175,30 200,50 190,54 215,72 205,76 230,95 220,99 245,115" className={TONE.danger} stroke="currentColor" strokeWidth={1.8} fill="none" />
      <T x={215} y={135} size={9} tone="danger" bold>DOWNTREND</T>
      <T x={215} y={150} size={8} tone="muted">lower highs + lows</T>
      {/* sideways / range */}
      <line x1={330} y1={45} x2={445} y2={45} className={TONE.border} stroke="currentColor" strokeDasharray="3 3" />
      <line x1={330} y1={105} x2={445} y2={105} className={TONE.border} stroke="currentColor" strokeDasharray="3 3" />
      <polyline points="335,100 355,52 375,100 395,52 415,100 435,52" className={TONE.accent} stroke="currentColor" strokeWidth={1.8} fill="none" />
      <T x={388} y={135} size={9} tone="accent" bold>SIDEWAYS / RANGE</T>
      <T x={388} y={150} size={8} tone="muted">bouncing in a box</T>
    </Svg>
  );
}

function PriceActionMap() {
  return (
    <Svg vb="0 0 460 210">
      {/* support & resistance lines */}
      <line x1={20} y1={60} x2={300} y2={60} className={TONE.danger} stroke="currentColor" strokeDasharray="4 3" />
      <T x={24} y={54} anchor="start" size={8} tone="danger" bold>RESISTANCE (ceiling)</T>
      <line x1={20} y1={150} x2={440} y2={150} className={TONE.accentSoft} stroke="currentColor" strokeDasharray="4 3" />
      <T x={24} y={164} anchor="start" size={8} tone="accentSoft" bold>SUPPORT (floor)</T>
      {/* price path: bounce off support, pullback, breakout through resistance, expansion */}
      <polyline
        points="20,120 50,148 80,100 110,140 140,95 175,62 200,90 230,60 265,58 300,40 340,70 370,30 410,55 440,18"
        className={TONE.fg} stroke="currentColor" strokeWidth={1.8} fill="none"
      />
      <Arrow x1={55} y1={158} x2={70} y2={138} tone="accentSoft" />
      <T x={78} y={172} size={8} tone="muted">bounce</T>
      <T x={130} y={128} size={8} tone="muted">pullback</T>
      <circle cx={300} cy={40} r={4} className={TONE.accent} fill="currentColor" />
      <T x={300} y={30} size={8} tone="accent" bold>BREAKOUT ↑</T>
      <T x={405} y={80} size={8} tone="muted">expansion (big candles)</T>
    </Svg>
  );
}

function MarketStructureSwings() {
  return (
    <Svg vb="0 0 460 200">
      <polyline points="20,150 55,90 90,120 130,55 165,85 205,35 240,70" className={TONE.accentSoft} stroke="currentColor" strokeWidth={1.8} fill="none" />
      {/* label HH / HL on uptrend */}
      <T x={55} y={82} size={8} tone="accentSoft">HH</T>
      <T x={92} y={135} size={8} tone="accentSoft">HL</T>
      <T x={130} y={47} size={8} tone="accentSoft">HH</T>
      <T x={167} y={100} size={8} tone="accentSoft">HL</T>
      <T x={205} y={27} size={8} tone="accentSoft">HH</T>
      <T x={120} y={185} size={9} tone="accentSoft" bold>uptrend = higher highs &amp; higher lows</T>
      {/* BOS marker */}
      <line x1={205} y1={35} x2={260} y2={35} className={TONE.accent} stroke="currentColor" strokeDasharray="3 2" />
      <T x={262} y={38} anchor="start" size={8} tone="accent" bold>BOS ✓ trend continues</T>
      {/* CHoCH: first lower low */}
      <polyline points="240,70 275,55 305,110 340,80 375,130" className={TONE.danger} stroke="currentColor" strokeWidth={1.8} fill="none" />
      <circle cx={305} cy={110} r={4} className={TONE.danger} fill="currentColor" />
      <T x={312} y={112} anchor="start" size={8} tone="danger" bold>CHoCH — first lower low = warning</T>
    </Svg>
  );
}

function CandleZoo() {
  const candle = (
    x: number, tone: Tone, openY: number, closeY: number, hi: number, lo: number, label: string,
  ) => (
    <g key={label} className={TONE[tone]} stroke="currentColor">
      <line x1={x} y1={hi} x2={x} y2={lo} strokeWidth={1.3} />
      <rect x={x - 8} y={Math.min(openY, closeY)} width={16} height={Math.max(3, Math.abs(openY - closeY))} fill="currentColor" fillOpacity={0.2} strokeWidth={1.3} />
      <T x={x} y={175} size={8} tone="muted">{label}</T>
    </g>
  );
  return (
    <Svg vb="0 0 460 190">
      {candle(35, 'muted', 78, 82, 40, 120, 'doji')}
      {candle(95, 'accentSoft', 55, 68, 48, 120, 'hammer')}
      {candle(155, 'danger', 100, 88, 40, 112, 'shooting star')}
      {candle(215, 'accentSoft', 110, 55, 50, 115, 'marubozu')}
      {candle(275, 'muted', 70, 82, 50, 130, 'pin bar')}
      {/* engulfing: two candles */}
      <g className={TONE.danger} stroke="currentColor">
        <rect x={330} y={70} width={12} height={22} fill="currentColor" fillOpacity={0.2} strokeWidth={1.2} />
      </g>
      <g className={TONE.accentSoft} stroke="currentColor">
        <rect x={346} y={62} width={16} height={40} fill="currentColor" fillOpacity={0.2} strokeWidth={1.3} />
      </g>
      <T x={350} y={175} size={8} tone="muted">engulfing</T>
      {/* inside bar */}
      <g className={TONE.muted} stroke="currentColor">
        <rect x={410} y={55} width={14} height={55} fill="none" strokeWidth={1.2} />
        <rect x={414} y={72} width={6} height={22} fill="currentColor" fillOpacity={0.25} strokeWidth={1.2} />
      </g>
      <T x={417} y={175} size={8} tone="muted">inside bar</T>
      <T x={230} y={16} size={9} bold>each shape = who won the bar, buyers or sellers</T>
    </Svg>
  );
}

function VolumeProfile() {
  return (
    <Svg vb="0 0 460 200">
      {/* price line */}
      <polyline points="20,120 60,90 100,110 140,60 180,95 220,70" className={TONE.fg} stroke="currentColor" strokeWidth={1.6} fill="none" />
      {/* time-volume bars */}
      {([[30, 18], [60, 34], [90, 22], [120, 44], [150, 20], [180, 30]] as const).map(([x, h]) => (
        <rect key={x} x={x - 6} y={185 - h} width={12} height={h} className={TONE.accent} stroke="currentColor" fill="currentColor" fillOpacity={0.2} strokeWidth={1} />
      ))}
      <T x={100} y={198} size={8} tone="muted">volume by TIME (tall = busy)</T>
      {/* volume profile: horizontal histogram on the right */}
      {([
        [40, 26], [60, 40], [80, 70], [100, 95], [120, 55], [140, 30],
      ] as const).map(([y, w]) => (
        <rect key={y} x={300} y={y - 8} width={w} height={14} className={y === 100 ? TONE.warn : TONE.accentSoft} stroke="currentColor" fill="currentColor" fillOpacity={0.18} strokeWidth={1} />
      ))}
      <T x={400} y={104} anchor="start" size={8} tone="warn" bold>POC</T>
      <T x={365} y={38} anchor="start" size={8} tone="muted">VAH</T>
      <T x={355} y={138} anchor="start" size={8} tone="muted">VAL</T>
      <T x={360} y={175} size={8} tone="muted">volume by PRICE</T>
    </Svg>
  );
}

function LiquidityPools() {
  return (
    <Svg vb="0 0 460 190">
      {/* two equal highs */}
      <line x1={40} y1={55} x2={300} y2={55} className={TONE.danger} stroke="currentColor" strokeDasharray="4 3" />
      <T x={44} y={49} anchor="start" size={8} tone="danger">equal highs → stops pile up just above (liquidity)</T>
      {/* stops marker */}
      <T x={250} y={42} size={9} tone="warn">✦✦✦</T>
      {/* price approaches, sweeps above, snaps back */}
      <polyline points="30,120 70,80 110,58 150,95 190,60 230,40 250,32 232,75 260,110 300,140" className={TONE.fg} stroke="currentColor" strokeWidth={1.8} fill="none" />
      <circle cx={250} cy={32} r={4} className={TONE.danger} fill="currentColor" />
      <T x={258} y={28} anchor="start" size={8} tone="danger" bold>SWEEP: spike grabs stops…</T>
      <Arrow x1={255} y1={40} x2={275} y2={95} tone="danger" />
      <T x={300} y={135} anchor="start" size={8} tone="muted">…then price snaps back down (the trap)</T>
    </Svg>
  );
}

function SmcBlocks() {
  return (
    <Svg vb="0 0 460 190">
      {/* order block: last candle before big move */}
      <rect x={40} y={95} width={40} height={30} className={TONE.accent} stroke="currentColor" fill="currentColor" fillOpacity={0.14} />
      <T x={60} y={140} size={8} tone="accent" bold>ORDER BLOCK</T>
      <T x={60} y={152} size={7} tone="muted">base before the move</T>
      {/* big move up leaving a gap */}
      <polyline points="80,110 110,70 140,40" className={TONE.accentSoft} stroke="currentColor" strokeWidth={2} fill="none" />
      {/* FVG box */}
      <rect x={112} y={62} width={26} height={34} className={TONE.warn} stroke="currentColor" strokeDasharray="3 2" fill="currentColor" fillOpacity={0.1} />
      <T x={150} y={70} anchor="start" size={8} tone="warn" bold>FAIR VALUE GAP</T>
      <T x={150} y={82} anchor="start" size={7} tone="muted">skipped prices — price</T>
      <T x={150} y={92} anchor="start" size={7} tone="muted">often returns to fill it</T>
      {/* return to fill */}
      <polyline points="140,40 175,55 150,80 190,60" className={TONE.fg} stroke="currentColor" strokeWidth={1.4} fill="none" strokeDasharray="2 2" />
      <T x={230} y={175} size={8} tone="muted">fancy names for: old zones + skipped gaps often matter again</T>
    </Svg>
  );
}

function OrderGrid() {
  return (
    <Svg vb="0 0 460 190">
      <line x1={30} y1={95} x2={430} y2={95} className={TONE.fg} stroke="currentColor" strokeWidth={1.8} />
      <T x={434} y={98} anchor="end" size={9} bold>current price</T>
      {/* above */}
      <line x1={60} y1={45} x2={210} y2={45} className={TONE.accent} stroke="currentColor" strokeDasharray="5 3" />
      <T x={64} y={39} anchor="start" size={9} tone="accent" bold>BUY STOP — chase a breakout up</T>
      <line x1={250} y1={45} x2={410} y2={45} className={TONE.danger} stroke="currentColor" strokeDasharray="5 3" />
      <T x={254} y={39} anchor="start" size={9} tone="danger" bold>SELL LIMIT — sell high (premium)</T>
      {/* below */}
      <line x1={60} y1={145} x2={210} y2={145} className={TONE.accentSoft} stroke="currentColor" strokeDasharray="5 3" />
      <T x={64} y={159} anchor="start" size={9} tone="accentSoft" bold>BUY LIMIT — buy the dip (discount)</T>
      <line x1={250} y1={145} x2={410} y2={145} className={TONE.danger} stroke="currentColor" strokeDasharray="5 3" />
      <T x={254} y={159} anchor="start" size={9} tone="danger" bold>SELL STOP — chase a breakdown</T>
      <T x={230} y={102} size={8} tone="muted">limits wait for a better price · stops chase a break</T>
    </Svg>
  );
}

function MarketConditions() {
  return (
    <Svg vb="0 0 460 180">
      {/* momentum / trend: keeps going */}
      <polyline points="20,130 60,110 100,85 140,60 180,35" className={TONE.accentSoft} stroke="currentColor" strokeWidth={2} fill="none" />
      <Arrow x1={175} y1={40} x2={195} y2={28} tone="accentSoft" />
      <T x={95} y={155} size={9} tone="accentSoft" bold>MOMENTUM / TREND</T>
      <T x={95} y={168} size={8} tone="muted">a move that keeps going</T>
      {/* mean reversion: snaps back to average */}
      <line x1={260} y1={90} x2={440} y2={90} className={TONE.border} stroke="currentColor" strokeDasharray="4 3" />
      <T x={444} y={86} anchor="end" size={8} tone="muted">average</T>
      <polyline points="260,90 285,45 310,88 335,130 360,90 385,50 410,90 435,120" className={TONE.accent} stroke="currentColor" strokeWidth={1.8} fill="none" />
      <T x={350} y={155} size={9} tone="accent" bold>MEAN REVERSION</T>
      <T x={350} y={168} size={8} tone="muted">stretch too far → snaps back</T>
      <T x={225} y={18} size={9} bold>opposite bets — the skill is knowing which one you&apos;re in</T>
    </Svg>
  );
}

function SystemPlain() {
  const step = (x: number, tone: Tone, n: string, label: string) => (
    <g key={label}>
      <Box x={x} y={60} w={78} h={46} tone={tone} fill />
      <T x={x + 39} y={78} size={11} tone={tone} bold>{n}</T>
      <T x={x + 39} y={95} size={8} tone="muted">{label}</T>
    </g>
  );
  return (
    <Svg vb="0 0 470 160">
      {step(10, 'accent', '1', 'gather data')}
      {step(98, 'accentSoft', '2', 'make a guess')}
      {step(186, 'fg', '3', 'write it down')}
      {step(274, 'warn', '4', 'grade vs reality')}
      {step(362, 'accent', '5', 'learn if better')}
      {[88, 176, 264, 352].map((x) => (
        <Arrow key={x} x1={x} y1={83} x2={x + 10} y2={83} tone="muted" />
      ))}
      {/* loop-back arrow */}
      <path d="M401 108 q0 34 -195 34 q-196 0 -196 -34" className={TONE.muted} stroke="currentColor" strokeWidth={1.3} fill="none" strokeDasharray="4 3" />
      <T x={205} y={152} size={8} tone="muted">…then repeat, forever</T>
      <T x={235} y={28} size={10} bold>the whole machine — five steps that repeat</T>
    </Svg>
  );
}

function TabsTrading() {
  const tab = (x: number, y: number, tone: Tone, name: string, q: string) => (
    <g key={name}>
      <Box x={x} y={y} w={140} h={34} tone={tone} fill />
      <T x={x + 10} y={y + 15} anchor="start" size={9} tone={tone} bold>{name}</T>
      <T x={x + 10} y={y + 28} anchor="start" size={7.5} tone="muted">{q}</T>
    </g>
  );
  return (
    <Svg vb="0 0 460 190">
      {tab(15, 15, 'accent', '📊 Dashboard', "what's the read today?")}
      {tab(160, 15, 'accentSoft', '🎯 Trade plan', 'what should I do now?')}
      {tab(305, 15, 'fg', '📈 Forecast', 'the detail & the why')}
      {tab(15, 60, 'warn', '💡 Tips', 'are the tipsters right?')}
      {tab(160, 60, 'fg', '🧾 Predictions', 'the honest audit log')}
      {tab(305, 60, 'accent', '🔄 Loop', 'is the engine healthy?')}
      <T x={230} y={130} size={10} bold>the six trading tabs — top of the sidebar</T>
      <T x={230} y={150} size={8} tone="muted">daily flow: Dashboard → Trade plan → (broker) → back</T>
    </Svg>
  );
}

function TabsToolkit() {
  const tab = (x: number, y: number, tone: Tone, name: string, q: string) => (
    <g key={name}>
      <Box x={x} y={y} w={140} h={32} tone={tone} fill />
      <T x={x + 10} y={y + 14} anchor="start" size={9} tone={tone} bold>{name}</T>
      <T x={x + 10} y={y + 26} anchor="start" size={7.5} tone="muted">{q}</T>
    </g>
  );
  return (
    <Svg vb="0 0 460 200">
      {tab(15, 12, 'accentSoft', '🧮 Risk calc', 'size a trade safely')}
      {tab(160, 12, 'accent', '📓 Journal', 'grade yourself')}
      {tab(305, 12, 'warn', '🧪 Backtester', 'test before you trust')}
      {tab(15, 52, 'fg', '📉 Prices', 'the raw candles')}
      {tab(160, 52, 'fg', '🩺 Data health', 'is the fuel clean?')}
      {tab(305, 52, 'accentSoft', '🎓 Learn', 'this curriculum')}
      {tab(160, 92, 'muted', '⚙️ Settings', 'password & users')}
      <T x={230} y={140} size={10} bold>the toolkit tabs — everything around your trades</T>
      <T x={230} y={160} size={8} tone="muted">the Journal is where real improvement happens</T>
    </Svg>
  );
}

function TradeManagement() {
  // A long trade's life: entry, the 1R line where three rules fire, and the
  // horizon where the idea expires.
  const y0 = 150; // entry line
  const y1R = 92; // +1R line
  const yStop = 178; // original stop
  return (
    <Svg vb="0 0 440 210">
      {/* price path */}
      <path
        d="M40 150 L90 138 L130 146 L175 108 L215 96 L260 78 L305 86 L350 70"
        className={TONE.fg}
        stroke="currentColor"
        strokeWidth={1.6}
        fill="none"
      />

      {/* stop / entry / 1R levels */}
      <line x1={36} y1={yStop} x2={404} y2={yStop} className={TONE.danger}
        stroke="currentColor" strokeWidth={1.2} strokeDasharray="4 3" />
      <T x={32} y={yStop + 3} tone="danger" size={9} anchor="end">stop</T>

      <line x1={36} y1={y0} x2={404} y2={y0} className={TONE.border}
        stroke="currentColor" strokeWidth={1.2} />
      <T x={32} y={y0 + 3} tone="muted" size={9} anchor="end">entry</T>

      <line x1={36} y1={y1R} x2={404} y2={y1R} className={TONE.accent}
        stroke="currentColor" strokeWidth={1.2} strokeDasharray="4 3" />
      <T x={32} y={y1R + 3} tone="accent" size={9} anchor="end">+1R</T>

      {/* the three rules that fire at 1R */}
      <Arrow x1={215} y1={96} x2={215} y2={y0 - 4} tone="accent" dashed />
      <Box x={150} y={26} w={135} h={40} tone="accent" fill />
      <T x={217} y={41} tone="accent" size={9} bold>at +1R:</T>
      <T x={217} y={53} tone="fg" size={8.5}>stop to break-even + bank 50%</T>
      <T x={217} y={62} tone="muted" size={8}>then trail by 1 sigma</T>

      {/* trailing stop steps */}
      <path
        d="M215 132 L260 132 L260 116 L305 116 L305 122 L350 122"
        className={TONE.accentSoft}
        stroke="currentColor"
        strokeWidth={1.3}
        strokeDasharray="3 2"
        fill="none"
      />
      <T x={330} y={137} tone="accentSoft" size={8}>trailing stop</T>

      {/* time stop */}
      <line x1={370} y1={20} x2={370} y2={196} className={TONE.warn}
        stroke="currentColor" strokeWidth={1.3} strokeDasharray="5 3" />
      <T x={374} y={196} tone="warn" size={8.5} anchor="start">time</T>
      <T x={374} y={205} tone="warn" size={8.5} anchor="start">stop</T>

      <T x={110} y={196} tone="muted" size={8.5}>
        risk is on
      </T>
      <T x={280} y={196} tone="muted" size={8.5}>
        risk is off — only upside left
      </T>
    </Svg>
  );
}

function LossRootCauses() {
  return (
    <Svg vb="0 0 440 205">
      <T x={220} y={18} bold>Every losing trade goes in exactly one of two piles</T>

      {/* pile 1 */}
      <Box x={26} y={34} w={185} h={128} tone="accent" fill />
      <T x={118} y={54} tone="accent" size={11} bold>Good process</T>
      <T x={118} y={69} tone="muted" size={9}>you followed the plan</T>
      <T x={118} y={80} tone="muted" size={9}>and lost anyway</T>
      <line x1={44} y1={90} x2={193} y2={90} className={TONE.border}
        stroke="currentColor" strokeWidth={1} />
      <T x={118} y={107} tone="fg" size={9.5} bold>Change: nothing</T>
      <T x={118} y={124} tone="muted" size={8.5}>a 55% system loses 45</T>
      <T x={118} y={135} tone="muted" size={8.5}>times in 100. None of</T>
      <T x={118} y={146} tone="muted" size={8.5}>them are mistakes.</T>

      {/* pile 2 */}
      <Box x={229} y={34} w={185} h={128} tone="danger" fill />
      <T x={321} y={54} tone="danger" size={11} bold>Process error</T>
      <T x={321} y={69} tone="muted" size={9}>oversized · moved stop</T>
      <T x={321} y={80} tone="muted" size={9}>no setup · revenge</T>
      <line x1={247} y1={90} x2={396} y2={90} className={TONE.border}
        stroke="currentColor" strokeWidth={1} />
      <T x={321} y={107} tone="fg" size={9.5} bold>Change: the habit</T>
      <T x={321} y={124} tone="muted" size={8.5}>ranked by R bled, not</T>
      <T x={321} y={135} tone="muted" size={8.5}>by count — one big loss</T>
      <T x={321} y={146} tone="muted" size={8.5}>beats five small ones.</T>

      <T x={220} y={186} tone="warn" size={9}>
        Treating pile one as pile two is how good systems get dismantled.
      </T>
    </Svg>
  );
}

function Abstention() {
  // Distribution of predicted probabilities: confident tails act, middle abstains.
  const cx = 220;
  const base = 150;
  const bars: { x: number; h: number }[] = [
    { x: 58, h: 14 }, { x: 76, h: 22 }, { x: 94, h: 34 }, { x: 112, h: 50 },
    { x: 130, h: 68 }, { x: 148, h: 84 }, { x: 166, h: 96 }, { x: 184, h: 104 },
    { x: 202, h: 108 }, { x: 220, h: 110 }, { x: 238, h: 108 }, { x: 256, h: 104 },
    { x: 274, h: 96 }, { x: 292, h: 84 }, { x: 310, h: 68 }, { x: 328, h: 50 },
    { x: 346, h: 34 }, { x: 364, h: 22 },
  ];
  const inBand = (x: number) => Math.abs(x - cx) < 58;
  return (
    <Svg vb="0 0 440 205">
      <T x={220} y={16} bold>Where the model is willing to speak</T>

      {/* abstain band */}
      <rect x={cx - 58} y={26} width={116} height={base - 26} rx={6}
        className={TONE.muted} fill="currentColor" fillOpacity={0.10} />

      {bars.map(({ x, h }) => (
        <rect
          key={x}
          x={x - 7}
          y={base - h}
          width={14}
          height={h}
          rx={2}
          className={inBand(x) ? TONE.muted : TONE.accent}
          fill="currentColor"
          fillOpacity={inBand(x) ? 0.35 : 0.75}
        />
      ))}

      {/* axis */}
      <line x1={40} y1={base} x2={400} y2={base} className={TONE.border}
        stroke="currentColor" strokeWidth={1.2} />
      <T x={48} y={base + 14} tone="muted" size={9} anchor="start">35% up</T>
      <T x={cx} y={base + 14} tone="muted" size={9}>50/50</T>
      <T x={392} y={base + 14} tone="muted" size={9} anchor="end">65% up</T>

      {/* margin markers */}
      <line x1={cx - 58} y1={26} x2={cx - 58} y2={base} className={TONE.accent}
        stroke="currentColor" strokeWidth={1.3} strokeDasharray="4 3" />
      <line x1={cx + 58} y1={26} x2={cx + 58} y2={base} className={TONE.accent}
        stroke="currentColor" strokeWidth={1.3} strokeDasharray="4 3" />

      <T x={cx} y={68} tone="muted" size={9.5} bold>stands aside</T>
      <T x={cx} y={82} tone="muted" size={8.5}>no edge here</T>

      <T x={108} y={base + 30} tone="accent" size={9.5} bold>calls it</T>
      <T x={332} y={base + 30} tone="accent" size={9.5} bold>calls it</T>
      <T x={220} y={base + 46} tone="warn" size={8.5}>
        Coverage floor: it must be willing to act on at least 15% of hours to count.
      </T>
    </Svg>
  );
}

// ---- "How the mentor keeps itself honest" ---------------------------------

/** A tinted, borderless area: zones, bars and highlighted cells. */
function Fill({
  x,
  y,
  w,
  h,
  tone,
  opacity = 0.15,
  rx = 4,
}: {
  x: number;
  y: number;
  w: number;
  h: number;
  tone: Tone;
  opacity?: number;
  rx?: number;
}) {
  return (
    <rect
      x={x}
      y={y}
      width={w}
      height={h}
      rx={rx}
      className={TONE[tone]}
      fill="currentColor"
      fillOpacity={opacity}
    />
  );
}

/** A plain line with no arrowhead: axes, thresholds, guides. */
function Rule({
  x1,
  y1,
  x2,
  y2,
  tone = 'border',
  dashed = false,
  width = 1.2,
}: {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  tone?: Tone;
  dashed?: boolean;
  width?: number;
}) {
  return (
    <line
      x1={x1}
      y1={y1}
      x2={x2}
      y2={y2}
      className={TONE[tone]}
      stroke="currentColor"
      strokeWidth={width}
      strokeDasharray={dashed ? '4 3' : undefined}
    />
  );
}

function Dot({ cx, cy, tone, r = 4 }: { cx: number; cy: number; tone: Tone; r?: number }) {
  return <circle cx={cx} cy={cy} r={r} className={TONE[tone]} fill="currentColor" />;
}

function BreakevenHurdle() {
  // Win-rate scale 49%..53%.
  const x = (p: number) => 40 + (p - 49) * 90;
  const rows = [
    { y: 52, label: '24-hour forecast', hurdle: 51.77, tag: 'breakeven 51.8%' },
    { y: 104, label: '5-day forecast', hurdle: 50.71, tag: 'breakeven 50.7%' },
  ];
  return (
    <Svg vb="0 0 440 215">
      <T x={220} y={16} bold>
        The win rate a call needs to pay for the spread
      </T>
      {rows.map((r) => (
        <g key={r.label}>
          <T x={40} y={r.y - 7} size={9.5} anchor="start" bold>
            {r.label}
          </T>
          <Fill x={x(49)} y={r.y} w={x(r.hurdle) - x(49)} h={22} tone="danger" opacity={0.16} />
          <Fill x={x(r.hurdle)} y={r.y} w={x(53) - x(r.hurdle)} h={22} tone="accent" opacity={0.2} />
          <Rule x1={x(r.hurdle)} y1={r.y - 4} x2={x(r.hurdle)} y2={r.y + 26} tone="accent" width={2} />
          <T x={x(r.hurdle) + 5} y={r.y - 7} size={9} anchor="start" tone="accent" bold>
            {r.tag}
          </T>
          <T x={x(49) + 6} y={r.y + 15} size={8.5} tone="danger" anchor="start">
            loses after costs
          </T>
          <T x={(x(r.hurdle) + x(53)) / 2} y={r.y + 15} size={8.5} tone="accent">
            pays
          </T>
        </g>
      ))}

      {/* coin flip and a 51% model */}
      <Rule x1={x(50)} y1={44} x2={x(50)} y2={146} tone="muted" dashed />
      <Rule x1={x(51)} y1={44} x2={x(51)} y2={146} tone="warn" dashed />

      <Rule x1={40} y1={146} x2={400} y2={146} />
      {[49, 50, 51, 52, 53].map((p) => (
        <T key={p} x={x(p)} y={158} size={8.5} tone="muted">
          {p}%
        </T>
      ))}
      <T x={x(50)} y={172} size={8.5} tone="muted">
        coin flip
      </T>
      <T x={x(51)} y={172} size={8.5} tone="warn">
        a 51% model
      </T>

      <T x={220} y={192} size={9} tone="fg">
        breakeven = 50% + cost ÷ (2 × typical move)
      </T>
      <T x={220} y={206} size={8.5} tone="muted">
        1.2 pips per trade against a typical move of ~34 pips (24 h) or ~84 pips (5 days)
      </T>
    </Svg>
  );
}

function PromotionFloors() {
  const floors = [
    { x: 12, head: '1 · Honest?', a: 'Brier ≤ 0.248', b: 'beats always-50/50' },
    { x: 158, head: '2 · Willing to speak?', a: 'acts on ≥ 15%', b: 'of hours' },
    { x: 304, head: '3 · Worth trading?', a: 'hit rate ≥ breakeven', b: '(after costs)' },
  ];
  return (
    <Svg vb="0 0 440 215">
      <T x={220} y={16} bold>
        Three floors, then a fair race
      </T>
      {floors.map((f) => (
        <g key={f.head}>
          <Box x={f.x} y={30} w={124} h={60} />
          <T x={f.x + 62} y={48} size={9.5} bold>
            {f.head}
          </T>
          <T x={f.x + 62} y={64} size={9} tone="accent">
            {f.a}
          </T>
          <T x={f.x + 62} y={78} size={8.5} tone="muted">
            {f.b}
          </T>
        </g>
      ))}
      <Arrow x1={136} y1={60} x2={156} y2={60} />
      <Arrow x1={282} y1={60} x2={302} y2={60} />
      <T x={220} y={106} size={8.5} tone="danger">
        Fail any floor → refused, and the message names which one
      </T>

      <Arrow x1={366} y1={90} x2={330} y2={126} />
      <Box x={90} y={128} w={260} h={40} />
      <T x={220} y={144} size={9.5} bold>
        4 · Beat the champion on the same fresh data
      </T>
      <T x={220} y={159} size={8.5} tone="muted">
        by at least 0.002 Brier. Its old score doesn&apos;t count.
      </T>

      <Arrow x1={220} y1={168} x2={220} y2={180} tone="accent" />
      <Box x={150} y={182} w={140} h={26} tone="accent" fill />
      <T x={220} y={199} size={10} tone="accent" bold>
        New champion
      </T>
    </Svg>
  );
}

function AbstainByProfit() {
  const x = (coverage: number) => 60 + 3.4 * coverage;
  const y = (hit: number) => 160 - (hit - 49) * 13.33;
  return (
    <Svg vb="0 0 440 215">
      <T x={220} y={16} bold>
        Choosing the quiet band by profit
      </T>

      {/* zones that disqualify a band */}
      <Fill x={60} y={40} w={x(15) - 60} h={120} tone="muted" opacity={0.12} rx={0} />
      <Fill x={x(15)} y={y(51.8)} w={400 - x(15)} h={160 - y(51.8)} tone="danger" opacity={0.1} rx={0} />
      <T x={85} y={146} size={8} tone="muted">
        too few
      </T>
      <T x={85} y={156} size={8} tone="muted">
        hours
      </T>
      <T x={220} y={154} size={8.5} tone="danger">
        doesn&apos;t pay
      </T>

      <Rule x1={60} y1={y(51.8)} x2={400} y2={y(51.8)} tone="warn" dashed />
      <T x={398} y={y(51.8) - 5} size={8.5} tone="warn" anchor="end">
        breakeven 51.8%
      </T>

      {/* candidate bands */}
      <Dot cx={x(100)} cy={y(50.6)} tone="danger" />
      <T x={392} y={y(50.6) + 15} size={8.5} tone="danger" anchor="end">
        always speak: 50.6%
      </T>
      <circle cx={x(38)} cy={y(52.3)} r={9} className={TONE.accent} stroke="currentColor" strokeWidth={1.4} fill="none" />
      <Dot cx={x(38)} cy={y(52.3)} tone="accent" />
      <T x={x(38) + 13} y={y(52.3) - 6} size={9} tone="accent" anchor="start" bold>
        chosen: 52.3% on 38% of hours
      </T>
      <Dot cx={x(16)} cy={y(54)} tone="accent" />
      <T x={x(16) + 8} y={y(54) - 3} size={8.5} tone="muted" anchor="start">
        54% on 16%: pays, fewer chances
      </T>
      <Dot cx={x(9)} cy={y(57)} tone="muted" />
      <T x={x(9) + 8} y={y(57) - 3} size={8.5} tone="muted" anchor="start">
        57% on 9%: looks best, too few hours
      </T>

      {/* axes */}
      <Rule x1={60} y1={160} x2={400} y2={160} />
      <Rule x1={60} y1={40} x2={60} y2={160} />
      <T x={62} y={34} size={9} tone="muted" anchor="start">
        hit rate
      </T>
      {[0, 15, 50, 100].map((c) => (
        <T key={c} x={x(c)} y={172} size={8.5} tone="muted">
          {c}%
        </T>
      ))}
      <T x={230} y={186} size={9} tone="muted">
        share of hours the model speaks on
      </T>
      <T x={220} y={205} size={8.5} tone="warn">
        If no band clears breakeven, it abstains nowhere and the gate judges it as it is.
      </T>
    </Svg>
  );
}

function OverlappingWindows() {
  const hour = 5; // px per hour; 72 hours across
  const calls = Array.from({ length: 10 }, (_, i) => i);
  return (
    <Svg vb="0 0 440 215">
      <T x={220} y={16} bold>
        Overlapping calls vs independent windows
      </T>
      <T x={40} y={36} size={9} anchor="start" bold>
        Every hourly call (each looks 24 hours ahead)
      </T>
      {calls.map((i) => (
        <Fill key={i} x={40 + i * hour} y={44 + i * 7} w={24 * hour} h={5} tone="muted" opacity={0.45} rx={2} />
      ))}
      <T x={222} y={72} size={9} anchor="start" tone="warn">
        neighbours share 23 of 24 hours,
      </T>
      <T x={222} y={85} size={9} anchor="start" tone="warn">
        so one move is counted many times
      </T>

      <T x={40} y={128} size={9} anchor="start" bold>
        Independent windows (what is counted)
      </T>
      {[0, 1, 2].map((d) => (
        <g key={d}>
          <Fill x={40 + d * 24 * hour} y={136} w={24 * hour - 3} h={16} tone="accent" opacity={0.45} />
          <T x={40 + d * 24 * hour + 60} y={148} size={8.5} tone="fg">
            one result
          </T>
        </g>
      ))}

      <Rule x1={40} y1={164} x2={400} y2={164} />
      {['Mon 09:00', 'Tue 09:00', 'Wed 09:00', 'Thu 09:00'].map((label, d) => (
        <T key={label} x={40 + d * 24 * hour} y={176} size={8} tone="muted">
          {label}
        </T>
      ))}
      <T x={220} y={200} size={9} tone="accent">
        About one independent result per trading day on the 24-hour forecast.
      </T>
    </Svg>
  );
}

function IntervalShrink() {
  const y = (pct: number) => 160 - (pct - 30) * 2.2545;
  const breakeven = 51.77;
  const samples = [
    { n: '10', x: 120, lo: 31.3, hi: 83.2 },
    { n: '30', x: 185, lo: 42.3, hi: 75.4 },
    { n: '79 (Oct)', x: 250, lo: 48.5, hi: 69.6 },
    { n: '161', x: 315, lo: 51.9, hi: 66.9 },
    { n: '400', x: 380, lo: 54.6, hi: 64.2 },
  ];
  return (
    <Svg vb="0 0 440 215">
      <T x={220} y={16} bold>
        The same 59.5% win rate, very different certainty
      </T>
      <Rule x1={20} y1={y(breakeven)} x2={410} y2={y(breakeven)} tone="danger" dashed />
      <T x={20} y={y(breakeven) - 5} size={8.5} tone="danger" anchor="start">
        breakeven 51.8%
      </T>
      {samples.map((s) => {
        const proven = s.lo > breakeven;
        return (
          <g key={s.n}>
            <Fill
              x={s.x - 9}
              y={y(s.hi)}
              w={18}
              h={y(s.lo) - y(s.hi)}
              tone={proven ? 'accent' : 'warn'}
              opacity={0.3}
            />
            <Dot cx={s.x} cy={y(59.5)} tone="fg" r={3} />
            <T x={s.x + 13} y={y(s.hi) + 4} size={8} tone="muted" anchor="start">
              {s.hi.toFixed(0)}%
            </T>
            <T x={s.x + 13} y={y(s.lo) + 2} size={8} tone="muted" anchor="start">
              {s.lo.toFixed(0)}%
            </T>
            <T x={s.x} y={178} size={8.5} tone={proven ? 'accent' : 'warn'} bold>
              {s.n}
            </T>
          </g>
        );
      })}
      <T x={250} y={192} size={9} tone="muted">
        independent results
      </T>
      <T x={220} y={207} size={8.5} tone="fg">
        Proven only once the whole 95% range sits above breakeven.
      </T>
    </Svg>
  );
}

function CotPublicationLag() {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const cx = (i: number) => 20 + i * 58 + 27;
  return (
    <Svg vb="0 0 440 200">
      <T x={220} y={16} bold>
        COT: dated when published, not when measured
      </T>
      {days.map((d, i) => (
        <g key={d}>
          {i === 1 && <Fill x={20 + i * 58} y={36} w={54} h={34} tone="muted" opacity={0.2} rx={7} />}
          {i === 4 && <Fill x={20 + i * 58} y={36} w={54} h={34} tone="warn" opacity={0.18} rx={7} />}
          {i === 5 && <Fill x={20 + i * 58} y={36} w={54} h={34} tone="accent" opacity={0.25} rx={7} />}
          <Box x={20 + i * 58} y={36} w={54} h={34} />
          <T x={cx(i)} y={57} size={10} bold>
            {d}
          </T>
        </g>
      ))}
      <T x={cx(1)} y={86} size={8.5} tone="muted">
        positions
      </T>
      <T x={cx(1)} y={97} size={8.5} tone="muted">
        measured
      </T>
      <T x={cx(4)} y={86} size={8.5} tone="warn">
        published
      </T>
      <T x={cx(4)} y={97} size={8.5} tone="warn">
        3:30 pm NY
      </T>
      <T x={cx(5)} y={86} size={8.5} tone="accent">
        model may
      </T>
      <T x={cx(5)} y={97} size={8.5} tone="accent">
        use it
      </T>

      <Arrow x1={cx(1)} y1={118} x2={cx(5)} y2={118} tone="accent" />
      <T x={(cx(1) + cx(5)) / 2} y={113} size={9} tone="accent" bold>
        dated +4 days
      </T>

      <Fill x={78} y={130} w={228} h={20} tone="danger" opacity={0.12} />
      <T x={192} y={144} size={9} tone="danger">
        using it in here = peeking at the future
      </T>
      <T x={220} y={178} size={9} tone="muted">
        A backtest that files it under Tuesday sees three days nobody had yet.
      </T>
    </Svg>
  );
}

function LiveRecalibration() {
  const x = (p: number) => 70 + (p - 20) * 5;
  const y = (p: number) => 180 - (p - 20) * 2.333;
  // sigmoid(0.6 * logit(p)), precomputed
  const curve: [number, number][] = [
    [20, 30.3],
    [30, 37.6],
    [40, 43.9],
    [50, 50],
    [60, 56.1],
    [70, 62.4],
    [80, 69.7],
  ];
  const points = curve.map(([p, q]) => `${x(p)},${y(q)}`).join(' ');
  return (
    <Svg vb="0 0 440 215">
      <T x={220} y={16} bold>
        Correcting overconfidence from live results
      </T>
      <Rule x1={x(20)} y1={y(20)} x2={x(80)} y2={y(80)} tone="muted" dashed />
      <polyline
        points={points}
        className={TONE.accent}
        stroke="currentColor"
        strokeWidth={2}
        fill="none"
      />
      <T x={330} y={46} size={8.5} tone="muted" anchor="end">
        stretch 1: unchanged
      </T>
      <T x={290} y={102} size={8.5} tone="accent" anchor="start">
        stretch 0.6: pulled toward 50%
      </T>

      {/* the worked example */}
      <Rule x1={x(62)} y1={180} x2={x(62)} y2={y(62)} tone="border" dashed width={1} />
      <Dot cx={x(62)} cy={y(62)} tone="muted" r={3} />
      <Arrow x1={x(62)} y1={y(62) + 3} x2={x(62)} y2={y(57.3) - 2} tone="accent" />
      <Dot cx={x(62)} cy={y(57.3)} tone="accent" r={3.5} />
      <T x={x(62) - 8} y={y(62) - 2} size={9} tone="accent" anchor="end" bold>
        62% becomes ~57%
      </T>
      <Dot cx={x(50)} cy={y(50)} tone="fg" r={3} />
      <T x={80} y={56} size={8.5} anchor="start">
        • 50% stays 50%; no call changes side
      </T>

      <Rule x1={70} y1={180} x2={370} y2={180} />
      <Rule x1={70} y1={40} x2={70} y2={180} />
      {[20, 50, 80].map((p) => (
        <T key={p} x={x(p)} y={192} size={8.5} tone="muted">
          {p}%
        </T>
      ))}
      <T x={220} y={206} size={9} tone="muted">
        what the model says
      </T>
      <T x={74} y={34} size={9} tone="muted" anchor="start">
        what it says after correction
      </T>
    </Svg>
  );
}

function ChampionLifecycle() {
  return (
    <Svg vb="0 0 440 210">
      <T x={220} y={16} bold>
        Champion, challenger and three strikes
      </T>
      <Box x={14} y={30} w={96} h={40} />
      <T x={62} y={54} size={10} bold>
        Challenger
      </T>
      <Arrow x1={110} y1={50} x2={138} y2={50} />
      <Box x={140} y={30} w={130} h={40} />
      <T x={205} y={46} size={9}>
        three floors, then
      </T>
      <T x={205} y={60} size={9}>
        beat champion by 0.002
      </T>
      <Arrow x1={270} y1={50} x2={298} y2={50} tone="accent" />
      <Box x={300} y={30} w={124} h={40} tone="accent" fill />
      <T x={362} y={54} size={10} tone="accent" bold>
        Champion
      </T>

      <Arrow x1={362} y1={70} x2={362} y2={94} />
      <Box x={282} y={96} w={152} h={30} />
      <T x={358} y={115} size={9}>
        re-checked every retrain
      </T>
      <T x={358} y={150} size={14} tone="danger" bold>
        ✗ ✗ ✗
      </T>
      <T x={358} y={166} size={8.5} tone="danger">
        three failures in a row
      </T>
      <T x={358} y={190} size={8.5} tone="accent">
        ✓ one pass resets the count
      </T>

      <Arrow x1={300} y1={146} x2={196} y2={146} tone="danger" />
      <Box x={34} y={128} w={160} h={38} tone="warn" fill />
      <T x={114} y={144} size={9.5} tone="warn" bold>
        Baseline rule takes over
      </T>
      <T x={114} y={158} size={8.5} tone="muted">
        until a model earns the job
      </T>
      <Arrow x1={62} y1={128} x2={62} y2={73} tone="muted" dashed />
      <T x={68} y={104} size={8} tone="muted" anchor="start">
        challengers keep trying
      </T>
    </Svg>
  );
}

function FormingVsFinished() {
  return (
    <Svg vb="0 0 440 215">
      <T x={220} y={16} bold>
        A bar saved too early vs a finished bar
      </T>
      <Rule x1={40} y1={120} x2={400} y2={120} tone="border" dashed width={1} />
      <T x={38} y={116} size={8} tone="muted" anchor="start">
        open
      </T>

      {/* the snapshot, with the real candle as a ghost behind it */}
      <rect x={106} y={60} width={28} height={60} rx={2} className={TONE.border}
        stroke="currentColor" strokeDasharray="3 3" fill="none" />
      <Rule x1={120} y1={36} x2={120} y2={60} tone="border" dashed width={1} />
      <Rule x1={120} y1={120} x2={120} y2={160} tone="border" dashed width={1} />
      <Rule x1={120} y1={102} x2={120} y2={130} tone="warn" width={1.6} />
      <Fill x={108} y={110} w={24} h={10} tone="warn" opacity={0.7} rx={1} />
      <T x={120} y={182} size={9.5} tone="warn" bold>
        saved at 14:08
      </T>
      <T x={120} y={196} size={8.5} tone="muted">
        typically ~23% of the hour&apos;s real range
      </T>

      {/* the finished bar */}
      <Rule x1={320} y1={36} x2={320} y2={160} tone="accent" width={1.6} />
      <Fill x={306} y={60} w={28} h={60} tone="accent" opacity={0.7} rx={1} />
      <T x={320} y={182} size={9.5} tone="accent" bold>
        finished at 15:00, stored 15:02
      </T>
      <T x={320} y={196} size={8.5} tone="muted">
        the real high, low and close
      </T>

      <T x={220} y={88} size={9} tone="muted">
        the next fetch
      </T>
      <T x={220} y={100} size={9} tone="muted">
        replaces it, logged
      </T>
      <Arrow x1={160} y1={110} x2={290} y2={110} tone="accent" />
    </Svg>
  );
}

function GradeOwnBar() {
  const hours = ['15:00', '16:00', '17:00', '18:00', '19:00', '20:00'];
  const bx = (i: number) => 40 + i * 60;
  return (
    <Svg vb="0 0 440 205">
      <T x={220} y={16} bold>
        Which bar grades a call with an 18:00 horizon?
      </T>
      {hours.map((h, i) => (
        <g key={h}>
          {i === 2 && <Fill x={bx(i)} y={56} w={56} h={30} tone="danger" opacity={0.18} rx={7} />}
          {i === 3 && <Fill x={bx(i)} y={56} w={56} h={30} tone="accent" opacity={0.25} rx={7} />}
          <Box x={bx(i)} y={56} w={56} h={30} />
          <T x={bx(i) + 28} y={75} size={8.5}>
            {h} bar
          </T>
        </g>
      ))}
      <Rule x1={bx(3)} y1={42} x2={bx(3)} y2={96} tone="warn" width={1.6} />
      <T x={bx(3)} y={38} size={9} tone="warn" bold>
        horizon 18:00
      </T>

      <Arrow x1={188} y1={116} x2={188} y2={90} tone="danger" />
      <T x={196} y={128} size={9} tone="danger" anchor="end">
        old: the bar before the horizon,
      </T>
      <T x={196} y={140} size={9} tone="danger" anchor="end">
        often only minutes old
      </T>
      <Arrow x1={248} y1={116} x2={248} y2={90} tone="accent" />
      <T x={240} y={128} size={9} tone="accent" anchor="start">
        now: the bar containing the horizon,
      </T>
      <T x={240} y={140} size={9} tone="accent" anchor="start">
        once it has finished (19:00)
      </T>
      <T x={220} y={172} size={9}>
        A call waits for its own finished bar before it is graded.
      </T>
      <T x={220} y={190} size={8.5} tone="muted">
        The October audit: 2,134 of 2,229 hourly calls had been graded one bar early.
      </T>
    </Svg>
  );
}

function PlanAnatomy() {
  const parts = [
    { x: 20, y: 30, head: 'Why?', sub: 'a reason it might work' },
    { x: 170, y: 30, head: 'Entry', sub: 'rule, filled next open' },
    { x: 320, y: 30, head: 'Stop', sub: 'ATR or structure' },
    { x: 20, y: 134, head: 'Target', sub: 'an R multiple' },
    { x: 170, y: 134, head: 'Time limit', sub: 'exit after N bars' },
    { x: 320, y: 134, head: 'Size', sub: 'risk engine, ≤ 2%' },
  ];
  return (
    <Svg vb="0 0 440 200">
      <T x={220} y={18} bold>
        A complete trading plan
      </T>
      {parts.map((p, i) => {
        const top = p.y < 100;
        const tx = 200 + (i % 3) * 20;
        return (
          <g key={p.head}>
            <Box x={p.x} y={p.y} w={100} h={40} />
            <T x={p.x + 50} y={p.y + 17} size={10} bold>
              {p.head}
            </T>
            <T x={p.x + 50} y={p.y + 31} size={8.5} tone="muted">
              {p.sub}
            </T>
            <Arrow
              x1={p.x + 50}
              y1={top ? p.y + 40 : p.y}
              x2={tx}
              y2={top ? 84 : 118}
              tone="muted"
            />
          </g>
        );
      })}
      <Box x={170} y={84} w={100} h={34} tone="accent" fill />
      <T x={220} y={105} size={10.5} tone="accent" bold>
        the plan
      </T>
      <T x={220} y={192} size={9} tone="muted">
        Results in R after costs, so a plan&apos;s breakeven is 0R per trade.
      </T>
    </Svg>
  );
}

function WalkForwardHoldout() {
  const dev = [0, 1, 2, 3, 4];
  const bx = (i: number) => 40 + i * 62;
  const rows = [0, 1, 2, 3, 4];
  return (
    <Svg vb="0 0 440 215">
      <T x={220} y={16} bold>
        Walk-forward, then one final exam
      </T>
      <T x={193} y={34} size={9} tone="muted">
        development history
      </T>
      <T x={388} y={34} size={9} tone="warn" bold>
        held-out
      </T>
      {rows.map((r) => {
        const y = 42 + r * 28;
        const exam = r === 4;
        return (
          <g key={r}>
            {dev.map((i) => {
              const choose = exam ? true : i <= r;
              const trade = !exam && i === r + 1;
              return (
                <g key={i}>
                  {choose && <Fill x={bx(i)} y={y} w={58} h={20} tone="muted" opacity={0.22} />}
                  {trade && <Fill x={bx(i)} y={y} w={58} h={20} tone="accent" opacity={0.4} />}
                  {!choose && !trade && (
                    <rect x={bx(i)} y={y} width={58} height={20} rx={4} className={TONE.border}
                      stroke="currentColor" strokeWidth={1} fill="none" />
                  )}
                  {choose && (
                    <T x={bx(i) + 29} y={y + 14} size={8} tone="muted">
                      choose
                    </T>
                  )}
                  {trade && (
                    <T x={bx(i) + 29} y={y + 14} size={8} tone="accent" bold>
                      trade
                    </T>
                  )}
                </g>
              );
            })}
            {exam ? (
              <>
                <Fill x={352} y={y} w={72} h={20} tone="warn" opacity={0.35} />
                <T x={388} y={y + 14} size={8} tone="warn" bold>
                  exam, once
                </T>
              </>
            ) : (
              <rect x={352} y={y} width={72} height={20} rx={4} className={TONE.border}
                stroke="currentColor" strokeWidth={1} strokeDasharray="3 3" fill="none" />
            )}
          </g>
        );
      })}
      <T x={220} y={194} size={8.5} tone="muted">
        Held-out starts 1 Jan 2024 (daily ideas) and 1 Apr 2026 (hourly ideas), fixed in code.
      </T>
      <T x={220} y={208} size={8.5} tone="muted">
        A setting that lost money in the earlier blocks doesn&apos;t trade the next one.
      </T>
    </Svg>
  );
}

function RisingBar() {
  const x = (n: number) => 60 + (Math.log10(n) / Math.log10(500)) * 330;
  const y = (s: number) => 170 - s * 26;
  // Expected best t-score from pure luck across n tries (deflation.py's E[max]).
  const luck: [number, number][] = [
    [1, 0],
    [2, 0.52],
    [5, 1.19],
    [10, 1.58],
    [20, 1.9],
    [74, 2.42],
    [200, 2.77],
    [500, 3.05],
  ];
  const points = luck.map(([n, s]) => `${x(n)},${y(s)}`).join(' ');
  return (
    <Svg vb="0 0 440 215">
      <T x={220} y={16} bold>
        Why the bar rises with every try
      </T>
      <Rule x1={60} y1={y(1.96)} x2={390} y2={y(1.96)} tone="border" dashed />
      <T x={64} y={y(1.96) - 4} size={8} tone="muted" anchor="start">
        one test on its own: ~2
      </T>
      <polyline points={points} className={TONE.muted} stroke="currentColor" strokeWidth={2} fill="none" />
      <T x={386} y={y(3.05) - 8} size={8.5} tone="muted" anchor="end">
        best score from luck alone
      </T>

      <Dot cx={x(74)} cy={y(4.38)} tone="warn" r={5} />
      <T x={x(74) - 9} y={y(4.38) - 2} size={9} tone="warn" anchor="end" bold>
        the lab&apos;s bar today ≈ 4.4
      </T>
      <T x={x(74) - 9} y={y(4.38) + 10} size={8} tone="muted" anchor="end">
        74 trials, plus a 95% safety margin
      </T>
      <Dot cx={x(74)} cy={y(0.97)} tone="accent" r={5} />
      <T x={x(74) + 9} y={y(0.97) + 3} size={9} tone="accent" anchor="start" bold>
        best idea so far ≈ 1.0
      </T>

      <Rule x1={60} y1={170} x2={390} y2={170} />
      <Rule x1={60} y1={36} x2={60} y2={170} />
      {[1, 10, 74, 500].map((n) => (
        <T key={n} x={x(n)} y={182} size={8.5} tone="muted">
          {n}
        </T>
      ))}
      {[0, 2, 4].map((s) => (
        <T key={s} x={54} y={y(s) + 3} size={8.5} tone="muted" anchor="end">
          {s}
        </T>
      ))}
      <T x={62} y={32} size={9} tone="muted" anchor="start">
        score
      </T>
      <T x={225} y={198} size={9} tone="muted">
        settings ever tried (log scale)
      </T>
    </Svg>
  );
}

function LabLifecycle() {
  return (
    <Svg vb="0 0 440 215">
      <T x={220} y={16} bold>
        An idea&apos;s life in the lab
      </T>
      <Box x={10} y={40} w={76} h={32} />
      <T x={48} y={60} size={9.5} bold>
        new idea
      </T>
      <Arrow x1={86} y1={56} x2={112} y2={56} />
      <Box x={114} y={40} w={104} h={32} />
      <T x={166} y={60} size={9.5} bold>
        back-test gate
      </T>

      <Arrow x1={166} y1={72} x2={166} y2={106} tone="danger" />
      <T x={172} y={92} size={8} tone="danger" anchor="start">
        fails
      </T>
      <Box x={114} y={108} w={104} h={40} tone="danger" fill />
      <T x={166} y={125} size={9.5} tone="danger" bold>
        rejected
      </T>
      <T x={166} y={139} size={8} tone="muted">
        never trades · 8 of 8 so far
      </T>

      <Arrow x1={218} y1={56} x2={246} y2={56} tone="accent" />
      <T x={232} y={50} size={8} tone="accent">
        passes
      </T>
      <Box x={248} y={40} w={84} h={32} tone="warn" />
      <T x={290} y={60} size={9.5} bold>
        paper trading
      </T>
      <Arrow x1={332} y1={56} x2={352} y2={56} tone="accent" />
      <Box x={354} y={40} w={80} h={32} tone="accent" fill />
      <T x={394} y={60} size={9.5} tone="accent" bold>
        recommended
      </T>
      <T x={342} y={32} size={8} tone="muted">
        checkpoint every 30 trades
      </T>

      <Arrow x1={384} y1={72} x2={384} y2={106} tone="warn" />
      <Arrow x1={404} y1={108} x2={404} y2={74} tone="accent" dashed />
      <Box x={354} y={108} w={80} h={32} tone="warn" />
      <T x={394} y={128} size={9.5} tone="warn" bold>
        demoted
      </T>
      <T x={394} y={154} size={8} tone="muted">
        can earn it back
      </T>

      <Arrow x1={290} y1={72} x2={290} y2={160} tone="danger" />
      <Arrow x1={364} y1={140} x2={322} y2={162} tone="danger" />
      <Box x={248} y={162} w={84} h={30} tone="danger" fill />
      <T x={290} y={181} size={9.5} tone="danger" bold>
        retired
      </T>
      <T x={284} y={98} size={8} tone="danger" anchor="end">
        significantly
      </T>
      <T x={284} y={109} size={8} tone="danger" anchor="end">
        losing
      </T>
      <T x={220} y={208} size={9} tone="accent">
        Paper only: nothing ever reaches a broker.
      </T>
    </Svg>
  );
}

function AutonomyLoop() {
  const boxes = [
    { x: 20, y: 34, head: 'The app', sub: 'predicts, grades, retrains' },
    { x: 270, y: 34, head: 'Self-report', sub: 'health + issue codes' },
    { x: 270, y: 134, head: 'Maintenance agent', sub: 'daily 06:30 UTC · one change' },
    { x: 20, y: 134, head: 'Server auto-deploy', sub: 'refuse · check · roll back' },
  ];
  return (
    <Svg vb="0 0 440 215">
      <T x={220} y={16} bold>
        Who looks after what
      </T>
      {boxes.map((b) => (
        <g key={b.head}>
          <Box x={b.x} y={b.y} w={150} h={46} />
          <T x={b.x + 75} y={b.y + 20} size={10} bold>
            {b.head}
          </T>
          <T x={b.x + 75} y={b.y + 35} size={8.5} tone="muted">
            {b.sub}
          </T>
        </g>
      ))}
      <Arrow x1={170} y1={57} x2={268} y2={57} />
      <T x={219} y={51} size={8} tone="muted">
        reports
      </T>
      <Arrow x1={345} y1={80} x2={345} y2={132} />
      <T x={351} y={110} size={8} tone="muted" anchor="start">
        reads
      </T>
      <Arrow x1={270} y1={157} x2={172} y2={157} />
      <T x={221} y={151} size={8} tone="muted">
        pushes code
      </T>
      <Arrow x1={95} y1={134} x2={95} y2={82} tone="accent" />
      <T x={101} y={112} size={8} tone="accent" anchor="start">
        ships only if healthy
      </T>

      <Box x={180} y={92} w={80} h={28} tone="accent" />
      <T x={220} y={110} size={9.5} tone="accent" bold>
        you (Telegram)
      </T>
      <Arrow x1={300} y1={80} x2={258} y2={94} tone="accent" dashed />
      <Arrow x1={150} y1={134} x2={186} y2={121} tone="accent" dashed />
      <T x={220} y={204} size={9} tone="muted">
        Fix days Sunday to Friday; Saturday is the one improve day.
      </T>
    </Svg>
  );
}

function DeployGate() {
  return (
    <Svg vb="0 0 440 215">
      <T x={220} y={16} bold>
        Every 10 minutes on the server
      </T>
      <Box x={8} y={32} w={72} h={32} />
      <T x={44} y={52} size={9} bold>
        new code
      </T>
      <Arrow x1={80} y1={48} x2={98} y2={48} />
      <Box x={100} y={32} w={82} h={32} />
      <T x={141} y={52} size={9} bold>
        protected?
      </T>
      <Arrow x1={182} y1={48} x2={200} y2={48} />
      <T x={191} y={42} size={8} tone="muted">
        no
      </T>
      <Box x={202} y={32} w={92} h={32} />
      <T x={248} y={46} size={8.5}>
        back up (if needed),
      </T>
      <T x={248} y={58} size={8.5}>
        build, start
      </T>
      <Arrow x1={294} y1={48} x2={312} y2={48} />
      <Box x={314} y={32} w={118} h={32} />
      <T x={373} y={46} size={8.5} bold>
        healthy in 5 min,
      </T>
      <T x={373} y={58} size={8.5} bold>
        no crash in logs?
      </T>

      <Arrow x1={141} y1={64} x2={141} y2={98} tone="danger" />
      <T x={147} y={84} size={8} tone="danger" anchor="start">
        yes
      </T>
      <Box x={100} y={100} w={82} h={30} tone="danger" fill />
      <T x={141} y={119} size={9.5} tone="danger" bold>
        refused
      </T>

      <Arrow x1={340} y1={64} x2={334} y2={98} tone="accent" />
      <Arrow x1={406} y1={64} x2={406} y2={98} tone="warn" />
      <T x={324} y={84} size={8} tone="accent" anchor="end">
        yes
      </T>
      <T x={412} y={84} size={8} tone="warn" anchor="start">
        no
      </T>
      <Box x={300} y={100} w={64} h={30} tone="accent" fill />
      <T x={332} y={119} size={9.5} tone="accent" bold>
        live ✓
      </T>
      <Box x={370} y={100} w={64} h={30} tone="warn" fill />
      <T x={402} y={113} size={8.5} tone="warn" bold>
        rolled
      </T>
      <T x={402} y={124} size={8.5} tone="warn" bold>
        back ↺
      </T>

      <Arrow x1={141} y1={130} x2={170} y2={158} tone="muted" />
      <Arrow x1={332} y1={130} x2={300} y2={158} tone="muted" />
      <Arrow x1={402} y1={130} x2={360} y2={158} tone="muted" />
      <Box x={60} y={160} w={320} h={28} tone="accent" />
      <T x={220} y={178} size={9}>
        Telegram message + recorded in the report, every time
      </T>
      <T x={220} y={206} size={8.5} tone="muted">
        Between deploys: if the app stops answering for ~30 minutes, it is restarted.
      </T>
    </Svg>
  );
}

function ProtectedThresholds() {
  const left = [
    'Brier floor 0.248 (margin 0.002)',
    'breakeven floor (cost-based)',
    'coverage ≥ 15% of hours',
    'demote after 3 failed re-checks',
    '30-result verdict floor',
    '95% confidence level',
    'costs: 0.8 spread + 0.2 slippage',
  ];
  const right = [
    'windows needed to measure breakeven',
    'COT 4-day publication lag',
    'lab: held-out start dates',
    'lab: walk-forward blocks, min. trades',
    'lab: 30-trade live checkpoints',
    'lab: its gate and promotion code',
    'the safety net itself',
  ];
  return (
    <Svg vb="0 0 440 215">
      <T x={220} y={16} bold>
        Locked: only a human may change these
      </T>
      <Box x={14} y={26} w={412} h={136} tone="warn" />
      {left.map((t, i) => (
        <T key={t} x={28} y={48 + i * 16} size={8.5} anchor="start">
          • {t}
        </T>
      ))}
      {right.map((t, i) => (
        <T key={t} x={226} y={48 + i * 16} size={8.5} anchor="start">
          • {t}
        </T>
      ))}
      <Box x={36} y={174} w={176} h={28} tone="accent" fill />
      <T x={124} y={192} size={9} tone="accent" bold>
        lock 1: a test pins them
      </T>
      <Box x={228} y={174} w={176} h={28} tone="accent" fill />
      <T x={316} y={192} size={9} tone="accent" bold>
        lock 2: the server refuses edits
      </T>
    </Svg>
  );
}

function HonestScorecard() {
  const columns: { x: number; tone: Tone; head: string; items: string[] }[] = [
    {
      x: 10,
      tone: 'accent',
      head: 'Strong',
      items: [
        'volatility forecast',
        'sizing from the stop',
        'the cost hurdle',
        'independent windows',
        'held-out tests',
        'locked thresholds',
      ],
    },
    {
      x: 153,
      tone: 'warn',
      head: 'Unproven',
      items: [
        '24-hour direction',
        '(range includes breakeven)',
        '5-day direction',
        '(baseline rule for now)',
        'trading plans: 0 of 8',
        'COT positioning',
      ],
    },
    {
      x: 296,
      tone: 'danger',
      head: 'Never',
      items: [
        'placing trades',
        'talking to a broker',
        'promising returns',
        '"probably" read as',
        '"certainly"',
      ],
    },
  ];
  return (
    <Svg vb="0 0 440 200">
      <T x={220} y={16} bold>
        An honest scorecard
      </T>
      {columns.map((c) => (
        <g key={c.head}>
          <Box x={c.x} y={28} w={134} h={160} tone={c.tone} fill />
          <T x={c.x + 67} y={48} size={11} tone={c.tone} bold>
            {c.head}
          </T>
          {c.items.map((item, i) => (
            <T key={item} x={c.x + 67} y={72 + i * 18} size={8.5}>
              {item}
            </T>
          ))}
        </g>
      ))}
    </Svg>
  );
}

const FIGURES: Record<string, () => ReactNode> = {
  'honest-thesis': HonestThesis,
  'data-pipeline': DataPipeline,
  'feature-families': FeatureFamilies,
  'point-in-time': PointInTime,
  'trade-management': TradeManagement,
  'loss-root-causes': LossRootCauses,
  abstention: Abstention,
  'direction-model': DirectionModel,
  'vol-cone': VolCone,
  reliability: Reliability,
  'learning-loop': LearningLoop,
  'risk-sizing': RiskSizing,
  tipster: Tipster,
  // general curriculum
  'pair-ratio': PairRatio,
  leverage: Leverage,
  spread: Spread,
  'risk-vs-predict': RiskVsPredict,
  'drawdown-recovery': DrawdownRecovery,
  'size-formula': SizeFormula,
  guardrails: Guardrails,
  'trend-context': TrendContext,
  'sr-zones': SrZones,
  'candle-anatomy': CandleAnatomy,
  'ma-lag': MaLag,
  'rsi-regime': RsiRegime,
  'atr-stop': AtrStop,
  'expectancy-formula': ExpectancyFormula,
  'r-ruler': RRuler,
  'winrate-myth': WinrateMyth,
  lookahead: Lookahead,
  overfitting: Overfitting,
  'costs-erase-edge': CostsEraseEdge,
  'journal-vs-memory': JournalVsMemory,
  'trend-types': TrendTypes,
  'price-action-map': PriceActionMap,
  'market-structure-swings': MarketStructureSwings,
  'candle-zoo': CandleZoo,
  'volume-profile': VolumeProfile,
  'liquidity-pools': LiquidityPools,
  'smc-blocks': SmcBlocks,
  'order-grid': OrderGrid,
  'market-conditions': MarketConditions,
  'system-plain': SystemPlain,
  'tabs-trading': TabsTrading,
  'tabs-toolkit': TabsToolkit,
  'order-types': OrderTypes,
  'sessions-clock': SessionsClock,
  'spread-anatomy': SpreadAnatomy,
  'leverage-seesaw': LeverageSeesaw,
  'plan-pyramid': PlanPyramid,
  'daily-routine-timeline': DailyRoutineTimeline,
  'account-ladder': AccountLadder,
  'mentor-day-flow': MentorDayFlow,
  'ticket-anatomy': TicketAnatomy,
  'drift-watch': DriftWatch,
  'process-vs-outcome': ProcessVsOutcome,
  'tilt-spiral': TiltSpiral,
  'review-tags': ReviewTags,
  // methods & tools
  'schools-of-analysis': SchoolsOfAnalysis,
  'top-down': TopDown,
  'edge-pipeline': EdgePipeline,
  'predictable-vs-not': PredictableVsNot,
  distributions: Distributions,
  'charts-platforms': ChartsPlatforms,
  'data-calendar': DataCalendar,
  'risk-tools': RiskTools,
  'automation-stack': AutomationStack,
  'weekly-routine': WeeklyRoutine,
  // chart terminology
  'bull-bear': BullBear,
  'trend-structure': TrendStructure,
  'moves-in-trend': MovesInTrend,
  'candle-types': CandleTypes,
  fibonacci: Fibonacci,
  'trade-anatomy': TradeAnatomy,
  // how the mentor keeps itself honest
  'breakeven-hurdle': BreakevenHurdle,
  'promotion-floors': PromotionFloors,
  'abstain-by-profit': AbstainByProfit,
  'overlapping-windows': OverlappingWindows,
  'interval-shrink': IntervalShrink,
  'cot-publication-lag': CotPublicationLag,
  'live-recalibration': LiveRecalibration,
  'champion-lifecycle': ChampionLifecycle,
  'forming-vs-finished': FormingVsFinished,
  'grade-own-bar': GradeOwnBar,
  'plan-anatomy': PlanAnatomy,
  'walk-forward-holdout': WalkForwardHoldout,
  'rising-bar': RisingBar,
  'lab-lifecycle': LabLifecycle,
  'autonomy-loop': AutonomyLoop,
  'deploy-gate': DeployGate,
  'protected-thresholds': ProtectedThresholds,
  'honest-scorecard': HonestScorecard,
};

export function LessonFigure({ figureKey, caption }: { figureKey: string; caption: string }) {
  const Fig = FIGURES[figureKey];
  if (!Fig) return null;
  return (
    <figure className="rounded-xl border border-mentor-border bg-mentor-panelLight/40 p-4">
      <div className="mx-auto max-w-md">
        <Fig />
      </div>
      <figcaption className="mt-2 text-center text-xs text-mentor-muted">{caption}</figcaption>
    </figure>
  );
}
