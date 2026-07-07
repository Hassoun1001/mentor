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

const FIGURES: Record<string, () => ReactNode> = {
  'honest-thesis': HonestThesis,
  'data-pipeline': DataPipeline,
  'feature-families': FeatureFamilies,
  'point-in-time': PointInTime,
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
