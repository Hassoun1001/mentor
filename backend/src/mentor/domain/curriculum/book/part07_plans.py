"""Stage 7 — Trading plans. Every plan uses the same headings."""

from __future__ import annotations

from mentor.domain.curriculum.book._kit import (
    Bar,
    Chart,
    Evidence,
    Figure,
    HLine,
    Lesson,
    Mark,
    Q,
    QuizQuestion,
    Series,
    Verdict,
    Zone,
    candle_chart,
    chapter,
    fact,
)
from mentor.domain.curriculum.charts import bollinger, equity_paths, path, sma


def _plan(
    *,
    slug: str,
    title: str,
    summary: str,
    minutes: int,
    concepts: tuple[str, ...],
    goal: str,
    idea: str,
    suits: str,
    entry: str,
    stop: str,
    target: str,
    sizing: str,
    fails: str,
    steps: tuple[str, ...],
    example: str,
    mistakes: tuple[str, ...],
    verdict: Verdict,
    evidence: str,
    try_it: str,
    quiz: tuple[QuizQuestion, ...],
    takeaways: tuple[str, ...],
    charts: tuple[Chart, ...],
    sources: tuple[str, ...] = (),
) -> Lesson:
    """A trading-plan lesson. The headings are fixed so all plans can be compared."""
    body = (
        f"{idea.strip()}\n\n"
        f"### Who it suits\n\n{suits.strip()}\n\n"
        "### The rules\n\n"
        f"- **Entry:** {entry.strip()}\n"
        f"- **Stop:** {stop.strip()}\n"
        f"- **Target:** {target.strip()}\n"
        f"- **Sizing:** {sizing.strip()}\n\n"
        f"### When it fails\n\n{fails.strip()}"
    )
    return Lesson(
        slug=slug,
        title=title,
        summary=summary,
        est_minutes=minutes,
        key_concepts=concepts,
        goal=goal,
        body_md=body,
        steps=steps,
        example_md=example.strip(),
        mistakes=mistakes,
        evidence=Evidence(verdict, evidence.strip()),
        try_it=try_it,
        quiz=quiz,
        takeaways=takeaways,
        charts=charts,
        sources=sources,
    )


_SIZING = "Risk a fixed small share of the account (for example 0.5–1%). Size = risk amount ÷ stop distance."


