"""The curriculum catalog.

Modules and lessons are defined here as immutable Python objects so the
content is reviewed in code, the build is deterministic, and seeding the
database is a no-op. Add a lesson by appending to `CATALOG` and writing
its body — that's it.

Lesson bodies are markdown. They render in the frontend Lessons reader.
The voice is deliberate: explain the concept, name the failure mode,
point at the relevant app feature.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from mentor.domain.errors import ValidationError


@dataclass(frozen=True, slots=True)
class Lesson:
    slug: str
    module_id: str
    order_in_module: int
    title: str
    summary: str
    body_md: str
    est_minutes: int
    key_concepts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Module:
    id: str
    order: int
    title: str
    summary: str
    lessons: tuple[Lesson, ...]

    @property
    def est_minutes(self) -> int:
        return sum(lesson.est_minutes for lesson in self.lessons)


# ---------------------------------------------------------------------------
# Module 1 — Market basics
# ---------------------------------------------------------------------------

_MARKET_BASICS = (
    Lesson(
        slug="market-basics/what-you-are-trading",
        module_id="market-basics",
        order_in_module=1,
        title="What you're actually trading",
        summary="A currency pair is not a thing — it's a ratio.",
        est_minutes=4,
        key_concepts=("pair", "base", "quote", "ratio"),
        body_md="""
A currency pair like **EUR/USD** is a ratio: how many US dollars one euro
costs *right now*. When the quote moves from 1.0850 to 1.0900, the euro
got 0.46% more expensive in dollar terms — nothing else.

You are never trading "the euro." You're trading the *relationship*
between two currencies. If both rise versus the world, EUR/USD might not
move at all. That's why economic data on either side moves the pair.

### What this means in practice

- The pair has two stories at once. A great euro story can be cancelled
  by a great dollar story.
- "Strong dollar" and "strong euro" are not opposites in the news, but
  they are in your P&L.
- Whenever you see a headline about USD, it's news about EUR/USD too —
  just from the other side.
""".strip(),
    ),
    Lesson(
        slug="market-basics/lots-pips-leverage",
        module_id="market-basics",
        order_in_module=2,
        title="Lots, pips, and leverage",
        summary="The three numbers that decide your exposure.",
        est_minutes=5,
        key_concepts=("pip", "lot", "leverage", "margin", "contract size"),
        body_md="""
- **Pip** — the smallest standard increment. `0.0001` for most majors,
  `0.01` for JPY pairs.
- **Lot** — the standard trade size. One standard lot is **100,000 units**
  of the base currency. A mini is 10,000, a micro is 1,000.
- **Leverage** — borrowed exposure. 100:1 leverage means your $1,000 of
  margin controls $100,000 of currency. The gain and loss both multiply.

A 0.10 lot on EUR/USD at 1.08 means you're holding €10,000 of exposure,
worth about $10,800. A one-pip move is worth $1. A hundred-pip move is
$100 — about 1% of the notional, often more than 10% of the margin.

### Why this matters

Leverage is the reason you can lose more than you've planned in a hurry.
The position-size calculator turns the *risk you're willing to take* into
*lots*. Use it. Don't size by feel.
""".strip(),
    ),
    Lesson(
        slug="market-basics/spread-is-your-first-expense",
        module_id="market-basics",
        order_in_module=3,
        title="Spread is your first expense",
        summary="Every round-trip starts in the red.",
        est_minutes=3,
        key_concepts=("bid", "ask", "spread", "transaction cost"),
        body_md="""
The **bid** is the price someone will pay you for the pair right now.
The **ask** is the price someone will sell it to you. The gap is the
**spread**, and the spread is a fee.

Open a EUR/USD position with a 0.8 pip spread and you start ~$0.80 in
the red on a 0.10 lot. Tight, but real. Now consider scalping: 30 trades
a day × 0.8 pips × $1 = $24/day of pure cost, before slippage. A small
"edge" can vanish into the spread.

### When the spread is dangerous

- During news releases — spreads can jump 5–10×.
- At session open/close — liquidity thins, spreads widen.
- On exotic pairs — even off-news the spread costs more than the edge
  most strategies could ever produce.

