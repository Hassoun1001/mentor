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
class Figure:
    """A diagram shown inside a lesson.

    ``key`` names a themed SVG the frontend knows how to draw; ``caption``
    is the one-line explanation shown beneath it. Content stays code-shipped
    — the backend never sends pixels, only the key + caption.
    """

    key: str
    caption: str


@dataclass(frozen=True, slots=True)
class QuizQuestion:
    """A self-check multiple-choice question for a lesson.

    Active recall beats re-reading. ``correct_index`` points into ``options``;
    ``explanation`` is shown after the learner answers, right or wrong.
    """

    prompt: str
    options: tuple[str, ...]
    correct_index: int
    explanation: str

    def __post_init__(self) -> None:
        if len(self.options) < 2:
            raise ValidationError("a quiz question needs >= 2 options")
        if not (0 <= self.correct_index < len(self.options)):
            raise ValidationError("correct_index out of range")


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
    figures: tuple[Figure, ...] = ()
    quiz: tuple[QuizQuestion, ...] = ()


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
        figures=(
            Figure(key="pair-ratio", caption="A pair is a ratio: how many dollars one euro costs."),
        ),
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
        figures=(
            Figure(
                key="leverage",
                caption="Leverage magnifies a small margin into large exposure — both ways.",
            ),
        ),
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
        figures=(
            Figure(key="spread", caption="The bid–ask gap is a fee you pay on every round trip."),
        ),
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
        quiz=(
            QuizQuestion(
                prompt="Who is more likely to survive long-term?",
                options=(
                    "55% win rate, risking 10% per trade",
                    "45% win rate, risking 1% per trade",
                    "they're equivalent — only win rate matters",
                ),
                correct_index=1,
                explanation="Sizing beats accuracy. Risking 10% per trade, a normal losing streak "
                "ruins the account regardless of a good win rate. 1% survives to compound.",
            ),
        ),
        figures=(
            Figure(
                key="risk-vs-predict",
                caption="Small risk + lower win rate can beat big risk + higher win rate.",
            ),
        ),
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
        figures=(
            Figure(
                key="drawdown-recovery",
                caption="The deeper the loss, the disproportionately larger the gain to recover.",
            ),
        ),
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
        figures=(
            Figure(
                key="size-formula",
                caption="Size comes from the stop — the target never enters the formula.",
            ),
        ),
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
        figures=(
            Figure(
                key="guardrails",
                caption="Three layered limits — the daily loss cap is the one that stops tilt.",
            ),
        ),
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
        figures=(
            Figure(
                key="trend-context",
                caption="Use the chart for context; the 'obvious' pattern is already priced.",
            ),
        ),
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
        figures=(
            Figure(
                key="sr-zones",
                caption="Support and resistance are zones the market remembers, not exact lines.",
            ),
        ),
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
        figures=(
            Figure(
                key="candle-anatomy",
                caption="One candle = open, high, low, close. That's the whole signal.",
            ),
        ),
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
        figures=(
            Figure(
                key="ma-lag",
                caption="A moving average always trails price — a filter, not a turn signal.",
            ),
        ),
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
        figures=(
            Figure(
                key="rsi-regime",
                caption="RSI can stay 'overbought' throughout a trend — not a sell button.",
            ),
        ),
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
        figures=(
            Figure(
                key="atr-stop",
                caption="Place the stop beyond the normal noise band (2–3× ATR), not inside it.",
            ),
        ),
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
        quiz=(
            QuizQuestion(
                prompt="Win 40% of the time, avg win 2R, avg loss 1R. Expectancy per trade?",
                options=("negative — it loses money", "+0.2R per trade", "exactly break-even"),
                correct_index=1,
                explanation="(0.40 × 2R) − (0.60 × 1R) = +0.2R per trade. "
                "A low win rate can still be very profitable.",
            ),
        ),
        figures=(
            Figure(
                key="expectancy-formula",
                caption="Expectancy is the average result per trade — positive means it pays.",
            ),
        ),
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
        figures=(
            Figure(
                key="r-ruler",
                caption="R normalises every trade: a stop-out is −1R, a double is +2R.",
            ),
        ),
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
        figures=(
            Figure(
                key="winrate-myth", caption="Six losses and two big wins can still net positive R."
            ),
        ),
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
        quiz=(
            QuizQuestion(
                prompt="Which of these is lookahead bias?",
                options=(
                    "using today's closing price to decide today's entry",
                    "paying the spread on every trade",
                    "holding only one position at a time",
                ),
                correct_index=0,
                explanation="Using data you couldn't have had at decision time (today's close) is "
                "lookahead — it makes a backtest print money that live trading never will.",
            ),
        ),
        figures=(
            Figure(
                key="lookahead",
                caption="Using future data to decide the past is the subtlest fatal backtest bug.",
            ),
        ),
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
        figures=(
            Figure(
                key="overfitting",
                caption="A model that fits every training wiggle fits the noise — not next year.",
            ),
        ),
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
        figures=(
            Figure(
                key="costs-erase-edge",
                caption="Spread + commission + slippage can erase a paper edge entirely.",
            ),
        ),
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
        figures=(
            Figure(
                key="journal-vs-memory",
                caption="Memory edits the losses away; the journal keeps the honest record.",
            ),
        ),
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
        figures=(
            Figure(
                key="tilt-spiral",
                caption="After a loss, risk creeps up — the daily limit is the circuit breaker.",
            ),
        ),
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
        figures=(
            Figure(
                key="review-tags",
                caption="Mistake tags reveal patterns before they show up in your P&L.",
            ),
        ),
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
# Module 8 — Under the hood: how the mentor predicts
# ---------------------------------------------------------------------------

_UNDER_THE_HOOD = (
    Lesson(
        slug="under-the-hood/what-we-can-predict",
        module_id="under-the-hood",
        order_in_module=1,
        title="What this system can and can't predict",
        summary="It predicts what's genuinely predictable and measures the rest — honestly.",
        est_minutes=5,
        key_concepts=("efficient market", "direction vs volatility", "honesty", "baseline"),
        figures=(
            Figure(
                key="honest-thesis",
                caption="Direction is nearly random; we forecast the range instead.",
            ),
        ),
        body_md="""
Most trading apps promise to tell you *which way* price will go. This one
starts with an uncomfortable truth we measured on ten years of EUR/USD:

> Guessing the **direction** of the next move is about **53%** accurate —
> barely better than a coin flip, and not enough to beat costs.

So we don't sell you a crystal ball. Instead the system does three honest
things:

- **Predicts what's actually predictable.** The *size* of the next move
  (volatility) really does cluster and can be forecast. Direction mostly
  can't. We lean into the first and stay humble about the second.
- **Measures everything out-of-sample.** Every model is tested on data it
  never trained on. A new model ships **only if it beats a simple, honest
  baseline**. If it doesn't help, we keep the simpler one and say so.
- **Tells you the odds, not a verdict.** A forecast here is a probability
  with a confidence band and a plain-English reason — never "buy now."

### Why this is the honest choice

Markets are *efficient*: obvious information is already in the price. If a
simple pattern worked, a million machines would have traded it away. Being
honest about that is the whole product — it's what keeps you solvent.
""".strip(),
    ),
    Lesson(
        slug="under-the-hood/where-the-data-comes-from",
        module_id="under-the-hood",
        order_in_module=2,
        title="Where the numbers come from",
        summary="Prices, interest rates, the dollar, and the news — from free, real sources.",
        est_minutes=5,
        key_concepts=("data sources", "failover", "FRED", "GDELT", "point-in-time"),
        figures=(
            Figure(
                key="data-pipeline",
                caption="Real data flows in, gets cleaned and aligned, then feeds the models.",
            ),
        ),
        body_md="""
A forecast is only as good as the data behind it. The system pulls four
kinds of **real** data, all from free sources:

- **Prices** — the EUR/USD candles themselves, from **Twelve Data** with
  **Yahoo Finance** as a backup. If one source is down, the other fills in
  (this is called *failover*). Ten years of daily history is stored locally.
- **Interest rates** — US 2-year and 10-year yields and the 2s10s curve,
  from the **FRED** database. Rate differences move currencies more than
  headlines do.
- **The dollar & fear gauge** — a broad US-dollar index and the **VIX**
  (Wall Street's "fear index"), also from FRED.
- **News mood** — a daily sentiment score from **GDELT**, which reads world
  news and measures how positive or negative coverage has been.

### Cleaning matters as much as collecting

Two sources rarely agree perfectly, and different feeds timestamp a "daily"
bar differently. The system **aligns** everything to the same clock and
**de-duplicates** overlapping days, so the model sees one clean history —
not a double-counted mess. Every value is stored so we never have to
re-download it to train.
""".strip(),
    ),
    Lesson(
        slug="under-the-hood/what-the-model-sees",
        module_id="under-the-hood",
        order_in_module=3,
        title="What the model looks at (and no peeking at the future)",
        summary="A short list of clues — and an ironclad rule against using tomorrow's data.",
        est_minutes=6,
        key_concepts=("features", "indicators", "lookahead bias", "point-in-time"),
        figures=(
            Figure(
                key="feature-families",
                caption="Three small groups of clues: price/indicators, news mood, macro drivers.",
            ),
            Figure(
                key="point-in-time",
                caption="The model sees only the past; the answer lies in the future.",
            ),
        ),
        body_md="""
The model doesn't stare at the raw price. It reads a short, deliberate list
of **features** — numbers summarising the recent past. They come in three
small families:

- **Price & indicators** — recent returns, moving-average distances, RSI,
  MACD, ATR (how much price normally moves), distance from recent highs/lows.
- **News mood** — the GDELT sentiment score and how it's trending.
- **Macro drivers** — the change in US rates, the yield curve, the dollar
  index, and the VIX.

We keep the list *small* on purpose. More knobs let a model memorise noise
that never repeats (*overfitting*). A handful of meaningful clues generalises
better.

### The golden rule: no peeking

The single most common way backtests lie is **lookahead bias** — accidentally
using information from the future to "predict" the past. This system forbids
it *structurally*: at any moment in time, a feature can be built **only from
bars on or before that moment**. The thing we're trying to predict always
lives strictly in the future. That's why our honest accuracy numbers are
lower than a naive backtest would show — and why they hold up live.
""".strip(),
    ),
    Lesson(
        slug="under-the-hood/predicting-direction",
        module_id="under-the-hood",
        order_in_module=4,
        title="Predicting direction: rules, then trees, then humility",
        summary="A transparent rule sets the bar; a machine-learning model ships only if it wins.",
        est_minutes=6,
        key_concepts=("baseline", "gradient boosting", "regime", "probability"),
        figures=(
            Figure(
                key="direction-model",
                caption="Rule baseline → boosted trees → a regime check for odd days.",
            ),
        ),
        body_md="""
For the *direction* question ("is price more likely up or down over the next
few days?") the system runs a small pipeline:

1. **A transparent rule model** — a handful of if-this-then-that rules you
   could check by hand (trend filter, momentum, RSI extremes). This is the
   **baseline**: the honest yardstick everything else must beat.
2. **A gradient-boosting model** — a machine-learning method that builds many
   small decision trees, each fixing the last one's mistakes. It reads all the
   features and outputs a probability of "up".
3. **A regime check** — before trusting the model, the system asks *"are today's
   conditions like the ones it trained on?"* If today is off-script (unusually
   volatile, outside the normal range), it **shrinks the confidence** or abstains
   rather than pretending to know.

### The honesty gate

The fancy model is only used **if it beats the simple rule out-of-sample**.
On EUR/USD direction, it barely does — because direction is nearly random.
That's fine: the system reports the real number and never dresses a coin flip
up as a signal. The output is always a probability plus the reasons behind it,
so you can judge it yourself.
""".strip(),
    ),
    Lesson(
        slug="under-the-hood/predicting-the-range",
        module_id="under-the-hood",
        order_in_module=5,
        title="Predicting the range, not the arrow",
        summary="Volatility clusters — so we can honestly forecast how big the next move will be.",
        est_minutes=6,
        key_concepts=("volatility", "EWMA", "clustering", "expected move", "conformal band"),
        quiz=(
            QuizQuestion(
                prompt="Why can the system honestly forecast a *range* but not the *direction*?",
                options=(
                    "it can't — both are guesses",
                    "volatility clusters (big moves follow big moves); direction is ~random",
                    "ranges are easier to guess than arrows for no real reason",
                ),
                correct_index=1,
                explanation="Volatility clustering is a robust, measurable effect, so "
                "future range is forecastable. Direction is ~53% out-of-sample — a coin flip.",
            ),
        ),
        figures=(
            Figure(
                key="vol-cone",
                caption="An expected move of ±X pips, plus a wider band covering ~90% of outcomes.",
            ),
        ),
        body_md="""
Here's the honest win. Direction is nearly random, but **volatility clusters**:
big days tend to follow big days, and quiet follows quiet. That's one of the
most reliable facts in finance — and it means the *size* of the coming move
really is forecastable.

So the system predicts a **range**, not an arrow:

> "Expected move over the next 5 days is about **±X pips** — a calm / normal /
> wide day versus history."

How it works:

- **The baseline (EWMA)** — a transparent formula that gives recent moves more
  weight than old ones. It's already a strong volatility forecast.
- **A machine-learning model** — trained to predict future realised volatility
  from features like recent volatility and ATR. It **only ships when it beats
  the EWMA baseline** on proper volatility scores. On our data it genuinely does
  at longer horizons.
- **A coverage band** — using a method called *conformal prediction*, the system
  adds an honest band: e.g. "the move lands between 13 and 179 pips about 90% of
  the time." Not a guess at one number — a range with a stated hit rate.

### Why you care

Knowing the expected range tells you how far to place a stop so normal noise
doesn't hit it, and whether today is a "sit on your hands" kind of day.
""".strip(),
    ),
    Lesson(
        slug="under-the-hood/trustworthy-probabilities",
        module_id="under-the-hood",
        order_in_module=6,
        title="Making 60% actually mean 60%",
        summary="Calibration turns raw model scores into probabilities you can trust.",
        est_minutes=6,
        key_concepts=("calibration", "reliability diagram", "ECE", "isotonic"),
        figures=(
            Figure(
                key="reliability",
                caption="A reliability diagram: when it says 60%, does it happen 60% of the time?",
            ),
        ),
        body_md="""
A probability is only useful if it's **honest**. If the model says "60% chance
up" a hundred times, up should happen about 60 of those times. Raw machine-learning
scores usually aren't this honest out of the box — a "70%" might really be a "55%".
Fixing that is called **calibration**.

### How we check it

The **reliability diagram** plots what the model *said* against what *actually
happened*. Perfect honesty is the diagonal line: predicted equals realised. Points
above or below the line show over- or under-confidence. We summarise the whole
picture in one number, the **ECE** (expected calibration error) — the average gap
from the diagonal. Lower is better.

### How we fix it

After training, the system fits a small correction called **isotonic regression**
on data the model never saw, which gently reshapes the raw scores so they line up
with reality. We only keep it **if it lowers the ECE without hurting accuracy**.
On our data it roughly **halves** the calibration error — so when the app shows a
percentage, it means what it says.

This is the heart of the product: not louder predictions, but **trustworthy** ones.
""".strip(),
    ),
    Lesson(
        slug="under-the-hood/the-self-learning-loop",
        module_id="under-the-hood",
        order_in_module=7,
        title="The system that grades itself",
        summary="Every prediction is logged, checked against reality, and used to improve.",
        est_minutes=6,
        key_concepts=("audit log", "resolver", "post-mortem", "champion challenger"),
        figures=(
            Figure(
                key="learning-loop",
                caption="Predict → wait → grade → retrain a challenger → keep it only if it wins.",
            ),
        ),
        body_md="""
A forecaster that never checks its own work can't be trusted. This one runs a
continuous loop:

1. **Predict** — every forecast is written to an audit log the moment it's made,
   so it can't be quietly forgotten or edited later.
2. **Resolve** — once enough time passes for the outcome to be known, the system
   compares the prediction to what actually happened (a *hit* or a *miss*).
3. **Post-mortem** — it aggregates the hits and misses: how accurate was it, is it
   well-calibrated, which conditions went with its mistakes? Honest self-criticism,
   not a highlight reel.
4. **Champion vs challenger** — periodically it trains a fresh "challenger" model.
   The challenger **replaces the reigning champion only if it's measurably better**
   on held-out data. Otherwise the champion stays. No model gets promoted on hope.

### What the loop can and can't do

It steadily improves *calibration* and *robustness* — the trustworthiness of the
numbers. It does **not** manufacture a market-beating edge on direction, and the
system never pretends it does. Improving honesty is the goal, and the loop is how
it's enforced automatically.
""".strip(),
    ),
    Lesson(
        slug="under-the-hood/forecast-to-position-size",
        module_id="under-the-hood",
        order_in_module=8,
        title="From a forecast to a position size",
        summary="The volatility forecast flows straight into your stop, your size, and your risk.",
        est_minutes=5,
        key_concepts=("position sizing", "ATR stop", "risk of ruin", "event freeze"),
        figures=(
            Figure(
                key="risk-sizing",
                caption="Expected move → a sensible stop → a size that risks only your chosen %.",
            ),
        ),
        body_md="""
A prediction is worthless if it doesn't change what you *do*. The volatility
forecast connects directly to the risk engine:

- **A sensible stop.** The expected move tells you how far price normally travels.
  Put your stop *beyond* that noise (the app suggests roughly 1.5× the expected
  move) so you're not knocked out by routine wiggle.
- **A size that respects your budget.** Given that stop and the percentage of your
  account you're willing to risk, the position-size calculator works out the exact
  lot size — and always **rounds down**, because the risk budget is a ceiling, never
  a target.
- **An event freeze.** When predicted volatility is unusually high (a wide regime),
  the app flags it: consider sitting out or halving size, because a fixed stop is far
  more likely to be hit.
- **Risk of ruin.** A separate simulator runs thousands of imaginary trade sequences
  to show the odds of a deep drawdown under your rules — so "1% per trade" stops being
  a slogan and becomes a survival curve you can see.

The chain is the whole point: **honest forecast → honest stop → honest size**.
""".strip(),
    ),
    Lesson(
        slug="under-the-hood/tracking-tipsters",
        module_id="under-the-hood",
        order_in_module=9,
        title="Tracking tipsters — measurement, not advice",
        summary="Paste a tip, price it at the moment it was said, and see if following it paid.",
        est_minutes=5,
        key_concepts=("track record", "leaderboard", "follow-him backtest", "expectancy"),
        figures=(
            Figure(
                key="tipster",
                caption="Parse the message → price each call → score → rank → simulate following.",
            ),
        ),
        body_md="""
Friends and group chats hand out stock tips constantly. This tool doesn't judge
whether a tip is *good* — it **measures** what actually happened, honestly:

1. **Parse** — paste the message; an assistant pulls out each ticker and what was
   suggested (buy, buy-on-dip, watch, avoid).
2. **Price** — it snapshots the price on the day the tip was given, so the entry is
   the real one, not a flattering later price.
3. **Score** — it tracks the return since then and builds a **scorecard**: hit rate,
   average return, and whether the "buy on dip" calls actually dipped.
4. **Leaderboard** — with several tipsters, it ranks them by **risk-adjusted** return
   (steady beats lucky), so one big win doesn't crown someone reckless.
5. **"What if I'd followed him?"** — a backtest mechanically buys every actionable
   call, sized by the same 1%-risk discipline, and draws the **equity curve**, the
   worst drawdown, and the **expectancy** (average result per trade in risk units).

### The honest frame

There are **no predictions** here — every price already happened. It's a track record
so you can decide how much weight a tipster deserves. Past calls don't predict future
ones, and none of this is advice.
""".strip(),
    ),
)