_THE_PLAN = Lesson(
    slug="becoming-pro/the-trading-plan",
    title="The written trading plan",
    summary="If it is not written down, it is a mood. Five layers, built from the bottom up.",
    est_minutes=9,
    key_concepts=("trading plan", "setup", "entry criteria", "exit rules", "review"),
    figures=(Figure("plan-pyramid", "A plan has risk at the base and review at the top."),),
    goal="Write a complete trading plan, simple enough that someone else could follow it.",
    body_md="""
Ask a funded professional for their trading plan and they will show you a document. Ask a struggling beginner and they will describe a feeling. The plan has five layers, **built from the bottom up**.

1. **Risk rules (the base).** Maximum risk per trade, for example 1%. Maximum loss per day, for example 3%, after which you stop. Maximum open risk. These rules keep you trading next month.
2. **Market and schedule.** What you trade and when. One market is plenty to start. Scattering across ten markets is how beginners avoid getting good at any.
3. **Setups.** The two or three specific situations you are allowed to trade, written precisely enough for a stranger to follow. "Looks bullish" is not a setup. "Price above the 200 EMA, pullback to support, stop under the swing low" is.
4. **Execution rules.** Stop and target placed with the entry. No adding to losers. No moving stops away from price.
5. **Review.** A journal entry after every trade, and a review every week. This layer is what makes the other four improve.

### The test

Could you give this plan to a friend, and have them take your next ten trades without asking you anything? If not, it is still a mood.

In this app, the **Trade plan** page covers layers 1 to 4, the pre-trade **checklist** is layer 4, and the **Journal** with its weekly review is layer 5.
""".strip(),
    charts=(
        Chart(
            title="A sample plan's layers",
            caption="Illustrative weighting of how much of a plan is about each layer. The risk layers are what let you keep trading long enough to learn.",
            data_kind="illustrative",
            kind="bars",
            y_format="pct",
            y_label="Share of your plan",
            bars=(
                Bar("Risk rules", 35, "danger"),
                Bar("Setups", 25, "accent"),
                Bar("Execution", 15, "accent"),
                Bar("Review", 15, "accentSoft"),
                Bar("Market and schedule", 10, "muted"),
            ),
        ),
    ),
    steps=(
        "Write your risk rules first.",
        "Choose one market and your trading hours.",
        "Write one setup precisely.",
        "Write execution rules, including when you will not trade.",
        "Schedule a weekly review, and do it.",
    ),
    example_md="""
A short but real plan:

- **Risk:** 0.75% per trade, 2% daily loss, 2.25% open risk.
- **Market:** EUR/USD only, 16:00–20:00 Dubai time.
- **Setup:** daily uptrend, pullback to prior resistance on 1H, bullish rejection candle.
- **Execution:** stop below rejection low (at least 1× ATR(14) from entry), target 2R, no entries 30 minutes either side of a major release.
- **Review:** journal after each trade, weekly review on Sunday.

Now ask a friend to read it and tell you what is unclear.
""".strip(),
    mistakes=(
        "Starting with the strategy and leaving risk until later.",
        "Writing a plan that sounds impressive but is too vague to follow.",
        "Changing the plan after every loss.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
A written plan is standard professional practice, and regulators and educators recommend it. We know of no strong controlled study that isolates the effect of a written plan on returns. Its main value is behavioural: it is harder to break a rule you wrote down.

A plan cannot rescue a strategy with no edge. It just makes the results measurable.
""".strip(),
    ),
    try_it="Write a one-page plan using the five layers. Hand it to someone and ask them to explain back what you would do.",
    quiz=(
        Q(
            "What belongs at the BASE of a trading plan?",
            (
                "The entry signals and chart patterns",
                "Risk rules: max loss per trade, per day, per week",
                "Profit targets for the month",
            ),
            1,
            "Setups change. Survival rules do not.",
        ),
        Q(
            "How do you know a setup is written well enough?",
            (
                "It sounds smart",
                "A stranger could follow it without asking questions",
                "It has many indicators",
            ),
            1,
            "A clear rule leaves no room for mood.",
        ),
    ),
    takeaways=(
        "Write the plan down, starting with risk.",
        "A good setup is exact enough for a stranger to follow.",
        "Review makes the plan improve.",
    ),
)

_STYLE = Lesson(
    slug="plans/choosing-a-style",
    title="Choosing a style that fits your life",
    summary="Your job, your temperament and your time matter as much as the method.",
    est_minutes=7,
    key_concepts=("style", "timeframe", "temperament", "time commitment"),
    goal="Pick a trading style that fits your life, not one that looks exciting.",
    body_md="""
There is no best style. There is a style you can actually follow. Consider four things.

- **Time:** how many hours a day can you really be at a screen?
- **Temperament:** can you sit through long losing streaks? Can you bear long, boring holds?
- **Capital:** smaller accounts cannot size many trades properly and costs bite harder.
- **Costs:** the shorter your timeframe, the larger your costs relative to your target.

| Style | Holds for | Screen time | Costs vs. target |
|---|---|---|---|
| Scalping | Seconds to minutes | Very high | Very high |
| Day | Minutes to hours | High | High |
| Swing | Days to weeks | Low to medium | Medium |
| Position | Weeks to months | Low | Low |

For someone with a full-time job, **swing** or **position** trading is usually the realistic choice. It also tends to be the most forgiving for a beginner because decisions can be made calmly.
""".strip(),
    charts=(
        Chart(
            title="Costs as a share of a typical target",
            caption="Calculated with a 1-pip round-trip cost. Assumed targets: scalp 5 pips, day trade 25, swing 100, position 300.",
            data_kind="calculated",
            kind="bars",
            y_format="pct",
            y_label="Cost as a share of target",
            bars=(
                Bar("Scalp", 20, "danger"),
                Bar("Day", 4, "warn"),
                Bar("Swing", 1, "accent"),
                Bar("Position", 0.3, "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Write the hours you can really trade each day.",
        "Pick the style that fits those hours.",
        "Test whether you can stay calm with the holding time and losing streaks.",
        "Commit to one style for at least 3 months.",
    ),
    example_md="""
Sara works 9 to 5 in Dubai and has two kids. She can review charts for about 45 minutes in the evening.

**Scalping** is impossible. **Day trading** the London–New York overlap clashes with her evenings. **Swing** trading on the daily and 4-hour charts fits. She can decide in the evening, place orders with stops and targets, and live her life.
""".strip(),
    mistakes=(
        "Choosing scalping because it looks exciting.",
        "Trying to day trade while also working a full-time job.",
        "Switching styles after a few losses.",
    ),
    evidence=fact(
        "This lesson is about fit, not profit. There is evidence that frequent trading hurts ordinary traders, which is a reason to be cautious with the shorter styles."
    ),
    try_it="Write down your typical week, hour by hour. Mark where trading could really fit.",
    quiz=(
        Q(
            "What style usually fits a full-time job best?",
            ("Scalping", "Swing or position trading", "Tick trading"),
            1,
            "Swing and position trading need much less screen time.",
        ),
        Q(
            "Why do short-term styles face a harder test?",
            ("Costs are large relative to the target", "Regulators ban them", "They always lose"),
            0,
            "The same costs are a bigger share of smaller moves.",
        ),
    ),
    takeaways=(
        "Pick a style that fits your life.",
        "Shorter styles face higher costs relative to the target.",
        "Beginners often do best on longer timeframes.",
    ),
)

_SCALP = _plan(
    slug="plans/scalping",
    title="Scalping",
    summary="Many tiny trades. The hardest style for a retail trader.",
    minutes=8,
    concepts=("scalping", "execution", "spread", "latency"),
    goal="Understand what scalping needs, and why most retail traders should not start here.",
    idea="**Scalping** means making many very short trades, often seconds to minutes long, aiming for small gains. The whole business depends on low costs and fast, reliable execution.",
    suits="Rare people with very low costs, fast execution, deep concentration and a lot of screen time. Generally not for beginners, and not for most retail accounts.",
    entry="A short-term trigger at a level, or an order-flow signal, in the most liquid hours.",
    stop="Very close, often only a few ticks or pips, but it must be wider than normal noise.",
    target="A small multiple of the risk, often 0.5–1R. Many scalpers take partial profits early.",
    sizing=_SIZING,
    fails="When costs rise, liquidity thins, news spikes hit, or your connection lags. A few bad fills can wipe out many small wins.",
    steps=(
        "Calculate your total cost per round trip.",
        "Find the smallest stop and target where costs are a small share of the target.",
        "Trade only the most liquid hours.",
        "Keep a strict daily loss limit.",
        "Measure your average gain per trade after costs.",
    ),
    example="""
EUR/USD at a tight 0.4 pip spread, 0.2 pip commission per trade and 0.3 pip of slippage is **0.9 pips** of cost per round trip.

With a 6-pip stop and 6-pip target, costs are **15%** of the target. You need a win rate of about **57.5%** just to break even.

If the broker's spread widens to 1 pip in quiet hours, the same setup fails. Most retail scalpers do not know their real numbers.
""",
    mistakes=(
        "Scalping without knowing your cost per trade.",
        "Trading through news on a tight stop.",
        "Counting wins and ignoring fees.",
    ),
    verdict=Verdict.WEAK,
    evidence="""
Large studies of frequent traders show poor results: fewer than 1% of Taiwanese day traders earned reliable profits after fees, and most persistent Brazilian day traders lost money. Those studies cover day traders and not only scalpers, but scalpers face the same or higher costs.

Professional scalping and market-making firms do profit, using speed, data and rebates that retail traders do not have. Do not assume those results transfer.
""",
    try_it="Compute your break-even win rate for a 5-pip scalp at your real costs. Could you honestly achieve that?",
    quiz=(
        Q(
            "What matters most for scalping?",
            ("Very low costs and fast execution", "Long-term forecasts", "Wide stops"),
            0,
            "With small targets, costs decide everything.",
        ),
        Q(
            "Most retail traders should…",
            (
                "Start with scalping",
                "Avoid scalping until they have tested results",
                "Only scalp during news",
            ),
            1,
            "Costs and competition make this the hardest style.",
        ),
    ),
    takeaways=(
        "Scalping is a costs-and-speed game.",
        "It is the hardest style for retail traders.",
        "Know your break-even win rate first.",
    ),
    charts=(
        Chart(
            title="Break-even win rate for a 1:1 scalp",
            caption="Calculated: a 6-pip stop and target with different round-trip costs.",
            data_kind="calculated",
            kind="bars",
            y_format="pct",
            y_label="Break-even win rate",
            x_label="Round-trip cost",
            bars=(
                Bar("0.3 pips", 52.5, "accentSoft"),
                Bar("0.6 pips", 55.0, "accent"),
                Bar("0.9 pips", 57.5, "warn"),
                Bar("1.5 pips", 62.5, "danger"),
            ),
        ),
    ),
    sources=("barber-day-2014", "chague-2020"),
)

_DAY = _plan(
    slug="plans/day-trading",
    title="Day trading",
    summary="Closing all positions by the end of the day.",
    minutes=8,
    concepts=("day trading", "intraday", "session"),
    goal="Know what day trading requires and how a simple day-trade plan works.",
    idea="**Day trading** means opening and closing positions within the same day. You carry no overnight risk, but you have to be present and your costs are large compared to your target.",
    suits="People who can be at a screen for the active hours of their market, every day, and who stay calm under time pressure.",
    entry="A defined setup in the active session, for example a pullback to the day's VWAP with the trend on a higher timeframe.",
    stop="Beyond the setup, wider than normal noise on the timeframe you use, such as 1× ATR of the 15-minute chart.",
    target="1.5R to 3R, or end of session, whichever comes first.",
    sizing=_SIZING + " Include a daily loss limit, typically 2–3 times your per-trade risk.",
    fails="In low-volatility days, quiet holiday periods, or sudden news. Overtrading is the main danger.",
    steps=(
        "Pick one market and one session.",
        "Identify the higher-timeframe trend before the session.",
        "Take only the setups in your plan.",
        "Close everything by the end of the session.",
        "Stop trading at your daily loss limit.",
    ),
    example="""
S&P 500 Micro E-mini at $5 per point.

Your rule: buy a pullback to VWAP in the first two hours, if the opening range broke up. Stop 8 points, target 12 points. Account $10,000, 0.75% risk = **$75**.

Contracts = $75 / (8 × $5) = **1.875, so 1 contract**. Risk $40, target $60. It is small and that is correct. Most new day traders use position sizes far too big for their stops.
""",
    mistakes=(
        "Trading outside your chosen session.",
        "Adding trades because the day has been quiet.",
        "Holding overnight because a trade went against you.",
    ),
    verdict=Verdict.WEAK,
    evidence="""
Research on day traders is sobering. In Brazil, about 3% of those who persisted came out ahead after costs. In Taiwan, fewer than 1% earned predictable profits after fees.

Some individuals do profit. That is different from saying day trading is a good bet for most people.
""",
    try_it="For a week, write down only your planned entries in one session on demo. Check how many you actually took, and how many others you took that were not in the plan.",
    quiz=(
        Q(
            "What is the main benefit of day trading?",
            ("No overnight risk", "Guaranteed income", "No costs"),
            0,
            "But the cost is high intensity and high costs relative to the target.",
        ),
        Q(
            "What did the Brazilian study find?",
            (
                "About 3% of persistent day traders profited after fees",
                "Most made a living",
                "Day trading was risk-free",
            ),
            0,
            "Very few came out ahead.",
        ),
    ),
    takeaways=(
        "Day trading avoids overnight risk.",
        "Costs and intensity are high.",
        "Most who try do not succeed.",
    ),
    charts=(
        Chart(
            title="Day-trading outcomes in the published research",
            caption="Share of traders in two studies who earned reliable profits, as defined by each study. Definitions differ, so compare with care.",
            data_kind="published",
            kind="bars",
            y_format="pct",
            y_label="Share of traders profitable",
            source_note="Barber, Lee, Liu & Odean (2014), Chague, De-Losso & Giovannetti (2020).",
            bars=(
                Bar("Brazil: profit after fees", 3.0, "danger"),
                Bar("Taiwan: reliable net profit", 1.0, "danger"),
            ),
        ),
    ),
    sources=("barber-day-2014", "chague-2020"),
)

_SWING = _plan(
    slug="plans/swing-trading",
    title="Swing trading",
    summary="Holding for days to weeks. Often the best fit for people with a day job.",
    minutes=8,
    concepts=("swing trading", "daily chart", "overnight risk"),
    goal="Set up a swing trading plan that fits around a normal life.",
    idea="**Swing trading** means holding positions for days or weeks to capture a larger move. Decisions can be calm, but you carry overnight and weekend risk.",
    suits="People with a job who can spare 30–60 minutes a day. Most new traders should start here.",
    entry="A pullback in the direction of the daily trend, or a breakout from a clear consolidation.",
    stop="Below the swing low (for a long) or 2× ATR(14), whichever makes sense.",
    target="2R–3R, or a major level. Partial exits are optional.",
    sizing=_SIZING + " Remember gap risk: stops can fill worse than planned over a weekend.",
    fails="In choppy, sideways markets, or when news hits over a weekend and prices gap.",
    steps=(
        "Check the weekly trend once a week.",
        "On the daily chart, find a setup in that direction.",
        "Place your order with stop and target attached.",
        "Check once or twice a day. Do not micro-manage.",
        "Decide your weekend rule.",
    ),
    example="""
EUR/USD daily uptrend. Pullback to 1.0850, the last higher low is 1.0800.

- Entry 1.0855, stop 1.0795 (60 pips, 1R).
- Target 1.0975 (120 pips, 2R).
- Account $8,000, 1% risk = $80; lots = $80 / (60 × $10) = **0.13 lots**.

If you win, you make about $156. If you lose, you lose about $78. Over many trades, you need your expectancy to be positive after spreads and swap.
""",
    mistakes=(
        "Watching every tick and interfering.",
        "Taking swing trades without considering weekend risk.",
        "Ignoring swap costs on longer holds.",
    ),
    verdict=Verdict.MIXED,
    evidence="""
Medium-horizon trend effects have support (Moskowitz et al.), and there is less cost drag than for short-term trading. But there are few independent studies of retail swing traders specifically, and any individual swing method still needs testing.
""",
    try_it="Find three swing setups on a daily chart from the past year using one fixed rule. Write the entry, stop, target, and what happened.",
    quiz=(
        Q(
            "Which risk does swing trading have that day trading avoids?",
            ("Overnight and weekend gaps", "Spread", "Leverage"),
            0,
            "Holding overnight means gaps can jump past your stop.",
        ),
        Q(
            "Why is swing trading often suitable for beginners?",
            (
                "It is guaranteed to work",
                "It needs less screen time and lower relative costs",
                "It has no losses",
            ),
            1,
            "It leaves time to think and costs are smaller compared to targets.",
        ),
    ),
    takeaways=(
        "Swing trading fits around a normal life.",
        "Expect overnight and weekend risk.",
        "A clear daily plan does most of the work.",
    ),
    charts=(
        candle_chart(
            path([(0, 1.0800), (15, 1.0950), (25, 1.0855), (40, 1.1020)], seed=151, noise=0.25),
            title="A swing trade from pullback to target",
            caption="Illustrative prices. A pullback in an uptrend, entry at 1.0855, stop below the swing, target 2R higher.",
            hlines=(HLine(1.0795, "Stop", "danger"), HLine(1.0975, "Target (2R)", "accentSoft")),
            marks=(Mark(25, 1.0855, "Entry", "fg", "up"),),
        ),
    ),
    sources=("moskowitz-2012",),
)

_POSITION = _plan(
    slug="plans/position-trading",
    title="Position trading",
    summary="Holding for months. Close to investing, with defined risk.",
    minutes=7,
    concepts=("position trading", "weekly chart", "macro"),
    goal="Understand long-horizon trading, and what it requires of you.",
    idea="**Position trading** means holding for weeks to months, based on weekly or monthly charts and larger economic trends. It needs patience above everything.",
    suits="Patient people with enough capital to ride wide swings, and who can hold through long dull periods.",
    entry="A long-term trend or macro view, entered after a pullback on the weekly chart.",
    stop="Wide: often 3× ATR(14) on the weekly chart.",
    target="Trailing stop, or until the original reason for the trade changes.",
    sizing=_SIZING + " Because stops are wide, position sizes are small.",
    fails="When macro drivers change suddenly, or financing and swap costs eat into a long hold.",
    steps=(
        "Write the reason you think this trend will last.",
        "Find a pullback on the weekly chart.",
        "Place a wide stop and a small position.",
        "Review weekly, not daily.",
        "Exit if your reason changes.",
    ),
    example="""
A trader buys EUR/USD at **1.0800** based on a widening rate differential, with a stop at **1.0500** (300 pips).

Account $20,000, 1% risk = $200. Lots = $200 / (300 × $10) = **0.07 lots**. The position is small because the stop is wide.

Swap: 0.07 lots, 180 days, $1.20 per lot per day = about **$15**, small compared to the trade's risk.
""",
    mistakes=(
        "Using a tight stop on a long-term idea.",
        "Forgetting financing costs.",
        "Abandoning the plan after one bad week.",
    ),
    verdict=Verdict.SUPPORTED,
    evidence="""
Long-horizon trend signals have the strongest research support among trading approaches here (Moskowitz, Ooi and Pedersen; Hurst et al. over more than a century). But the published results come from diversified portfolios, often by managers who run such strategies. A single market or a small account can have very long losing runs.
""",
    try_it="Pick one market. Write your position-trading reason in a sentence, and the event that would make you exit.",
    quiz=(
        Q(
            "Position trading usually uses…",
            ("Very tight stops", "Wide stops and small sizes", "No stops"),
            1,
            "Wide stops need small sizes.",
        ),
        Q(
            "Why review weekly and not daily?",
            (
                "Long-term trades need a long-term view; daily checks invite interference",
                "Daily data is banned",
                "It reduces fees",
            ),
            0,
            "Frequent checks encourage interference.",
        ),
    ),
    takeaways=(
        "Position trading rewards patience.",
        "Wide stops mean small sizes.",
        "Financing costs matter on long holds.",
    ),
    charts=(
        Chart(
            title="Trend following in research: a simple picture",
            caption="Simulated, not real returns. A strategy with a small positive expectancy, showing long flat periods between gains. Real results vary.",
            data_kind="calculated",
            kind="lines",
            y_format="plain",
            y_label="Account (start = 100)",
            x_label="Trades",
            series=equity_paths(
                n_paths=1, n_trades=150, win_rate=0.4, win_r=2.2, risk_pct=1.0, seed=23
            ),
        ),
    ),
    sources=("moskowitz-2012", "hurst-2017"),
)

_tp = path(
    [(0, 100), (10, 105), (15, 103), (25, 110), (30, 107.5), (45, 118)], seed=161, noise=0.25
)
_tp_close = _tp.closes

_TREND = _plan(
    slug="plans/trend-following",
    title="Trend following",
    summary="Buy what is rising, sell what is falling, and let winners run.",
    minutes=10,
    concepts=("trend following", "momentum", "time series momentum", "breakout", "trailing stop"),
    goal="Understand and build a simple rule-based trend-following plan.",
    idea="""**Trend following** buys markets that have been rising and sells those that have been falling. It does not try to predict a top or bottom. It accepts many small losses in exchange for occasional large wins.""",
    suits="Patient people who can accept long losing or flat periods. It works best with several markets, not one.",
    entry="Price above the 100-day moving average and making a new 50-day high (or the opposite for shorts).",
    stop="A trailing stop, such as 3× ATR(14) below the highest price since entry.",
    target="No fixed target. The trailing stop is the exit.",
    sizing=_SIZING + " Spread risk over many uncorrelated markets if you can.",
    fails="In long sideways periods, where it takes many small losses (whipsaw), and in sudden reversals, where the trailing stop gives back profits.",
    steps=(
        "Choose several liquid markets.",
        "Test the rules with costs on your own data first.",
        "Enter on the rule without opinions.",
        "Trail the stop only as the trade moves in your favour.",
        "Accept long stretches with no progress.",
    ),
    example="""
EUR/USD closes above its 100-day average and at a new 50-day high of **1.0950**. ATR is 70 pips.

- Entry 1.0955, trailing stop 210 pips below the high: **1.0745**.
- Account $20,000, 1% risk = $200. Lots = $200 / (210 × $10) = **0.09 lots**.

The price rises to 1.1400, and the trailing stop moves up to 1.1190. Then it reverses and stops you out at 1.1190: **+235 pips, about +1.1R**. Then you may have 4 small losses in a row before the next trend. That is normal.
""",
    mistakes=(
        "Taking profits early, then missing the big move.",
        "Trading only one market.",
        "Switching methods during a dull period.",
    ),
    verdict=Verdict.SUPPORTED,
    evidence="""
This is one of the best-documented effects in finance. Moskowitz, Ooi and Pedersen found significant positive time-series momentum across all 58 liquid futures they studied. Hurst, Ooi and Pedersen found trend following produced positive returns over more than a century, including good results in 8 of the 10 largest 60/40 portfolio drawdowns.

Limits: results come from diversified portfolios run with low costs. The authors of the century paper work for a manager that uses these strategies. Single-market retail results can be very different. Daniel and Moskowitz show momentum can crash in sharp rebounds after market falls. The past is not a guarantee.
""",
    try_it="Backtest a 50-day-high entry with a 3× ATR trailing stop on one market in your Strategy Lab. Then try it on a second market. Compare.",
    quiz=(
        Q(
            "Trend following typically has…",
            (
                "A high win rate with small wins",
                "A low win rate with occasional big wins",
                "No losing trades",
            ),
            1,
            "Many small losses and a few large winners.",
        ),
        Q(
            "When does trend following usually suffer?",
            ("In long sideways markets", "In strong trends", "Only on Mondays"),
            0,
            "Whipsaws create many small losses in ranges.",
        ),
    ),
    takeaways=(
        "Follow price, do not predict it.",
        "Trend following has some of the strongest research support, but with caveats.",
        "Expect long flat stretches.",
    ),
    charts=(
        candle_chart(
            _tp,
            title="A trend-following trade",
            caption="Illustrative prices. The 20-period average (real calculation) stays below price during the trend. The exit comes only when price drops through a trailing stop.",
            series=(Series("20-period average", sma(_tp_close, 20), "accent"),),
            marks=(Mark(25, _tp_close[25], "Hold", "muted"),),
        ),
    ),
    sources=("moskowitz-2012", "hurst-2017", "daniel-2016"),
)

_bo = path(
    [(0, 100), (8, 104), (14, 101), (20, 104.2), (26, 101.2), (32, 104), (35, 108), (48, 114)],
    seed=167,
    noise=0.2,
)

_BREAKOUT = _plan(
    slug="plans/breakout",
    title="Breakout trading",
    summary="Buying as price escapes a range or level.",
    minutes=8,
    concepts=("breakout", "range", "volatility expansion", "false breakout"),
    goal="Be able to trade a breakout with exact rules, and handle the false ones.",
    idea="**Breakout trading** enters when price moves through a level or out of a range, expecting the move to continue. It works best when volatility is expanding.",
    suits="People who can accept many small failed breakouts, and who can place orders ahead of time.",
    entry="A stop order just beyond a clear range high or low, ideally after a compression.",
    stop="On the other side of the range, or at the midpoint if that still leaves room for noise.",
    target="Range height projected from the break, or a trailing stop.",
    sizing=_SIZING + " A wide range means a small position.",
    fails="In sideways markets, where false breakouts are common. Slippage makes it worse.",
    steps=(
        "Find a clear range with at least two touches of each side.",
        "Measure the range height.",
        "Place stop orders above and below, with the stop on the other side.",
        "Cancel the opposite order when one fills.",
        "Skip if costs are too high relative to the range.",
    ),
    example="""
GBP/USD has traded between **1.2600 and 1.2680** for two weeks.

- Buy stop at 1.2685, stop 1.2640 (45 pips), target 1.2765 (80 pips).
- Account $10,000, 1% = $100. Lots = $100 / (45 × $10) = **0.22 lots**.

If it breaks up and reaches the target: about +$176. If it reverses into the range, you lose about $100. Expect some false breakouts.
""",
    mistakes=(
        "Buying breakouts that have already run far.",
        "Forgetting about slippage on the stop order.",
        "Ignoring whether the market is actually moving.",
    ),
    verdict=Verdict.MIXED,
    evidence="""
Brock, Lakonishok and LeBaron found that trading-range-break rules on long Dow data were informative. Later data snooping and cost-adjusted studies, such as Sullivan et al., reduced those claims. Results depend heavily on the market, period and definition. Test your exact rules.
""",
    try_it="Find 10 ranges in one market. For each, note how far price went after the break, and how many failed within 5 candles.",
    quiz=(
        Q(
            "Where does the stop usually go on a breakout?",
            ("On the other side of the range", "Exactly at entry", "No stop is needed"),
            0,
            "A return into the range means the idea failed.",
        ),
        Q(
            "Breakouts tend to fail most in…",
            ("Sideways markets", "Strong trends", "Thick liquidity"),
            0,
            "Ranges produce many false breakouts.",
        ),
    ),
    takeaways=(
        "Trade breakouts with an order placed in advance.",
        "Expect false breakouts.",
        "Test before trusting.",
    ),
    charts=(
        candle_chart(
            _bo,
            title="Range and breakout",
            caption="Illustrative prices. A range between 101 and 104, then a break to the upside.",
            zones=(Zone(101, 104.3, "Range", "muted", 0, 34),),
            marks=(Mark(35, 108, "Breakout", "accentSoft"),),
        ),
    ),
    sources=("brock-1992", "stw-1999"),
)

_PULLBACK = _plan(
    slug="plans/pullback",
    title="Pullback trading",
    summary="Waiting for a dip in a trend, then joining it.",
    minutes=8,
    concepts=("pullback", "retracement", "trend", "reward-to-risk"),
    goal="Be able to trade pullbacks with a clear definition of when the idea has failed.",
    idea="**Pullback trading** waits for a counter-move inside a trend and joins the trend at a better price. It aims for better reward-to-risk than chasing.",
    suits="Patient traders who can wait and who are willing to miss some moves.",
    entry="In an uptrend, a pullback to a support zone, or moving average, with a rejection candle.",
    stop="Below the most recent higher low, with room for normal movement.",
    target="The previous high, then a trailing stop if you hold further.",
    sizing=_SIZING,
    fails="When the pullback is the beginning of a real reversal. Being early is expensive.",
    steps=(
        "Confirm the larger trend.",
        "Mark the area where a pullback might stop.",
        "Wait for a sign price has stopped falling.",
        "Enter with a stop below the last higher low.",
        "Skip the trade if the reward-to-risk is below your rule.",
    ),
    example="""
EUR/USD daily uptrend, last higher low 1.0800, last high 1.1050. The price pulls back to 1.0880 and prints a rejection candle.

- Entry 1.0890, stop 1.0790 (100 pips).
- Target 1.1050 (160 pips, 1.6R).

If your plan requires 2R, skip it. If the price falls below 1.0800, the pullback was probably a reversal, and the stop did its job.
""",
    mistakes=(
        "Buying every dip, even in a downtrend.",
        "Moving the stop lower during the pullback.",
        "Taking a pullback entry with too little reward.",
    ),
    verdict=Verdict.MIXED,
    evidence="""
Pullback entries combine trend (which has support) with a retracement entry (which has less). Direct evidence on pullback entries specifically is limited. Retracement levels such as Fibonacci have not been shown to be special. Test your own rule against simply entering at random points in the same trends.
""",
    try_it="List every pullback in a trend over the last year using your rule. Compare the average result with entering at a random point on the same trend.",
    quiz=(
        Q(
            "What ends a pullback idea?",
            ("A close below the last higher low", "A red candle", "A slow day"),
            0,
            "That is the point where the structure changes.",
        ),
        Q(
            "What is the main risk?",
            ("Mistaking the start of a reversal for a pullback", "Too much profit", "Using a stop"),
            0,
            "A deep pullback and a reversal look the same at first.",
        ),
    ),
    takeaways=(
        "Join the trend at a better price.",
        "Have a clear point at which the idea fails.",
        "Do not buy dips in downtrends.",
    ),
    charts=(
        candle_chart(
            path([(0, 100), (12, 110), (20, 105), (34, 116)], seed=173, noise=0.2),
            title="A pullback in an uptrend",
            caption="Illustrative prices. The pullback to about 105 held above the prior low, and the trend continued.",
            marks=(Mark(20, 105, "Entry area", "accentSoft", "up"),),
        ),
    ),
    sources=("batchelor-2006",),
)

_mr = path(
    [(0, 100), (8, 104.5), (16, 99.5), (26, 104.8), (34, 99.8), (44, 103)], seed=179, noise=0.25
)
_mr_u, _mr_m, _mr_l = bollinger(_mr.closes, 14, 2.0)

_MEAN = _plan(
    slug="plans/mean-reversion",
    title="Mean reversion",
    summary="Fading moves that have gone too far from the average.",
    minutes=9,
    concepts=("mean reversion", "stretch", "z-score"),
    goal="Understand mean reversion, and when it is dangerous.",
    idea="**Mean reversion** bets that a price far from its average will come back. It is the opposite of trend following, and it often has a high win rate with occasional large losses.",
    suits="People who like high win rates and can accept that a small number of losses will be large.",
    entry="In a clearly non-trending market, fade a move beyond a band, such as a close below the lower Bollinger Band.",
    stop="Beyond a defined extreme. Use a hard stop, because a trend can keep going.",
    target="The middle of the range or the moving average.",
    sizing=_SIZING + " Be strict: this is the strategy most likely to be undone by one big trend.",
    fails="When a real trend starts. A market can stay stretched for much longer than you can stay solvent.",
    steps=(
        "Confirm the market is ranging, not trending.",
        "Define what stretched means for this market.",
        "Enter at your stretch rule with a hard stop.",
        "Target the middle of the range.",
        "Stop trading if the market starts trending.",
    ),
    example="""
EUR/GBP has been in a 100-pip range for 6 weeks. Price closes below the lower Bollinger Band at **0.8540**. The midline is **0.8580**.

- Buy 0.8545, stop 0.8515 (30 pips), target 0.8580 (35 pips).

Win rate needs to exceed about 46% to break even before costs. The danger is obvious: if a new trend starts, price goes straight through your stop. Skip this around central bank decisions.
""",
    mistakes=(
        "Fading a strong trend because it 'looks too high'.",
        "Averaging down without a stop.",
        "Believing a high win rate means low risk.",
    ),
    verdict=Verdict.MIXED,
    evidence="""
Short-horizon reversal effects have been documented in various markets, and pairs trading (the next lesson) is a form of mean reversion. But such edges are often small, costly to trade, and have tended to fade as more traders use them. Crash risk is real: mean-reversion strategies can look great until the one trend that hurts badly.
""",
    try_it="List the last 20 times your market closed outside a 2-standard-deviation band. For each, note how far it came back.",
    quiz=(
        Q(
            "Mean reversion usually has…",
            (
                "A low win rate and big wins",
                "A high win rate with occasional large losses",
                "No losses",
            ),
            1,
            "It tends to win often but can lose big when a trend starts.",
        ),
        Q(
            "When should you avoid fading?",
            ("In strong trends or before major news", "In calm ranges", "Never"),
            0,
            "Those are when mean reversion gets run over.",
        ),
    ),
    takeaways=(
        "Mean reversion is the opposite of trend following.",
        "Use hard stops. Never average down without a limit.",
        "High win rates can hide big losses.",
    ),
    charts=(
        candle_chart(
            _mr,
            title="Fading the band in a range",
            caption="Illustrative prices, real 14-period Bollinger Bands. In a range, outer-band touches tend to fade. In a trend, they do not.",
            series=(
                Series("Upper band", _mr_u, "accent", "dashed"),
                Series("Average", _mr_m, "muted"),
                Series("Lower band", _mr_l, "accent", "dashed"),
            ),
        ),
    ),
    sources=("gatev-2006",),
)

_RANGE = _plan(
    slug="plans/range-trading",
    title="Range trading",
    summary="Buying near the floor and selling near the ceiling.",
    minutes=7,
    concepts=("range", "support", "resistance"),
    goal="Trade a defined range safely, and know when to leave.",
    idea="**Range trading** buys near the floor and sells near the ceiling of a sideways market. It is a simple form of mean reversion.",
    suits="Patient traders who are willing to skip trades when the range is not clean.",
    entry="Near the floor after a rejection, or near the ceiling after a rejection.",
    stop="Beyond the floor or ceiling, by a small buffer.",
    target="The other side of the range, or the midpoint.",
    sizing=_SIZING,
    fails="When the range breaks. Ranges always end eventually.",
    steps=(
        "Confirm at least two touches of each boundary.",
        "Wait for price to reach an edge.",
        "Enter on a rejection, with a stop beyond the edge.",
        "Take profit before the opposite edge.",
        "If the range breaks, stop range trading and reassess.",
    ),
    example="""
USD/CHF trades 0.8800–0.8900 for a month. Price tests 0.8802 with a rejection candle.

- Buy 0.8810, stop 0.8785 (25 pips), target 0.8880 (70 pips).

Reward-to-risk is **2.8:1**. If the range breaks, you lose 25 pips and stop trading this range.
""",
    mistakes=(
        "Trading the middle of the range.",
        "Refusing to accept the range has broken.",
        "Using a range plan in a trending market.",
    ),
    verdict=Verdict.MIXED,
    evidence="""
Range trading relies on the market staying in a range, and no reliable method identifies in advance when a range will end. The approach has weak direct evidence, but it is a straightforward application of defined risk.
""",
    try_it="Identify one clean range, and write a plan for it. Then write down what you would do if the range breaks.",
    quiz=(
        Q(
            "Where is the worst place to enter a range trade?",
            ("Near the floor", "In the middle", "Near the ceiling"),
            1,
            "In the middle the reward-to-risk is poor.",
        ),
        Q(
            "What should happen when the range breaks?",
            (
                "Stop range trading and reassess",
                "Add to the losing trade",
                "Move the stop further away",
            ),
            0,
            "The range plan no longer applies.",
        ),
    ),
    takeaways=("Trade the edges, not the middle.", "Ranges end.", "A break means change the plan."),
    charts=(
        candle_chart(
            path(
                [(0, 100), (8, 103.8), (16, 100.2), (24, 103.6), (32, 100.4), (40, 104)],
                seed=181,
                noise=0.2,
            ),
            title="A clean range",
            caption="Illustrative prices. The trade is near the edges, and any close outside changes the plan.",
            zones=(
                Zone(103.2, 104.2, "Sell zone", "danger"),
                Zone(100, 101, "Buy zone", "accentSoft"),
            ),
        ),
    ),
)

_CARRY = _plan(
    slug="plans/carry-trade",
    title="Carry trade",
    summary="Earning the interest gap, and the crash risk that comes with it.",
    minutes=9,
    concepts=("carry", "interest differential", "swap", "crash risk"),
    goal="Understand how carry trades make money, and why they can lose it all at once.",
    idea="A **carry trade** holds a high-interest currency against a low-interest currency, and earns the interest difference each day. You are paid to wait, but the currency can move against you.",
    suits="Patient traders who understand the risk of sudden crashes, and who keep position sizes small.",
    entry="Choose a pair with a large, stable interest rate gap, ideally when volatility is low.",
    stop="A defined level based on volatility. Exit when volatility spikes, regardless of level.",
    target="There is no fixed target. Collect the carry while conditions hold.",
    sizing=_SIZING + " Small: carry can lose years of income in weeks.",
    fails="In sudden risk-off events, when high-yield currencies fall sharply and positions are unwound together.",
    steps=(
        "Find the interest rate gap between two currencies.",
        "Check your broker's actual swap rate, which may be worse than the gap.",
        "Size small.",
        "Set a rule to exit if volatility jumps.",
        "Check central bank expectations regularly.",
    ),
    example="""
Say a high-yield currency pays **4.5%** more per year than a low-yield one. Your broker pays a swap equivalent to 3.5% per year after its costs.

On $20,000 notional held for a year, you earn about **$700** in carry if the exchange rate does not change. If the exchange rate falls 10% in a panic, you lose **$2,000**. Years of carry can vanish in a few weeks.
""",
    mistakes=(
        "Ignoring swap rates actually paid by your broker.",
        "Using high leverage because carry feels safe.",
        "Holding carry through a sudden volatility spike.",
    ),
    verdict=Verdict.SUPPORTED,
    evidence="""
Carry is among the most documented effects in markets. Koijen, Moskowitz, Pedersen and Vrugt found carry predicts returns across asset classes. Lustig, Roussanov and Verdelhan linked currency carry to a common global risk factor.

But the risk is well documented too: Brunnermeier, Nagel and Pedersen found carry returns are negatively skewed, meaning slow gains and sudden crashes. The chart above is a simulated shape, not real returns.
""",
    try_it="Find the real overnight swap your broker charges or pays on two pairs. Compute what that is per year on your position size.",
    quiz=(
        Q(
            "What does a carry trade earn?",
            ("The interest rate difference", "Only exchange rate gains", "Commission rebates"),
            0,
            "It collects the interest gap, and is exposed to exchange-rate moves.",
        ),
        Q(
            "Carry returns are usually…",
            ("Steady, then sudden large losses", "Perfectly symmetric", "Risk-free"),
            0,
            "Brunnermeier et al. find them negatively skewed.",
        ),
    ),
    takeaways=("Carry pays you to wait.", "It has serious crash risk.", "Small size is essential."),
    charts=(
        Chart(
            title="A carry pattern: slow gains, sudden falls",
            caption="Simulated, not real returns: a steady gain per period with rare large drops, the negative-skew shape reported in research.",
            data_kind="calculated",
            kind="lines",
            y_format="plain",
            y_label="Account (start = 100)",
            x_label="Periods",
            series=(
                Series(
                    "Carry",
                    tuple(
                        round(100 + i * 0.6 - (0 if i < 40 else 20) - (0 if i < 110 else 25), 2)
                        for i in range(160)
                    ),
                    "accent",
                ),
            ),
        ),
    ),
    sources=("koijen-2018", "brunnermeier-2008", "lustig-2011"),
)

_NEWS = _plan(
    slug="plans/news-and-events",
    title="News and event trading",
    summary="Trading scheduled releases and earnings, and the high bar to do it well.",
    minutes=8,
    concepts=("news trading", "event", "earnings", "drift"),
    goal="Understand what is required to trade news, and why most should avoid the first moments.",
    idea="**News trading** tries to profit from scheduled events such as central bank decisions, data releases or company earnings. It offers big moves and very poor conditions.",
    suits="Very few retail traders. Those who do it have a tested rule, a fast connection and small size.",
    entry="After the first reaction, once the spread normalises and a clear direction forms.",
    stop="Wider than usual, with size reduced to compensate.",
    target="A fixed R multiple, or a time-based exit.",
    sizing=_SIZING + " Halve your normal risk, because fills can be poor.",
    fails="In volatile first moments, when spreads widen and stops slip. Also when you are right about the news and the market still goes the other way.",
    steps=(
        "Know the event calendar.",
        "Write your plan for three outcomes: better, in line, worse.",
        "Do not enter in the first seconds.",
        "Enter only on a clear post-release structure.",
        "Reduce size and accept wider stops.",
    ),
    example="""
US CPI is forecast at 0.3% and comes in at 0.5%. EUR/USD falls 50 pips in five minutes.

Your plan: wait 15 minutes, then sell a pullback with a stop above the post-release high.

- Entry 1.0840, stop 1.0875 (35 pips), target 1.0770 (70 pips).
- Halved risk of 0.5% on $10,000: $50. Lots = $50 / (35 × $10) = **0.14 lots**.

If the spread at entry is still abnormal, you do not enter.
""",
    mistakes=(
        "Entering in the first seconds.",
        "Assuming you know which way the market will react.",
        "Keeping normal size through major news.",
    ),
    verdict=Verdict.MIXED,
    evidence="""
Events do move markets. Lucca and Moench found US stocks gained unusually in the day before Fed meetings, a pattern a later update found to be mainly around meetings with press conferences. These are effects in specific conditions and may shrink as they become known.

Reacting faster than professional systems is not realistic, and retail traders often pay the worst spreads.
""",
    try_it="Pick three recent releases. Write down what you would have done, the spread at the time, and what happened 15 minutes and 2 hours later.",
    quiz=(
        Q(
            "What is the biggest danger of trading the first seconds after news?",
            ("Wide spreads and bad fills", "Too little excitement", "No volatility"),
            0,
            "Conditions are at their worst in those first moments.",
        ),
        Q(
            "Why reduce size around news?",
            (
                "Fills are worse and moves are larger",
                "Regulators require it",
                "It makes news more accurate",
            ),
            0,
            "You are accepting worse conditions.",
        ),
    ),
    takeaways=(
        "News creates moves and poor conditions.",
        "Do not enter in the first moments.",
        "Reduce size.",
    ),
    charts=(
        candle_chart(
            path(
                [(0, 1.0820), (8, 1.0825), (9, 1.0870), (16, 1.0815), (30, 1.0790)],
                seed=191,
                noise=0.2,
            ),
            title="Spike and reversal around a release",
            caption="Illustrative prices. The first spike reversed. Reacting quickly to a release often means paying the worst price.",
            marks=(Mark(9, 1.0870, "Release", "warn"),),
        ),
    ),
    sources=("lucca-2015",),
)

_PAIRS = _plan(
    slug="plans/pairs-and-stat-arb",
    title="Pairs trading and statistical arbitrage",
    summary="Betting on the gap between two related markets.",
    minutes=9,
    concepts=("pairs trading", "statistical arbitrage", "spread", "z-score", "cointegration"),
    goal="Understand the idea of pairs trading and why it is harder than it looks.",
    idea="**Pairs trading** buys one asset and sells a related one when the gap between them is unusually wide, betting the gap will close. **Statistical arbitrage** extends this idea to many positions at once.",
    suits="Traders with good data, low costs and the ability to sell short. Hard to run on a small retail account.",
    entry="When the spread between two closely related assets is more than about 2 standard deviations from its average.",
    stop="A maximum spread level or time limit, in case the relationship has really broken.",
    target="The spread returns to its average.",
    sizing="Size each side so that a move in the spread produces the planned risk.",
    fails="When the relationship truly breaks: a merger, a bankruptcy, a change in the business. And costs can consume small edges.",
    steps=(
        "Pick pairs with a good economic reason to move together.",
        "Measure the spread and its normal range over a formation period.",
        "Enter when it is unusually wide.",
        "Exit at a target spread or a time limit.",
        "Re-check the relationship regularly.",
    ),
    example="""
Two oil companies usually trade near a 1.05 price ratio. It widens to 1.15, more than 2 standard deviations from its 1-year average.

Sell the expensive one, buy the cheap one in dollar-matched amounts, and target a return to 1.05 over 3 months. If one company announces a merger, the old relationship may no longer apply: exit by your time limit or spread limit.
""",
    mistakes=(
        "Picking pairs with no reason to move together.",
        "Using too much leverage because it 'looks hedged'.",
        "Assuming spreads always close.",
    ),
    verdict=Verdict.MIXED,
    evidence="""
Gatev, Goetzmann and Rouwenhorst tested pairs trading on US daily data from 1962 to 2002 and found about 11% average annual excess return for the top pairs, enough to cover conservative transaction cost estimates. Later studies report profits have fallen, as more traders and better technology reduced the opportunity.
""",
    try_it="Pick two related instruments. Chart the ratio of their prices for two years, and mark the moments it was unusually wide. What happened next?",
    quiz=(
        Q(
            "What does pairs trading bet on?",
            (
                "The spread between two assets returning to normal",
                "Both assets rising",
                "A single company's earnings",
            ),
            0,
            "It trades the relationship, not the direction.",
        ),
        Q(
            "What is the biggest risk?",
            ("The relationship breaks for good", "It is too easy", "Spreads are always stable"),
            0,
            "Mergers and business changes can end a relationship.",
        ),
    ),
    takeaways=(
        "Pairs trade the relationship, not direction.",
        "Evidence is real but profits have shrunk.",
        "A broken relationship is the key risk.",
    ),
    charts=(
        Chart(
            title="A spread that widens and returns",
            caption="Illustrative spread with bands at 2 standard deviations. Real spreads can keep widening.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Spread",
            x_label="Days",
            series=(
                Series(
                    "Spread",
                    (
                        0.0,
                        0.2,
                        0.5,
                        0.3,
                        0.6,
                        1.0,
                        1.5,
                        2.2,
                        2.4,
                        1.8,
                        1.2,
                        0.6,
                        0.2,
                        -0.3,
                        -0.2,
                        0.1,
                    ),
                    "accent",
                ),
            ),
            hlines=(HLine(2.0, "+2 std dev", "warn"), HLine(-2.0, "-2 std dev", "warn")),
        ),
    ),
    sources=("gatev-2006",),
)

_SEASON = _plan(
    slug="plans/seasonal",
    title="Seasonal trading",
    summary="Calendar effects, and how little they tend to survive.",
    minutes=7,
    concepts=("seasonality", "calendar effect", "sell in May"),
    goal="Know what calendar effects are and how to test them.",
    idea="**Seasonal trading** looks for patterns tied to the calendar, such as the month of the year, or days around holidays. Agriculture and energy have real seasons. Stock market seasons are more debated.",
    suits="Patient traders who are comfortable taking a small position when a rule says to.",
    entry="On a specific date or calendar rule, set in advance.",
    stop="A wide volatility-based stop.",
    target="The end of the seasonal window.",
    sizing=_SIZING,
    fails="Often. A seasonal pattern is an average over many years and can fail in any given year. It also tends to fade once widely known.",
    steps=(
        "State the seasonal idea, and why it might exist.",
        "Test it over many years, using data you did not use to find it.",
        "Check how much of the result comes from a few years.",
        "Include costs.",
        "Trade small, and only if it survives.",
    ),
    example="""
"Sell in May": US stocks tend to do worse from May to October than from November to April.

A plan: hold an equity index only from November to April. Costs are small because you trade twice a year. In some years, the summer is strong, and you will lag the market. This is a long-horizon rule, not a tactic for a single year.
""",
    mistakes=(
        "Believing a pattern because it appeared in a chart of 10 years.",
        "Trading a seasonal pattern with full size.",
        "Assuming last year's pattern will repeat.",
    ),
    verdict=Verdict.MIXED,
    evidence="""
Bouman and Jacobsen found that stock returns from November to April beat May to October in 36 of 37 countries between 1970 and 1998. Later work disagrees about how strong this is after adjusting for outliers and how it behaves over time.

Commodity seasons, like harvests, have real physical causes. But traders know those too, and they are often partly in the price.
""",
    try_it="Pick one month of the year for your market, and list its return for each of the last 10 years. Are they consistent or noisy?",
    quiz=(
        Q(
            "Which study found sell-in-May effects in 36 of 37 countries?",
            ("Bouman and Jacobsen", "Fama", "Elliott"),
            0,
            "It remains debated how strong and stable the effect is.",
        ),
        Q(
            "Why be careful with seasonal patterns?",
            (
                "They are averages that fail in many individual years",
                "They are guaranteed",
                "They are illegal",
            ),
            0,
            "A seasonal pattern is a tendency.",
        ),
    ),
    takeaways=(
        "Seasonal patterns are averages.",
        "They can fail often in a given year.",
        "Test on data you did not use to find them.",
    ),
    charts=(
        Chart(
            title="Average monthly return, illustrative",
            caption="Illustrative only, showing how a seasonal chart usually looks. An average like this can hide very different results in each year.",
            data_kind="illustrative",
            kind="bars",
            y_format="pct",
            y_label="Average return",
            bars=tuple(
                Bar(m, r, "accentSoft" if r > 0 else "danger")
                for m, r in (
                    ("Nov", 1.8),
                    ("Dec", 1.4),
                    ("Jan", 1.1),
                    ("May", 0.2),
                    ("Jun", -0.1),
                    ("Sep", -0.5),
                )
            ),
        ),
    ),
    sources=("bouman-2002",),
)

_OPT_INCOME = _plan(
    slug="plans/options-income",
    title="Options income: covered calls and cash-secured puts",
    summary="Selling options for income, and the risk you are taking on.",
    minutes=9,
    concepts=("covered call", "cash-secured put", "premium", "assignment"),
    goal="Understand how options income strategies work and what risk they hide.",
    idea="Selling options brings in cash now, called a **premium**. In exchange you accept a risk. A **covered call** sells the right to buy shares you own. A **cash-secured put** sells the right to sell shares to you at a set price.",
    suits="Investors who already own shares, or who would be happy to own them, and who understand assignment.",
    entry="Sell a call above the current price, or a put below it, usually 30–45 days to expiry.",
    stop="Have a rule to close if the underlying moves strongly against you. A covered call is still long stock.",
    target="Keep the premium, or close at about 50% of the maximum gain.",
    sizing="Limit the amount of capital tied up in any one underlying.",
    fails="In crashes: a covered call still falls with the stock, while your upside was sold. And a sharp rise forces your shares away at a price you may not like.",
    steps=(
        "Choose only stocks or funds you would happily own.",
        "Choose an expiry and a strike price.",
        "Sell the option and collect the premium.",
        "Have a plan for assignment.",
        "Track total return, including what you gave up.",
    ),
    example="""
You own 100 shares at $50 and sell one call at $55 expiring in 40 days, for $1.20 per share ($120).

- If the stock ends at $52: keep shares and the $120.
- If the stock rises to $60: your shares are called away at $55. You earn $5 + $1.20 per share, $620 total, but you miss $5 of further rise.
- If the stock falls to $40: you lose $10 per share and keep $1.20, a loss of $880.
""",
    mistakes=(
        "Thinking income is free money.",
        "Selling options on things you do not want to own.",
        "Ignoring that a covered call still has most of the stock's downside.",
    ),
    verdict=Verdict.MIXED,
    evidence="""
Research on index option-writing strategies shows that buy-write and put-write indexes have had attractive risk-adjusted results and smaller drawdowns than the S&P 500 in some periods (for example, a study by Callan for Cboe). Be aware that this work was commissioned by an exchange.

Retail option traders, overall, tend to lose money and pay wide spreads (Bryzgalova, Pavlova and Sikorskaya). Option selling can hide tail risk.
""",
    try_it="Pick one stock you own or would own. Compute the premium, the maximum gain and the loss if the stock falls 20% for a covered call.",
    quiz=(
        Q(
            "What does a covered call seller give up?",
            ("Upside above the strike", "All downside", "Dividends"),
            0,
            "You sell the upside above the strike in return for the premium.",
        ),
        Q(
            "What happens to a covered call in a crash?",
            ("You lose much of the stock's fall, minus the premium", "You make money", "Nothing"),
            0,
            "You still own the stock.",
        ),
    ),
    takeaways=(
        "Premium is payment for accepting risk.",
        "A covered call keeps most of the downside.",
        "Only sell on what you would own.",
    ),
    charts=(
        Chart(
            title="Payoff of a covered call at expiry",
            caption="Calculated: shares bought at $50, call sold at $55 for $1.20. Above $55, gains are capped. Below, the loss is close to owning the stock.",
            data_kind="calculated",
            kind="lines",
            y_format="usd",
            y_label="Profit at expiry (per share)",
            x_label="Stock price at expiry",
            x_labels=tuple(str(p) for p in range(40, 66, 2)),
            series=(
                Series(
                    "Covered call",
                    tuple(round((min(p, 55) - 50 + 1.2) * 100, 0) for p in range(40, 66, 2)),
                    "accent",
                ),
            ),
        ),
    ),
    sources=("cboe-callan", "bryzgalova-2023"),
)

_OPT_HEDGE = _plan(
    slug="plans/options-hedging",
    title="Hedging with options",
    summary="Paying for protection, and deciding whether it is worth it.",
    minutes=8,
    concepts=("protective put", "hedge", "insurance", "cost of carry"),
    goal="Know when a hedge makes sense, and how to work out what it costs.",
    idea="A **hedge** reduces the risk of a position. A **protective put** gives you the right to sell at a set price, which limits your loss, for a known cost.",
    suits="People who hold positions they do not want to sell but who want protection, especially before a known event.",
    entry="Buy a put below the current price, sized to the position.",
    stop="The maximum loss is defined by the put. Your stop is built in.",
    target="Keep the hedge through the risk period, then close or let it expire.",
    sizing="Hedge only the part of the position you need protected.",
    fails="If the put is expensive, it can cost more than the risk it covers. Repeatedly buying protection can drag on long-term returns.",
    steps=(
        "Name the risk you want to reduce.",
        "Pick the strike price that gives the protection you need.",
        "Compute the premium as a percentage of the position.",
        "Decide what timeframe needs covering.",
        "Compare with simply reducing size.",
    ),
    example="""
You hold 100 shares at $100, and you want protection through an earnings report. A put at $90, expiring after earnings, costs $3 per share ($300).

- If the stock falls to $70, the shares lose $3,000 and the put gains $1,700 (90 − 70 = 20, minus $3 premium per share). Net loss: $1,300.
- If the stock rises to $110, the put expires worthless and you are $700 ahead.

If instead you sold half your shares, you would have cut your risk in half without paying a premium.
""",
    mistakes=(
        "Buying expensive protection every month.",
        "Forgetting that a hedge costs money even in the good outcome.",
        "Not comparing with simply trading smaller.",
    ),
    verdict=Verdict.MIXED,
    evidence="""
Options can definitely reduce risk, because their payoffs are defined by contract. Whether regular hedging improves long-term returns depends on price. Implied volatility is often higher than realised volatility over time, so protection tends to be expensive on average. Retail buyers in particular pay wide spreads and tend to lose (Bryzgalova et al.).
""",
    try_it="Pick a position. Price a protective put for one month. Compare the cost with the cost of reducing the position by a quarter.",
    quiz=(
        Q(
            "What does a protective put do?",
            (
                "Sets a floor under your loss for a cost",
                "Increases your leverage",
                "Pays you income",
            ),
            0,
            "It is insurance. You pay a premium.",
        ),
        Q(
            "What is the main cost of regular hedging?",
            ("Premiums paid over time", "Regulatory fees", "None"),
            0,
            "Protection costs money.",
        ),
    ),
    takeaways=(
        "A hedge reduces risk for a known cost.",
        "Protection is often expensive.",
        "Sometimes the best hedge is simply a smaller position.",
    ),
    charts=(
        Chart(
            title="Payoff with and without a put",
            caption="Calculated at expiry. Shares bought at $100. A $90 put costs $3. The put creates a floor on losses.",
            data_kind="calculated",
            kind="lines",
            y_format="usd",
            y_label="Profit per 100 shares",
            x_label="Stock price at expiry",
            x_labels=tuple(str(p) for p in range(70, 131, 5)),
            series=(
                Series("Stock only", tuple((p - 100) * 100 for p in range(70, 131, 5)), "muted"),
                Series(
                    "With a $90 put",
                    tuple(max(p, 90) * 100 - 10000 - 300 for p in range(70, 131, 5)),
                    "accent",
                ),
            ),
        ),
    ),
    sources=("bryzgalova-2023",),
)

CHAPTERS = (
    chapter(
        "plans",
        "building-a-plan",
        "Building a plan",
        "Write the plan, and pick a style you can really follow.",
        (_THE_PLAN, _STYLE),
    ),
    chapter(
        "plans",
        "styles",
        "Styles",
        "From seconds to months: what each timeframe really demands.",
        (_SCALP, _DAY, _SWING, _POSITION),
    ),
    chapter(
        "plans",
        "strategies",
        "Strategies",
        "Every major strategy, with its rules, evidence, and how it fails.",
        (
            _TREND,
            _BREAKOUT,
            _PULLBACK,
            _MEAN,
            _RANGE,
            _CARRY,
            _NEWS,
            _PAIRS,
            _SEASON,
            _OPT_INCOME,
            _OPT_HEDGE,
        ),
    ),
)