The backtester (Phase 3) models spread on every trade. Without that,
paper edges are fiction.
""".strip(),
    ),
)

# ---------------------------------------------------------------------------
# Module 2 — Risk first (the heart of the curriculum)
# ---------------------------------------------------------------------------

_RISK_FIRST = (
    Lesson(
        slug="risk-first/why-risk-beats-prediction",
        module_id="risk-first",
        order_in_module=1,
        title="Why risk management beats prediction",
        summary="Most traders fail on sizing, not on direction.",
        est_minutes=6,
        key_concepts=("position sizing", "expectancy", "drawdown", "ruin"),
        body_md="""
The myth says good traders predict the market. The truth is they manage
their *losses*. A trader who is right 55% of the time but risks 10% of
the account on each trade will go broke; a trader who is right 45% of
the time but risks 1% can grind out years of returns.

The reason is asymmetry. Losing 50% requires gaining 100% to recover.
Losing 80% requires 500%. Big losses are the only kind that matter.

### The product reflects this

- The **risk engine** is Phase 0 — built before any signal.
- The **position-size calculator** sizes every trade from your stop, not
  your hope.
- **Guardrails** block the trade if it would put the account over its
  per-day or per-portfolio risk budget.

If a feature gets in the way of disciplined sizing, the feature is
wrong. Not the discipline.
""".strip(),
    ),
    Lesson(
        slug="risk-first/the-one-percent-rule",
        module_id="risk-first",
        order_in_module=2,
        title="The 1% rule and where it comes from",
        summary="It's not magic — it's how long you can survive a losing streak.",
        est_minutes=7,
        key_concepts=("risk per trade", "drawdown", "losing streak", "risk of ruin"),
        body_md="""
Risking 1% per trade is not a sacred number. It's a *survival* number.

Plug it in: a strategy with a 50% hit rate has a ~10% chance of losing
7 trades in a row over a 100-trade sample. At 1% per trade, that's a
~6.8% drawdown — uncomfortable but recoverable. At 5%? A 30% drawdown
that requires ~43% to recover. At 10%? You're done.

### What to keep

- **1–2%** is the textbook range for discretionary traders.
- The risk engine flags anything above 2% as **aggressive**.
- The hard ceiling baked into the calculator is **10%** — refusing
  larger inputs entirely so a typo doesn't blow the account.

The curriculum's last module covers risk-of-ruin properly with a
Monte-Carlo simulator. Until then, use the rule.
""".strip(),
    ),
    Lesson(
        slug="risk-first/size-from-your-stop",
        module_id="risk-first",
        order_in_module=3,
        title="Sizing from your stop, not your target",
        summary="The stop is a fact. The target is a hope.",
        est_minutes=5,
        key_concepts=("position size", "stop", "pip value", "ceiling"),
        body_md="""
The position-size formula:

```
risk_amount       = account × risk_pct
stop_distance     = |entry − stop|
pip_distance      = stop_distance / pip_size
pip_value         = contract_size × pip_size × quote_to_account_rate
lots              = risk_amount / (pip_distance × pip_value)
```

Notice what's *not* in there: the target. The target affects R:R, not
size. If you have a 30-pip stop and risk $100, you size for that — no
matter how far away the target is.

The calculator rounds **down** to the broker's minimum lot. That's
deliberate: the risk budget is a *ceiling*, not a target. A larger lot
would put you over budget, and that's the one thing the system will
never do.

If the rounded size is `0`, the lesson is the same as the calculator's:
your stop is too far for the budget you've set. Tighten the stop, raise
the budget, or skip the trade.
""".strip(),
    ),
    Lesson(
        slug="risk-first/account-guardrails",
        module_id="risk-first",
        order_in_module=4,
        title="Account guardrails",
        summary="One bad trade is normal. Three in a row is a pattern.",
        est_minutes=5,
        key_concepts=("max risk per trade", "max open risk", "daily loss limit", "tilt"),
        body_md="""
Three guardrails layer on top of per-trade sizing:

- **Max risk per trade** — the hard cap on a single position.
- **Max simultaneous open risk** — the cap on every open trade
  *combined*. Two 2% trades is 4% on the table.
- **Daily loss limit** — when realised loss hits this, the day is
  over. No more trades.