# ---------------------------------------------------------------------------
# Module — Studying & predicting the markets (methods)
# ---------------------------------------------------------------------------

_MARKET_STUDY = (
    Lesson(
        slug="market-study/schools-of-analysis",
        module_id="market-study",
        order_in_module=1,
        title="The four ways people read a market",
        summary="Technical, fundamental, quantitative, sentiment — four lenses on one price.",
        est_minutes=6,
        key_concepts=("technical", "fundamental", "quantitative", "sentiment"),
        figures=(
            Figure(
                key="schools-of-analysis",
                caption="Four lenses on the same price — the best traders borrow from all of them.",
            ),
        ),
        body_md="""
Every method of studying a market is one of four lenses. None is "the
truth" — each answers a different question, and serious traders combine
them.

- **Technical** — reads *price itself*: trend, levels, volatility. Good
  for *timing and risk* (where to enter, where the stop goes). Weak at
  *why* anything moves.
- **Fundamental** — reads the *drivers*: interest rates, growth,
  inflation, trade flows. For EUR/USD the rate difference between the US
  and Europe matters most. Good for *direction over weeks/months*, poor
  for timing.
- **Quantitative** — reads the *statistics*: does this signal have a
  measurable, repeatable edge after costs? This is what turns opinions
  into tested numbers. It's the honesty check on the other three.
- **Sentiment / positioning** — reads the *crowd*: are traders already
  all-in one way? Extremes often precede reversals.

### How to use them together

Fundamentals tell you the *bias*, technicals tell you *when and where*,
quant tells you *whether it actually works*, and sentiment warns you when
everyone already agrees. This app leans **quantitative and risk-first** on
purpose — because untested technical or fundamental "edges" are how most
accounts die.
""".strip(),
    ),
    Lesson(
        slug="market-study/top-down-workflow",
        module_id="market-study",
        order_in_module=2,
        title="Top-down: zoom out before you zoom in",
        summary="Big-picture trend first, precise trigger last — never the reverse.",
        est_minutes=5,
        key_concepts=("multi-timeframe", "context", "setup", "trigger"),
        figures=(
            Figure(
                key="top-down",
                caption="Work from the big trend down to the exact trigger, not the other way.",
            ),
        ),
        body_md="""
Staring at a 5-minute chart is how you get chopped up. Professionals work
**top-down** — from the big picture to the precise entry:

1. **Higher timeframe (monthly / weekly)** — what's the dominant trend?
   Only fight it with a very good reason.
2. **Daily** — what's the current context: trending, ranging, near a big
   level, calm or volatile?
3. **Setup** — a *location* worth trading (a pullback into support in an
   uptrend, say). Not a trade yet — a candidate.
4. **Trigger** — the precise entry and, more importantly, the stop that
   invalidates the idea.

### Why the order matters

Each level sets the *risk* for the next. If the weekly trend is up, a
daily pullback is a buying zone, not a short. Flip the order — start from
the 5-minute — and you trade noise with no context, which is indistinguishable
from gambling. The volatility read in this app tells you how wide step 4's
stop should be for today's conditions.
""".strip(),
    ),
    Lesson(
        slug="market-study/building-an-edge",
        module_id="market-study",
        order_in_module=3,
        title="Building an edge you can trust",
        summary="Idea → backtest → forward test → small live → scale. Most ideas die on the way.",
        est_minutes=6,
        key_concepts=("hypothesis", "backtest", "forward test", "validation"),
        figures=(
            Figure(
                key="edge-pipeline",
                caption="An edge must survive each gate before real size — most ideas don't.",
            ),
        ),
        body_md="""
An "edge" is just a rule with a *positive expected value after costs*.
You don't find one by staring at charts — you build it through a pipeline
that's designed to *kill* bad ideas cheaply:

1. **Hypothesis** — a specific, testable claim: "buying EUR/USD after a
   3-day drop into the weekly uptrend beats random." Write it down.
2. **Backtest** — test it on history, honestly: point-in-time data, real
   spread and slippage, out-of-sample hold-out. (The lessons on lookahead
   and overfitting are the traps here.)
3. **Forward test** — run it on *new* data it never saw, or paper-trade
   it live. This is where most "great" backtests fall apart.
4. **Small live** — trade it with tiny size. Real fills and real emotions
   are data the backtest can't give you.
5. **Scale** — only once it's proven itself do you size up — still within
   the 1% rule.

### The honest part

Most ideas die at step 2 or 3, and that's the pipeline *working*. Killing
a bad idea for the price of a backtest is the cheapest money you'll ever
make. This app's champion/challenger loop is exactly this discipline,
automated.
""".strip(),
    ),
    Lesson(
        slug="market-study/what-actually-predicts",
        module_id="market-study",
        order_in_module=4,
        title="What actually predicts markets (and what doesn't)",
        summary="A short list has real evidence; a long list is mostly noise after costs.",
        est_minutes=6,
        key_concepts=("momentum", "mean reversion", "volatility", "carry"),
        figures=(
            Figure(
                key="predictable-vs-not",
                caption="A few effects have real evidence; the popular rest is mostly noise.",
            ),
        ),
        body_md="""
Decades of academic and practitioner research point to a *short* list of
effects with genuine, repeatable evidence — and a long list of popular
ideas that mostly don't survive honest testing after costs.

### Has real evidence

- **Trend / momentum** — what's been rising tends to keep rising for a
  while. The most robust anomaly across markets.
- **Volatility clustering** — big moves follow big moves. This is why *the
  range* is forecastable even when direction isn't (it's what this app's
  volatility model exploits).
- **Mean reversion** — stretched moves partly snap back, especially over
  short horizons and at extremes.
- **Carry** — higher-yielding assets/currencies tend to earn their yield
  premium, punctuated by sharp reversals.

### Mostly noise (after costs)

Precise chart patterns, trading the news *after* it's public, round-number
"magic", and gut feel. They *feel* predictive because we remember the hits
and forget the misses.

### The takeaway

Anchor your study in the effects that have evidence, and demand that
anything else prove itself out-of-sample before you risk money on it.
""".strip(),
    ),
    Lesson(
        slug="market-study/probabilistic-thinking",
        module_id="market-study",
        order_in_module=5,
        title="Think in probabilities, not predictions",
        summary="Trade distributions and base rates, not certainties.",
        est_minutes=5,
        key_concepts=("probability", "base rate", "expected value", "variance"),
        figures=(
            Figure(
                key="distributions",
                caption="Every trade is one draw from a distribution — think in odds.",
            ),
        ),
        body_md="""
The single biggest mindset shift is to stop asking "will this trade win?"
and start asking "what are the *odds*, and what's the *payoff*?"

- **Every trade is one sample** from a distribution of outcomes. A good
  trade can lose; a bad trade can win. Judge the *decision*, not the single
  result.
- **Base rates first.** If direction is ~53% at best, any claim of "80%
  sure" should make you suspicious, not excited. Start from the honest base
  rate and demand real evidence to move off it.
- **Expected value, not hope.** A 40%-chance trade paying 3:1 is excellent;
  a 90%-chance trade paying 1:5 is a slow bleed. The payoff matters as much
  as the probability.
- **Respect variance.** Even a positive-edge strategy has long losing
  streaks. Sizing (the 1% rule) and the journal are what let you survive the
  variance long enough for the edge to show up.

This is the whole philosophy of the app: it hands you *calibrated
probabilities and ranges*, not verdicts, so you can make good bets and let
the math play out.
""".strip(),
    ),
)

# ---------------------------------------------------------------------------
# Module — The trader's toolkit (best tools)
# ---------------------------------------------------------------------------

_TOOLKIT = (
    Lesson(
        slug="toolkit/charts-and-platforms",
        module_id="toolkit",
        order_in_module=1,
        title="Charts & platforms",
        summary="Where you see the market and place trades — and what each is good for.",
        est_minutes=5,
        key_concepts=("TradingView", "MetaTrader", "broker platform", "charting"),
        figures=(
            Figure(
                key="charts-platforms",
                caption="A tool to study, a platform to execute — keep them separate.",
            ),
        ),
        body_md="""
Two different jobs, often two different tools:

- **Charting / analysis** — **TradingView** is the modern default: fast
  charts, every indicator, drawing tools, alerts, and a huge script library
  (Pine). Great for *studying* and setting alerts.
- **Execution** — your **broker's platform** or **MetaTrader (MT4/MT5)**.
  This is where orders actually fill. Its charts are secondary; its job is
  reliable fills, clear order tickets, and correct margin.

### What to actually use them for

- Draw *major* levels and the trend on a clean chart — resist the urge to
  stack ten indicators.
- Set **alerts** instead of watching all day (staring causes overtrading).
- Always confirm the platform shows the **spread** and your **stop** before
  you click. The chart is analysis; the ticket is real money.

This app is your *analysis and risk* layer — the forecast, the volatility
range, the position-size calculator, the journal — sitting alongside
whatever platform you execute on.
""".strip(),
    ),
    Lesson(
        slug="toolkit/data-and-calendars",
        module_id="toolkit",
        order_in_module=2,
        title="Data & economic calendars",
        summary="Know what's scheduled, and get clean data from real sources.",
        est_minutes=5,
        key_concepts=("economic calendar", "FRED", "data feed", "news"),
        figures=(
            Figure(
                key="data-calendar",
                caption="Scheduled events + clean data feeds → one honest picture to trade from.",
            ),
        ),
        body_md="""
You can't manage risk around events you didn't know were coming.

- **Economic calendar** — **ForexFactory** (free) lists every scheduled
  release with its expected impact. The essentials for EUR/USD: central-bank
  decisions (Fed, ECB), inflation (CPI), jobs (US NFP), and GDP. Around
  high-impact prints, spreads widen and stops get hunted — many traders
  simply **freeze** (this app flags high-volatility regimes for the same
  reason).
- **Macro data** — **FRED** (the St. Louis Fed) is the gold standard: US
  rates, the dollar index, VIX, and thousands of series, free and clean.
  This app already pulls its rate/DXY/VIX features from FRED.
- **Prices** — **Yahoo Finance** and **Twelve Data** give free historical
  candles for forex and stocks.
- **News mood** — **GDELT** turns world news into a daily sentiment score
  (the app uses it), though remember: news *timing* is rarely tradable once
  it's public.

### Rule of thumb

Check the calendar every morning. Green-light days are for setups;
red-flag days (big releases) are for smaller size or sitting out.
""".strip(),
    ),
    Lesson(
        slug="toolkit/risk-and-journaling-tools",
        module_id="toolkit",
        order_in_module=3,
        title="Risk & journaling tools",
        summary="The boring tools that actually keep you solvent.",
        est_minutes=5,
        key_concepts=("position-size calculator", "journal", "spreadsheet", "expectancy"),
        figures=(
            Figure(
                key="risk-tools",
                caption="Position-size calculator + journal + spreadsheet — the survival kit.",
            ),
        ),
        body_md="""
The unglamorous tools are the ones that keep you in the game.

- **Position-size calculator** — turns *risk % + stop distance* into an
  exact lot size, so you never size by feel. This app has one built in, and
  it rounds *down* so the risk budget stays a ceiling.
- **Trade journal** — a row per trade with entry, stop, target, size,
  reason, and the realised R. Written *before* the trade, reviewed after.
  Memory lies; the journal doesn't. (The app's journal + pre-trade checklist
  do this for you.)
- **Spreadsheet** — even a simple sheet computes the numbers that matter:
  expectancy, profit factor, average R, max drawdown, and your mistake-tag
  frequencies.

### The one habit

Log **every** trade, including the ones you're not proud of — *especially*
those. After a hundred rows, filtering by tag ("FOMO", "moved stop") shows
you exactly where your money leaks. No indicator can teach you that.
""".strip(),
    ),
    Lesson(
        slug="toolkit/screening-and-automation",
        module_id="toolkit",
        order_in_module=4,
        title="Screening & automation",
        summary="Automate the tedious parts — never the risk discipline.",
        est_minutes=5,
        key_concepts=("screener", "alerts", "Python", "backtesting library"),
        figures=(
            Figure(
                key="automation-stack",
                caption="Screen, alert, and test with code — but keep a human on the risk.",
            ),
        ),
        body_md="""
Once you have a process, tools can remove the grunt work:

- **Screeners** — filter hundreds of instruments down to the few that meet
  your criteria (e.g. "near the 200-day, pulling back"). Saves hours of
  chart-flipping.
- **Alerts** — let the platform watch price for you and ping when a level
  is hit. This is the antidote to overtrading from boredom.
- **Code (Python)** — `pandas` for data, `backtesting.py` / `vectorbt` for
  testing, `scikit-learn` for models. This is how you test an idea on ten
  years of data in seconds — exactly what this app's backend does.

### The hard line

Automate *analysis, screening, alerts, and testing* freely. Be extremely
careful automating *execution* — a bot with a sizing bug can empty an
account faster than any human. If you do automate trades, the risk limits
(per-trade, daily loss) must live in the code, not in your intentions.
""".strip(),
    ),
    Lesson(
        slug="toolkit/weekly-workflow",
        module_id="toolkit",
        order_in_module=5,
        title="Putting it together: a weekly workflow",
        summary="Plan, trade, journal, review — a loop that compounds skill.",
        est_minutes=5,
        key_concepts=("routine", "preparation", "review", "process"),
        figures=(
            Figure(
                key="weekly-routine",
                caption="Plan → trade → journal → review, every week.",
            ),
        ),
        body_md="""
Tools only help inside a routine. A simple weekly loop beats sporadic
brilliance every time:

- **Plan (weekend)** — mark the higher-timeframe trend and major levels,
  read next week's economic calendar, and write the handful of setups you'll
  *wait* for. Decide your risk per trade in advance.
- **Trade (during the week)** — take only the planned setups. Size with the
  calculator, set the stop from the volatility read, and log the entry
  *before* you click. If it's not on the plan, it's not a trade.
- **Journal (daily)** — a two-minute entry per trade: what you saw, what you
  did, how you felt. Tag the mistakes honestly.
- **Review (weekend)** — sort the journal by R, read your best and worst
  five, tag the patterns, and adjust one thing. Then plan again.

### Why the loop matters

Markets are mostly noise; your *process* is the only thing you fully
control. The weekly loop turns scattered trades into a dataset you learn
from — and it's the same predict → resolve → review loop the app runs on
its own forecasts.
""".strip(),
    ),
)

