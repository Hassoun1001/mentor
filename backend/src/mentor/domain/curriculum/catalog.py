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
            "Pros don't watch charts all day. They run a routine: prepare, execute, review, leave."
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
            "Demo → tiny live → measured size-ups. Each rung has a graduation test you can't skip."
        ),
        est_minutes=7,
        key_concepts=(
            "demo account",
            "micro lots",
            "graduation criteria",
            "prop firms",
            "drawdown",
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
            "bullish",
            "bearish",
            "neutral",
            "uptrend",
            "downtrend",
            "sideways",
            "range-bound",
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
            "support",
            "resistance",
            "breakout",
            "breakdown",
            "pullback",
            "retracement",
            "reversal",
            "continuation",
            "consolidation",
            "expansion",
            "compression",
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
            "swing high",
            "swing low",
            "higher high",
            "higher low",
            "lower high",
            "lower low",
            "break of structure",
            "change of character",
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
            "doji",
            "hammer",
            "hanging man",
            "shooting star",
            "engulfing",
            "inside bar",
            "outside bar",
            "pin bar",
            "marubozu",
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
            "volume spike",
            "buying volume",
            "selling volume",
            "delta",
            "volume profile",
            "point of control",
            "value area high",
            "value area low",
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
            "smart money",
            "institutional",
            "narrative",
            "unfalsifiable",
            "honest skepticism",
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
            "order block",
            "breaker block",
            "mitigation block",
            "fair value gap",
            "imbalance",
            "premium",
            "discount",
            "equilibrium",
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
            "market order",
            "limit order",
            "stop order",
            "stop limit order",
            "buy stop",
            "sell stop",
            "buy limit",
            "sell limit",
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
            "volatility",
            "momentum",
            "trend",
            "mean reversion",
            "correlation",
            "liquidity",
            "slippage",
            "spread",
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
            "risk calculator",
            "journal",
            "backtester",
            "prices",
            "data health",
            "settings",
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


_RISK_FIRST_EXT = (
    Lesson(
        slug="risk-first/managing-the-open-trade",
        module_id="risk-first",
        order_in_module=5,
        title="Managing the trade after you're in",
        summary=(
            "Break-even, trailing, partials and time stops - decided while you are "
            "calm, not while money is moving."
        ),
        est_minutes=8,
        key_concepts=(
            "break-even",
            "trailing stop",
            "partial close",
            "time stop",
            "R multiple",
        ),
        figures=(
            Figure(
                key="trade-management",
                caption=(
                    "The four decisions that happen after entry, and where each one "
                    "sits relative to your risk."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "You are long, 40 pips in profit on a trade that risked 50 pips. "
                    "Price stalls. What does the plan say?"
                ),
                options=(
                    "Close now - a profit is a profit",
                    "Widen the stop so it has room to work",
                    "Nothing yet - 40 is not 1R; the rules trigger at 50",
                ),
                correct_index=2,
                explanation=(
                    "The whole point of pre-committing is that 'price stalled and I "
                    "felt nervous' is not one of the triggers. Your rules fire at 1R "
                    "(50 pips here), not when your pulse changes. And widening the "
                    "stop is never on the menu."
                ),
            ),
        ),
        body_md="""
Almost every trading course spends its time on **entry**. Where do I buy?
Where's my stop? What's my target? Then it stops talking - as if the
trade plays itself from there.

It doesn't. An hour after you enter, you are sitting there watching a
number move, and you have to make decisions. And here is the cruel part:
**those decisions are made in the worst possible mental state.** Money is
moving. You are hopeful, or scared, or both. That is not the moment to
be inventing a rule.

So we decide everything *now*, before a cent is at risk. Four rules.

---

## First: what "R" means

Everything below is measured in **R**, which just means *the amount you
risked on this trade*.

If your entry is 1.1000 and your stop is 1.0950, you are risking 50 pips.
So for this trade, **1R = 50 pips**. If price moves 50 pips your way,
you are "up 1R". If it moves 100 pips your way, you are "up 2R".

Why bother with this instead of pips or dollars? Because R makes every
trade comparable. A 20-pip trade and a 200-pip trade are wildly different
in pips but identical in R if you sized them properly. When you look back
at 100 trades, "average +0.3R" tells you something true. "Average +12
pips" tells you almost nothing.

---

## Rule 1 - Break-even at 1R

**What it means:** once price has moved 1R in your favour, move your stop
from its original spot up to your entry price.

**What it buys you:** the trade can no longer lose. If it turns around
and comes back, you get stopped out at roughly zero instead of -1R. You
have taken risk off the table entirely.

**What it costs you:** some winners will now stop you out at break-even
and *then* run to target without you. That is a real cost and you should
expect it to happen regularly. It is the price of never letting a winner
become a loser.

**Why 1R and not sooner?** This is the part beginners get wrong. Moving
to break-even after 10 pips feels safe, but 10 pips is *inside normal
noise* - the market wiggles that much without meaning anything. You would
be stopped out of nearly every trade by random movement. Waiting for a
full R means price has done something meaningful before you tighten up.

On your trade ticket, the app shows this as **"Move stop to break-even
at"** with the exact price.

---

## Rule 2 - Then trail, by one sigma

**What it means:** after break-even, keep moving your stop up behind
price as it advances. Never down. Only up (for a long; only down for a
short).

**How far behind?** This is where most trailing advice is useless. "Trail
by 20 pips" is a guess that ignores what the market is doing today. On a
quiet day 20 pips is miles away and you give back too much. On a wild day
20 pips is nothing and you get clipped instantly.

So the app trails by **one sigma of the expected move** - roughly, the
typical distance this market is travelling right now, from the volatility
forecast. Quiet market, tighter trail. Wild market, wider trail. Same
rule, different number, automatically.

You will see this on the ticket as **"Then trail by N pips"**, and N
changes day to day. That is not inconsistency; that is the point.

---

## Rule 3 - Bank half at 1R

**What it means:** at the same moment you move to break-even, close
**half** the position and keep the other half running to target.

**What it buys you:** two things, and the second matters more than the
first.

1. Real money in the account. Paper profit is not profit; it is a number
   that can evaporate.
2. **It makes holding the rest bearable.** This is the honest reason.
   Having banked something, you stop white-knuckling the remaining half.
   Traders who take nothing off frequently panic-close the *whole*
   position at the first pullback - and that costs far more than the
   upside they gave up by scaling out.

**What it costs you:** on the trades that run straight to a 3R target,
you made less than you could have. Accept that. You are buying the
ability to actually hold the runners, and that trade is worth it for most
people.

This one is marked **optional** on the ticket. If you know you can hold a
full position without flinching, you may be better off not scaling out.
Be honest with yourself rather than aspirational.

---

## Rule 4 - The time stop

This is the rule nobody teaches, and it is the one that quietly saves the
most money.

**What it means:** if neither your stop nor your target has been hit
within the forecast's horizon - 24 hourly bars, say - **close the trade.
Flat. Whatever the price is.**

**Why:** the prediction had an expiry date baked into it from the moment
it was made. The model was asked "what happens over the next 24 hours?"
It answered. Twenty-four hours later, that answer has been used up. It
says nothing whatsoever about hour 200.

A position sitting open long past its horizon is no longer your system's
trade. It is a *hope*, held because closing it would make the loss real.
Meanwhile it is occupying margin, occupying attention, and quietly
accruing swap charges every night.

The ticket shows this as **"Time stop: N bars"**.

---

## Rule 5 - the one that is not negotiable

> **Never move your stop away from price.**

Not "rarely". Not "only when you're really sure". Never.

Here is why this specific habit is so lethal: **it works.** Most of the
time, widening a stop on a losing trade means price comes back and you
escape. You get rewarded. So you do it again. And again. Each time the
reward trains the habit deeper.

Then one day price does not come back, and the position you kept
widening is now four times the size of a normal loss. That single trade
erases months. This is the single most common way a funded account dies -
not a bad entry, not a bad system, this.

A stop is a decision you made when you were thinking clearly. Moving it
because you are now uncomfortable is overruling your calm self with your
scared self. That trade never ends well.

---

## Putting it together

The ticket on your Trade page already has all of this filled in with real
numbers. Your job is not to compute it - it is to **do what it says**,
including on the trade where doing what it says feels wrong. That feeling
is the tax you pay for a process that survives.
""",
    ),
)

_PSYCHOLOGY_EXT2 = (
    Lesson(
        slug="psychology/learning-from-losses",
        module_id="psychology",
        order_in_module=5,
        title="Learning from losses without punishing yourself",
        summary=(
            "Most losses are not mistakes. Telling the difference is what turns a "
            "journal into an edge."
        ),
        est_minutes=7,
        key_concepts=(
            "root cause",
            "process error",
            "outcome bias",
            "resulting",
            "R bled",
        ),
        figures=(
            Figure(
                key="loss-root-causes",
                caption=(
                    "Losses split into two piles. Only one of them contains "
                    "anything you should change."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=("You followed your plan exactly and lost. What should you change?"),
                options=(
                    "Tighten the entry rules so it doesn't happen again",
                    "Nothing - tag it 'good process' and move on",
                    "Reduce size until you start winning again",
                ),
                correct_index=1,
                explanation=(
                    "Any edge that wins 55% of the time loses 45 times in 100. "
                    "Those 45 losses are not evidence of anything wrong. Changing a "
                    "working system because of a normal loss is called 'resulting', "
                    "and it is how good traders talk themselves into bad systems."
                ),
            ),
        ),
        body_md="""
Here is a question that sounds simple and is not:

> You just lost money. What went wrong?

The honest answer, most of the time, is **nothing**. And if you cannot
sit with that answer, your journal will slowly make you a worse trader
instead of a better one.

---

## The trap: judging decisions by outcomes

Poker players call it **resulting**: judging the quality of a *decision*
by the quality of its *outcome*. It is one of the most natural mistakes
a human brain makes, and in trading it is everywhere.

Think about what a 55%-win system actually looks like from the inside.
It loses 45 trades out of every 100. Those losses are not failures -
they are the system working exactly as designed. But they *feel*
identical to the losses caused by real mistakes. Same red number. Same
sting.

So the trader "fixes" things. Tightens an entry rule. Adds a filter.
Cuts size. Skips the next signal. And the system that was profitable
gets tuned into one that is not, one small reasonable-sounding change at
a time.

The cure is not more discipline. It is **separating the two kinds of
loss**, in writing, at the moment you close the trade.

---

## Two piles

**Pile one: the market beat a sound plan.** You followed your rules, the
size was right, the stop was where you said it would be, and it lost
anyway. This is the cost of doing business. There is nothing here to fix.
In this app that is the tag **"Good process, bad outcome"** - and it is
deliberately a real, first-class tag, not an afterthought.

**Pile two: you did something you control.** You entered without a setup.
You were three times normal size. You moved your stop. You took it to win
back the last one. These are habits, they repeat, and they *are* fixable.

Almost all improvement in trading comes from shrinking pile two. Almost
all self-inflicted damage comes from treating pile one as if it were pile
two.

---

## Why the tags are a fixed list

You might reasonably ask: why not just type what went wrong in your own
words?

Because the point of tagging is **counting**, and free text cannot be
counted. Write your losses up honestly for three months and you will have
"bad entry", "entry was bad", "rushed the entry", "shouldn't have taken
it" and "impatient" - five phrases describing one habit that is costing
you real money, and not one of them appears often enough to look like a
pattern. The habit hides in the spelling.

A fixed list of thirteen tags means the same habit lands in the same
bucket every time. After thirty losses, the pattern is unmissable.

---

## Ranked by damage, not by frequency

Open the review panel on the Journal page and you will notice the causes
are sorted by **R bled** - total risk lost - not by how often each one
happened.

That ordering is deliberate. Suppose you have:

- five trades tagged "bad timing", losing 0.2R each -> **1.0R total**
- one trade tagged "position too large", losing 3.0R -> **3.0R total**

Sorted by frequency, "bad timing" looks like your big problem: five
occurrences versus one. Sorted by damage, the truth appears - the
oversized trade cost you three times as much as all five timing errors
combined.

Fix the thing bleeding the most, not the thing happening the most. They
are frequently not the same thing, and frequency is the more seductive of
the two.

---

## How to actually do it

When you close a losing trade, the tag buttons appear. Two rules:

1. **Tag it immediately.** Not later. Ten minutes later you will have
   already started constructing a story where it wasn't your fault. The
   memory you want is the one you have right now.

2. **Be willing to use "Good process".** If you never reach for it, you
   are not being rigorous - you are being hard on yourself, and the
   review will fill up with false mistakes that send you chasing fixes
   for problems you do not have.

A loss you correctly diagnosed as normal variance costs you money once.
A loss you *misdiagnosed* as a mistake costs you money, plus the working
system you dismantled trying to prevent it.
""",
    ),
)

_UNDER_THE_HOOD_EXT2 = (
    Lesson(
        slug="under-the-hood/knowing-when-to-say-nothing",
        module_id="under-the-hood",
        order_in_module=11,
        title="Knowing when to say nothing",
        summary=(
            "Why the model is allowed to decline a call - and why its silence is information."
        ),
        est_minutes=7,
        key_concepts=(
            "abstention",
            "selective prediction",
            "coverage",
            "confidence margin",
            "Brier score",
        ),
        figures=(
            Figure(
                key="abstention",
                caption=(
                    "Only the confident tails get a call. The crowded middle is "
                    "where edges go to die."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=("The system says it acts on 30% of hours. Is that good or bad?"),
                options=(
                    "Bad - it should have an opinion every hour",
                    "Good if those 30% score better than all hours would; the "
                    "number itself is neutral",
                    "Bad - it means the model is broken",
                ),
                correct_index=1,
                explanation=(
                    "Coverage on its own means nothing. What matters is whether the "
                    "hours it acts on score meaningfully better than the average of "
                    "all hours. Both numbers are on the Loop page precisely so you "
                    "can check rather than assume."
                ),
            ),
        ),
        body_md="""
For most of this system's life it had a slightly silly obligation: every
single hour, it had to produce a direction. Up or down. No option to
shrug.

That obligation was quietly wrecking its score, and here is why.

---

## The problem, in one picture

Imagine sorting every hour of the last two years by how confident the
model was. At the two extremes - the hours it said 65% up, or 35% up -
it is genuinely picking up something real. In the enormous middle - the
hours it said 51%, 49%, 52% - it is doing nothing but describing noise
back to you with a decimal point attached.

Now: the middle is most of the hours. That is not a flaw in this model,
it is what EUR/USD *is* over a 24-hour horizon. Most hours genuinely do
not contain a predictable move.

When you average one number across everything, the useless middle drowns
the useful tails. The result is a score hovering around 0.25 - the
coin-flip mark - even when the tails are genuinely good. **The average
was hiding the edge.**

---

## The fix: let it decline

The model now learns a single number, called the **margin**.

It is the distance from 50/50 that a probability has to reach before the
model is willing to call anything at all. If the margin is 0.06, then:

- 58% up -> distance is 8 points -> **above the margin, it calls it**
- 52% up -> distance is 2 points -> **below the margin, it stays quiet**

When it stays quiet, your Trade page shows **stand aside** and tells you
plainly that this hour sits inside the band where the model learned it
has no edge.

**That is not a failure. That is the most useful thing it can say.** A
system that tells you "I don't know" on the 70% of hours where it doesn't
know is worth vastly more than one that manufactures an opinion to fill
the silence.

---

## Coverage: the number that keeps it honest

There is an obvious way to cheat here, and we have to close it.

If the model is allowed to pick its own margin with no constraints, it
will push the margin sky-high, keep the four luckiest hours in the
sample, and report a spectacular score. Technically true. Completely
worthless - four hours proves nothing, and you cannot trade a system that
speaks four times a year.

So there are two guardrails:

**1. A coverage floor.** A policy must be willing to act on at least
**15% of hours** to even be considered. Below that, the remaining sample
is too small for its score to mean anything, and it is thrown out
regardless of how good the number looks.

**2. The margin is chosen on one slice of data and graded on another.**
The model picks its margin using the calibration window, then that margin
is tested on a completely separate stretch of history it has never seen.
This matters more than it sounds: a threshold picked and scored on the
same data is just a *description* of that data. Only a threshold that
survives fresh data is a **prediction rule**.

---

## What the Loop page shows you

Look at the panel titled **"When the model is willing to speak"** and you
get four numbers:

- **Brier when it acts** - the score on hours it chose to call. This is
  the number that matters.
- **Brier across all hours** - what it would have scored under the old
  every-hour obligation.
- **Gain from abstaining** - the difference. **This can be zero or
  negative**, and when it is, the model does not abstain at all. It is
  allowed to conclude that shutting up bought it nothing.
- **Accuracy when it acts** - how often the calls it did make were right.

Plus the coverage bar: what share of hours it speaks on versus stands
aside.

---

## Where this leaves you

Two things follow, and both are uncomfortable in a useful way.

**Fewer signals is the intended outcome.** If the system now stands aside
most days, it is not broken and it is not being lazy. It is refusing to
give you a trade it has no reason to believe in. The urge to trade
anyway, on the grounds that you opened the app and want something to do,
is exactly the urge this feature exists to resist.

**And it might find nothing.** It is entirely possible that no confidence
band on this market shows a real edge - that the tails are noise too. If
so, the gain will read zero, the model will not abstain, and the honest
conclusion is that this system does not currently have an edge worth
trading. That would be a genuinely useful thing to learn, and it is
better to learn it from a number on a page than from an account balance.

---

## Since then: the margin is chosen by profit

Everything above still holds, with one change made in July 2026. The
margin is no longer picked to make the Brier score look best. It is picked
by asking which quiet band leaves calls that would actually **pay for the
spread**. The lesson *"Saying 'no opinion' when a call can't pay"* in the
module **How the mentor keeps itself honest** explains the new rule.
""",
    ),
)

# ---------------------------------------------------------------------------
# Module 18 — How the mentor keeps itself honest (everything added since July 2026)
# ---------------------------------------------------------------------------

_HONEST_EVIDENCE = (
    Lesson(
        slug="keeping-honest/the-cost-hurdle",
        module_id="keeping-honest",
        order_in_module=1,
        title="Better than a coin flip isn't enough: the cost hurdle",
        summary=(
            "Every trade pays the spread, win or lose, so a call has to be right more than "
            "half the time just to break even."
        ),
        est_minutes=8,
        key_concepts=(
            "breakeven win rate",
            "spread",
            "round-trip cost",
            "promotion floors",
            "Brier score",
        ),
        figures=(
            Figure(
                key="breakeven-hurdle",
                caption=(
                    "After costs, a 24-hour call must clear about 51.8% and a 5-day call about "
                    "50.7%. A 51% model loses on one and pays on the other."
                ),
            ),
            Figure(
                key="promotion-floors",
                caption=(
                    "A new model must be honest, willing to speak and worth trading, then beat "
                    "the champion on the same fresh data."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "A model is right 51% of the time on the 24-hour forecast. What happens "
                    "after costs?"
                ),
                options=(
                    "It makes a small, steady profit",
                    "It breaks even exactly",
                    "It loses money, because the hurdle is about 51.8%, not 50%",
                ),
                correct_index=2,
                explanation=(
                    "Each trade pays about 1.2 pips whether it wins or loses. Against a "
                    "typical 34-pip daily move, 51% right loses roughly 52 pips per 100 "
                    "calls. Better than a coin is not the same as worth trading."
                ),
            ),
            QuizQuestion(
                prompt=(
                    "Why is the hurdle lower for the 5-day forecast (about 50.7%) than for the "
                    "24-hour one (about 51.8%)?"
                ),
                options=(
                    "The 5-day model is better",
                    "The same 1.2-pip cost is a smaller slice of a bigger typical move",
                    "The spread is cheaper on daily charts",
                ),
                correct_index=1,
                explanation=(
                    "The cost per trade is the same, but a 5-day move is typically around 84 "
                    "pips against about 34 pips for 24 hours. A fixed cost matters less "
                    "when the move it is paid out of is bigger."
                ),
            ),
            QuizQuestion(
                prompt=(
                    "A challenger has a Brier score of 0.240, speaks on 40% of hours, and is "
                    "right 50.5% of the time on the 24-hour lane. Is it promoted?"
                ),
                options=(
                    "No, it fails the breakeven floor: honest probabilities don't pay the spread",
                    "Yes, because its Brier score beats 0.248",
                    "Yes, as long as it beats the champion",
                ),
                correct_index=0,
                explanation=(
                    "All three floors must hold. It passes the Brier and coverage floors, "
                    "but 50.5% is below the roughly 51.8% it needs to pay for its trades, "
                    "so it is refused and the message says exactly that."
                ),
            ),
        ),
        body_md="""
Here is a trap that caught this system until July 2026, and catches most
people who build a trading model.

You build a model. It is right **51%** of the time. That beats a coin
flip, so it has an edge, right?

It is also a model that **loses money on every trade it suggests**.

---

## Why: you pay the spread whether you win or lose

Every trade you open and close costs something: the spread, plus a little
slippage on the way in and out. The mentor charges **1.2 pips per round
trip** on EUR/USD: a 0.8-pip spread plus 0.2 pips of slippage on each leg.
That is the same figure the backtester has always charged.

The cost is paid on winners **and** on losers:

- a winning call earns the move **minus** the cost;
- a losing call loses the move **plus** the cost.

So winning half the time is not enough. You need to win a little more than
half just to stand still.

## A worked example in pips

Over the stored price history, a typical 24-hour EUR/USD move is about
**34 pips** (and about **84 pips** over 5 trading days). Take 100 calls on
the 24-hour forecast:

- **51% right:** 51 wins × (34 − 1.2) = +1,673 pips. 49 losses × (34 + 1.2)
  = −1,725 pips. Net: about **−52 pips**. Better than a coin, still losing.
- **About 51.8% right:** roughly zero. That is the **breakeven**.
- **55% right:** 55 × 32.8 − 45 × 35.2 = **+220 pips**.

The rule behind it, in plain words:

> breakeven = 50% + cost ÷ (2 × typical move)

For the 24-hour forecast that is 50% + 1.2 ÷ 68 ≈ **51.8%**. For the 5-day
forecast it is 50% + 1.2 ÷ 168 ≈ **50.7%**. The longer forecast has the
lower hurdle because a fixed cost is a smaller share of a bigger move.

## These numbers are measured, not typed in

The system recomputes the hurdle from the stored price history every time
it needs it, using windows that don't overlap (the lesson on honest win
rates explains why that matters). So the figures drift as the market
changes. In mid-October 2026 they read **51.77%** for the 24-hour forecast
and **50.71%** for the 5-day one. An early measurement on a quieter 90-day
sample read 52.36%. If there are fewer than 30 independent windows to
measure from, the system says plainly that it could not measure the hurdle
instead of inventing one.

One honest simplification: the rule assumes wins and losses are about the
same size. A model whose wins are reliably bigger than its losses would
face a lower hurdle, but that is an edge it would have to *prove*, so the
system doesn't assume it.

---

## The three floors a new model must clear

Every week, and earlier if the drift watch fires, the system trains fresh
**challenger** models. Before a challenger can take over, it has to clear
three separate floors:

1. **Honest probabilities (the Brier floor).** The Brier score measures
   how far stated probabilities sit from what actually happened; lower is
   better. Always saying "50/50" scores 0.25. A challenger must score
   **0.248 or better** on the hours it acts on: beat "50/50" by a margin
   of 0.002.
2. **Willing to speak (the coverage floor).** If it sometimes declines to
   call, it must still act on at least **15% of hours**. Otherwise it could
   hide in a handful of lucky hours.
3. **Worth trading (the breakeven floor).** Its hit rate on the hours it
   acts on must clear the measured breakeven for its forecast.

Then it must **beat the current champion**, with both scored on the same
fresh stretch of data, by at least 0.002 Brier.

Why three floors and not one? Because Brier knows nothing about the spread.
A model can be perfectly calibrated, clear 0.248, be right 51% of the time,
and lose money on every call. Before July only the first two floors
existed. When a challenger fails, the message names which floor stopped
it, because "failed the gate" tells nobody what to fix.

**Real examples.** July's challengers were right 46.8% and 48.2% of the
time: wrong more often than right, before costs are even counted. The
24-hour champion promoted on 6 October tested at 58.3% against a hurdle of
about 51.8%. The 5-day forecast has no champion at all: its latest
challenger scored 0.260 Brier, worse than the 0.248 floor, so a simple,
transparent baseline rule keeps making the 5-day calls until a model earns
the job.

### What this means for you

- Whenever you see a win rate in the app, compare it with the
  **breakeven**, not with 50%. The Loop page and the weekly report print
  them side by side for that reason.
- "Baseline rule" on a forecast is not a fault. It means no trained model
  has earned the job yet.
- The same arithmetic applies to you and to anyone selling signals: a 52%
  hit rate on short-term trades is roughly breakeven after costs, not an
  edge.
""".strip(),
    ),
    Lesson(
        slug="keeping-honest/abstaining-by-profit",
        module_id="keeping-honest",
        order_in_module=2,
        title='Saying "no opinion" when a call can\'t pay',
        summary=(
            "The model chooses where to stay quiet by asking which calls would pay for the "
            "spread, not which would make its score look neat."
        ),
        est_minutes=6,
        key_concepts=(
            "abstention",
            "margin",
            "coverage floor",
            "breakeven",
            "cherry-picking",
        ),
        figures=(
            Figure(
                key="abstain-by-profit",
                caption=(
                    "Each dot is one possible quiet band. The rule takes the loosest band whose "
                    "calls clear breakeven while still covering 15% of hours."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "Breakeven is 51.8% and the coverage floor is 15%. Band 1 speaks on 60% of "
                    "hours at 52.5% right; band 2 on 25% at 54%; band 3 on 8% at 60%. Which wins?"
                ),
                options=(
                    "Band 3, because it has the best hit rate",
                    "Band 2, because it is the best one that still covers 15%",
                    "Band 1, the loosest band whose calls still clear breakeven",
                ),
                correct_index=2,
                explanation=(
                    "Band 3 covers too few hours to count. Bands 1 and 2 both pay, and once "
                    "calls pay, more of them is more money, so the rule takes the loosest: band 1."
                ),
            ),
            QuizQuestion(
                prompt="No quiet band leaves calls that clear breakeven. What happens?",
                options=(
                    "The model keeps only its best few hours, however few",
                    "The model speaks on every hour and the promotion gate judges it as it is",
                    "The system lowers the breakeven until something passes",
                ),
                correct_index=1,
                explanation=(
                    "Shrinking the calls down to a lucky-looking sliver is how an edge is "
                    "manufactured. The honest move is to abstain nowhere and let the gate "
                    "refuse the model, which it almost certainly will."
                ),
            ),
        ),
        body_md="""
The lesson *"Knowing when to say nothing"* in the Under the hood module
introduced **abstention**: the model may decline to call an hour when its
probability sits too close to 50/50. The distance from 50/50 a call must
reach is called the **margin**. This lesson is about how that margin is
chosen, which changed in July 2026.

---

## The old rule: make the score look best

At first the margin was chosen to give the best Brier score on the calls
the model kept. Brier measures *calibration*: whether "60%" really means
60%. It knows nothing about the spread. So the model could fall silent on
hours that would have paid and keep talking on hours that wouldn't, because
good calibration and profit do not always point the same way.

## The new rule: choose by profit

The system now tries margins from zero (speak every hour) upwards. For each
one it looks at the hours the model would still speak on and asks two
questions:

1. Is that still **at least 15% of hours**?
2. Is the hit rate on those hours **at or above the breakeven**?

Among the margins that pass both, it picks the **loosest**, the one that
speaks most often, because once calls pay, more calls means more money.

And if **no** margin passes, the model doesn't abstain at all. It speaks
on every hour, and the promotion gate judges it as it is (and almost
certainly refuses it).

## A worked example

Suppose that on the data used to choose the margin:

- margin 0 (always speak): right **50.6%** of the time on all hours.
  Below the 51.8% breakeven. Fails.
- margin 0.04: right **52.3%** on 38% of hours. Passes both tests.
- margin 0.08: right **54%** on 16% of hours. Also passes.
- margin 0.10: right **57%** on 9% of hours. Looks best, but covers too
  few hours. Fails.

The rule picks **0.04**: the loosest margin that pays. Not 0.10, which
looks best but rests on too few hours to mean anything. Not 0.08, which
pays too but gives fewer chances to trade.

The chosen margin is then graded on a **separate** stretch of history it
never saw. A threshold picked and scored on the same data only describes
that data. One that survives fresh data is a rule.

## Why "abstain nowhere" is the honest fallback

The tempting alternative is to keep narrowing until some sliver of hours
looks profitable. Slice any history finely enough and you will always find
a lucky slice. That is cherry-picking, and the rule refuses to do it. When
it first ran on live data there was no profitable band at all: the margin
came out at zero and the gate refused the model on accuracy (47.7% against
a 52.4% hurdle at the time). That was the correct, honest result.

One more detail. A later feature (live recalibration, lesson 5) can adjust
how confident the model sounds. The stand-aside check still compares the
margin with the model's **own original** probability, because that is the
scale the margin was learned on.

### What this means for you

- **Stand aside** on the Trade page is a decision, not a malfunction. It
  means this hour sits where the model learned its calls don't pay.
- If the Loop page shows the model never abstains, it usually means no
  quiet band would have made the remaining calls pay. In other words,
  there is no edge yet to pay with.
- Apply the same discipline to yourself: don't filter your own backtest
  down to the few setups that happened to work.
""".strip(),
    ),
    Lesson(
        slug="keeping-honest/honest-win-rates",
        module_id="keeping-honest",
        order_in_module=3,
        title="Honest win rates: overlap, sample size, and the truth emerging",
        summary=(
            "Why one market day can be counted 24 times, why 30 independent results is the bare "
            "minimum, and why a falling win rate is often just the truth showing up."
        ),
        est_minutes=9,
        key_concepts=(
            "overlapping windows",
            "independent windows",
            "sample size",
            "confidence interval",
            "regression to the mean",
        ),
        figures=(
            Figure(
                key="overlapping-windows",
                caption=(
                    "Hourly calls on a 24-hour horizon share 23 of their 24 hours. Only calls "
                    "whose windows don't touch count as separate results."
                ),
            ),
            Figure(
                key="interval-shrink",
                caption=(
                    "The same 59.5% win rate: with few results the plausible range is huge. "
                    "It clears breakeven only after about 161 independent results."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "The 24-hour forecast made about 120 calls this week (5 trading days). "
                    "Roughly how many independent results does the week add?"
                ),
                options=(
                    "About 120, one per call",
                    "About 5, roughly one per trading day",
                    "About 24, one per hour of the day",
                ),
                correct_index=1,
                explanation=(
                    "Each call covers the next 24 hours, so calls made within the same day "
                    "share almost all their market time. Counted honestly, that is about one "
                    "independent result per trading day."
                ),
            ),
            QuizQuestion(
                prompt="A forecast is right on 7 of 8 independent windows. What can you conclude?",
                options=(
                    "It has a strong edge",
                    "It is overfitted",
                    "Nothing yet: below 30 independent results no verdict is possible",
                ),
                correct_index=2,
                explanation=(
                    "Streaks like that happen by luck all the time. Below 30 independent "
                    "results the app shows no win rate at all, only progress toward a first "
                    "verdict."
                ),
            ),
            QuizQuestion(
                prompt=(
                    "Win rate 59.5% on 79 independent windows, 95% range 48.5% to 69.6%, "
                    "breakeven 51.77%. Is the edge proven?"
                ),
                options=(
                    "No, the range still includes breakeven, so it can't be told apart from"
                    " a model that only covers its costs",
                    "Yes, 59.5% is above 51.77%",
                    "Yes, because 79 is more than 30",
                ),
                correct_index=0,
                explanation=(
                    "Thirty is the minimum before any verdict, not proof. The range of "
                    "plausible true win rates still reaches below breakeven, so the honest "
                    "verdict is 'not yet distinguishable'."
                ),
            ),
        ),
        body_md="""
A win rate is the most persuasive number in trading and one of the easiest
to get wrong. Three problems, and how the mentor deals with each.

---

## Problem 1: one market day counted 24 times

The 24-hour forecast is made **every hour**, and each one asks where price
will be 24 hours later. The 09:00 call covers 09:00 to 09:00 the next day.
The 10:00 call covers 10:00 to 10:00. They share **23 of their 24 hours**.

So if EUR/USD rallies 80 pips on Tuesday, every "down" call made on Monday
is wrong *together*. Counting them as 20 separate failures counts one
market event 20 times.

**A real example (July 2026).** The Loop page once showed the model's
recent win rate at **11%**. It looked like a collapse. In fact it was a
single short stance losing to a two-day EUR/USD rally, counted about 18
times. Counted honestly, as one stance and one result, the win rate over
the same stretch was **56%**: coin-flip territory, neither a collapse nor
genius.

**The fix: independent windows.** Starting from the newest call and
walking back, the system keeps a call only if its 24-hour window ends
before the previously kept call began. Every kept result covers its own
stretch of market time, which works out at roughly **one independent
result per trading day** on the 24-hour forecast and fewer on the 5-day
one. The same rule is used everywhere a result is counted: the headline
win rate, the drift watch, live recalibration, the strategy lab's trades,
and the move-size estimate behind the breakeven.

## Problem 2: a small sample says nothing

Five right out of five sounds like a great model. But a fair coin lands
heads five times in a row about **once in every 32 tries**. Production hit
exactly this once: after collapsing the overlap, the sample fell to five
results, all correct, and the old verdict announced a real edge.

So there is now a **30-result floor**. Below 30 independent results
nothing is ever called significant, whatever it looks like, and the Loop
page shows "—" with "N / 30 toward a first verdict" instead of a win rate.
(It once printed "25%" from just four windows on the 5-day forecast, which
read as a crisis and meant nothing.)

And 30 is a floor, not proof. Every win rate also comes with a **95%
range**: the band where the true win rate plausibly sits, given how many
results there are. A thin edge needs far more than 30 results before that
band lifts clear of breakeven.

**Mid-October 2026, the 24-hour forecast:** 79 independent windows, 59.5%
right. The 95% range is **48.5% to 69.6%**. That range still includes the
51.77% breakeven, so the honest verdict is *"not yet distinguishable from
breakeven."* At this rate it needs about **161** independent windows to
tell, which is several more months of trading days.

## Problem 3: a falling win rate is often the truth emerging

Early numbers are noisy, and big early numbers tend to drift back toward
the true rate as results pile up. Statisticians call this **regression to
the mean**.

In August the owner noticed the win rate had "dropped" and asked for an
investigation. It was traced end to end: every graded result was correct,
the new price feed had introduced no errors, and there was **no bug**. The
24-hour independent win rate had simply moved from **56% on 9 results to
48% on 27**, toward the roughly 50% you would expect if there is no edge.
The earlier, happier number was the misleading one.

It works in reverse too. In October, after fixing which price bar each
call is graded against (lesson 6), the 24-hour win rate on the *same* 79
windows went from 53.2% to 59.5%. That is not new skill. It is the same
calls, graded correctly, and the range still includes breakeven.

### What this means for you

- Read the **independent** win rate, next to the **breakeven**, and read
  the verdict sentence under it. That sentence is the result; the
  percentage alone is not.
- A drop is not automatically a problem, and a rise is not automatically
  an edge. Ask two questions: how many independent results, and does the
  range clear breakeven?
- The raw signal count and equity curve sit in a collapsed "not a track
  record" section on the Loop page. An equity curve of overlapping signals
  is the most persuasive and least informative chart in trading.
- Apply it to yourself: your last eight trades tell you almost nothing
  about your edge.
""".strip(),
    ),
    Lesson(
        slug="keeping-honest/new-data-sources",
        module_id="keeping-honest",
        order_in_module=4,
        title="New data: a better price feed, and who is positioned where",
        summary=(
            "Twelve Data now supplies prices with Yahoo as backup, and the weekly COT report adds "
            "a genuinely different clue, dated the day it was published."
        ),
        est_minutes=7,
        key_concepts=(
            "Twelve Data",
            "failover",
            "COT report",
            "speculative positioning",
            "publication lag",
            "lookahead bias",
        ),
        figures=(
            Figure(
                key="cot-publication-lag",
                caption=(
                    "COT describes Tuesday's positions but is published on Friday. The model "
                    "may only use it from Saturday on."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "A COT report shows large speculators' positions as of Tuesday. From when "
                    "may a model use it?"
                ),
                options=(
                    "From Tuesday, the date it describes",
                    "From Friday morning",
                    "From Saturday, after it has actually been published",
                ),
                correct_index=2,
                explanation=(
                    "It is released Friday afternoon New York time. Using it any earlier would "
                    "let a backtest see information nobody had yet, which is lookahead bias."
                ),
            ),
            QuizQuestion(
                prompt="Twelve Data returns an error at 14:02. What happens?",
                options=(
                    "The system asks Yahoo instead and carries on as normal",
                    "The hour's prediction fails",
                    "Everything waits until Twelve Data recovers",
                ),
                correct_index=0,
                explanation=(
                    "The price feed is a failover chain. If the first source errors or "
                    "returns nothing, the next one answers, and nothing downstream needs to "
                    "know which source it was."
                ),
            ),
        ),
        body_md="""
Two changes to what the system reads, one about reliability and one about
looking at the market from a genuinely different angle.

---

## Prices: Twelve Data first, Yahoo as backup

Since mid-July 2026 **Twelve Data** has been the primary source of
EUR/USD hourly and daily bars, with **Yahoo Finance** as the backup. The
mechanism is called **failover**: the system asks the first source, and if
it errors or returns nothing, it asks the next. The rest of the system
never needs to know which one answered.

Why Twelve Data first: it delivers bars stamped cleanly on the hour.
Yahoo labels its live hourly bar with the time of the last trade, such as
10:29:05, which once put 275 phantom rows between real hours (lesson 6
tells that story).

An honest caveat: the older years of daily history come from Yahoo, whose
definition of where a "day" starts differs slightly from Twelve Data's.
The daily series is therefore a mix of two conventions. It is known,
flagged, and waiting on a deliberate decision rather than a quiet patch.

## COT: who is positioned where

Every week the US futures regulator, the **CFTC**, publishes the
**Commitments of Traders** report: how different groups of traders are
positioned in futures markets, including euro futures. The interesting
group is **large speculators** (hedge funds and other big directional
traders).

The mentor turns it into two clues:

- **How crowded**: speculators' net position as a share of all open
  contracts.
- **How it shifted**: the change from last week.

Why bother? Every other input the model has is some version of price, or
something that is already priced in: indicators, rates, the dollar index.
COT is different in kind. It is *who holds what*, not *what price did*.
Trading folklore says extreme crowding tends to come before reversals,
because the crowd runs out of new buyers. Whether that helps predict
EUR/USD is exactly what the system tests.

## The lookahead trap, and how it is avoided

The report shows positions **as of Tuesday**, but it is not published
until **Friday at 3:30 pm New York time**. If you file it under Tuesday, a
backtest gets to use it on Wednesday, Thursday and Friday, when nobody
in the real world had it yet. The backtest looks great and live trading
disappoints. This is the classic COT mistake.

The mentor dates every report by its **publication**: Tuesday plus four
days, which is the Saturday after release. Neither the hourly nor the
daily model can peek at it on Friday. That costs a day of freshness on a
signal that only changes weekly; safety is the cheaper side of the trade.
A test proves the value is invisible the day before it is released.

## What it found, honestly

The system loaded **1,448 weeks** of history, back to 1986. When the first
model was trained with COT, the measured importance of the positioning
clues came out at **0.00000**: on the evidence so far, positioning does
not help predict EUR/USD direction. That is an honest and fairly expected
result. The clues stay wired in, and the promotion gate re-judges them on
every retrain, so if they ever start to help in some market regime the
system can find out. If the CFTC site is unreachable, the clue is simply
missing that day; nothing else stops.

### What this means for you

- If a price differs from your broker's by a fraction of a pip, that is
  normal: feeds differ slightly.
- If you read COT positioning on a charting site, remember it is already
  three days old the moment it is published.
- Any backtest that uses data with a publication delay (economic
  releases, COT, company results) must date it by **release**, not by the
  period it describes.
""".strip(),
    ),
    Lesson(
        slug="keeping-honest/learning-from-live-mistakes",
        module_id="keeping-honest",
        order_in_module=5,
        title="Learning from its own live mistakes",
        summary=(
            "How the champion's real results correct how sure it sounds, how challengers are "
            "judged fairly, and when a champion loses its job."
        ),
        est_minutes=8,
        key_concepts=(
            "live recalibration",
            "overconfidence",
            "held-out check",
            "champion and challenger",
            "demotion",
        ),
        figures=(
            Figure(
                key="live-recalibration",
                caption=(
                    "If live results show '62%' calls landing nearer 55%, the correction pulls "
                    "stated confidence toward 50/50. It never pushes a call past it."
                ),
            ),
            Figure(
                key="champion-lifecycle",
                caption=(
                    "Challengers race the champion on the same fresh data. Three failed "
                    "re-checks in a row and the baseline rule takes over."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "Over 40 independent live results, the champion's 65% calls were right "
                    "about 55% of the time. What can live recalibration do?"
                ),
                options=(
                    "Pull its stated confidence toward 50%, if that holds up on the newer half",
                    "Flip some of its calls to the other direction",
                    "Retrain the model's features on those 40 results",
                ),
                correct_index=0,
                explanation=(
                    "The correction only stretches or shrinks the distance from 50/50, and it "
                    "ships only if it improves the score on results it was not fitted on. "
                    "Forty results are far too few to re-decide features."
                ),
            ),
            QuizQuestion(
                prompt=(
                    "The champion fails its re-check on one retrain, passes the next, then "
                    "fails again. Is it demoted?"
                ),
                options=(
                    "Yes, two failures are enough",
                    "No: it takes three failures in a row, and a pass resets the count",
                    "Yes, any failure demotes it",
                ),
                correct_index=1,
                explanation=(
                    "One rough week shouldn't dethrone a model, so a single pass resets the "
                    "count. Only three consecutive failures hand the job to the baseline rule."
                ),
            ),
            QuizQuestion(
                prompt=(
                    "Why is the challenger compared with the champion re-scored on the same "
                    "fresh data, rather than with the champion's old stored score?"
                ),
                options=(
                    "It saves computing time",
                    "Old scores are deleted after a week",
                    "Some market periods are easier to predict than others; only the same "
                    "data makes it a fair race",
                ),
                correct_index=2,
                explanation=(
                    "A score earned in a calm period isn't comparable with one earned in a "
                    "wild period. Re-scoring both models on the same window removes that "
                    "unfairness."
                ),
            ),
        ),
        body_md="""
The lesson *"The system that grades itself"* described the basic loop:
predict, wait, grade, retrain, keep the better model. Since then the live
results do more than trigger retrains. Three pieces.

---

## Part 1: correcting how sure it sounds

The model's "60% up" was learned from history. Live trading is a later,
different market. If, over its live record, the model's 60% calls have
really been landing 53% of the time, the honest thing is to *say* 53%.

**Why only confidence, and nothing else?** The live record grows by
roughly one independent result per trading day. Thirty results cannot
support re-deciding which clues matter; that would chase noise straight
into the model. They *can* support one number: how far to stretch or
shrink the model's distance from 50/50.

**How it works.** The correction is a single **stretch factor**:

- below 1: the model has been overconfident, so its calls are pulled
  toward 50%;
- exactly 1: leave it alone;
- above 1: it has been underconfident, so its calls are pushed outward.

50% always stays 50%, and a call can never change sides: a 55% "up" can
become 52% "up", never 48%. It corrects how sure the model sounds, not
what it thinks.

**The safety rules**, the same discipline as everywhere else:

1. Only **independent** live results of the **current champion** since it
   was promoted count. Calls made by the baseline rule are excluded.
2. **30-result floor.** Below 30, no correction is fitted at all.
3. **Choose on one half, check on the other.** The stretch is chosen on
   the older half of the record and checked on the newer half, in time
   order.
4. **It must clearly help.** It ships only if it improves the Brier score
   on the newer half by at least 0.002. "No correction" wins every tie.
5. **It looks rarely.** The check runs once per retrain, not every hour,
   because repeated peeking is another way to fool yourself.

**An example.** Say there are 40 independent live results. On the older
20, calls the model gave around 62% were landing nearer 55%. The best
stretch for those is 0.6, which turns 62% into about 57%. Then comes the
real test: on the newer 20, does 57% score better than 62% by at least
0.002? Only if it does is the correction applied.

**Where it stands (mid-October 2026):** the 24-hour champion has 7 of the
30 results it needs, so its first check is expected around late November.
One honest limitation: the correction belongs to one champion. If
champions were replaced every week or two, none would ever reach 30 and the
correction would never apply. That is deliberate: a new model starts on its
own calibration instead of inheriting another model's mistakes. The
model's original probability is always stored alongside, so corrections
never pile on top of each other.

---

## Part 2: champion and challenger, judged fairly

Each retrain (weekly, or early if the drift watch fires) produces
challengers. To take over, a challenger must clear the three floors from
lesson 1 and then **beat the champion by at least 0.002 Brier, with both
scored on the same fresh window**. The champion's old score, earned in a
different market period, doesn't count. Some periods are simply easier to
predict than others, and only the same data makes it a fair race.

A real decision from the weekly report: *"Challenger (technical) Brier
0.2624 did not beat champion 0.2372 (re-graded on the same fresh window)…
champion kept."* "Champion kept" is the most common outcome, and a healthy
one.

## Part 3: demotion after three strikes

The champion is re-checked against the floors at every retrain. If it
fails **three retrains in a row**, it loses the job and the transparent
**baseline rule** takes over until a model genuinely earns it. A single
pass resets the count, so one rough week can't dethrone anyone and the
crown doesn't flip back and forth. The weekly report shows each forecast's
current count of failed re-checks.

### What this means for you

- Over time the confidence numbers should become more *trustworthy*, not
  more exciting. When the correction does kick in, it will most likely
  pull calls toward 50%.
- "Champion kept" after a retrain is good news: nothing better turned up,
  and nothing worse was installed.
- When a forecast is run by the baseline rule, treat its calls as
  low-information.
""".strip(),
    ),
    Lesson(
        slug="keeping-honest/finished-bars",
        module_id="keeping-honest",
        order_in_module=6,
        title="Clean prices: storing and grading only finished bars",
        summary=(
            "For three months each hourly bar was saved minutes after it opened. What went wrong, "
            "how it was repaired, and why every call is now graded on its own finished bar."
        ),
        est_minutes=8,
        key_concepts=(
            "price bar",
            "forming vs finished",
            "data integrity",
            "revision log",
            "grading",
        ),
        figures=(
            Figure(
                key="forming-vs-finished",
                caption=(
                    "Saved eight minutes in, a bar holds a fraction of the hour's real range. "
                    "Now a bar is stored only once it has finished."
                ),
            ),
            Figure(
                key="grade-own-bar",
                caption=(
                    "The old grader used the bar before the horizon. Now a call waits for the "
                    "finished bar that contains its horizon."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt="The system saves the 14:00 hourly bar at 14:08. What's wrong with that?",
                options=(
                    "Nothing, as long as the open price is right",
                    "The timezone is wrong",
                    "It holds only 8 minutes of a 60-minute bar, so its high, low and close"
                    " are not final",
                ),
                correct_index=2,
                explanation=(
                    "A bar is only final when its period ends. Saved early, its high and low "
                    "miss most of the hour and its close is just the price at 14:08."
                ),
            ),
            QuizQuestion(
                prompt=(
                    "After the re-grade, the 24-hour win rate on the same 79 windows rose from "
                    "53.2% to 59.5%. What does that show?"
                ),
                options=(
                    "The model got better",
                    "The same calls were graded against the correct bars: a measurement fix, "
                    "not new skill",
                    "The re-grade was rigged",
                ),
                correct_index=1,
                explanation=(
                    "No forecast changed, only the price each one was checked against. The "
                    "range of plausible win rates still includes breakeven, so nothing is "
                    "proven either way."
                ),
            ),
        ),
        body_md="""
This lesson is about a bug, told plainly, because how a system handles its
own mistakes says more about it than any feature does.

---

## What a bar is

An hourly **bar** (or candle) records four prices for one hour: open,
high, low and close. It is only final when the hour is over. Until then it
is still **forming**: the high and low can still stretch, and the close is
just the latest price.

## What went wrong

From mid-July to 13 October 2026 the system fetched each bar a few minutes
after it opened, saved it, and never updated it. The database was told to
ignore any later version of a row it already had, so the finished bar
fetched an hour later was thrown away.

The audit on 13 October found:

- **2,310 hourly bars** (every one since 16 July) and **86 daily bars**
  had been saved before they finished, most within ten minutes of opening;
- the typical saved hourly bar held only **23%** of the hour's real
  high-to-low range;
- **774** saved bars were more than 5 pips off; the worst, 16 September at
  18:00, had a close **66.5 pips** wrong;
- **275** extra rows from Yahoo were stamped between hours (10:29:05) and
  didn't belong at all.

What that touched, honestly: models trained since July learned partly from
these bars, backtests of recent months saw prices that never closed, and
grading used them.

## How it was fixed

1. **Only finished bars are stored**, stamped exactly on the hour. The
   fetch now runs two minutes after each hour (and at 00:02 UTC for daily
   bars).
2. **A bar saved too early is "provisional"**, and the next fetch replaces
   it with the finished version. A finished bar is never overwritten:
   feeds quietly revise by fractions of a pip, and history that shifts every
   time you read it is history nothing can be tested against.
3. **Every correction is logged** with the old values, and any batch can be
   undone with one command. The production repair (approved by the owner)
   corrected 1,796 hourly bars, removed the 275 misplaced rows, and
   corrected 26 daily bars.

A sign the repair worked: one hour's close and the next hour's open should
be nearly the same price. The average gap between them since July fell
from **3.65 pips to 0.40 pips**.

What was **not** rewritten: each prediction keeps the price it was made
from. That is the record of what the model actually saw at the time.

## Grading each call on its own finished bar

A second bug surfaced the same day. The grader, which runs every 15
minutes, used the nearest *earlier* bar whenever the bar at the call's
horizon wasn't stored yet. So **2,134 of 2,229** hourly calls and **105 of
106** daily calls were graded one bar early, on a bar that was itself only
a few minutes old.

Now a call is graded on the **finished bar that contains its horizon** (or
the first bar after it, if the market was closed), and it waits until that
bar has finished. With the owner's approval, past calls were re-graded the
same way, reversibly: only the outcome price and the up/down result
changed, never the forecast, its probability, or which calls exist.

The effect on the 24-hour forecast: the independent win rate on the same
79 windows moved from **53.2% to 59.5%**. Two cautions. It is the same
calls graded correctly, not new evidence of skill. And the range of
plausible win rates still includes breakeven, so nothing is proven.

A related false alarm was fixed too. The report used to flag a call as
overdue the minute its horizon passed, though its bar can't exist until an
hour later. Now a call only counts as late once its bar should have
finished, been fetched and been graded.

### What this means for you

- Charts covering July to October now show the corrected prices.
- The next retrain learns from the corrected data automatically.
- A rule for any data you use: a candle isn't real until it has closed.
  Indicators calculated on a forming candle change ("repaint") as the
  candle grows.
""".strip(),
    ),
)

_HONEST_LAB = (
    Lesson(
        slug="keeping-honest/strategy-lab-testing",
        module_id="keeping-honest",
        order_in_module=7,
        title="The strategy lab: testing a trading plan properly",
        summary=(
            "A trading idea becomes a complete plan, then gets tested the way a careful trader "
            "would: walk-forward, after costs, with an untouched final exam."
        ),
        est_minutes=9,
        key_concepts=(
            "trading plan",
            "walk-forward testing",
            "held-out period",
            "R-multiple",
            "transaction costs",
        ),
        figures=(
            Figure(
                key="plan-anatomy",
                caption=(
                    "A plan the lab can test answers six questions: why, entry, stop, target, "
                    "time limit and size."
                ),
            ),
            Figure(
                key="walk-forward-holdout",
                caption=(
                    "Choose settings on the past, trade the next block, repeat. The held-out "
                    "stretch at the end is used exactly once."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "Why does the lab choose each block's settings using only the blocks before it?"
                ),
                options=(
                    "It runs faster",
                    "That is the only choice a trader could have made at the time; using later "
                    "data would be peeking at the future",
                    "Older data is more accurate",
                ),
                correct_index=1,
                explanation=(
                    "Walk-forward testing replays history the way it was lived: decide with "
                    "what you knew, then trade what came next."
                ),
            ),
            QuizQuestion(
                prompt=(
                    "A plan averaged +0.3R per trade in development but lost money on the "
                    "held-out period. Does it pass?"
                ),
                options=(
                    "No: the held-out period must be positive on its own, with at least 10 trades",
                    "Yes, its development average is positive",
                    "Yes, as long as it has 30 trades in total",
                ),
                correct_index=0,
                explanation=(
                    "The held-out period is the final exam. A plan that shines in development "
                    "and fails the exam is the textbook sign of a setting fitted to the past."
                ),
            ),
        ),
        body_md="""
A forecast answers one question: *which way?* Trading needs several more:
when do I get in, where am I wrong, where do I take profit, how long do I
give it, and how much do I risk? The **strategy lab** (added in October
2026, on the **Lab** tab) tests complete trading plans that answer all of
them, the way a careful professional would.

---

## A plan is six answers

1. **Why might this work?** A plain-language reason, economic or
   behavioural. An idea that can't state its own reason is usually a
   pattern found by staring at noise.
2. **Entry**, for example "buy when the day closes above the highest high
   of the last 20 days".
3. **Stop**, either a multiple of the average daily range (ATR) or a
   structural level such as the far side of a range.
4. **Target**, as an R-multiple (2R means twice the distance risked).
5. **Time limit**: get out after so many bars if neither stop nor target
   is hit.
6. **Size**, from the app's own risk engine, never more than 2% of the
   account per trade.

Results are measured in **R** (profit or loss divided by the amount
risked), so they don't depend on account size.

**Example hypothesis** (the "buy the dip in a trend" idea): *"Inside an
established trend, a sharp few-day move against it is often just
profit-taking. Entering on that dip gets a better price than chasing, and
the trend is the reason to expect a recovery."*

## Realistic fills, real costs

The lab's simulator is deliberately unkind:

- a signal at a bar's close is filled at the **next bar's open**, made
  worse by half the spread plus slippage;
- if the market opens beyond the stop or target, the order is cancelled
  (a trader doesn't chase);
- if one bar touches both the stop and the target, it assumes the **stop**
  was hit first;
- a gap through the stop fills at the open, which is worse than the stop;
- costs are the same 1.2 pips per round trip the rest of the app charges;
- only one position at a time, so trades never overlap.

Because costs are already inside every R figure, a plan's breakeven is
simply **0R** per trade. The **same simulator** later runs paper trading,
so a paper record is the tested plan meeting the future, not a lookalike.

## Walk-forward: choosing settings the way a real trader would

Each idea comes with a handful of settings to try (a 20-day channel or a
55-day one, a 2R target or 3R). The cheating way to test is to run every
setting over all of history and report the best. That only proves the
best setting fitted the past.

The lab instead cuts the development history into **five blocks**. For
blocks 2 to 5 in turn, it picks the setting using **only the earlier
blocks**, then trades that setting through the next block. Trades used to
choose a setting must have closed before the test block starts. If no
setting made money in the earlier blocks, the plan doesn't trade the next
one at all, because a trader wouldn't run a plan that just lost in
testing. A setting also needs at least 10 trades before it can be chosen.

## The final exam: an untouched held-out period

Everything from **1 January 2024** (for daily ideas) and **1 April 2026**
(for hourly ideas) is held back. The dates are fixed in the code, so
nobody can slide them around until a plan looks good. The held-out stretch
is used **once**: the setting is chosen on all development data, then
traded through it.

## What it takes to pass

All out-of-sample trades (the walk-forward blocks plus the held-out
period) are pooled, and every one of these must hold:

- at least **30** trades that don't overlap in time;
- an average R whose **95% range sits above zero**;
- a score above **today's bar**, which rises with every idea ever tried
  (the next lesson);
- the held-out period **on its own**: at least 10 trades and a positive
  average.

### What this means for you

- Use the six questions for your own plan. Write the answers down before
  you place a trade.
- When someone shows you a backtest, ask four things: was it walk-forward?
  Was there an untouched held-out period? Were costs included? How many
  settings were tried before this one?
""".strip(),
    ),
    Lesson(
        slug="keeping-honest/the-rising-bar",
        module_id="keeping-honest",
        order_in_module=8,
        title="Why the bar rises with every idea tried",
        summary=(
            "Try enough ideas and one will look brilliant by luck. The lab counts every attempt, "
            "raises the bar to match, and makes survivors prove themselves on paper. First "
            "result: 8 ideas, all rejected."
        ),
        est_minutes=9,
        key_concepts=(
            "multiple testing",
            "deflated Sharpe ratio",
            "trial ledger",
            "paper trading",
            "promotion and retirement",
        ),
        figures=(
            Figure(
                key="rising-bar",
                caption=(
                    "The best score pure luck produces grows with the number of tries. The "
                    "lab's bar sits above it; the best idea so far sits far below."
                ),
            ),
            Figure(
                key="lab-lifecycle",
                caption=(
                    "Rejected ideas never trade. Survivors paper-trade, and earn "
                    "'recommended' only on a live record."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt="Why does the bar rise with every idea tested, even the ones that failed?",
                options=(
                    "To discourage people from testing ideas",
                    "More tries means a higher best score from luck alone, and forgetting "
                    "failures makes the survivors look special",
                    "Old ideas go stale",
                ),
                correct_index=1,
                explanation=(
                    "If 74 settings have been tried, the best of them would look good even "
                    "if none had an edge. Counting every try is what keeps the winner honest."
                ),
            ),
            QuizQuestion(
                prompt=(
                    "'Buy the dip in a trend' averaged +0.17R on its held-out trades. Why was it "
                    "still rejected?"
                ),
                options=(
                    "Its held-out result was negative",
                    "It had fewer than 10 trades",
                    "Its overall score (about 1.0) was far below the bar (about 4.4) set by"
                    " 74 trials",
                ),
                correct_index=2,
                explanation=(
                    "A small positive average is exactly what luck produces when you try many "
                    "things. Against a bar adjusted for 74 trials, it is nowhere near proven."
                ),
            ),
            QuizQuestion(
                prompt="Why does paper trading only consider promotion every 30 trades?",
                options=(
                    "Checking after every trade and stopping at the first pass would find "
                    "edges in pure noise",
                    "To save database space",
                    "The broker only reports every 30 trades",
                ),
                correct_index=0,
                explanation=(
                    "Each look is another chance for luck to cross the line. Rationing the "
                    "looks, and counting every one of them, keeps the bar meaningful."
                ),
            ),
        ),
        body_md="""
## The problem: luck scales with tries

Ask 20 people to flip a coin ten times and someone will get eight heads.
That person isn't skilled; there were just 20 of them. Testing trading
ideas works the same way. Try 74 settings on the same history and the best
one will look good **even if none of them has any edge**.

This isn't a risk to manage. With enough tries it is a certainty, and it
has to be corrected for. Statisticians call it the **multiple-testing
problem**.

## The fix: count every try, and raise the bar to match

**The trial ledger.** Every setting the lab has ever tested is written to
an append-only ledger, whether it was chosen or not and whether it passed
or not. Nothing is ever deleted from it. Quietly forgetting the failures is
the classic way to make a survivor look special.

**The score.** Each idea gets a score: its average R, divided by how much
its results vary, times the square root of the number of trades. Roughly,
it measures how far above zero the average sits compared with the noise.
For a single test, a score around 2 is the usual line for "probably not
luck".

**The bar.** Across many tries, the *best* score pure luck produces climbs:
about **2.4 for 70 tries** and about **3.0 for 500**. The lab computes that
expected best-of-luck score for every trial ever recorded, raises it
further when the trials disagree with each other more than noise would,
and then adds the app's usual 95% safety margin. This is the **deflated
Sharpe ratio** (Bailey and López de Prado, 2014). In mid-October 2026,
with **74 trials** in the ledger, the bar stood at about **4.4**.

One more safeguard: lopsided results, such as a few huge winners, are only
ever allowed to make the bar *harder*, never easier.

## The honest first result: 8 ideas, 8 rejections

The starter library has eight well-known ideas, 74 settings in all. Every
one was rejected:

- **Channel breakout (turtle style), daily:** lost 0.32R per trade on
  average over 31 out-of-sample trades.
- **Time-series momentum, daily:** +0.02R over 112 trades, then −0.04R on
  the held-out period.
- **Buy the dip in a trend, daily:** the best of the eight. +0.08R over 135
  trades and +0.17R on 41 held-out trades. Score about **1.0** against a bar
  of about **4.4**: promising-looking, nowhere near proven.
- **Volatility squeeze breakout, daily:** only 5 trades in total,
  averaging −0.59R.
- **Narrow-range breakout (NR4/NR7), daily:** −0.58R per trade.
- **Moving-average crossover with a trend filter, daily:** no setting made
  money in development, so it never traded out of sample.
- **Range fade, hourly:** −0.07R over 88 trades.
- **London-open breakout, hourly:** −0.06R over 206 trades. Every setting
  lost in development, so the held-out period was, by design, never traded.

That is good news about the lab, not bad news. These are popular,
widely taught ideas, and watching them fail an honest test after costs is
genuinely valuable. A lab that "found" an edge in half of them would be the
one to distrust.

## If an idea ever passes: paper trading

Passing the back-test earns an idea the right to be **watched**, nothing
more. It then paper-trades the live market every hour with the same
simulator, and nothing ever reaches a broker.

- **Recommended** only at checkpoints, every **30 independent paper
  trades**, and only if the average R's 95% range is above zero and the
  score beats a bar that counts every live look by every paper strategy.
- **Why checkpoints?** Re-testing after every trade and stopping at the
  first pass is a reliable way to find an edge in noise.
- **Demoted** if a checkpoint no longer clears the bar, or if its trades
  since promotion average zero R or worse. It keeps paper trading and can
  earn the label back later.
- **Retired** if its live record is significantly negative.

## Who may add ideas

The maintenance agent may add **at most one idea a week**, with at most 8
settings, a new permanent name and a plain-language reason. It may never
edit an idea that has already been tested, and never resubmit a rejected
idea with tweaked settings under a new name, because that is a search for
a lucky setting disguised as a new idea. Every new idea raises the bar for
every idea after it, which is exactly why ideas are added sparingly.

### What this means for you

- A **recommended** plan on the Lab page would be rare and earned live.
  Today there are none, and that is the honest state of things.
- For your own testing: if you have tried 30 indicator settings, your best
  one's backtest is inflated. Keep a written list of everything you tried,
  not just what worked.
""".strip(),
    ),
)

_HONEST_OPS = (
    Lesson(
        slug="keeping-honest/running-unattended",
        module_id="keeping-honest",
        order_in_module=9,
        title="Running unattended: reports, alerts and the maintenance agent",
        summary=(
            "How the system tells you what it has been doing, in plain words, and how an "
            "automated maintainer fixes its code one careful change at a time."
        ),
        est_minutes=8,
        key_concepts=(
            "self-report",
            "Telegram alerts",
            "maintenance agent",
            "fix day",
            "improve day",
        ),
        figures=(
            Figure(
                key="autonomy-loop",
                caption=(
                    "The app reports on itself, the agent reads the report and makes at most "
                    "one change, and the server decides whether that change ships."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt="It's Tuesday and the report is all green. What does the agent do?",
                options=(
                    "Looks for something to improve anyway",
                    "Retrains the models",
                    "Changes nothing and writes a log entry saying so: doing nothing is a "
                    "valid run",
                ),
                correct_index=2,
                explanation=(
                    "Tuesday is a fix day, and there is nothing to fix. Every change carries "
                    "risk, so an unnecessary one is a cost, not a contribution."
                ),
            ),
            QuizQuestion(
                prompt=(
                    "What does each problem in the self-report carry, so tomorrow's reader can "
                    "tell an old problem from a new one?"
                ),
                options=(
                    "A stable issue code",
                    "A random number",
                    "The time of day it was noticed",
                ),
                correct_index=0,
                explanation=(
                    "The same problem always gets the same code, so 'still broken since "
                    "Monday' and 'new today' can be told apart without guesswork."
                ),
            ),
        ),
        body_md="""
Trade Mentor is meant to run for months without anyone touching it. That
takes three layers:

1. **The app looks after its models**: it fetches prices, predicts,
   grades, retrains, promotes and demotes models, and corrects its own
   confidence (the earlier lessons in this module).
2. **A maintenance agent looks after the code.** That's this lesson.
3. **The server's safety net** decides whether any code change actually
   goes live. That's the next lesson.

---

## The self-report: the system's own weekly check-up

Every **Saturday at 06:00 UTC** the system writes a report on itself. A
live version is always available at the public address
`/api/v1/health/report`. It contains only summary numbers, never secrets.
It covers:

- **health checks**: is the price feed fresh, are predictions being graded,
  is retraining happening, is alerting set up?
- each forecast's **independent live record against its own breakeven**,
  with the plain verdict sentence;
- week-on-week accuracy, and what each retrain decided and why;
- progress toward the first live confidence correction;
- jobs that are failing and warnings that keep recurring;
- the strategy lab's status;
- what the server did with the latest code changes.

Every problem gets a **stable code**, so whoever reads it next, human or
agent, can tell "still broken since Monday" from "new today". The report
opens with a one-line headline; on a good week it reads *"Everything ran
and nothing needs attention."*

## Telegram alerts in plain words

You get a short Telegram summary of the weekly report, plus an alert
whenever something notable happens. In October 2026 every message was
rewritten in three parts:

1. a **headline** saying what happened;
2. a line or two of **why**, in everyday words;
3. a final 👉 line saying **what, if anything, you should do**.

Forecast alerts give the chance of the predicted direction, so a 31%
chance of "up" reads as a **69% chance of down**, with the horizon in hours
or trading days. No error scores, codes, commit numbers or file paths.

## The daily maintenance agent

A scheduled AI agent runs once a day at **06:30 UTC**. It reads the
report, its own log of past runs, and the code.

- **Fix days (Sunday to Friday):** it only fixes what the report says is
  broken, in priority order: failures first, then failing jobs and
  recurring errors, then warnings. If nothing is broken, it changes
  nothing.
- **Improve day (Saturday):** it may make **one** small, evidence-backed
  improvement, such as a test for untested code, a sturdier data
  connection, clearer wording, or a new *candidate* clue for the models
  (the promotion gate, not the agent, decides whether it is ever used). At
  most once a week, that improvement may be one new strategy-lab idea.

Its rules include:

- **one theme per run**, and every change must point at evidence: an issue
  in the report, a failing check, a test that exposes a bug. "Seemed
  cleaner" doesn't count;
- **all checks must pass** before it pushes anything, and no test may be
  skipped, deleted or watered down;
- **never** place trades or talk to a broker; never handle passwords or
  keys; never delete data;
- **never loosen an honesty threshold** (the next lesson explains why);
- if the server rolled back its last change, find out why and fix or
  revert it. **Never push the same change again.**
- **always write the log**: an entry in `ops/autonomy/LOG.md`, newest
  first, even when it changed nothing.

A real entry from 14 October: a fix day, report all green, so *"no code
change"*. It also noted that the 24-hour win rate's jump that morning came
from the re-grade (lesson 6), *"not new evidence of skill"*. That's the
tone it is held to.

### What this means for you

- Your weekly check can be one message: the Saturday summary. If its
  headline says nothing needs attention, nothing does.
- If an alert's 👉 line says no action is needed, you can believe it.
- To see what changed and why, read `ops/autonomy/LOG.md`.
""".strip(),
    ),
    Lesson(
        slug="keeping-honest/the-safety-net",
        module_id="keeping-honest",
        order_in_module=10,
        title="The safety net: auto-deploy, rollback and protected thresholds",
        summary=(
            "The server checks every change before and after it goes live, undoes bad ones by "
            "itself, and refuses any attempt to lower the honesty bars."
        ),
        est_minutes=8,
        key_concepts=(
            "auto-deploy",
            "rollback",
            "watchdog",
            "protected thresholds",
            "secrets in logs",
        ),
        figures=(
            Figure(
                key="deploy-gate",
                caption=(
                    "Every 10 minutes: refuse protected changes, back up, build, prove it "
                    "healthy, or roll back. You hear about it either way."
                ),
            ),
            Figure(
                key="protected-thresholds",
                caption=(
                    "The numbers only a human may change: the bars that stop the system "
                    "flattering itself. Two locks guard them."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt=(
                    "A change deploys, but the report page doesn't answer within five minutes. "
                    "What happens?"
                ),
                options=(
                    "The server rolls back to the previous version and tells you on Telegram",
                    "It stays live until someone notices",
                    "The server deletes the database and starts again",
                ),
                correct_index=0,
                explanation=(
                    "A new version has to prove itself healthy. If it can't, the server puts "
                    "the last good version back by itself and messages you."
                ),
            ),
            QuizQuestion(
                prompt=(
                    "The agent tries to lower the 30-result floor to 15 'to get verdicts "
                    "sooner'. What happens?"
                ),
                options=(
                    "It deploys like any other change",
                    "The server refuses it: it is a protected threshold, and lowering it would "
                    "let noise pass as proof",
                    "It deploys and is reviewed a week later",
                ),
                correct_index=1,
                explanation=(
                    "Lowering a bar makes the numbers look better without making anything "
                    "better. Only a human can change these, deliberately."
                ),
            ),
            QuizQuestion(
                prompt=(
                    "Why does the copy of the deploy program that actually runs live outside "
                    "the code repository?"
                ),
                options=(
                    "It runs faster there",
                    "GitHub doesn't allow it",
                    "So a bad change can't disable the very thing that undoes bad changes",
                ),
                correct_index=2,
                explanation=(
                    "If the safety net could be edited by the changes it guards against, one "
                    "bad push could switch it off. Keeping it outside the repository prevents "
                    "that."
                ),
            ),
        ),
        body_md="""
An automated maintainer is only safe if something it can't control checks
its work. That is the server's job.

---

## Auto-deploy, every 10 minutes

A program on the server checks for new code every 10 minutes. When it
finds some, it:

1. **Refuses** the change if it touches a protected file, changes a
   protected threshold, adds a skipped test, or deletes a test file.
2. **Backs up the database** first if the change alters its structure.
3. **Builds and starts** the new version.
4. **Demands proof of health**: the health page and the report page must
   answer within five minutes, and the logs must show no crash once
   startup has settled.
5. **Rolls back** to the previous version by itself if any of that fails.
6. **Tells you on Telegram** in every case, and records the outcome in the
   self-report so the agent learns what happened to its change (and is
   forbidden to push the same change again).

Between deploys it acts as a **watchdog**: if the app stops answering for
about 30 minutes (three checks in a row), it restarts it.

The copy of this program that actually runs is **installed outside the
code repository**, so a bad change can't disable the thing that undoes bad
changes. When a human deliberately wants to change something protected,
they run the deploy by hand on the server with an explicit override. The
automatic schedule never uses it.

## The protected thresholds, and why they're locked

These are the numbers that stop the system from flattering itself:

- the **promotion margin** (0.002) and the **coin-flip** and
  **breakeven** floors;
- the **15% coverage** floor and the **minimum-gain** rules;
- **demotion after 3** failed re-checks;
- the **30-result** verdict floor and the **95%** confidence level;
- the minimum number of windows needed to measure the breakeven;
- the **cost model**: 0.8-pip spread and 0.2-pip slippage;
- the **COT publication lag**;
- the strategy lab's walk-forward blocks, minimum trades, **held-out
  dates**, 30-trade checkpoints, and the code that applies its bar.

Why lock them? Tell an automated maintainer to "improve the numbers" and
sooner or later it will discover that lowering a bar improves them. Drop
the 30-result floor to 10, and a lucky streak gets announced as a proven
edge. Set the cost to zero, and the breakeven falls to 50%, so the 51%
model from lesson 1 suddenly "makes money". The dashboard looks better and
nothing is better.

So the thresholds have **two locks**: a test that fails if any of them
changes, and the server's tripwire that refuses any change that edits
them. Only a human can change them, deliberately.

## Keeping secrets out of the logs

A review of the live logs in October found the Twelve Data API key written
in plain text on every hourly price fetch, and the Telegram bot token on
every alert. Both services put the key in the web address, and the
networking library logged every address it called.

The fix had two parts. Routine per-request logging was turned down, and a
redaction filter now runs over everything that reaches a log, replacing
any key or token with `***`, including inside error messages. The agent's
rules forbid it from handling secrets or weakening that filter, and the
deploy program reads the Telegram credentials from the server's own
settings without ever printing them.

### What this means for you

- A **"rolled back"** message on Telegram means the safety net worked:
  the last good version is running.
- A **"refused"** message means a change tried to touch something only you
  may change.
- If you ever change a threshold yourself, ask one question first: does
  this make the system more honest, or just make its numbers look better?
""".strip(),
    ),
    Lesson(
        slug="keeping-honest/what-it-can-and-cannot-do",
        module_id="keeping-honest",
        order_in_module=11,
        title="What the mentor can and cannot do, honestly",
        summary=(
            "Its real strengths are measuring risk and refusing to fool itself. Its record on "
            "direction is unproven. How to use it accordingly."
        ),
        est_minutes=5,
        key_concepts=(
            "proven vs unproven",
            "volatility forecast",
            "honesty machinery",
            "decision support",
        ),
        figures=(
            Figure(
                key="honest-scorecard",
                caption=(
                    "Strong: risk sizing and honesty checks. Unproven: direction. Never "
                    "offered: guarantees or automatic trading."
                ),
            ),
        ),
        quiz=(
            QuizQuestion(
                prompt="Which part of the system stands on the firmest ground?",
                options=(
                    "The 24-hour direction call",
                    "The volatility forecast and risk sizing, plus the honesty checks",
                    "The strategy lab's recommended plans",
                ),
                correct_index=1,
                explanation=(
                    "How far price is likely to move is far more predictable than which way. "
                    "The direction record is still unproven, and the lab has recommended "
                    "nothing."
                ),
            ),
            QuizQuestion(
                prompt="The direction forecast says 62% up. How should you use it?",
                options=(
                    "Trade it at maximum size",
                    "Ignore everything else on the screen",
                    "As one input: size from your stop, and remember its record isn't proven",
                ),
                correct_index=2,
                explanation=(
                    "A probability is not a promise, and this one comes from a record that "
                    "can't yet be told apart from breakeven. The sizing from your stop is "
                    "the part you can rely on."
                ),
            ),
        ),
        body_md="""
After everything in this module, here is the plain summary.

---

## What it does well

- **Measuring risk.** How *far* EUR/USD is likely to move is genuinely
  more predictable than which *way*: calm tends to follow calm and storms
  follow storms. The volatility forecast sets the stop distance, which
  sets the position size and the expected move on the trade ticket, and it
  has been audited against what price actually did.
- **Refusing to fool itself.** The cost hurdle, independent windows, the
  30-result floor, held-out tests, the rising bar in the strategy lab, and
  thresholds that only a human can change. None of this makes money. It
  stops you losing money to self-deception, which is the most common way
  traders lose it.
- **The risk engine and the journal**, which size every trade from the
  stop and keep you honest about your own behaviour.

## What is not proven

- **Direction.** In mid-October 2026 the 24-hour champion's live record was
  79 independent windows with a plausible range that still includes
  breakeven; it needs about 161 to tell. The 5-day forecast has no trained
  model that has earned the job, so a simple baseline rule makes its calls.
- **Trading plans.** The strategy lab has tested 8 ideas and rejected all
  8. Nothing is recommended.
- **Positioning data.** COT has so far shown no measurable help.

## What it will never do

- Place a trade or connect to a broker. It advises; you act.
- Promise returns. "62% up" means *probably*, under the conditions it was
  measured in, never *certainly*.

### What this means for you

- Treat the direction forecast as **one input**, never the only reason for
  a trade. Treat **stand aside** as a good reason not to trade.
- **Size every trade from the stop** with the risk engine. That is the part
  on the firmest ground.
- Read the **verdict sentences**, not single numbers, in the weekly report
  and on the Loop page.
- If a forecast's verdict ever says it is **distinguishable from
  breakeven** after well over a hundred independent windows, that will be
  real news. Until then, treat its direction as unproven.
""".strip(),
    ),
)


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
        lessons=_RISK_FIRST + _RISK_FIRST_EXT,
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
        lessons=_PSYCHOLOGY + _PSYCHOLOGY_EXT + _PSYCHOLOGY_EXT2,
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
        lessons=_UNDER_THE_HOOD + _UNDER_THE_HOOD_EXT + _UNDER_THE_HOOD_EXT2,
    ),
    Module(
        id="keeping-honest",
        order=18,
        title="How the mentor keeps itself honest",
        summary=(
            "Everything added since July 2026: the cost hurdle, honest win rates, clean prices, "
            "the strategy lab, and how the system runs and repairs itself unattended."
        ),
        lessons=_HONEST_EVIDENCE + _HONEST_LAB + _HONEST_OPS,
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