The daily loss limit is the most important of the three. After two
losses, the brain wants to "get it back." That instinct is what hands
the account to the market. The limit removes the choice.

The guardrail report names the rule, shows current vs. limit, and
gives a mentor-voiced note when you're close. The frontend can
choose to block or just warn — that's policy. The rule itself is
domain.
""".strip(),
    ),
)

# ---------------------------------------------------------------------------
# Module 3 — Reading charts
# ---------------------------------------------------------------------------

_READING_CHARTS = (
    Lesson(
        slug="reading-charts/trend-and-obvious-patterns",
        module_id="reading-charts",
        order_in_module=1,
        title="Trend and the fallacy of obvious patterns",
        summary="If it's obvious to you, it's obvious to a million machines.",
        est_minutes=5,
        key_concepts=("trend", "pattern recognition", "efficiency", "noise"),
        body_md="""
A chart pattern that's "clearly" a head-and-shoulders is also clearly a
head-and-shoulders to every algo with a TA library. The information was
priced in seconds after the third shoulder formed.

The chart is best used for **context**, not signal:

- Which direction has price been moving for the timeframe I care about?
- Are we near a level the market obviously remembers?
- Is volatility (the bar size) calm or wild?

Use it to size the trade and pick the stop. Don't use it to predict
where price will go next — that's the opposite of how the smart money
uses charts.
""".strip(),
    ),
    Lesson(
        slug="reading-charts/support-resistance",
        module_id="reading-charts",
        order_in_module=2,
        title="Support and resistance as memory, not magic",
        summary="Old prices matter because traders remember them.",
        est_minutes=5,
        key_concepts=("support", "resistance", "level", "self-fulfilling", "stop hunt"),
        body_md="""
Support and resistance aren't physical laws. They're places where lots
of stops cluster, where breakouts happen, and where the market hunts
for liquidity. They work because traders behave consistently at them —
until they don't.

### Pragmatic use

- Mark **major** levels only (weekly highs/lows, prior swing extremes).
- Treat them as **zones**, not lines — price respects ranges, not pixels.
- Expect the **stop hunt**: a brief penetration before the reversal.
  This is why ATR-scaled stops survive moves that 5-pip stops do not.
""".strip(),
    ),
    Lesson(
        slug="reading-charts/candlesticks",
        module_id="reading-charts",
        order_in_module=3,
        title="Candlesticks: what they show, what they don't",
        summary="Open / high / low / close — that's the whole signal.",
        est_minutes=4,
        key_concepts=("OHLC", "wick", "body", "context"),
        body_md="""
A candle compresses an interval of price into four numbers: open, high,
low, close. The body is open→close, the wicks reach to the extremes.
That's everything.

**Pin bars**, **engulfing**, **dojis** — these are names. Names are not
evidence. A doji at the top of a long run-up may matter; a doji in a
random consolidation does not.

Use candles to:

- Read recent volatility (bar size).
- See where price spent time vs. where it briefly visited.
- Notice mismatch — a fat green body that closes near the low is a
  rejection, not a buy signal.

The forecasting pipeline does not use candle patterns as features in
v1. The reason is honest: their statistical edge after costs is small.
""".strip(),
    ),
)

# ---------------------------------------------------------------------------
# Module 4 — Indicators & their failure modes
# ---------------------------------------------------------------------------

_INDICATORS = (
    Lesson(
        slug="indicators/moving-averages",
        module_id="indicators",
        order_in_module=1,
        title="Moving averages and why they lag",
        summary="They smooth the past; they cannot summon the future.",
        est_minutes=5,
        key_concepts=("SMA", "EMA", "lag", "trend filter", "whipsaw"),
        body_md="""
A 200-period moving average tells you where price was on average over
the last 200 periods. By construction, it is the slowest possible
summary of recent price — its job is to lag.

That makes it useful as a **trend filter**: "above the 200 → I look for
longs; below → shorts." It is not useful as a turn signal: by the time
the average crosses, the move is well underway.

### Failure modes

- **Whipsaw** — in sideways markets, every cross is a fake.
- **Choice of period** is arbitrary, and small changes flip the signal.
- **Crossover systems** are catnip for new traders because they look
  great in cherry-picked backtests. The benchmark you must beat in
  Phase 3 is a simple MA crossover — most "fancy" strategies don't.