# ---------------------------------------------------------------------------
# Module — The language of the charts (terminology + how to read it)
# ---------------------------------------------------------------------------

_CHART_LANGUAGE = (
    Lesson(
        slug="chart-language/direction-words",
        module_id="chart-language",
        order_in_module=1,
        title="Bullish, bearish, long, short",
        summary="The words for market direction — and the bias each one sets.",
        est_minutes=4,
        key_concepts=("bullish", "bearish", "long", "short", "rally", "sell-off"),
        quiz=(
            QuizQuestion(
                prompt="You 'go short' EUR/USD. You make money if…",
                options=("the euro rises", "the euro falls", "the price stays flat"),
                correct_index=1,
                explanation="Short = sell first to buy back cheaper, so you profit "
                "when price falls. Long is the opposite.",
            ),
        ),
        figures=(
            Figure(
                key="bull-bear",
                caption="Bullish = buyers push price up; bearish = sellers push it down.",
            ),
        ),
        body_md="""
Before anything else, traders name the *direction*:

- **Bullish** — expecting price to **rise** (the bull attacks *upward*
  with its horns). A **rally** is a strong up-move.
- **Bearish** — expecting price to **fall** (the bear swipes *down*). A
  **sell-off** is a sharp down-move.
- **Long** — a trade that *profits if price rises* (you bought). "Going
  long EUR/USD" = betting the euro strengthens.
- **Short** — a trade that *profits if price falls* (you sold first,
  planning to buy back cheaper). Yes, you can profit from a fall.

### How to use it to read the market

Direction words are your **bias label**, not a prediction. Say it out loud
before every trade: *"I'm bullish EUR/USD, so I'm looking for longs on a
pullback — and I'm wrong if it breaks below the last swing low."* Naming the
bias *and its invalidation* is what separates a plan from a hope. The
forecast card's probability is just a calibrated version of this same
bullish/bearish lean.
""".strip(),
    ),
    Lesson(
        slug="chart-language/trend-structure",
        module_id="chart-language",
        order_in_module=2,
        title="Trend, uptrend, downtrend, range",
        summary="A trend is just higher highs and higher lows — until they break.",
        est_minutes=5,
        key_concepts=("trend", "uptrend", "downtrend", "range", "higher high", "higher low"),
        quiz=(
            QuizQuestion(
                prompt="What actually defines an uptrend?",
                options=(
                    "price is above a moving average",
                    "a series of higher highs and higher lows",
                    "RSI is above 70",
                ),
                correct_index=1,
                explanation="An uptrend is structurally higher highs AND higher lows. "
                "It stays intact until price makes a lower low and breaks that structure.",
            ),
        ),
        figures=(
            Figure(
                key="trend-structure",
                caption="An uptrend is a staircase of higher highs and higher lows.",
            ),
        ),
        body_md="""
A **trend** is the market's direction over time, and it has a precise,
checkable definition — not a vibe:

- **Uptrend** — a series of **higher highs (HH)** and **higher lows (HL)**.
  Each rise goes further; each dip stops higher. A rising staircase.
- **Downtrend** — **lower highs (LH)** and **lower lows (LL)**. A falling
  staircase.
- **Range (sideways)** — highs and lows roughly level. No trend; price
  oscillates between support and resistance.

### How to use it to anticipate

This is one of the genuinely useful structural reads:

- **The trend is intact while the pattern holds.** In an uptrend, a dip that
  stops above the previous low and turns up is a **continuation** — often a
  buying spot.
- **The warning is a broken structure.** The first time an uptrend makes a
  **lower low** (breaks the last higher low), the uptrend is in doubt. That's
  your signal to tighten stops or stand aside — not to blindly buy the dip.

"The trend is your friend" is really "trade *with* the staircase until it
stops climbing." Trend/momentum is one of the few effects with real evidence.
""".strip(),
    ),
    Lesson(
        slug="chart-language/moves-within-a-trend",
        module_id="chart-language",
        order_in_module=3,
        title="Breakout, pullback, reversal",
        summary="The three moves that make up every trend — and how to trade each.",
        est_minutes=5,
        key_concepts=("breakout", "pullback", "retracement", "reversal", "consolidation"),
        quiz=(
            QuizQuestion(
                prompt="A dip that holds above the last higher low, then turns back up, is a…",
                options=("reversal", "pullback (a continuation)", "breakout"),
                correct_index=1,
                explanation="That's a pullback — the trend resumes. It becomes a possible "
                "reversal only if it breaks below the last higher low.",
            ),
        ),
        figures=(
            Figure(
                key="moves-in-trend",
                caption="Breakout → pullback → continuation; a lower low warns of reversal.",
            ),
        ),
        body_md="""
Zoom in and a trend is built from a few repeating moves. Knowing their
names tells you what to *expect next*:

- **Breakout** — price pushes *through* a level (support/resistance) that
  had been holding. Often the start of a new leg — but beware the **fakeout**,
  a breakout that immediately fails.
- **Pullback / retracement** — a temporary counter-move *against* the trend.
  In an uptrend, a pullback into support is the classic lower-risk **buy
  zone** (buy the dip, not the top).
- **Consolidation** — price pauses and coils sideways, gathering energy
  before the next move. Tight ranges often precede breakouts.
- **Reversal** — the trend actually *turns*: an uptrend starts making lower
  lows. Different from a pullback, which resumes the trend.

### How to use it to predict

The edge is in *distinguishing a pullback from a reversal*. A dip that holds
above the last higher low and turns up = pullback (trade with the trend). A
dip that breaks below it = possible reversal (step aside). Combine with the
volatility read: in a **wide** regime, expect deeper pullbacks and give the
setup more room.
""".strip(),
    ),
    Lesson(
        slug="chart-language/candles-vocabulary",
        module_id="chart-language",
        order_in_module=4,
        title="Candle words: body, wick, doji, pin bar",
        summary="What the shapes are called — and what each says about the fight.",
        est_minutes=5,
        key_concepts=("candle", "body", "wick", "doji", "engulfing", "pin bar", "gap"),
        quiz=(
            QuizQuestion(
                prompt="A small-bodied candle with a long lower wick, at support, hints that…",
                options=(
                    "sellers are firmly in control",
                    "buyers rejected the lower prices",
                    "nothing — candle shapes are random",
                ),
                correct_index=1,
                explanation="A long lower wick means price was pushed down and bought back up — a "
                "rejection of lows. It's only worth noting at a level you already care about.",
            ),
        ),
        figures=(
            Figure(
                key="candle-types",
                caption="Long wicks = rejection; a big engulfing body = one side taking over.",
            ),
        ),
        body_md="""
A **candle** shows one interval's open, high, low, close. The vocabulary
describes its *shape*, and the shape hints at who won the interval:

- **Body** — the open-to-close range (filled). A big body = strong
  conviction one way. **Wick / shadow** — the thin lines to the high and
  low = prices that were *rejected*.
- **Doji** — open ≈ close, so a tiny body with wicks. **Indecision**;
  meaningful only at the end of a strong move.
- **Engulfing** — a candle whose body completely covers the previous one.
  A **bullish engulfing** after a drop = buyers taking over.
- **Pin bar / hammer** — a small body with a long wick. A long *lower* wick
  = the market tried lower and got **rejected** (buyers stepped in).
- **Gap** — a jump between one candle's close and the next's open (common
  after weekends/news).

### How to use it — carefully

Candles are best as **confirmation at a level you already care about**, never
alone. A hammer *at support in an uptrend* is worth noticing; the same hammer
in the middle of nowhere is noise. Honest caveat: single-candle "signals"
have a small edge after costs — this app deliberately doesn't trade them.
Use them to *read the fight*, not as buy buttons.
""".strip(),
    ),
    Lesson(
        slug="chart-language/fibonacci-and-levels",
        module_id="chart-language",
        order_in_module=5,
        title="Fibonacci, support, resistance & lines",
        summary="Where pullbacks tend to pause — and why the levels partly work.",
        est_minutes=6,
        key_concepts=("Fibonacci", "retracement", "support", "resistance", "trendline"),
        quiz=(
            QuizQuestion(
                prompt="Why do Fibonacci retracement levels sometimes 'work'?",
                options=(
                    "the golden ratio has real predictive power over markets",
                    "so many traders watch them that orders cluster at the levels",
                    "they guarantee price will reverse there",
                ),
                correct_index=1,
                explanation="It's largely self-fulfilling — a place to watch and manage "
                "risk, not a guarantee. Levels fail often; use them to place stops.",
            ),
        ),
        figures=(
            Figure(
                key="fibonacci",
                caption="After a swing, price often retraces to the 38–62% Fibonacci zone.",
            ),
        ),
        body_md="""
Once there's a move, traders look for *where a pullback might stop*. The
vocabulary of levels:

- **Support** — a price area where buyers have stepped in before (a floor).
  **Resistance** — where sellers have (a ceiling). They're **zones**, not
  exact lines.
- **Trendline / channel** — a line connecting the swing lows (up) or highs
  (down); a channel adds a parallel line on the other side.
- **Fibonacci retracement** — horizontal levels at **23.6%, 38.2%, 50%,
  61.8%** of the last swing. After a rally, price often **retraces** to the
  38–62% zone before continuing. **Extensions** (127%, 161.8%) project
  targets beyond the move.
- **Pivot points** — levels calculated from the prior period's high/low/close;
  common intraday reference points.

### How to use it to anticipate — and the honest catch

Levels give you **where** to look for a pullback to end, so you can plan an
entry with a tight, logical stop just beyond the level. But be honest about
*why* Fibonacci "works": there's no magic in the ratio — it works partly
because **so many traders watch the same levels** that their orders cluster
there (self-fulfilling), and it fails often enough that a level is a *place to
watch*, never a guarantee. Use levels to place risk, not to predict with
certainty.
""".strip(),
    ),
    Lesson(
        slug="chart-language/units-and-orders",
        module_id="chart-language",
        order_in_module=6,
        title="Pips, lots, stops & order types",
        summary="The mechanics vocabulary that turns a read into an actual trade.",
        est_minutes=5,
        key_concepts=("pip", "lot", "spread", "stop-loss", "take-profit", "R:R"),
        quiz=(
            QuizQuestion(
                prompt="Stop 30 pips away, target 60 pips away. The reward-to-risk is…",
                options=("2:1", "1:2", "1:1"),
                correct_index=0,
                explanation="Reward ÷ risk = 60 ÷ 30 = 2, i.e. 2:1 — risk 1 to make 2.",
            ),
        ),
        figures=(
            Figure(
                key="trade-anatomy",
                caption="Entry, stop-loss, take-profit and pips — the anatomy of one trade.",
            ),
        ),
        body_md="""
Finally, the words that turn a read into an order:

- **Pip** — the standard price increment (`0.0001` on most pairs; a
  **pipette** is a tenth of that). Moves and spreads are measured in pips.
- **Tick** — the smallest price change an instrument can make. **Point** —
  often used loosely for a pip or a whole-number move, depending on market.
- **Lot** — trade size. 1 standard lot = 100,000 units (mini 10k, micro 1k).
- **Spread** — the bid–ask gap you pay to enter. **Leverage / margin** — the
  borrowed exposure and the deposit that backs it.
- **Stop-loss** — the order that caps your loss (where your idea is *wrong*).
  **Take-profit** — where you bank the win. **Market order** fills now;
  **limit order** waits for a chosen price.
- **R:R (risk-to-reward)** — reward distance ÷ risk distance. A stop 30 pips
  away and a target 60 away is **2:1**.

### How it all comes together

A complete trade is one sentence: *"Go **long** at 1.0850, **stop-loss** 30
**pips** below (−1R), **take-profit** 60 pips above (**2:1 R:R**), sized so
that −1R is 1% of the account."* Every term above is just a piece of that
sentence — and this app's position-size calculator turns the pip stop into
the exact lot size for you.
""".strip(),
    ),
)

# ---------------------------------------------------------------------------
# Module 12 — Becoming a professional
# ---------------------------------------------------------------------------