""".strip(),
    ),
    Lesson(
        slug="indicators/rsi-and-the-overbought-trap",
        module_id="indicators",
        order_in_module=2,
        title="RSI and the overbought trap",
        summary='"Overbought" is not a sell signal in a trending market.',
        est_minutes=4,
        key_concepts=("RSI", "momentum", "divergence", "regime"),
        body_md="""
RSI measures recent up-moves vs. down-moves. Above 70 it's "overbought,"
below 30 it's "oversold." In a *range*, that works as a contrarian
hint. In a *trend*, it doesn't — RSI can pin at 80 for hours while
price keeps running.

### Use cases that survive

- **Divergence** at major levels — price makes a new high but RSI
  doesn't. Worth noticing, never enough alone.
- **Regime tag** — extreme readings tell you the regime is *trending*,
  not that it's about to reverse.
""".strip(),
    ),
    Lesson(
        slug="indicators/atr-and-volatility",
        module_id="indicators",
        order_in_module=3,
        title="ATR and volatility-aware stops",
        summary="Stop distance should scale with how much price normally moves.",
        est_minutes=4,
        key_concepts=("ATR", "volatility", "stop", "noise floor"),
        body_md="""
**Average True Range** is the average size of the last N bars'
true ranges. It's a noise floor: a stop closer than ~1× ATR sits
inside everyday wiggle and gets hit on randomness.

### Practical rule

- **2–3× ATR** is the typical range for swing stops.
- Calm markets (low ATR) allow tighter stops and bigger sizes — same
  risk in dollars, smaller distance.
- Volatile markets (high ATR) need wider stops, which means *smaller
  sizes for the same risk*. The position-size calculator handles this
  automatically.

The ATR helper returns a stop *distance* in price units. Combine it
with the entry to get the stop price.
""".strip(),
    ),
)

# ---------------------------------------------------------------------------
# Module 5 — Expectancy & the math of survival
# ---------------------------------------------------------------------------

_EXPECTANCY = (
    Lesson(
        slug="expectancy/the-math-of-survival",
        module_id="expectancy",
        order_in_module=1,
        title="The math of survival",
        summary="Expectancy is the only number that matters over many trades.",
        est_minutes=6,
        key_concepts=("expectancy", "win rate", "R:R", "edge"),
        body_md="""
**Expectancy** = (win rate × avg win) − (loss rate × avg loss).

It's the average outcome per trade. Positive means the strategy makes
money over time; negative means it bleeds. Zero means it pays the
spread.

### The 40% / 2R example

40% wins, 60% losses, average win = 2R, average loss = 1R:

```
E[R] = 0.4 × 2  -  0.6 × 1  =  +0.2 R per trade
```

Over 100 trades, expected gain is +20R. With a 1% risk per trade
(R = $100), that's +$2,000 on a $10,000 account — minus costs and
variance.

### Why this changes how you think

- You don't need to win often. You need a positive expected value and
  enough trades to express it.
- A "high win rate" strategy with negative expectancy still loses money.
- A "low win rate" strategy with positive expectancy makes money — but
  you have to survive the losing streaks emotionally. That's why
  guardrails exist.
""".strip(),
    ),
    Lesson(
        slug="expectancy/r-multiples",
        module_id="expectancy",
        order_in_module=2,
        title="R-multiples",
        summary="One number that compares strategies across account sizes.",
        est_minutes=4,
        key_concepts=("R-multiple", "Tharp", "normalisation"),
        body_md="""
An **R-multiple** is a trade's outcome divided by the trade's initial
risk. Stop-out = −1R. A trade that gained twice what it risked = +2R.
A break-even trade = 0R.

R-multiples normalise everything:

- Strategy A makes 5% with 0.5% risk per trade.
- Strategy B makes 5% with 2% risk per trade.

Same dollar gain. A returned **+10R**; B returned **+2.5R**. Per-trade,
A had a 4× larger edge. R-multiples make that obvious.

The journal stores realised R on every closed trade. Analytics derives
expectancy, profit factor, largest win/loss — all from that one column.
""".strip(),
    ),
    Lesson(
        slug="expectancy/why-low-win-rate-can-be-profitable",
        module_id="expectancy",
        order_in_module=3,
        title="Why a 40%-win system can be highly profitable",
        summary="Expectancy doesn't care how often you're right.",
        est_minutes=4,
        key_concepts=("win rate", "R:R", "expectancy", "psychology"),
        body_md="""
A 40% win rate at 3R wins / 1R losses returns +0.8R per trade. That's
a phenomenal strategy. Almost no one can trade it — because losing 60%
of the time, in stretches of 5+ losses, feels terrible.

This is why the journal matters more than the signal. Without a written
record, six losses in a row feel like proof the strategy is broken.
With the journal, six losses in a row look like an expected slice of
the distribution.

If the expectancy is positive and the rules haven't changed, keep
trading. If you can't, the system's expectancy doesn't matter — you
won't survive long enough to realise it.
""".strip(),
    ),
)

# ---------------------------------------------------------------------------
# Module 6 — Backtesting honestly
# ---------------------------------------------------------------------------

_BACKTESTING = (
    Lesson(
        slug="backtesting/lookahead-bias",
        module_id="backtesting",
        order_in_module=1,
        title="Lookahead bias — the subtlest fatal bug",
        summary="If your backtest used data from the future, it isn't a backtest.",
        est_minutes=5,
        key_concepts=("lookahead", "point-in-time", "data leakage"),
        body_md="""
**Lookahead bias** happens when a backtest uses information the trader
could not actually have had at the moment of the trade. Examples:

- Using today's close to decide today's entry.
- Standardising features using the *full* sample, including the future.
- Filling forward a value that wasn't published until tomorrow.

The result is a backtest that prints money and a live system that
prints losses. There is no warning — the equity curve just diverges.

### Defence

The Phase 3 backtester is **event-driven**: each timestep can only see
data with a timestamp earlier than itself. The framework enforces it;
the code can't accidentally violate it.

Every signal must survive this before it's allowed on the dashboard.
""".strip(),
    ),
    Lesson(
        slug="backtesting/overfitting",
        module_id="backtesting",
        order_in_module=2,
        title="Overfitting and how to spot it",
        summary="A model that fits noise won't fit the next year.",
        est_minutes=5,
        key_concepts=("overfitting", "out-of-sample", "walk-forward", "complexity"),
        body_md="""
Tune any model long enough and it will fit the training data perfectly.
The problem is the training data contains *noise* — coincidences that
won't repeat. The fit is to the noise, and live performance falls off
a cliff.

### Tells

- A backtest with implausibly low drawdown.
- Parameters that look "tuned" (precise decimals, oddly specific
  thresholds).
- Performance that collapses on out-of-sample data.

### Defence

- Hold out a chunk of history the model never sees during training.
- **Walk-forward**: roll the train/test window through time.
- **Penalise complexity**: prefer the simpler model when both perform
  similarly.

The plan is explicit: every signal must beat the simple baseline rule
model. If the fancier model isn't materially better out-of-sample, the
simpler one wins.
""".strip(),
    ),
    Lesson(
        slug="backtesting/transaction-costs",
        module_id="backtesting",
        order_in_module=3,
        title="Transaction costs erase paper edges",
        summary="Spread + commission + slippage is the silent killer.",
        est_minutes=4,
        key_concepts=("spread", "commission", "slippage", "frictionless"),
        body_md="""
A frictionless backtest assumes you buy at the close and sell at the
close. Live, you cross the spread on entry and exit, you pay a
commission, and your fill is rarely the price you saw. On EUR/USD that
might be 1–2 pips per round trip — small per trade, enormous over a
thousand.

### Rule

Every backtest models spread, commission, and slippage. If a strategy
needs frictionless costs to be profitable, it isn't profitable. Don't
trade it.
""".strip(),
    ),
)

# ---------------------------------------------------------------------------
# Module 7 — Psychology & process
# ---------------------------------------------------------------------------

_PSYCHOLOGY = (
    Lesson(
        slug="psychology/journaling-beats-memory",
        module_id="psychology",
        order_in_module=1,
        title="Journaling beats memory",
        summary="Memory edits your trading record. The journal doesn't.",
        est_minutes=4,
        key_concepts=("journal", "review", "self-report bias"),
        body_md="""