_BECOMING_PRO = (
    Lesson(
        slug="becoming-pro/order-types",
        module_id="becoming-pro",
        order_in_module=1,
        title="Order types: market, limit, stop",
        summary="The three buttons on every broker, and when a pro presses each one.",
        est_minutes=6,
        key_concepts=("market order", "limit order", "stop order", "stop-loss", "take-profit"),
        figures=(
            Figure(
                key="order-types",
                caption=(
                    "Three order types around the current price — each fires in a different "
                    "direction."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "You want to buy EUR/USD, but only if it first drops to a cheaper price. "
                    "Which order?"
                ),
                options=(
                    "Market order",
                    "Buy limit below the current price",
                    "Buy stop above the current price",
                ),
                correct_index=1,
                explanation=(
                    "A buy *limit* rests below the market and fills only if price comes "
                    "down to it — 'I'll buy, but only at a discount.' A buy *stop* is the "
                    "opposite: it triggers when price rises through a level."
                ),
            ),
        ),
        body_md="""
Every broker gives you the same three tools. Professionals differ from
beginners mostly in *which one they reach for*.

- **Market order** — "fill me *now* at whatever the price is." Instant, but
  you pay the spread and, in fast markets, *slippage* (a worse fill than the
  screen showed). Use it when being in the trade matters more than the last
  0.2 pips.
- **Limit order** — "fill me *only at this price or better*." A buy limit
  sits **below** the market; a sell limit sits **above** it. You choose the
  price, the market chooses whether you get filled. Pros use limits to be
  *paid* patience instead of paying urgency.
- **Stop order** — "when price *reaches* this level, fire a market order."
  A buy stop sits **above** the market (used to enter on a breakout); a sell
  stop sits **below** (that's your **stop-loss** on a long position).

### The two orders that must exist on every trade

The moment you're in a position, two orders should already be resting:

1. **Stop-loss** — the exit that caps your loss at the amount you chose
   *before* entering. Not optional. Ever.
2. **Take-profit** (a limit) — the exit that banks the win at your target.

This app's **Trade plan** page computes both for you — the stop beyond the
day's normal noise, the target at your chosen reward:risk — so the decision
is made calmly *before* the money is on the line, not during.

### The failure mode

Beginners enter with market orders on impulse and "manage" the exit live.
That converts every trade into an emotion test. Professionals decide the
full exit plan first, place all three orders together, and then — this is
the hard part — *leave them alone*.
""".strip(),
    ),
    Lesson(
        slug="becoming-pro/sessions-clock",
        module_id="becoming-pro",
        order_in_module=2,
        title="The 24-hour market: sessions and when to trade",
        summary="FX never sleeps, but it isn't equally alive. Know when your pair actually moves.",
        est_minutes=6,
        key_concepts=("Sydney", "Tokyo", "London", "New York", "session overlap", "liquidity"),
        figures=(
            Figure(
                key="sessions-clock",
                caption=(
                    "The four sessions across a UTC day — the London–New York overlap is where "
                    "EUR/USD does most of its business."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt="When does EUR/USD typically move the most?",
                options=(
                    "During the Sydney session",
                    "During the London–New York overlap",
                    "Exactly at midnight UTC",
                ),
                correct_index=1,
                explanation=(
                    "Roughly 12:00–16:00 UTC, when both European and American desks are "
                    "at their screens, is when EUR/USD sees its deepest liquidity and "
                    "largest moves."
                ),
            ),
        ),
        body_md="""
Forex trades 24 hours a day, five days a week — but "open" is not the same
as "alive". The day is really four overlapping **sessions**, following the
sun: **Sydney → Tokyo → London → New York**.

For EUR/USD, the rhythm is very consistent:

- **Asian hours** (roughly 23:00–07:00 UTC) — quiet. Ranges are small,
  spreads can be wider. Signals fire less often and mean less.
- **London open** (~07:00–08:00 UTC) — the day wakes up. The first burst of
  real volume often sets the day's direction *or* fakes it.
- **The London–New York overlap** (~12:00–16:00 UTC) — the main event. Most
  of the day's range, most of the news releases (US data lands 12:30/14:00
  UTC), tightest spreads.
- **Late New York** (~20:00 UTC on) — winding down. Moves fade; Friday
  afternoons especially are noise.

### Why a professional cares

Three practical consequences:

1. **Trade where the liquidity is.** The same 20-pip signal is meaningful
   in the overlap and mostly noise at 3 a.m.
2. **Costs change by session.** Spreads widen when liquidity is thin — the
   quiet hours quietly charge you more per trade.
3. **The weekend gap is real.** The market closes Friday ~22:00 UTC and
   reopens Sunday ~22:00 UTC — price can *jump* over your stop. Holding
   size over the weekend is a decision, not a default.

This system already knows the clock: its data-quality gate treats the
weekend as normal, and its hourly predictions simply have more to chew on
when the market is genuinely active.
""".strip(),
    ),
    Lesson(
        slug="becoming-pro/costs-of-trading",
        module_id="becoming-pro",
        order_in_module=3,
        title="What trading actually costs",
        summary="Spread, swap, and slippage — the silent partners taking a cut of every trade.",
        est_minutes=6,
        key_concepts=("spread", "swap", "slippage", "commission", "cost per trade"),
        figures=(
            Figure(
                key="spread-anatomy",
                caption=(
                    "You buy at the ask and sell at the bid — the gap is the broker's cut, paid "
                    "on entry."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "EUR/USD shows bid 1.1000 / ask 1.1001. You buy and instantly sell. What "
                    "happened?"
                ),
                options=(
                    "You broke even",
                    "You lost one pip — the spread",
                    "You made one pip",
                ),
                correct_index=1,
                explanation=(
                    "You bought at 1.1001 (ask) and sold at 1.1000 (bid). The 1-pip gap "
                    "went to the broker. Every round trip starts one spread behind."
                ),
            ),
        ),
        body_md="""
Every trade starts *losing*. Understanding why — and how much — separates
people who survive from people who wonder where the money went.

- **Spread** — there are always two prices: the **bid** (what you sell at)
  and the **ask** (what you buy at). The gap between them is the spread —
  typically 0.5–1.5 pips on EUR/USD. You pay it the instant you enter.
- **Commission** — some accounts charge a flat fee per lot instead of (or
  on top of) a wider spread. Same cost, different label.
- **Swap / rollover** — hold a position overnight and you pay (or earn)
  the interest-rate difference between the two currencies. Small daily,
  meaningful over weeks — and it's *why* rate differentials move FX at all.
- **Slippage** — in fast markets your market order fills at a worse price
  than you clicked. Around big news it can be many pips. It's not the
  broker cheating; it's the queue moving while you walk to it.

### Why this matters more than it looks

Say your strategy nets +4 pips per trade before costs, and costs average
1.5 pips. **Costs just ate 37% of your edge.** A strategy that trades ten
times a day pays the spread ten times a day — which is why high-frequency
"scalping" with a retail spread is a donation, not a business.

The system takes this seriously everywhere: the backtester charges spread
and slippage on every simulated trade, and the paper P&L on the Loop page
deducts a spread per trade — so no number you see here pretends trading
is free.
""".strip(),
    ),
    Lesson(
        slug="becoming-pro/leverage-and-margin",
        module_id="becoming-pro",
        order_in_module=4,
        title="Leverage and margin, without the horror stories",
        summary=(
            "Leverage is a loan, margin is the deposit — and position size is the real decision."
        ),
        est_minutes=7,
        key_concepts=("leverage", "margin", "margin call", "notional", "effective leverage"),
        figures=(
            Figure(
                key="leverage-seesaw",
                caption=(
                    "Leverage multiplies both sides of the seesaw — profits and losses swing by "
                    "the same factor."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "With 1:100 leverage on a $1,000 account, what does a pro actually risk per "
                    "trade?"
                ),
                options=(
                    "The full $100,000 the leverage allows",
                    "Whatever the broker's margin call permits",
                    "Still ~1% of the account — leverage doesn't change the risk rule",
                ),
                correct_index=2,
                explanation=(
                    "Leverage changes what you *can* buy, not what you *should* risk. "
                    "The stop distance and the 1% rule set the position size; leverage "
                    "just makes that size mechanically possible."
                ),
            ),
        ),
        body_md="""
Leverage has ruined more retail accounts than bad predictions ever did —
not because it's evil, but because nobody explained it as what it is:
**a loan**.

- **Leverage 1:30** means the broker lets you control a position 30× your
  cash. Buying 1 mini-lot of EUR/USD (~$11,000 notional) with 1:30 leverage
  requires about **$370 of margin** — your good-faith deposit.
- **Margin** is not a fee. It's your own money set aside while the loan is
  out. Close the trade; it comes back.
- **Margin call / stop-out** — if floating losses eat your account down to
  the broker's limit, they close your positions *for* you, at the worst
  possible moment. A margin call is not bad luck; it's the receipt for
  oversizing.

### The number that matters: effective leverage

Ignore the broker's maximum. Ask: *my total position notional ÷ my account*.
Professionals typically run **2–5× effective leverage**, even when 30× or
100× is on offer. Why? Run the seesaw both ways:

> At 10× leverage, a routine 1% adverse move = **10% of your account**.
> Three of those in a row — a perfectly normal week — is nearly a third of
> your money, and you *will* start making fear-based decisions.

### How this system keeps you honest

You never pick leverage here. You pick **risk per trade** (0.5–2%), and the
Trade plan sizes the position from the stop distance. The resulting
effective leverage is whatever honest arithmetic produces — usually
boringly small. Boring is the point: the traders still here in year five
are the ones who were boring in year one.
""".strip(),
    ),
    Lesson(
        slug="becoming-pro/the-trading-plan",
        module_id="becoming-pro",
        order_in_module=5,
        title="The written trading plan",
        summary="If it isn't written down before the trade, it isn't a plan — it's a mood.",
        est_minutes=7,
        key_concepts=("trading plan", "setup", "entry criteria", "exit rules", "review"),
        figures=(
            Figure(
                key="plan-pyramid",
                caption=(
                    "A plan is built bottom-up: risk rules first, setups last — most beginners "
                    "build it upside-down."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt="What belongs at the BASE of a trading plan?",
                options=(
                    "The entry signals and chart patterns",
                    "Risk rules: max loss per trade, per day, per week",
                    "Profit targets for the month",
                ),
                correct_index=1,
                explanation=(
                    "Setups change; survival rules don't. Risk limits are the "
                    "foundation everything else stands on — a plan that starts with "
                    "entries is a wish list."
                ),
            ),
        ),
        body_md="""
Ask a funded professional for their trading plan and they'll show you a
document. Ask a struggling beginner and they'll describe a feeling. The
document wins, every year, and it has five layers — **built from the
bottom up**:

1. **Risk rules (the base).** Max risk per trade (e.g. 1%). Max loss per
   day (e.g. 3% — then you *stop*, no exceptions). Max open risk at once.
   These are the rules that guarantee you're still trading next month.
2. **Market & schedule.** *What* you trade (one pair is plenty to start)
   and *when* (your sessions, from the previous lesson). Scattering across
   ten markets is how beginners avoid getting good at one.
3. **Setups.** The two or three specific situations you're allowed to
   trade, written precisely enough that a stranger could follow them.
   "Looks bullish" is not a setup. "Price above the 200-EMA, pullback to
   support, stop under the swing low" is.
4. **Execution rules.** Orders in before entry (stop + target). No adding
   to losers. No moving stops away from price. Ever.
5. **Review cadence (the top).** The journal after every trade; the weekly
   review every weekend. This layer is what makes the other four improve.

### The test of a real plan

Could you hand it to a friend and have *them* take your next ten trades
without asking you anything? If not, it's still a mood.

Inside this app, the pieces map one-to-one: the **Trade plan** page is
layers 1–4 computed live, the pre-trade **checklist** is layer 4 made
clickable, and the **Journal** with its weekly review is layer 5. The plan
isn't homework *about* trading here — it's the interface itself.
""".strip(),
    ),
    Lesson(
        slug="becoming-pro/daily-routine",
        module_id="becoming-pro",
        order_in_module=6,
        title="A professional's trading day",
        summary=(
            "Pros don't watch charts all day. They run a routine: prepare, execute, review, "
            "leave."
        ),
        est_minutes=6,
        key_concepts=("routine", "preparation", "execution window", "review", "screen time"),
        figures=(
            Figure(
                key="daily-routine-timeline",
                caption=(
                    "Under two focused hours: prepare before the session, execute inside it, "
                    "review after — the rest of the day is life."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt="How much screen time does a disciplined process-driven day actually need?",
                options=(
                    "All day — more watching means more opportunities",
                    "Roughly 1–2 focused hours around your chosen session",
                    "None — set and forget forever",
                ),
                correct_index=1,
                explanation=(
                    "More screen time past your plan's window doesn't add opportunity — "
                    "it adds impulse trades. Prepare, execute the window, review, stop."
                ),
            ),
        ),
        body_md="""
The image of a trader glued to six monitors is a movie prop. A retail
professional's day, done right, is short and almost ritualistic:

**Before the session (15–20 min)**
- Read the calendar: any high-impact news today? (This app's dashboard
  shows it; the event-freeze warns you.)
- Check the system's morning read: direction lean, volatility regime,
  expected range.
- Decide *in advance*: am I trading today? Which setup am I waiting for?
  Where would the stop go? — If today's answer is "nothing qualifies",
  that's a **complete, successful trading day.**

**During your window (30–60 min)**
- Watch only for the setup you pre-committed to. It appears → run the
  checklist → place entry, stop, and target together → walk away.
- It doesn't appear → you're done. No improvising after the window.

**After the close (10 min)**
- Journal the trade (or the no-trade): what you did, why, how it felt.
- Glance at the system's own scoreboard — is the loop healthy, did its
  calls resolve?

**Weekly (30 min, weekend)**
- Read the week's journal. Tag the mistakes. Pick *one* thing to do
  differently next week. One.

### The uncomfortable truth this schedule encodes

Almost everything that loses beginners money happens *outside* those
windows: the bored lunchtime entry, the revenge trade after a stop-out,
the 11 p.m. "one more". A routine isn't about discipline as suffering —
it's about making the losing hours structurally impossible.
""".strip(),
    ),
    Lesson(
        slug="becoming-pro/from-demo-to-real",
        module_id="becoming-pro",
        order_in_module=7,
        title="From demo to real money: the ladder",
        summary=(
            "Demo → tiny live → measured size-ups. Each rung has a graduation test you can't "
            "skip."
        ),
        est_minutes=7,
        key_concepts=(
            "demo account", "micro lots", "graduation criteria", "prop firms", "drawdown"
        ),
        figures=(
            Figure(
                key="account-ladder",
                caption=(
                    "Each rung has an exit exam: consistency over trades, not profit over days."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt="What's the graduation test from demo to a small live account?",
                options=(
                    "Doubling the demo account as fast as possible",
                    "50+ trades following the written plan with positive expectancy",
                    "One month without any losing trades",
                ),
                correct_index=1,
                explanation=(
                    "Sample size + rule-following + positive expectancy is the test. "
                    "Fast doubling proves oversizing, and no-loss months prove nothing "
                    "except a small sample."
                ),
            ),
        ),
        body_md="""
Nobody starts at full size. The professional path is a ladder, and each
rung has an explicit exam:

**Rung 1 — Demo (1–3 months).** Free practice with fake money. The goal is
*not* profit — demo profits are easy because fear is absent. The goal is
**mechanics**: 50+ trades placed exactly per your written plan, journal
complete, zero rule violations. Pass that, move up.

**Rung 2 — Tiny live (3–6 months).** Real money, micro lots — risking
cents to a few dollars per trade. This rung exists for one reason: to meet
the *feelings*. The heart-rate on a real stop-out cannot be simulated.
Exam: expectancy still positive across 50+ live trades, and your rules
survived contact with your emotions.

**Rung 3 — Meaningful size, stepwise.** Increase risk only after each
50-trade block stays disciplined. A common rule: double size only after a
profitable, rule-clean quarter; *halve* it after hitting a 10% drawdown.
Sizing down after losses is what professionals do and gamblers don't.

**A word on prop firms.** Companies that "fund" traders after an exam fee
are everywhere now. Know the math: their profit comes mostly from exam
fees, and their tight daily-loss limits are designed to fail impatient
traders. If you ever try one, do it *after* rung 2 — with the same plan,
same size discipline — and treat the fee as tuition, not investment.

### Where this system fits

It's your rung-0-to-2 co-pilot: paper-trade its calls (Loop page), size by
rules (Trade plan), journal everything, and let its honest scoreboards
tell you when your own numbers — not your feelings — say you've earned the
next rung.
""".strip(),
    ),
)

# ---------------------------------------------------------------------------
# Module 13 — Trading with Mentor, day to day
# ---------------------------------------------------------------------------

_USING_MENTOR = (
    Lesson(
        slug="using-mentor/a-day-with-mentor",
        module_id="using-mentor",
        order_in_module=1,
        title="A day with Mentor: which page, when, why",
        summary="The five-minute daily flow through the app — from briefing to journal.",
        est_minutes=5,
        key_concepts=("dashboard", "trade plan", "loop", "journal", "daily flow"),
        figures=(
            Figure(
                key="mentor-day-flow",
                caption=(
                    "Dashboard → Trade plan → (maybe) trade → Journal → Loop: the whole daily "
                    "circuit."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt="The Trade plan page says STAND ASIDE. What's the professional response?",
                options=(
                    "Find a different indicator that says trade",
                    "Nothing — no trade today is a valid, complete outcome",
                    "Halve the size and trade anyway",
                ),
                correct_index=1,
                explanation=(
                    "Stand-aside means the odds are too close to a coin flip to pay "
                    "spread on. Overriding it re-introduces exactly the impulse the "
                    "system exists to remove."
                ),
            ),
        ),
        body_md="""
The app has a lot of pages; a trading day only needs four of them, in
order:

1. **Dashboard (2 min).** The greeting screen answers three questions:
   what's the model's lean, is there dangerous news today (event freeze),
   and how is *your* trading going (your pulse). If the freeze banner is
   up, your day may already be decided: stand down.
2. **Trade plan (2 min).** The system's read turned into an actionable
   ticket: stance, entry, stop, target, size for *your* account and risk
   setting. Two honest outcomes: a sized plan — or **STAND ASIDE** in
   plain letters. Both are answers. Run the checklist before any click.
3. **Your broker (1 min, only if trading).** Copy the ticket: entry, stop,
   target, size. All three orders in together. Walk away.
4. **Journal (2 min, after close).** Log what happened *and how you
   behaved*. The system grades its predictions automatically; the journal
   is where you grade yourself.

Weekly, add five minutes on the **Loop** page: is the engine healthy
(heartbeats green), has it retrained, what does its honest scoreboard say?

### The design intention

Notice what's *not* in the flow: staring at live charts, scrolling
opinions, reacting to candles. The app is deliberately shaped so that the
default path is prepare → decide → execute → review — the professional
loop — and the losing behaviours simply have no button.
""".strip(),
    ),
    Lesson(
        slug="using-mentor/reading-the-trade-ticket",
        module_id="using-mentor",
        order_in_module=2,
        title="Reading the trade ticket, line by line",
        summary="Every number on the Trade plan page, where it comes from, and what to do with it.",
        est_minutes=7,
        key_concepts=("entry", "stop-loss", "take-profit", "lots", "risk amount", "reward:risk"),
        figures=(
            Figure(
                key="ticket-anatomy",
                caption=(
                    "Each ticket line traces back to a model: direction from the champion, stop "
                    "from volatility, size from your risk rule."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt="Why is the ticket's stop-loss placed at ~1.5× the expected daily move?",
                options=(
                    "To make the potential loss as small as possible",
                    "So routine market noise can't hit it, only a genuinely wrong call",
                    "Because brokers require that distance",
                ),
                correct_index=1,
                explanation=(
                    "A stop inside the day's normal wiggle gets hit by randomness even "
                    "when the direction call was right. 1.5 sigma puts it beyond noise, "
                    "so being stopped out actually means the idea failed."
                ),
            ),
        ),
        body_md="""
The Trade plan ticket looks simple — five numbers. Each one is the output
of a different part of the system, and knowing the lineage tells you how
much to trust it.

- **Stance (LONG / SHORT / STAND ASIDE)** — from the current *champion*
  direction model. Below ~10% confidence the system refuses to pick a
  side; that refusal is a feature, not a failure.
- **Entry** — simply the latest price. No prediction here; you're entering
  at market.
- **Stop loss** — the volatility model's expected move over the horizon,
  times 1.5. It answers: *how far can price wander by pure noise?* — and
  then stands just beyond it. Wider volatility day → wider stop →
  **smaller position**, automatically.
- **Take profit** — the stop distance times your chosen reward:risk (2:1
  by default). With 2:1 you can be right only 40% of the time and still
  profit — that's the whole math of asymmetry.
- **Position size (lots)** — your account × your risk % ÷ the stop
  distance in money. The one line where *your* numbers enter. Change the
  account or risk input and watch only this line move: prediction and
  sizing are deliberately separate machines.

### The two lines people misread

**"Money at risk"** is not what the trade will lose — it's the *maximum*
loss if the stop is hit, which you chose in advance. **Confidence** is not
certainty — 43% confidence means "a modest lean", and the warning banner
will honestly tell you to consider half size. The ticket never hides its
own doubt; read the doubt as carefully as the direction.
""".strip(),
    ),
    Lesson(
        slug="using-mentor/trusting-the-odds",
        module_id="using-mentor",
        order_in_module=3,
        title="When to trust the odds (and when to stand down)",
        summary="P(up) is a probability, not a promise — here's how a pro consumes one.",
        est_minutes=6,
        key_concepts=("probability", "calibration", "sample size", "expectancy", "stand aside"),
        figures=(
            Figure(
                key="reliability",
                caption=(
                    "Calibration: when the system says 60%, it should happen about 60% of the "
                    "time — that's the only promise."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt="The system said 62% P(up) and price fell. Was the forecast wrong?",
                options=(
                    "Yes — it said up and the market went down",
                    "Not necessarily — 62% means down happens 38% of the time",
                    "Yes, and the model should be retrained immediately",
                ),
                correct_index=1,
                explanation=(
                    "A 62% call loses 38 times in 100 *when perfectly calibrated*. "
                    "Single outcomes can't judge a probability; only batches can — "
                    "which is exactly what the post-mortem measures."
                ),
            ),
        ),
        body_md="""
The hardest professional skill isn't reading charts — it's thinking in
probabilities without flinching. The system hands you probabilities all
day; here's the owner's manual.

**One forecast means almost nothing.** 58% P(up) that loses wasn't
"wrong" — outcomes judge *batches* of forecasts, never single ones. The
question that matters: *across the last hundred 58% calls, did roughly 58
land?* That's **calibration**, and the System → post-mortem page measures
it continuously so you don't have to trust, you can check.

**The odds price the trade, not just pick it.** 55% up with 2:1 reward:risk
is a good business; 55% with 1:2 is a slow leak. Expectancy =
(win% × win size) − (loss% × loss size). The ticket already does this
arithmetic — your job is only to not overrule it casually.

**Respect the abstentions.** The system stands aside when the odds are
near 50% — meaning *after costs, this coin flip charges admission*. The
most common way users destroy the value of a probabilistic tool is
trading its "no" days. Track it yourself for a month in the journal:
your override trades versus its plan trades. Let the data settle the
argument.

**Watch the walking, not the talking.** Any tool can print percentages.
This one grades itself in public — every call logged before the fact,
resolved against reality, summarized honestly. The day its live Brier
drifts, it retrains; the day a new model can't beat the champion, it
doesn't ship. Consume the odds with exactly that spirit: trust is earned
in batches, forever provisional.
""".strip(),
    ),
    Lesson(
        slug="using-mentor/watching-the-loop",
        module_id="using-mentor",
        order_in_module=4,
        title="Watching the learning engine",
        summary=(
            "Heartbeats, drift, promotions — how to read the Loop page like a pilot reads gauges."
        ),
        est_minutes=6,
        key_concepts=("heartbeats", "drift watch", "champion", "promotion", "paper P&L"),
        figures=(
            Figure(
                key="drift-watch",
                caption=(
                    "Live performance is graded continuously; when it slips past the champion's "
                    "proven level, retraining fires early."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "A retrain ran and the page says 'champion kept — a worse model never ships.' "
                    "Is that a failure?"
                ),
                options=(
                    "Yes — retraining should always produce a better model",
                    "No — the gate proved the current champion is still the best available",
                    "Yes — it means the system stopped learning",
                ),
                correct_index=1,
                explanation=(
                    "Most retrains *should* lose to a good champion. The gate exists "
                    "so only real improvements ship; 'kept' means the test worked."
                ),
            ),
        ),
        body_md="""
The Loop page is the cockpit of the machine that works while you sleep.
Four gauges, read top to bottom:

- **Heartbeats.** Each job — ingest, predict, resolve, retrain — shows its
  last run and a one-line note. All green and recent = the engine is
  alive. A red ingest heartbeat means the data feed hiccuped; the system
  will *refuse to predict* on suspect data rather than guess (that's the
  quality gate doing its job).
- **Events.** The notable moments: drift detected, predictions skipped for
  data quality, champions promoted, alerts sent. An empty feed on a young
  system is normal — silence here is health, not absence.
- **Retrain decisions.** Every challenger ever trained and whether it beat
  the champion *on the same fresh data*. Expect mostly "kept" — a
  champion that loses to every random Tuesday retrain was never good.
- **Paper P&L.** The honest scoreboard: what following every resolved live
  call would have earned, after spread. It starts empty on purpose — it
  only counts predictions made **before** the outcome, so every point on
  that curve is un-fakeable.

### What "worrying" actually looks like

Not a losing week — noise loses weeks. Worry about: heartbeats hours
stale during market hours, repeated quality-skips (feed trouble), or live
Brier drifting above the champion's test level *without* a drift-retrain
firing. Anything like that, the events feed will say so in words — this
page never makes you diagnose from a blank screen.
""".strip(),
    ),
    Lesson(
        slug="using-mentor/close-your-own-loop",
        module_id="using-mentor",
        order_in_module=5,
        title="Close your own loop",
        summary="The system grades itself automatically. The journal is where you grade yourself.",
        est_minutes=5,
        key_concepts=("journal", "expectancy", "review", "process vs outcome", "improvement loop"),
        figures=(
            Figure(
                key="journal-vs-memory",
                caption=(
                    "Memory flatters; the journal doesn't. Written records are the only honest "
                    "mirror."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "You followed the plan exactly and the trade lost. How should the journal "
                    "score it?"
                ),
                options=(
                    "A bad trade — it lost money",
                    "A good trade — process was perfect; the outcome was variance",
                    "Don't log losers, only learn from winners",
                ),
                correct_index=1,
                explanation=(
                    "Grade process, not outcome. Good-process losers are the cost of "
                    "doing business; bad-process winners are the ones that teach the "
                    "habits that eventually ruin you."
                ),
            ),
        ),
        body_md="""
Everything the system does — predict, resolve, post-mortem, retrain — is
one loop: *act, measure, adjust*. It runs that loop on itself every hour.
The missing loop is **yours**, and no model can run it for you.

The Journal page is that loop:

1. **Log every trade** — including the ones you *didn't* take when the
   plan said stand aside (those are decisions too). Entry, exit, size,
   and crucially: *did you follow the plan, and how did it feel?*
2. **Let the analytics accumulate.** Expectancy in R, win rate, profit
   factor — the same honest math the system applies to itself, applied
   to you. Twenty trades minimum before any conclusion; fifty before a
   confident one.
3. **Weekly, read and tag.** Mistake tags beat prose: `moved-stop`,
   `no-setup`, `oversized`, `revenge`. After a month, the tag counts are
   a diagnosis no coach could improve on.
4. **Change one thing.** The review's output is a single rule adjustment
   for next week. One. Changing five things at once teaches nothing.

### The graduation metric

Here's the professional benchmark hidden in this page: when your journal
shows **50+ trades, zero rule violations, and positive expectancy**, you
have evidence — not feelings — that you're ready for the next account
size. When it shows violations, the system's discipline pages (and your
own tags) tell you exactly which lesson to re-read. Either way, the
mirror doesn't flatter. That's the point of mirrors.
""".strip(),
    ),
)

# Extension lessons appended to existing modules ----------------------------

_UNDER_THE_HOOD_EXT = (
    Lesson(
        slug="under-the-hood/the-watchdogs",
        module_id="under-the-hood",
        order_in_module=10,
        title="The watchdogs: quality gate, drift watch, heartbeats",
        summary=(
            "Three guards that keep an unattended system honest: refuse bad data, catch decay, "
            "stay observable."
        ),
        est_minutes=6,
        key_concepts=("quality gate", "drift", "heartbeat", "cooldown", "observability"),
        figures=(
            Figure(
                key="drift-watch",
                caption=(
                    "The drift watch compares live rolling error to the champion's proven level — "
                    "degradation triggers an early retrain."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "The data feed delivers a 12-hour hole in the middle of Tuesday. What does "
                    "the system do?"
                ),
                options=(
                    "Predicts anyway — more predictions is better",
                    "Skips the prediction loudly and logs a quality event",
                    "Deletes the old data and starts over",
                ),
                correct_index=1,
                explanation=(
                    "A model fed a broken window produces confident garbage. The "
                    "quality gate skips the tick, says why, and the heartbeat shows "
                    "it — no silent failures."
                ),
            ),
        ),
        body_md="""
A system that runs unattended 24/7 needs more than good models — it needs
guards against the ways things quietly rot. Three watchdogs run alongside
the loop:

- **The quality gate** inspects the recent bars *before every prediction*.
  A mid-week hole in the data, or a feed that's gone stale while the
  market is open, means **no prediction this hour** — loudly, with the
  reason logged. It knows the FX calendar, so the normal weekend gap
  never false-alarms. Rule: refusing to answer beats answering from
  garbage.
- **The drift watch** runs after every grading pass. It computes the
  rolling error of the last ~40 *live* predictions and compares it to the
  champion's proven test error. Degrades past the margin → an immediate
  retrain, days before the weekly schedule would have caught it. A
  24-hour cooldown stops a rough patch from causing a retrain storm.
- **Heartbeats & events** make it all visible. Every job reports its last
  run and outcome; every notable moment (drift, skip, promotion, alert)
  lands in the events feed. The design rule: *nothing important happens
  silently.*

### Why bother, honestly

None of this adds predictive edge. What it adds is **trustworthiness**:
the property that when the Loop page looks healthy, it actually is — and
when something's wrong, the system says so in plain words before you
lose a week to a dead data feed. For an autonomous system, that property
is worth more than another indicator ever would be.
""".strip(),
    ),
)

_PSYCHOLOGY_EXT = (
    Lesson(
        slug="psychology/process-goals",
        module_id="psychology",
        order_in_module=4,
        title="Process goals beat profit goals",
        summary="You can't control outcomes, only behaviour — so set goals where control lives.",
        est_minutes=5,
        key_concepts=("process goals", "outcome goals", "variance", "control", "streaks"),
        figures=(
            Figure(
                key="process-vs-outcome",
                caption="Outcomes are process plus variance. Only one of those responds to effort.",
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt="Which is a process goal?",
                options=(
                    "Make $500 this week",
                    "Take only checklist-passing trades this week",
                    "Have a 70% win rate this month",
                ),
                correct_index=1,
                explanation=(
                    "Only behaviour is fully yours. Dollar and win-rate targets are "
                    "outcome goals — variance can wreck them in a perfectly played "
                    "week, and reward them in a badly played one."
                ),
            ),
        ),
        body_md="""
"Make $200 a day" is the most natural goal in trading — and one of the
most destructive. Here's the mechanism:

Outcomes = **process + variance**. In any single week, variance is loud:
a perfectly executed week can lose money, and a reckless one can win.
If your goal lives in outcomes, variance will regularly punish good
behaviour and reward bad behaviour — which is precisely how bad habits
get trained in. Psychologists call it *intermittent reinforcement*; it's
the same schedule that makes slot machines addictive.

**Process goals put the target where control lives:**

- Every trade risk-sized to plan — *fully controllable.*
- Zero trades outside my setups — *fully controllable.*
- Journal entry within an hour of closing — *fully controllable.*
- Stop trading after the daily loss limit — *fully controllable.*

Score your week on those, and a disciplined losing week is a **passed
week** — variance owes you nothing, but the compounding of good process
eventually collects.

### The system practices what this preaches

Notice that the machine itself is run on process goals: it doesn't chase
"be right this week" — it targets *calibrated probabilities, honest
grading, retrain on evidence*. Its outcomes wobble day to day; its
process never does. Copy that architecture into your own head: it is,
quietly, the entire secret.
""".strip(),
    ),
)

# ---------------------------------------------------------------------------
# Module — How markets move: structure & price action
# ---------------------------------------------------------------------------

_MARKET_STRUCTURE = (
    Lesson(
        slug="market-structure/direction-and-trend",
        module_id="market-structure",
        order_in_module=1,
        title="Which way is the market going? Direction & trend",
        summary=(
            "Bullish, bearish, neutral, uptrend, downtrend, sideways, range-bound — the six words "
            "that describe every chart."
        ),
        est_minutes=7,
        key_concepts=(
            "bullish", "bearish", "neutral", "uptrend", "downtrend", "sideways", "range-bound"
        ),
        figures=(
            Figure(
                key="trend-types",
                caption=(
                    "Three shapes every chart takes: rising (uptrend), falling (downtrend), or "
                    "going nowhere (sideways/range)."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "Price keeps making higher peaks and higher dips over weeks. What is this "
                    "called?"
                ),
                options=("A downtrend", "An uptrend (bullish)", "A range"),
                correct_index=1,
                explanation=(
                    "Higher peaks and higher dips = an uptrend, and traders feeling "
                    "optimistic about rising prices are 'bullish'."
                ),
            ),
        ),
        body_md="""
Before anything else, a trader asks one question about a chart: **which way
is it going?** There are only three possible answers, and a handful of words
for each. Learn these six words and you can describe any chart out loud.

### The mood words: bullish, bearish, neutral

- **Bullish** — you *expect price to rise*. Think of a bull attacking by
  throwing its horns **upward**. "I'm bullish on EUR/USD" = "I think it'll
  go up."
- **Bearish** — you *expect price to fall*. A bear swipes its paws
  **downward**. "Bearish" = "I think it'll go down."
- **Neutral** — you have *no strong view*. You expect price to drift or
  chop without a clear direction. Being neutral is a real, valid position —
  it usually means "not a good time to trade."

These words describe a *feeling or expectation*. The next words describe
what price is *actually doing*.

### The three shapes a chart can take

1. **Uptrend** — price is generally *rising* over time: each push up reaches
   a **higher peak**, and each dip stops at a **higher low** than the last.
   Staircase going up. An uptrend is the picture of a bullish market.
2. **Downtrend** — price is generally *falling*: **lower peaks** and **lower
   lows**. Staircase going down. This is a bearish market.
3. **Sideways / range-bound** — price is going *nowhere*, bouncing between a
   rough ceiling and a rough floor. "Sideways" and "range-bound" mean the
   same thing: stuck in a range. Markets spend a **huge** amount of time
   here — often more than they spend trending.

### Why this matters more than any indicator

The single most useful habit in trading is **trading with the trend, not
against it.** Buying in an uptrend or selling in a downtrend means the
overall current is helping you. Fighting the trend — buying in a downtrend
because it "looks cheap" — is how beginners lose steadily.

And in a **range**, both trend rules are off: price just ping-pongs, so
breakout signals fake out constantly and trend-following tools whipsaw. Knowing
you're in a range is itself a decision: usually, *stand aside*.

> This system's forecasts already lean on this: it measures whether the
> market is trending or calm (a "regime") and is honest that direction in a
> chop is close to a coin flip.
""".strip(),
    ),
    Lesson(
        slug="market-structure/price-action-moves",
        module_id="market-structure",
        order_in_module=2,
        title="How price actually moves: the price-action words",
        summary=(
            "Support, resistance, breakout, breakdown, pullback, retracement, reversal, "
            "continuation, consolidation, expansion, compression — all explained."
        ),
        est_minutes=9,
        key_concepts=(
            "support", "resistance", "breakout", "breakdown", "pullback",
            "retracement", "reversal", "continuation", "consolidation",
            "expansion", "compression",
        ),
        figures=(
            Figure(
                key="price-action-map",
                caption=(
                    "One chart labelling the whole vocabulary: floors, ceilings, breaks, pauses, "
                    "and turns."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "Price is in an uptrend, pauses and drifts down a bit, then continues up. "
                    "That dip was a…"
                ),
                options=("Reversal", "Pullback (a.k.a. retracement)", "Breakdown"),
                correct_index=1,
                explanation=(
                    "A temporary dip *against* the trend that then resumes is a pullback "
                    "/ retracement. A reversal would be the trend actually changing "
                    "direction for good."
                ),
            ),
        ),
        body_md="""
Price never moves in a straight line — it pushes, pauses, pulls back, and
occasionally turns around. Traders have a precise word for each of these
behaviours. Here is the whole vocabulary, grouped by what it describes.

### Floors and ceilings

- **Support** — a price *floor*. A level where buyers have repeatedly
  stepped in, so falling price tends to **stop and bounce**. Think of it as
  a floor holding price up.
- **Resistance** — a price *ceiling*. A level where sellers repeatedly
  appear, so rising price tends to **stall and drop back**. A ceiling
  pressing price down.

Support and resistance aren't magic lines — they're *zones* where past
buying or selling was heavy, so traders watch them and act, which partly
makes them self-fulfilling.

### Breaking through

- **Breakout** — price pushes *up through resistance* (the ceiling breaks).
  Often the start of a new up-move… or a trap.
- **Breakdown** — the opposite: price falls *down through support* (the
  floor gives way).
- A key idea: once broken, **support often becomes resistance and vice
  versa** — the old floor becomes the new ceiling.

### Pauses and continuations

- **Pullback / retracement** — a *temporary* move **against** the trend. In
  an uptrend, a pullback is a small dip before price continues up. The two
  words mean nearly the same thing; "retracement" is often used when
  measuring *how far* it pulled back (e.g. Fibonacci levels).
- **Continuation** — price *resumes* the original trend after a pause. The
  pullback ends, the trend continues.
- **Consolidation** — a *sideways pause*: price stops trending and moves in
  a tight range for a while, gathering energy before its next move. A
  breather.

### Turns and energy

- **Reversal** — the big one: the trend *actually changes direction*. An
  uptrend becomes a downtrend (or vice versa). The hardest thing to call in
  real time, because every reversal starts looking exactly like an ordinary
  pullback.
- **Expansion** — price starts moving in *big, wide* candles — volatility is
  rising, the market is "expanding." Often follows a breakout.
- **Compression** — the opposite: candles get *small and tight*, volatility
  is falling, price is coiling. Compression frequently comes *before* a big
  expansion move — the spring winds up before it releases.

### The one trap to remember

The most expensive confusion in trading is **pullback vs. reversal**. They
look identical at the start. That's exactly why you never bet the whole
account on one call, and why you place a **stop-loss**: it's the line that
says "if this 'pullback' keeps going, it was actually a reversal, and I'm
out."
""".strip(),
    ),
    Lesson(
        slug="market-structure/swings-bos-choch",
        module_id="market-structure",
        order_in_module=3,
        title="Market structure: swings, HH/HL, BOS & CHoCH",
        summary=(
            "How pros read trend from the shape of the swings — higher highs, lower lows, break "
            "of structure, and change of character."
        ),
        est_minutes=8,
        key_concepts=(
            "swing high", "swing low", "higher high", "higher low",
            "lower high", "lower low", "break of structure", "change of character",
        ),
        figures=(
            Figure(
                key="market-structure-swings",
                caption=(
                    "Reading trend from swing points: HH+HL is up, LH+LL is down; a BOS confirms "
                    "the trend, a CHoCH warns it may be turning."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "In a healthy uptrend (higher highs, higher lows), price suddenly makes a "
                    "LOWER low for the first time. This first crack is called a…"
                ),
                options=(
                    "Break of Structure confirming the uptrend",
                    "Change of Character (CHoCH) — an early warning the trend may be turning",
                    "Marubozu",
                ),
                correct_index=1,
                explanation=(
                    "The first lower low after a run of higher lows breaks the pattern — "
                    "that's a change of character, the earliest hint the uptrend could be "
                    "ending."
                ),
            ),
        ),
        body_md="""
"Market structure" sounds fancy but it's just **reading the trend from the
shape of the zig-zags**. Price moves in swings — up a bit, down a bit — and
the *peaks and troughs* of those swings tell you everything.

### Swing highs and swing lows

- A **swing high** is a peak: a candle higher than the ones on either side
  of it. A little mountain top.
- A **swing low** is a trough: a candle lower than its neighbours. A little
  valley bottom.

Mark the swing highs and lows on any chart and the trend jumps out at you.

### The four labels: HH, HL, LH, LL

Compare each swing to the one before it:

- **Higher High (HH)** — a peak *above* the previous peak.
- **Higher Low (HL)** — a trough *above* the previous trough.
- **Lower High (LH)** — a peak *below* the previous peak.
- **Lower Low (LL)** — a trough *below* the previous trough.

Now the rule that makes it click:

- **Uptrend = HH + HL** (rising peaks *and* rising troughs).
- **Downtrend = LH + LL** (falling peaks *and* falling troughs).
- Mixed signals (e.g. a higher high but a lower low) = **no clear structure**
  → likely a range.

### BOS — Break of Structure

A **Break of Structure** is when price breaks *past the last swing in the
direction of the trend*, confirming the trend continues. In an uptrend, when
price pushes above the previous higher high, that's a bullish BOS — the
uptrend just proved itself again. BOS = "the trend is still alive."

### CHoCH — Change of Character

A **Change of Character** is the *first crack* in the pattern. In an uptrend
of higher lows, the moment price makes a **lower low** for the first time,
the "character" of the market has changed — the trend *may* be turning. CHoCH
= "warning: the trend might be ending."

Note the honest order of events: a **CHoCH is an early warning**, and only a
follow-up **BOS in the new direction** confirms an actual reversal. Many
CHoCHs are just deep pullbacks that fail — which is why they're a heads-up to
tighten risk, not a guarantee to flip your whole position.

### Why learn this

These terms (HH/HL, BOS, CHoCH) are the backbone of how modern chart-readers
and "Smart Money" traders talk. You'll hear them constantly. Now you can
follow the conversation — and, more usefully, you can *see the trend
objectively* instead of guessing. That said: reading structure tells you the
trend's *shape*, not its *future*. It's context, not a crystal ball — exactly
how this app treats charts too.
""".strip(),
    ),
)


# ---------------------------------------------------------------------------
# Module — Candlesticks & volume
# ---------------------------------------------------------------------------

_CANDLES_VOLUME = (
    Lesson(
        slug="candles-volume/candlestick-zoo",
        module_id="candles-volume",
        order_in_module=1,
        title="The candlestick zoo: every pattern that matters",
        summary=(
            "Doji, hammer, hanging man, shooting star, engulfing, inside bar, outside bar, pin "
            "bar, marubozu — what each shape is telling you."
        ),
        est_minutes=9,
        key_concepts=(
            "doji", "hammer", "hanging man", "shooting star", "engulfing",
            "inside bar", "outside bar", "pin bar", "marubozu",
        ),
        figures=(
            Figure(
                key="candle-zoo",
                caption=(
                    "The nine candlestick shapes traders name most — each is a little story about "
                    "who won the bar, buyers or sellers."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "A candle with a tiny body at the top and a long lower wick appears after a "
                    "fall. What is it, and what does the long lower wick mean?"
                ),
                options=(
                    "A shooting star — sellers rejected higher prices",
                    "A hammer — sellers pushed price down but buyers slammed it back up",
                    "A doji — total indecision",
                ),
                correct_index=1,
                explanation=(
                    "A long lower wick means price was pushed way down during the bar but "
                    "buyers rejected it and closed near the top — a hammer, a potential "
                    "bottoming signal."
                ),
            ),
        ),
        body_md="""
Every candle is a **story about a fight** between buyers and sellers over one
time period. The **body** shows where price opened and closed; the **wicks**
(thin lines) show how far it stretched and got rejected. The shapes below are
just named outcomes of that fight. (New to candles? The "Reading charts" module
covers the basic anatomy first.)

### Indecision

- **Doji** — open and close are almost the *same*, so the body is a tiny
  line. Neither side won. A doji after a big move often warns of a pause or
  turn — the momentum just stalled.

### Rejection candles (one long wick)

The long wick is the key: it shows price went somewhere and got **violently
rejected**.

- **Hammer** — small body at the *top*, long wick *below*, appearing after a
  *fall*. Sellers pushed price down but buyers hammered it back up. Possible
  bottom.
- **Hanging Man** — looks identical to a hammer (small body up top, long
  lower wick) but appears after a *rise*. Same shape, opposite location —
  a possible top warning.
- **Shooting Star** — small body at the *bottom*, long wick *above*, after a
  *rise*. Buyers pushed up but sellers shot it back down. Possible top.
- **Pin Bar** — the general name for any candle with one long wick and a
  small body ("pin" = it pins a rejection). Hammers and shooting stars are
  both pin bars. The long wick points to where price *failed* to hold.

### Power candles

- **Marubozu** — a *big body with almost no wicks*. One side dominated the
  entire bar, open to close, no rejection. A bullish marubozu (big up candle)
  shows buyers in total control; bearish shows sellers.
- **Engulfing** — a *two-candle* pattern: a big candle whose body completely
  **swallows** the previous candle's body. A bullish engulfing (big green
  eating a red) after a fall is a strong turn signal; bearish engulfing after
  a rise is the reverse.

### Range candles (two-candle relationships)

- **Inside Bar** — a candle that fits *entirely inside* the previous
  candle's range. The market got quieter — a pause/compression that often
  precedes a breakout.
- **Outside Bar** — the opposite: a candle whose range *engulfs* the previous
  one (higher high *and* lower low). A burst of volatility; the market grabbed
  both sides.

### The honest truth about candle patterns

Candlestick patterns are **useful vocabulary and mild hints, not magic.** A
hammer at major support with the trend behind it is worth noticing; the same
hammer in the middle of nowhere is noise. Pros use them as *one input* — a
nudge that agrees or disagrees with the bigger picture — never as a
standalone "buy now" button. Tested in isolation, most single patterns barely
beat a coin flip, which is exactly why this system leans on measured
probability, not pattern-spotting.
""".strip(),
    ),
    Lesson(
        slug="candles-volume/volume-and-profile",
        module_id="candles-volume",
        order_in_module=2,
        title="Volume, delta, and the volume profile",
        summary=(
            "Volume spikes, buying vs selling volume, delta, volume profile, Point of Control, "
            "Value Area — reading the crowd's footprints."
        ),
        est_minutes=8,
        key_concepts=(
            "volume spike", "buying volume", "selling volume", "delta",
            "volume profile", "point of control", "value area high", "value area low",
            "open interest",
        ),
        figures=(
            Figure(
                key="volume-profile",
                caption=(
                    "Volume bars show WHEN trading was heavy; the volume profile (sideways "
                    "histogram) shows at WHICH PRICES — the fat part is the Point of Control."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "On a volume profile, the price level with the single most volume traded is "
                    "called the…"
                ),
                options=(
                    "Value Area High",
                    "Point of Control (POC)",
                    "Delta",
                ),
                correct_index=1,
                explanation=(
                    "The Point of Control is the price where the most volume changed "
                    "hands — the market's 'fair value' magnet. The Value Area is the "
                    "wider band (about 70% of volume) around it."
                ),
            ),
        ),
        body_md="""
Price tells you *where* the market went. **Volume** tells you *how much
conviction* was behind the move — how many contracts actually traded. It's
the crowd's footprints.

### Volume basics

- **Volume** — the number of units traded in a period, drawn as bars under
  the chart. Tall bar = lots of activity; short bar = quiet.
- **Volume spike** — a sudden, unusually tall bar. Something happened: news,
  a breakout, panic. Spikes mark moments the crowd *cared*.
- **Buying volume vs selling volume** — an attempt to split volume into
  trades that happened at the *ask* (aggressive buyers) versus the *bid*
  (aggressive sellers). More buying volume on a rise = a healthier move.
- **Delta** — the *difference* between buying and selling volume (buys minus
  sells). Positive delta = aggressive buyers dominated; negative = sellers.
  Delta diverging from price (price rising but delta falling) hints the move
  is running out of fuel.

### The confirmation rule

Volume is mostly used to **confirm or doubt** a price move:

- A breakout **on high volume** is more trustworthy — the crowd committed.
- A breakout **on low volume** is suspect — few backed it, so it often fails
  (a "fakeout").
- A trend on *shrinking* volume is quietly losing support.

### The volume profile (a different view)

A normal volume chart shows volume **by time** (bars along the bottom). A
**volume profile** flips it 90°: a *horizontal* histogram showing how much
volume traded **at each price level**. This answers a more useful question:
*where did the market do most of its business?*

- **Point of Control (POC)** — the price level with the **most** volume ever
  traded. The market's centre of gravity; price is often pulled back toward
  it like a magnet.
- **Value Area** — the band of prices where about **70%** of volume happened.
  Its edges are:
  - **Value Area High (VAH)** — the top of that band.
  - **Value Area Low (VAL)** — the bottom.
- Prices **above** the value area are considered "expensive" (premium);
  **below** it, "cheap" (discount). Price spending little time somewhere means
  the market rejected those levels quickly.

### Open interest (futures & options only)

- **Open Interest** — the number of contracts *currently open* (not yet
  closed) in futures/options markets. Rising open interest during a trend
  means new money is entering and backing the move; falling open interest
  means players are closing out — the move may be tiring. (Note: spot forex,
  like the EUR/USD this app trades, has *no* central open-interest figure —
  it's decentralised — so this concept applies mainly to futures.)

### The honest caveat

Volume analysis is genuinely informative in *centralised* markets (stocks,
futures) where every trade is reported. In **spot forex it's murkier** —
there's no single exchange, so "volume" is really your broker's slice, not
the whole market. Treat forex volume as a rough hint, not gospel.
""".strip(),
    ),
)

# ---------------------------------------------------------------------------
# Module — Smart Money Concepts (explained honestly)
# ---------------------------------------------------------------------------

_SMART_MONEY = (
    Lesson(
        slug="smart-money/what-smc-is",
        module_id="smart-money",
        order_in_module=1,
        title="Smart Money Concepts: the honest introduction",
        summary=(
            "What SMC is, where the ideas come from, and the crucial honesty check before you "
            "learn the jargon."
        ),
        est_minutes=6,
        key_concepts=(
            "smart money", "institutional", "narrative", "unfalsifiable", "honest skepticism"
        ),
        figures=(
            Figure(
                key="risk-vs-predict",
                caption=(
                    "SMC is a vocabulary for describing charts after the fact — useful language, "
                    "but not a proven crystal ball."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt="What is the honest way to treat Smart Money Concepts?",
                options=(
                    "As a secret institutional system that guarantees wins",
                    "As a useful vocabulary for describing price — helpful for "
                    "context, unproven as an edge",
                    "As proof that retail traders always lose",
                ),
                correct_index=1,
                explanation=(
                    "SMC gives you good language and pattern-awareness, but its core "
                    "claims are hard to test and mostly descriptive. Learn it, use it as "
                    "context, and stay skeptical of anyone selling certainty."
                ),
            ),
        ),
        body_md="""
"Smart Money Concepts" (SMC) is one of the most popular ways charts are
talked about online today, so you *will* hear this jargon everywhere — order
blocks, liquidity, fair value gaps. This app teaches it to you for one
reason: **so you understand the language**. But we do it honestly, which most
SMC content does not.

### The story SMC tells

The core narrative: big institutions ("smart money" — banks, funds) can't buy
or sell huge positions without moving price, so they *engineer* moves to trap
small traders ("retail"), grab their orders as **liquidity**, and fill their
own positions at good prices. SMC is a set of names for the footprints those
institutions supposedly leave.

### What's genuinely useful about it

- It makes you think about **where other traders' stop-losses sit** — and
  those clusters really do get hit, which is real and worth understanding.
- It gives you **precise words** for chart features (order block, FVG, sweep)
  so you can study and discuss price action clearly.
- It pushes you to **wait for confirmation** instead of guessing.

### The honest health warning

Here's what the YouTube gurus won't tell you:

- Most SMC ideas are **descriptive, not predictive**. After a move, you can
  always point to an "order block" that "caused" it — but that's labelling the
  past, which is easy. Calling it *before* the move, reliably, is the part
  nobody can prove.
- Many SMC claims are **unfalsifiable** — vague enough that any outcome can be
  explained, which means they can't really be tested. That's a red flag in
  any field.
- No published, honest study shows SMC beating a simple baseline after costs.
  If a secret institutional method reliably printed money, it wouldn't be a
  free YouTube video.

### How to hold it in your head

Learn SMC the way you'd learn any vocabulary: it lets you *read the room*.
Use it as **context** — "there's a cluster of stops above; a spike up there
might be a trap" — not as a **guarantee**. Combine it with risk management
(which *is* proven to matter) and calibrated probability (what this system
provides). The next two lessons teach the actual terms — clearly, and with
the same honest lens.
""".strip(),
    ),
    Lesson(
        slug="smart-money/liquidity-sweeps-stophunts",
        module_id="smart-money",
        order_in_module=2,
        title="Liquidity, sweeps & stop hunts",
        summary=(
            "Why clusters of stop-losses are 'liquidity', how a sweep grabs them, and what a stop "
            "hunt really is."
        ),
        est_minutes=7,
        key_concepts=("liquidity", "liquidity sweep", "stop hunt", "equal highs", "equal lows"),
        figures=(
            Figure(
                key="liquidity-pools",
                caption=(
                    "Stop-losses pile up just beyond obvious highs/lows — a 'liquidity pool'. A "
                    "sweep spikes through to trigger them, then price often snaps back."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "Price spikes just above an obvious resistance where many stop-losses sat, "
                    "triggers them, then immediately drops back below. This is a…"
                ),
                options=(
                    "Breakout to buy into",
                    "Liquidity sweep / stop hunt — the spike grabbed stops, then reversed",
                    "Marubozu",
                ),
                correct_index=1,
                explanation=(
                    "A quick poke beyond a level that triggers stops and then reverses is "
                    "a liquidity sweep (a.k.a. stop hunt) — the classic trap that catches "
                    "breakout buyers."
                ),
            ),
        ),
        body_md="""
This is the one SMC idea with the most real substance, because it's built on
something genuinely true: **stop-loss orders cluster in obvious places, and
clusters of orders are fuel.**

### Liquidity = resting orders

**Liquidity** means *orders waiting to be filled*. Where do lots of orders
wait? Just beyond **obvious levels**:

- Above an obvious **resistance** or a **swing high**, there sit: the
  stop-losses of everyone who sold (shorted), *plus* the buy orders of
  breakout traders. A big pool of buy orders.
- Below an obvious **support** or **swing low**: the stop-losses of everyone
  who bought, plus breakout sellers. A pool of sell orders.
- **Equal highs / equal lows** — when price makes two peaks (or troughs) at
  almost the same level, stops pile up *especially* thickly just beyond them.
  A neon sign saying "liquidity here."

A big player who needs to buy a lot *wants* to buy where there are many sell
orders to match against — i.e. right where all those stops are.

### The sweep (a.k.a. stop hunt)

A **liquidity sweep** or **stop hunt** is when price makes a sharp, brief
poke **beyond** an obvious level — triggering all those clustered stops — and
then **reverses back**. The move wasn't a real breakout; it was a raid to
grab the resting liquidity, after which price snaps back the other way.

The classic trap: an obvious resistance, everyone piles in to buy the
"breakout," price pokes just above to trigger stops and fill breakout buyers…
then collapses, leaving those buyers trapped.

### How to actually use this (carefully)

- **Be suspicious of clean breakouts through obvious levels**, especially on
  a spike with an immediate reversal. That's the sweep signature.
- Place your own stop-loss a little *further* from the obvious level than
  everyone else, so a shallow sweep doesn't clip you before your idea plays
  out.
- **Wait for the snap-back and confirmation** rather than chasing the poke.

### The honest limit

Sweeps are real, but you can only reliably name them **afterward** — in the
moment, a "sweep" and a genuine breakout look identical, and plenty of pokes
just keep going. So this is *risk-awareness*, not a signal: it tells you
*where* the danger and traps live, which makes you place smarter stops. It
does not tell you the future. Manage risk first; treat the pattern as
context.
""".strip(),
    ),
    Lesson(
        slug="smart-money/blocks-fvg-premium",
        module_id="smart-money",
        order_in_module=3,
        title="Order blocks, breaker blocks, FVG & premium/discount",
        summary=(
            "The rest of the SMC vocabulary decoded: order block, breaker block, mitigation "
            "block, fair value gap, imbalance, and the premium/discount/equilibrium map."
        ),
        est_minutes=8,
        key_concepts=(
            "order block", "breaker block", "mitigation block", "fair value gap",
            "imbalance", "premium", "discount", "equilibrium",
        ),
        figures=(
            Figure(
                key="smc-blocks",
                caption=(
                    "An order block is the last candle before a big move; a fair value gap is the "
                    "untraded gap left by that move; premium/discount split the range at its 50% "
                    "equilibrium."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "A fast move up leaves a three-candle gap where price barely traded. SMC "
                    "calls this untraded zone a…"
                ),
                options=(
                    "Order block",
                    "Fair Value Gap (FVG) / imbalance — price often returns to 'fill' it",
                    "Point of Control",
                ),
                correct_index=1,
                explanation=(
                    "A fast move that skips price levels leaves a fair value gap (an "
                    "imbalance); the idea is price often revisits it later to trade the "
                    "levels it skipped."
                ),
            ),
        ),
        body_md="""
Here's the rest of the SMC dictionary. Each term is just a *named chart
feature* — learn the shape, and keep the honesty lens from the intro lesson.

### The "block" family

- **Order Block** — the **last candle (or cluster) before a big, sharp
  move**. The idea: this is where big players placed their orders, so if price
  returns to that zone later, they may "defend" it and price could react. In
  practice it's simply "the base the last big move launched from."
- **Breaker Block** — an order block that **failed**: price broke through it
  instead of respecting it. Once broken, that zone is expected to flip role
  (old support becomes resistance) and act as a *breaker* on the way back.
- **Mitigation Block** — a zone a big player returns to in order to
  "mitigate" (improve or close out) an earlier position. In practice it looks
  much like an order block; the label is about the supposed *intent*.

Notice these three are variations on one real, simple idea you already know:
**old zones where price reacted before can matter again when revisited** —
which is really just support/resistance with fancier names.

### Fair Value Gap (FVG) & imbalance

- **Fair Value Gap (FVG)** — when price moves so fast it leaves a **gap of
  levels that barely traded** (seen as a space between the wicks of three
  consecutive candles). Also called an **imbalance** — buying and selling
  were lopsided, so some prices got "skipped."
- The theory: markets dislike leaving business undone, so price often
  **returns to "fill" the gap** later — trading the levels it skipped — before
  continuing. Sometimes true, often not; treat it as a *zone of interest*, not
  a promise.

### The premium / discount map

Take any recent price range (a swing low up to a swing high) and split it:

- **Equilibrium** — the **50% midpoint** of the range. "Fair value."
- **Premium** — the **upper half** (above 50%). Price here is "expensive" —
  SMC traders prefer to *sell* in premium.
- **Discount** — the **lower half** (below 50%). Price is "cheap" — they
  prefer to *buy* in discount.

It's a disciplined version of an old, sound instinct: **buy low in the range,
sell high in the range**. That part is genuinely reasonable.

### The through-line

Strip away the branding and most SMC tools reduce to three timeless ideas you
can trust: **support/resistance zones matter**, **stops cluster at obvious
levels**, and **buying low / selling high within a range beats chasing**. The
exotic names add precision and community, but not proven predictive power.
Learn the words so you can talk shop — then lean on risk management and
honest probability for the actual decisions.
""".strip(),
    ),
)

# ---------------------------------------------------------------------------
# Module — Orders & market conditions
# ---------------------------------------------------------------------------

_ORDERS_CONDITIONS = (
    Lesson(
        slug="orders-conditions/order-types-reference",
        module_id="orders-conditions",
        order_in_module=1,
        title="Every order type, and exactly when to use it",
        summary=(
            "Market, limit, stop, stop-limit, and the four combos: buy stop, sell stop, buy "
            "limit, sell limit."
        ),
        est_minutes=8,
        key_concepts=(
            "market order", "limit order", "stop order", "stop limit order",
            "buy stop", "sell stop", "buy limit", "sell limit",
        ),
        figures=(
            Figure(
                key="order-grid",
                caption=(
                    "The four resting orders around the current price: limits wait for a better "
                    "price, stops fire on a breakout — one of each above and below."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "You want to SELL only if price rises to a better (higher) level first. Which "
                    "order rests ABOVE the market?"
                ),
                options=("Sell stop", "Sell limit", "Buy limit"),
                correct_index=1,
                explanation=(
                    "A sell limit rests above the current price — 'sell, but only at this "
                    "higher price or better.' A sell stop rests below and fires on a "
                    "breakdown."
                ),
            ),
        ),
        body_md="""
Your broker gives you a few order types. Master them and you control *exactly*
when and at what price you enter and exit — instead of clicking in a panic.

### The three families

- **Market order** — "fill me **now**, at whatever price is available." Instant,
  but you pay the spread and risk slippage. Use when being in matters more
  than the last fraction of a pip.
- **Limit order** — "fill me **only at my price or better**." You wait for
  price to come to you. Never fills at a worse price, but might not fill at all.
- **Stop order** — "when price **reaches** my level, fire a market order." Used
  to enter on breakouts and — critically — as your **stop-loss** exit.
- **Stop-Limit order** — a stop that, once triggered, places a *limit* order
  instead of a market order. It protects you from terrible slippage (you won't
  fill beyond your limit) but risks *not filling at all* in a fast market. A
  precision tool; the plain stop is safer for a must-exit stop-loss.

### The four combos (this is where beginners get confused)

The trick: **limits want a *better* price (wait for the pullback); stops want a
*breakout* (chase the momentum).** Where each one rests relative to the current
price:

- **Buy Limit** — rests **below** the market. "Buy the dip at a discount."
- **Sell Limit** — rests **above** the market. "Sell the rally at a premium."
- **Buy Stop** — rests **above** the market. "Buy only if it breaks out
  upward." (Also becomes your stop-loss if you're short.)
- **Sell Stop** — rests **below** the market. "Sell only if it breaks down."
  (Also your stop-loss if you're long.)

Memory hook: **Limits below/above = patience for a better price. Stops
above/below = permission to chase a break.**

### The two orders that must exist on every trade

The instant you enter, two orders should already be resting: a **stop-loss**
(a stop order that caps your loss at the amount you chose) and a
**take-profit** (a limit order that banks the win at your target). Deciding
both *before* you enter is the whole difference between a plan and a gamble.

> This system's **Trade plan** page and **Risk calculator** hand you the exact
> entry, stop, and target so all three orders are ready before a single dollar
> is at risk.
""".strip(),
    ),
    Lesson(
        slug="orders-conditions/market-conditions",
        module_id="orders-conditions",
        order_in_module=2,
        title="Reading the weather: market conditions",
        summary=(
            "Volatility, momentum, trend, mean reversion, correlation, liquidity, slippage, and "
            "spread — the 'weather' you trade inside."
        ),
        est_minutes=8,
        key_concepts=(
            "volatility", "momentum", "trend", "mean reversion", "correlation",
            "liquidity", "slippage", "spread",
        ),
        figures=(
            Figure(
                key="market-conditions",
                caption=(
                    "Two opposite weather systems: a trending/momentum market that keeps going, "
                    "and a mean-reverting market that snaps back to average."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "A strategy that bets price will 'snap back' toward its average after "
                    "stretching too far is exploiting…"
                ),
                options=("Momentum", "Mean reversion", "Correlation"),
                correct_index=1,
                explanation=(
                    "Mean reversion assumes over-stretched price returns to its average — "
                    "the opposite of momentum, which assumes a move keeps going."
                ),
            ),
        ),
        body_md="""
A good trade in the wrong *conditions* still loses. Before entering, pros read
the market's "weather." Here are the eight words that describe it.

### How much it's moving

- **Volatility** — *how much price is moving*, regardless of direction. High
  volatility = big, fast candles; low = small, sleepy ones. Volatility decides
  how far your stop must sit to survive normal noise — which is why it drives
  position size. (It's also the one thing this system forecasts with a *real*
  edge, because volatility **clusters**: calm follows calm, wild follows wild.)
- **Momentum** — *how forcefully price is moving one way*. Strong momentum
  means a move is likely to continue for a bit; fading momentum warns it's
  tiring.

### Which way it behaves

- **Trend** — a persistent directional drift (covered in depth earlier).
  Trend-following strategies assume moves **continue**.
- **Mean Reversion** — the opposite behaviour: price stretched too far from its
  average tends to **snap back**. Mean-reversion strategies fade extremes.
  Crucially, **trend and mean reversion are opposite bets** — the whole skill is
  knowing which regime you're in. Trend tools get shredded in a mean-reverting
  range; reversion tools get run over in a strong trend.

### How markets relate

- **Correlation** — how two markets move *together*. +1 = they move in
  lockstep; −1 = perfect opposites; 0 = unrelated. EUR/USD and the US dollar
  index are strongly *negatively* correlated. Correlation matters for risk:
  three "different" trades that are all really the-same-dollar-bet is one big
  trade in disguise.

### The cost of doing business (the frictions)

- **Liquidity** — how easily you can trade *without moving the price*. Deep
  liquidity (major pairs, active hours) = tight costs and clean fills. Thin
  liquidity (exotic pairs, 3 a.m.) = wide costs and nasty fills.
- **Spread** — the gap between the buy (ask) and sell (bid) price. You pay it
  on entry. Widens when liquidity thins.
- **Slippage** — getting filled at a *worse* price than you clicked, because
  the market moved while your order travelled. Worst around news and in thin
  liquidity.

### Why this is the master skill

Matching your **strategy** to the **conditions** is more important than the
strategy itself. Breakout trading shines in expanding volatility and dies in a
quiet range; mean reversion prints in a range and gets destroyed in a trend.
This is exactly why the system measures the **regime** (calm vs. wild, trending
vs. not) before it trusts any signal — and why it will honestly tell you to
*stand aside* when the weather is wrong.
""".strip(),
    ),
)


# Extension lessons for the "using-mentor" module -----------------------------

_USING_MENTOR_EXT = (
    Lesson(
        slug="using-mentor/whole-system-plain-english",
        module_id="using-mentor",
        order_in_module=6,
        title="How the whole system works — in plain English",
        summary=(
            "The entire machine explained like you're five: where the numbers come from, how it "
            "guesses, how it grades itself, and how it gets smarter."
        ),
        est_minutes=8,
        key_concepts=("data", "prediction", "grading", "learning loop", "honesty"),
        figures=(
            Figure(
                key="system-plain",
                caption=(
                    "The whole machine in five boxes: gather data → make a guess → wait → check "
                    "if it was right → learn from it, forever."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt="In one sentence, what makes this system trustworthy?",
                options=(
                    "It predicts the market perfectly",
                    "It writes down every guess before the outcome, then grades "
                    "itself honestly and only keeps changes that prove better",
                    "It uses secret institutional data",
                ),
                correct_index=1,
                explanation=(
                    "The trust comes from public, before-the-fact predictions, honest "
                    "grading, and a rule that a new model only ships if it measurably beats "
                    "the old one. No crystal ball — just honesty."
                ),
            ),
        ),
        body_md="""
Forget the jargon for a moment. Here is the entire system explained the way
you'd explain it to a friend over coffee. It's just **five steps that repeat
forever.**

### Step 1 — Gather the facts

Every hour, the system quietly downloads fresh, real data from free sources:

- **Prices** — the actual EUR/USD candles.
- **Interest rates & the dollar** — from the US central bank's database (FRED):
  2-year and 10-year rates, the yield curve, a dollar index, and the "fear
  gauge" (VIX). Rate differences move currencies more than headlines do.
- **News mood** — a daily score of how positive or negative world news has been
  (from GDELT).

If the data looks broken (a gap, a frozen feed), it **refuses to continue** —
better to skip an hour than to guess from garbage.

### Step 2 — Make a careful guess

It feeds those facts to its current best model (the "champion") and produces a
**probability**, not a promise — for example, *"58% chance the next move is
up."* Alongside it: a confidence level, an expected price range, and a
plain-English reason. If the odds are near 50/50, it honestly says **stand
aside** — no trade.

### Step 3 — Write the guess down, before the outcome

Every prediction is **logged the instant it's made**, before anyone knows what
happens. This is the honesty foundation: you can't cheat a scoreboard you filled
in *before* the game.

### Step 4 — Grade itself against reality

Later, when enough time has passed, the system looks at what price *actually*
did and marks each old guess **right or wrong**. It keeps a running report card:
how accurate, how well-calibrated (when it says 60%, does it happen ~60% of the
time?), would following it have made money.

### Step 5 — Learn, but only from proof

Periodically — and immediately if its recent grades slip — it **trains new
candidate models** on all the fresh data and stages a contest. A new model only
becomes champion if it **measurably beats** the current one *and* beats a plain
coin-flip, tested on data neither model has seen. **A worse model never ships.**
Then the five steps repeat, forever.

### The one thing to remember

Nobody can predict EUR/USD reliably — the honest edge is about **53%** on
direction (barely above a coin flip), and this system will never pretend
otherwise. Its real value isn't magic accuracy; it's **discipline, honest
measurement, and risk management done automatically** — the same things that
separate professional traders from gamblers. It's a tireless, honest assistant,
not a money printer.
""".strip(),
    ),
    Lesson(
        slug="using-mentor/every-tab-trading",
        module_id="using-mentor",
        order_in_module=7,
        title="Every tab explained (1): the trading tabs",
        summary=(
            "Dashboard, Trade plan, Forecast, Tips, Predictions, and Loop — what each one shows "
            "and exactly how to use it."
        ),
        est_minutes=9,
        key_concepts=("dashboard", "trade plan", "forecast", "tips", "predictions", "loop"),
        figures=(
            Figure(
                key="tabs-trading",
                caption=(
                    "The six trading tabs and what each answers: what's the read, what should I "
                    "do, why, who else is calling it, and is the engine healthy?"
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "You want the system's current, ready-to-place recommendation with a stop and "
                    "size. Which tab?"
                ),
                options=("Predictions", "Trade plan", "Data health"),
                correct_index=1,
                explanation=(
                    "The Trade plan tab turns the current read into a concrete ticket — "
                    "stance, entry, stop, target, and position size for your account."
                ),
            ),
        ),
        body_md="""
The app has a lot of tabs, so here's exactly what each one is for and how to
use it. This lesson covers the **six trading tabs** (top of the sidebar); the
next covers the toolkit.

### 📊 Dashboard — your morning briefing
**What it shows:** the current read on EUR/USD (which way it leans, chance of
rising, confidence), whether dangerous news is due today (an "event freeze"
warning), and how *your own* trading is going.
**How to use it:** open it first, every day. Spend two minutes: Is there an
event freeze? What's the lean? If the freeze banner is red, your trading day
may already be decided — stand down.

### 🎯 Trade plan — what to do right now
**What it shows:** the read turned into a **concrete ticket** — go long / go
short / **stand aside**, plus exact entry, stop-loss, take-profit, and position
size for *your* account and chosen risk %.
**How to use it:** set your account size and risk (0.5–2%). If it shows a
plan, run the pre-trade checklist, then copy the numbers into your broker —
all three orders together. If it says **STAND ASIDE**, that's a complete answer:
no trade.

### 📈 Forecast — the detail behind the read
**What it shows:** the direction probability *and* the volatility forecast
(expected range) in more depth, with the model's reasoning and the features it
looked at.
**How to use it:** go here when you want the *why* behind the Dashboard's
one-line lean, or to pull the latest news.

### 💡 Tips — the stock-tip scorecard
**What it shows:** a leaderboard that tracks whether stock "tips" (from analysts
or tipsters) actually came true, with price movement and analyst targets.
**How to use it:** a reality check on anyone claiming great calls — the app
scores them honestly over time.

### 🧾 Predictions — the audit log
**What it shows:** every prediction the system has *ever* made, with what
actually happened (hit or miss) and a post-mortem analysing where it's
overconfident.
**How to use it:** this is the transparency tab. Check that the system's calls
are logged before the fact and graded honestly. It's the receipt behind every
claim.

### 🔄 Loop — the learning engine's cockpit
**What it shows:** whether the 24/7 engine is alive (heartbeats), notable events
(drift, retrains, promotions), the model contest history, and the honest paper
P&L of following its live calls.
**How to use it:** glance weekly. All heartbeats green = healthy. It's how you
confirm the machine is genuinely running and learning, not stuck.
""".strip(),
    ),
    Lesson(
        slug="using-mentor/every-tab-toolkit",
        module_id="using-mentor",
        order_in_module=8,
        title="Every tab explained (2): the toolkit tabs",
        summary=(
            "Risk calculator, Journal, Backtester, Prices, Data health, Learn, and Settings — "
            "what each does and when to reach for it."
        ),
        est_minutes=8,
        key_concepts=(
            "risk calculator", "journal", "backtester", "prices", "data health", "settings"
        ),
        figures=(
            Figure(
                key="tabs-toolkit",
                caption=(
                    "The toolkit tabs: size a trade, log & review your trades, test strategies, "
                    "inspect data, keep learning, and manage your account."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "Where do you record a trade you took and later review how disciplined you "
                    "were?"
                ),
                options=("Backtester", "Journal", "Prices"),
                correct_index=1,
                explanation=(
                    "The Journal is your logbook — it records trades and computes your own "
                    "expectancy and win rate so you can grade your *process*, not just "
                    "outcomes."
                ),
            ),
        ),
        body_md="""
These are the **toolkit tabs** — the supporting tools you reach for around your
trades.

### 🧮 Risk calculator — size any trade safely
**What it shows:** enter your account, risk %, entry, and stop, and it computes
the exact **position size** (lots), money at risk, and reward:risk.
**How to use it:** any time you plan a trade by hand. It guarantees you never
risk more than you decided — the single most important habit in trading.

### 📓 Journal — grade yourself
**What it shows:** a logbook of your trades, plus *your* statistics —
expectancy, win rate, profit factor — and a weekly review space.
**How to use it:** log **every** trade (and the no-trades), including how you
*behaved*. The system grades its own predictions; the Journal is where you grade
**yourself**. This is where real improvement happens.

### 🧪 Backtester — test before you trust
**What it shows:** run a strategy over years of history and see the results —
honestly, with spread and slippage charged, plus a side-by-side comparison of
strategies.
**How to use it:** before believing any strategy, test it here. It's built to
expose fake edges, not flatter them.

### 📉 Prices — the raw chart & data coverage
**What it shows:** the stored price history for a symbol and timeframe, with
data-quality gaps flagged.
**How to use it:** to eyeball the actual candles or confirm you have enough
history for a prediction.

### 🩺 Data health — is the fuel clean?
**What it shows:** how much price data you hold, where it came from, and whether
your sources agree.
**How to use it:** if predictions look off, check here first — a model is only as
honest as the data under it.

### 🎓 Learn — this curriculum
**What it shows:** every module and lesson (including this one), with progress
tracking and quizzes.
**How to use it:** work through it in order. Risk first, prediction last.

### ⚙️ Settings — your account
**What it shows:** change your password, and (if you're the admin) add other
users and choose exactly which tabs each can see.
**How to use it:** set a memorable password; add family or a friend with
limited access if you want to share.
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
        id="chart-language",
        order=4,
        title="The language of the charts",
        summary="Bullish, bearish, trend, Fibonacci, pip — every term, with how to read it.",
        lessons=_CHART_LANGUAGE,
    ),
    Module(
        id="market-structure",
        order=5,
        title="How markets move: structure & price action",
        summary=(
            "Direction, support & resistance, the price-action words, and market structure "
            "(HH/HL, BOS, CHoCH)."
        ),
        lessons=_MARKET_STRUCTURE,
    ),
    Module(
        id="candles-volume",
        order=6,
        title="Candlesticks & volume",
        summary=(
            "Every candlestick pattern that matters, plus volume, delta, and the volume profile."
        ),
        lessons=_CANDLES_VOLUME,
    ),
    Module(
        id="smart-money",
        order=7,
        title="Smart Money Concepts, explained honestly",
        summary=(
            "Liquidity, sweeps, order blocks, fair value gaps, premium/discount — the popular "
            "jargon decoded, with an honesty check."
        ),
        lessons=_SMART_MONEY,
    ),
    Module(
        id="indicators",
        order=8,
        title="Indicators & their failure modes",
        summary="Every indicator lies somewhere. Knowing where is the skill.",
        lessons=_INDICATORS,
    ),
    Module(
        id="orders-conditions",
        order=9,
        title="Orders & market conditions",
        summary=(
            "Every order type and when to use it, and the 'weather' you trade inside: volatility, "
            "momentum, trend vs mean reversion."
        ),
        lessons=_ORDERS_CONDITIONS,
    ),
    Module(
        id="expectancy",
        order=10,
        title="Expectancy & the math of survival",
        summary="Why a 40%-win system can be highly profitable — and why most aren't.",
        lessons=_EXPECTANCY,
    ),
    Module(
        id="backtesting",
        order=11,
        title="Backtesting honestly",
        summary="The three failure modes that turn paper edges into live losses.",
        lessons=_BACKTESTING,
    ),
    Module(
        id="psychology",
        order=12,
        title="Psychology & process",
        summary="Your behaviour is the biggest risk in the system. The journal is the cure.",
        lessons=_PSYCHOLOGY + _PSYCHOLOGY_EXT,
    ),
    Module(
        id="market-study",
        order=13,
        title="Studying & predicting the markets",
        summary="The four schools of analysis, a top-down workflow, and how to build a real edge.",
        lessons=_MARKET_STUDY,
    ),
    Module(
        id="toolkit",
        order=14,
        title="The trader's toolkit",
        summary="The best tools for charting, data, risk, journaling, and automation.",
        lessons=_TOOLKIT,
    ),
    Module(
        id="becoming-pro",
        order=15,
        title="Becoming a professional",
        summary=(
            "Orders, sessions, costs, leverage, the written plan, the routine, and the ladder to "
            "real money."
        ),
        lessons=_BECOMING_PRO,
    ),
    Module(
        id="using-mentor",
        order=16,
        title="Trading with Mentor, day to day",
        summary=(
            "How to actually use this app like a pro: the daily flow, the ticket, the odds, the "
            "loop."
        ),
        lessons=_USING_MENTOR + _USING_MENTOR_EXT,
    ),
    Module(
        id="under-the-hood",
        order=17,
        title="Under the hood: how the mentor predicts",
        summary=(
            "Every data source, prediction method, and watchdog the system uses, with diagrams."
        ),
        lessons=_UNDER_THE_HOOD + _UNDER_THE_HOOD_EXT,
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