Without a journal, you remember the wins and reframe the losses.
"I would have been right if not for that fed announcement." With the
journal, you can't. The row is what it is.

The discipline isn't writing the entry — it's writing it *before* the
trade. The pre-trade checklist forces it. After 100 trades you can
filter your journal for "fomo" and watch your average R-multiple
collapse. That's the lesson the signal can't teach you.
""".strip(),
    ),
    Lesson(
        slug="psychology/tilt",
        module_id="psychology",
        order_in_module=2,
        title="Tilt and how to break it",
        summary="The trade after a loss is almost always wrong.",
        est_minutes=4,
        key_concepts=("tilt", "revenge trading", "daily loss limit", "circuit breaker"),
        body_md="""
**Tilt** is what poker players call the emotional state that follows a
big loss. You take more risk, on worse setups, faster than usual.
Everyone tilts. Pretending you don't is part of the problem.

### Hard rules that work

- Daily loss limit. Hit it → stop for the day. Closed.
- Cooling-off period after any −2R or worse trade. Step away. Walk.
- No "revenge" entry within an hour of a stop-out. The setup that was
  perfect is suddenly less perfect; that's information.

The guardrail engine implements the daily loss limit. The rest is up
to you. The journal will show you when you broke them.
""".strip(),
    ),
    Lesson(
        slug="psychology/weekend-review",
        module_id="psychology",
        order_in_module=3,
        title="The cost of skipped reviews",
        summary="The trades you don't review are the ones you keep losing.",
        est_minutes=3,
        key_concepts=("weekly review", "mistake tags", "pattern", "improvement"),
        body_md="""
A weekly review takes thirty minutes. Open the journal, sort by R,
read the bottom five. Tag what went wrong. Read the top five. Tag
what went right.

Patterns appear in tags before they appear in P&L. "Moved stop"
showing up six times this month is a story. "FOMO entry" showing up
every Monday after the open is a story. Without the tags, those
stories never get told.

The mentor's weekend-review feature (Phase 5) surfaces these patterns
automatically. For now, do it by hand. Thirty minutes a week.
""".strip(),
    ),
)


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


CATALOG: Final[tuple[Module, ...]] = (
    Module(
        id="market-basics",
        order=1,
        title="Market basics",
        summary="What you're actually trading, and the three numbers that move it.",
        lessons=_MARKET_BASICS,
    ),
    Module(
        id="risk-first",
        order=2,
        title="Risk first",
        summary="Most traders fail on sizing. The risk engine is built first for a reason.",
        lessons=_RISK_FIRST,
    ),
    Module(
        id="reading-charts",
        order=3,
        title="Reading charts",
        summary="Charts are context, not crystal balls. Use them skeptically.",
        lessons=_READING_CHARTS,
    ),
    Module(
        id="indicators",
        order=4,
        title="Indicators & their failure modes",
        summary="Every indicator lies somewhere. Knowing where is the skill.",
        lessons=_INDICATORS,
    ),
    Module(
        id="expectancy",
        order=5,
        title="Expectancy & the math of survival",
        summary="Why a 40%-win system can be highly profitable — and why most aren't.",
        lessons=_EXPECTANCY,
    ),
    Module(
        id="backtesting",
        order=6,
        title="Backtesting honestly",
        summary="The three failure modes that turn paper edges into live losses.",
        lessons=_BACKTESTING,
    ),
    Module(
        id="psychology",
        order=7,
        title="Psychology & process",
        summary="Your behaviour is the biggest risk in the system. The journal is the cure.",
        lessons=_PSYCHOLOGY,
    ),
)


_BY_SLUG: Final[dict[str, Lesson]] = {
    lesson.slug: lesson for module in CATALOG for lesson in module.lessons
}


def list_modules() -> tuple[Module, ...]:
    return CATALOG


def get_lesson(slug: str) -> Lesson:
    try:
        return _BY_SLUG[slug]
    except KeyError as exc:
        raise ValidationError(f"unknown lesson slug: {slug!r}", field="slug") from exc
