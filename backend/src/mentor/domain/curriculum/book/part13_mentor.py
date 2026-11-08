"""Inside this app — how the mentor works, predicts and keeps itself honest."""

from __future__ import annotations

from mentor.domain.curriculum.book._kit import (
    Evidence,
    Figure,
    Lesson,
    Q,
    QuizQuestion,
    Verdict,
    chapter,
)


def _app(
    *,
    slug: str,
    title: str,
    summary: str,
    concepts: tuple[str, ...],
    goal: str,
    body: str,
    steps: tuple[str, ...],
    example: str,
    mistakes: tuple[str, ...],
    verdict: Verdict,
    evidence: str,
    try_it: str,
    quiz: tuple[QuizQuestion, ...],
    takeaways: tuple[str, ...],
    figures: tuple[tuple[str, str], ...],
    minutes: int = 6,
) -> Lesson:
    return Lesson(
        slug=slug,
        title=title,
        summary=summary,
        est_minutes=minutes,
        key_concepts=concepts,
        goal=goal,
        body_md=body.strip(),
        steps=steps,
        example_md=example.strip(),
        mistakes=mistakes,
        evidence=Evidence(verdict, evidence.strip()),
        try_it=try_it,
        quiz=quiz,
        takeaways=takeaways,
        figures=tuple(Figure(key, caption) for key, caption in figures),
    )


_LIVE_NOTE = "In early November 2026 the live record of windows that started while the market was open was 18 at 38.9% correct, below the roughly 51.8% break-even. That is a small sample, and it is not good."

_DAY = _app(
    slug="using-mentor/a-day-with-mentor",
    title="A day with Mentor: which page, when and why",
    summary="A trading day only needs four pages, in order.",
    concepts=("dashboard", "trade plan", "loop", "journal", "daily flow"),
    goal="Use the app in the same four steps each day.",
    body="""
The app has a lot of pages. A trading day only needs four, in order.

1. **Dashboard (2 minutes).** Three questions: what is the model's lean, is there dangerous news today (the **event freeze**), and how is your own trading going? If the freeze banner is up, your day may already be decided: stand down.
2. **Trade plan (2 minutes).** The system's read, turned into a ticket: stance, entry, stop, target, size for your account and risk. There are two honest outcomes: a sized plan, or **STAND ASIDE**. Both are answers. Run the checklist before any click.
3. **Your broker (1 minute, only if trading).** Copy the ticket. Place all three orders together. Walk away.
4. **Journal (2 minutes, after close).** Log what happened and how you behaved. The system grades its predictions; the journal is where you grade yourself.

Weekly, add five minutes on the **Loop** page: is the engine healthy, has it retrained, and what does its scoreboard say?

Notice what is not in this flow: staring at live charts, scrolling opinions, reacting to candles. The losing behaviours have no button.
""",
    steps=(
        "Open the Dashboard and read the freeze banner.",
        "Open Trade plan and follow it or stand aside.",
        "Place all orders together at your broker.",
        "Log it in the Journal.",
    ),
    example="""
At 16:00 Dubai time the Dashboard shows a freeze warning because of US inflation data. You open Trade plan anyway out of curiosity. It says **STAND ASIDE**. You do not trade today. That took four minutes, and it is a complete trading day.
""",
    mistakes=(
        "Hunting for another indicator after STAND ASIDE.",
        "Skipping the Journal because nothing happened.",
        "Opening the broker before reading the plan.",
    ),
    verdict=Verdict.FACT,
    evidence=f"This describes how the app is meant to be used. It does not mean the app's forecasts work. {_LIVE_NOTE}",
    try_it="Follow the four steps for five days and write down how long it takes.",
    quiz=(
        Q(
            "The Trade plan page says STAND ASIDE. What is the professional response?",
            (
                "Find a different indicator that says trade",
                "Nothing: no trade today is a valid, complete outcome",
                "Halve the size and trade anyway",
            ),
            1,
            "Standing aside is a real answer.",
        ),
    ),
    takeaways=(
        "Four pages, in order.",
        "Stand aside is a real answer.",
        "Grade yourself in the Journal.",
    ),
    figures=(("mentor-day-flow", "A daily flow through four pages."),),
)

_TICKET = _app(
    slug="using-mentor/reading-the-trade-ticket",
    title="Reading the trade ticket, line by line",
    summary="Five numbers, and how much to trust each one.",
    concepts=("entry", "stop-loss", "take-profit", "lots", "risk amount", "reward:risk"),
    goal="Know where each number on the ticket comes from, and how far to trust it.",
    body="""
The ticket looks simple. Each number comes from a different part of the system.

- **Stance** (LONG, SHORT or STAND ASIDE) comes from the current champion direction model. Below about 10% confidence, it refuses to pick a side.
- **Entry** is the latest price. It involves no prediction.
- **Stop loss** is the volatility model's expected move times 1.5. It answers: how far can price wander by noise? A wider-volatility day means a wider stop and a smaller position.
- **Take profit** is the stop distance times your chosen reward-to-risk (2:1 by default).
- **Position size** is your account × risk % ÷ stop distance in money. This is the one line where your numbers enter.

### Two lines people misread

**Money at risk** is the maximum loss if the stop is hit, not what the trade will lose. **Confidence** is not certainty: 43% confidence means a modest lean, and the banner will tell you to consider half size.
""",
    steps=(
        "Read the stance and confidence.",
        "Check that the stop is outside normal noise.",
        "Check that the money at risk matches your rule.",
        "Decide whether to act or stand aside.",
    ),
    example="""
Ticket: LONG at 1.0850, stop 1.0810 (40 pips), target 1.0930 (2:1), confidence 34%. Risk 1% of $5,000 = $50, so size = 0.12 lots.

A confidence of 34% means a modest lean. Taking the trade at normal size would be overruling the warning. The ticket shows its own doubt, so read it.
""",
    mistakes=(
        "Reading confidence as certainty.",
        "Changing the stop to fit a bigger size.",
        "Ignoring the money-at-risk line.",
    ),
    verdict=Verdict.MIXED,
    evidence=f"Volatility is more forecastable than direction, which gives the stop calculation a reasonable basis. The stance is unproven. {_LIVE_NOTE}",
    try_it="Open the Trade plan and explain each line to yourself in one sentence.",
    quiz=(
        Q(
            "Why is the ticket's stop-loss placed at about 1.5× the expected daily move?",
            (
                "To make the potential loss as small as possible",
                "So routine market noise can't hit it, only a genuinely wrong call",
                "Because brokers require it",
            ),
            1,
            "It sits just beyond normal noise.",
        ),
    ),
    takeaways=(
        "Each number has a different source.",
        "Confidence is not certainty.",
        "Read the doubt as carefully as the direction.",
    ),
    figures=(("ticket-anatomy", "Each line on the ticket, and where it comes from."),),
)

_ODDS = _app(
    slug="using-mentor/trusting-the-odds",
    title="When to trust the odds, and when to stand down",
    summary="How to read a probability without flinching.",
    concepts=("probability", "calibration", "sample size", "expectancy", "stand aside"),
    goal="Use the app's probabilities as one honest input, and judge them in batches.",
    body="""
**One forecast means almost nothing.** A 58% call that loses was not "wrong". What matters is whether, across the last hundred 58% calls, roughly 58 landed. That is **calibration**, and the post-mortem page measures it.

**The odds price the trade.** A 55% chance at 2:1 is a good business. At 1:2 it is a slow leak. The ticket already does this arithmetic.

**Respect the abstentions.** The system stands aside when the odds are near 50%, because after costs a coin flip charges admission. The most common way people destroy the value of a probabilistic tool is trading its "no" days.

**Watch the walking.** Every call here is logged before the fact and graded in public. Trust is earned in batches and is always provisional.
""",
    steps=(
        "Do not judge one forecast.",
        "Look at batches on the post-mortem page.",
        "Compare your override trades with plan trades in the journal.",
        "Follow stand-aside days.",
    ),
    example="""
For one month you log two groups: trades where you followed the plan, and trades you took when the plan said stand aside.

After 40 trades, the plan trades averaged +0.2R and your override trades averaged −0.4R. That number is more useful than any argument with yourself. (These numbers are an example only.)
""",
    mistakes=(
        "Calling a single loss proof the model is wrong.",
        "Trading on the app's 'no' days.",
        "Trusting the percentages without checking the record.",
    ),
    verdict=Verdict.MIXED,
    evidence=f"Calibration can be measured, and the system measures it. Being well calibrated is not the same as being profitable. {_LIVE_NOTE}",
    try_it="Log your overrides against the plan's calls for one month.",
    quiz=(
        Q(
            "The system said 62% up and price fell. Was the forecast wrong?",
            (
                "Yes, it said up and the market went down",
                "Not necessarily: 62% means down happens 38% of the time",
                "Yes, and the model should be retrained immediately",
            ),
            1,
            "Judge forecasts in batches.",
        ),
    ),
    takeaways=(
        "Judge forecasts in batches.",
        "The odds price the trade.",
        "Respect the system's abstentions.",
    ),
    figures=(("reliability", "Predicted probability against what actually happened."),),
)

_LOOP = _app(
    slug="using-mentor/watching-the-loop",
    title="Watching the learning engine",
    summary="The Loop page in four gauges.",
    concepts=("heartbeats", "drift watch", "champion", "promotion", "paper P&L"),
    goal="Read the Loop page and know what is worth worrying about.",
    body="""
The Loop page is the cockpit of the machine that works while you sleep.

- **Heartbeats:** each job (ingest, predict, resolve, retrain) shows its last run. A red ingest heartbeat means the data feed had a problem, and the system will refuse to predict on bad data.
- **Events:** drift detected, predictions skipped for data quality, champions promoted, alerts sent. An empty feed on a young system is normal.
- **Retrain decisions:** every challenger trained and whether it beat the champion on the same fresh data. Expect mostly "kept".
- **Paper P&L:** the honest scoreboard, only counting predictions made before the outcome.

### What worrying actually looks like

Not a losing week: noise loses weeks. Worry about heartbeats hours stale during market hours, repeated quality-skips, or live error drifting above the champion's test level without a drift-retrain firing.
""",
    steps=(
        "Check heartbeats weekly.",
        "Read the events feed.",
        "Check retrain decisions.",
        "Read the paper P&L as a record, not a promise.",
    ),
    example="""
The page says "champion kept: a worse model never ships". That is the gate doing its job. Most challengers lose, and that is expected.
""",
    mistakes=(
        "Worrying about a losing week.",
        "Treating 'champion kept' as failure.",
        "Reading the paper curve as a forecast.",
    ),
    verdict=Verdict.FACT,
    evidence=f"This describes what the page shows. The paper P&L records what happened and is not a guarantee. {_LIVE_NOTE}",
    try_it="Open the Loop page and write one sentence on the state of each gauge.",
    quiz=(
        Q(
            "A retrain ran and the page says 'champion kept'. Is that a failure?",
            (
                "Yes, retraining should always produce a better model",
                "No, the gate proved the current champion is still the best",
                "Yes, the system is stuck",
            ),
            1,
            "A worse model must never ship.",
        ),
    ),
    takeaways=(
        "Heartbeats, events, retrains, paper P&L.",
        "A worse model never ships.",
        "Noise loses weeks.",
    ),
    figures=(("drift-watch", "Live error compared with what the champion was tested at."),),
)

_CLOSE = _app(
    slug="using-mentor/close-your-own-loop",
    title="Close your own loop",
    summary="The system grades itself. You have to grade yourself.",
    concepts=("journal", "expectancy", "review", "process vs outcome", "improvement loop"),
    goal="Run your own loop of act, measure, adjust using the Journal.",
    body="""
Everything the system does is one loop: act, measure, adjust. The missing loop is yours.

1. **Log every trade**, including the ones you did not take when the plan said stand aside.
2. **Let the analytics build up.** Expectancy in R, win rate, profit factor. At least 20 trades before any conclusion, and 50 before a confident one.
3. **Weekly, read and tag.** Tags beat prose: `moved-stop`, `no-setup`, `oversized`, `revenge`.
4. **Change one thing.** The review's output is a single rule adjustment for next week.

### The graduation measure

When your journal shows **50 or more trades, no rule violations and positive expectancy**, you have evidence that you may be ready for the next account size. That is a modest bar, and Stage 10 shows why more trades tell you more. Either way, the mirror does not flatter you.
""",
    steps=("Log every trade.", "Tag it.", "Review weekly.", "Change one thing."),
    example="""
After 50 trades you have 42% wins, an average win of 2R, an average loss of 1R, and tags showing `moved-stop` 8 times.

Expectancy = 0.42 × 2 − 0.58 × 1 = **+0.26R**. If you stopped moving your stop you could keep more of that. Fix that one habit next.
""",
    mistakes=(
        "Grading trades by outcome alone.",
        "Changing five things at once.",
        "Treating 50 trades as proof of an edge.",
    ),
    verdict=Verdict.MIXED,
    evidence="The maths of expectancy is exact. There is no controlled study proving this particular loop improves results, and a 50-trade record is still a small sample.",
    try_it="Add tags to your last 10 trades and count them.",
    quiz=(
        Q(
            "You followed the plan exactly and the trade lost. How should the journal score it?",
            (
                "A bad trade, it lost money",
                "A good trade: process was perfect and the outcome was variance",
                "Don't log losers",
            ),
            1,
            "Process is what you control.",
        ),
    ),
    takeaways=(
        "You have to grade yourself.",
        "Tags make patterns visible.",
        "Change one thing at a time.",
    ),
    figures=(("journal-vs-memory", "The journal keeps what memory rewrites."),),
)

_WHOLE = _app(
    slug="using-mentor/whole-system-plain-english",
    title="How the whole system works, in plain English",
    summary="Five steps that repeat forever.",
    concepts=("data", "prediction", "grading", "learning loop", "honesty"),
    goal="Be able to explain the whole system to a friend.",
    body="""
Forget the jargon. The system is five steps that repeat.

**1. Gather the facts.** Every hour it downloads prices, interest rates, the dollar, a fear gauge called the VIX, and news mood. If the data looks broken, it refuses to continue.

**2. Make a careful guess.** The current best model (the **champion**) produces a probability, such as "58% chance up", with a confidence level, an expected range and a plain reason. Near 50/50 it says **stand aside**.

**3. Write the guess down first.** Each prediction is logged the moment it is made, before anyone knows what happens.

**4. Grade itself.** Later it marks each guess right or wrong, and keeps a report card.

**5. Learn, but only from proof.** It trains new models, and a new one only becomes champion if it measurably beats the current one and beats a coin flip, tested on data neither model has seen.

### The one thing to remember

Nobody can predict EUR/USD reliably. The honest edge on direction has been about 53% at best in testing, which is barely above a coin flip. The system's real value is discipline, honest measurement and risk management done automatically.
""",
    steps=(
        "Read the five steps.",
        "Explain them to someone in your own words.",
        "Find each step in the app.",
    ),
    example="""
At 14:00 the system gathers data, makes a "61% up" call and logs it. At 14:00 the next day, it grades that call. Next week, a new challenger model has a better score on new data, and only then does it replace the champion.
""",
    mistakes=(
        "Thinking the model knows what will happen.",
        "Forgetting costs when judging accuracy.",
        "Believing the app removes the need for your own judgement.",
    ),
    verdict=Verdict.MIXED,
    evidence=f"The grading loop is real, and every number is logged. The forecasts themselves are unproven and have recently been weak. {_LIVE_NOTE}",
    try_it="Explain the five steps out loud to someone, in under two minutes.",
    quiz=(
        Q(
            "In one sentence, what makes this system trustworthy?",
            (
                "It predicts the market perfectly",
                "It writes down every guess before the outcome, grades itself honestly and only keeps changes that prove better",
                "It uses the most data",
            ),
            1,
            "Honest grading is the foundation.",
        ),
    ),
    takeaways=(
        "Five steps, repeating.",
        "Every guess is logged first.",
        "A new model must prove itself.",
    ),
    figures=(("system-plain", "Five steps that repeat forever."),),
)

_TABS_1 = _app(
    slug="using-mentor/every-tab-trading",
    title="Every tab explained (1): the trading tabs",
    summary="Dashboard, Trade plan, Forecast, Tips, Predictions and Loop.",
    concepts=("dashboard", "trade plan", "forecast", "tips", "predictions", "loop"),
    goal="Know what each trading tab is for and when to open it.",
    body="""
- **Dashboard:** your morning briefing. The lean, event freeze and your own trading. Open it first every day.
- **Trade plan:** what to do now. A concrete ticket with stance, entry, stop, target and size, or **STAND ASIDE**.
- **Forecast:** the detail behind the read. Direction probability and expected range in more depth.
- **Tips:** a scorecard that tracks whether stock tips came true. A reality check on anyone claiming great calls.
- **Predictions:** the audit log. Every prediction ever made and whether it was right. This is the transparency tab.
- **Loop:** the learning engine's cockpit. Check it weekly.
""",
    steps=(
        "Open Dashboard first.",
        "Use Trade plan to act.",
        "Use Forecast for the why.",
        "Use Predictions and Loop to check the system.",
    ),
    example="""
You want to know why today's lean is bullish. Open **Forecast**, not the Trade plan. You want a ready ticket with a stop and a size: **Trade plan**. You want to check past calls: **Predictions**.
""",
    mistakes=(
        "Trying to use every tab every day.",
        "Treating a tip's score as a forecast.",
        "Skipping the audit log.",
    ),
    verdict=Verdict.FACT,
    evidence=f"A description of the tabs. None of these screens is evidence that the forecasts are good. {_LIVE_NOTE}",
    try_it="Open each tab once and write one line on what it does in your own words.",
    quiz=(
        Q(
            "You want the system's current, ready-to-place ticket with a stop and size. Which tab?",
            ("Predictions", "Trade plan", "Data health"),
            1,
            "Trade plan turns the read into a concrete ticket.",
        ),
    ),
    takeaways=("Dashboard first.", "Trade plan to act.", "Predictions and Loop to check."),
    figures=(("tabs-trading", "The trading tabs at a glance."),),
)

_TABS_2 = _app(
    slug="using-mentor/every-tab-toolkit",
    title="Every tab explained (2): the toolkit tabs",
    summary="Risk calculator, Journal, Backtester, Prices, Data health, Learn and Settings.",
    concepts=("risk calculator", "journal", "backtester", "prices", "data health", "settings"),
    goal="Know what each supporting tool is for.",
    body="""
- **Risk calculator:** enter account, risk %, entry and stop, and get the exact position size. Use it any time you plan a trade by hand.
- **Journal:** a logbook of your trades, your statistics and a weekly review space. This is where you grade yourself.
- **Backtester:** run a strategy over years of history with spread and slippage charged. It is built to expose fake edges.
- **Prices:** the raw chart and data coverage.
- **Data health:** whether your data is clean.
- **Learn:** this book, with progress tracking and quizzes.
- **Settings:** change your password, and add users with limited access.
""",
    steps=(
        "Size every trade with the calculator.",
        "Log every trade in the Journal.",
        "Test ideas in the Backtester before believing them.",
    ),
    example="""
You have a new idea. Backtester first. If it holds up after costs, paper-trade it. Risk calculator for the size. Journal for the result.
""",
    mistakes=("Sizing by feel.", "Believing a backtest with no costs.", "Ignoring data quality."),
    verdict=Verdict.FACT,
    evidence="A description of the tools. A backtest can show a strategy has been poor, but a good backtest does not prove a future edge.",
    try_it="Run one simple trade through the Risk calculator and record it in the Journal.",
    quiz=(
        Q(
            "Where do you record a trade you took and later review how disciplined you were?",
            ("Backtester", "Journal", "Prices"),
            1,
            "The Journal is your logbook.",
        ),
    ),
    takeaways=("Calculator, journal, backtester.", "Log every trade.", "Test before you trust."),
    figures=(("tabs-toolkit", "The toolkit tabs at a glance."),),
)

_WHAT = _app(
    slug="under-the-hood/what-we-can-predict",
    title="What this system can and cannot predict",
    summary="Direction is nearly random. Size is more predictable.",
    concepts=("direction", "volatility", "out-of-sample", "honesty"),
    goal="Know what the system can realistically forecast.",
    body="""
Most trading apps promise to tell you which way price will go. This one starts with an uncomfortable measurement from about ten years of EUR/USD: guessing the **direction** of the next move is around **53%** accurate at best, barely better than a coin flip and not enough to beat costs on many horizons.

So the system does three honest things.

- **It predicts what is more predictable.** The *size* of the next move (volatility) clusters and can be forecast. Direction mostly cannot.
- **It measures everything out of sample.** A new model ships only if it beats a simple baseline.
- **It gives the odds, not a verdict.** A forecast is a probability with a confidence band and a plain reason.

Markets are largely efficient: obvious information is already in the price. Being honest about this is what keeps you solvent.
""",
    steps=(
        "Read the forecast as a probability.",
        "Focus on the expected range.",
        "Do not treat a lean as a guarantee.",
    ),
    example="""
The forecast says 54% up, expected 24-hour range ±50 pips. The useful part is the range, which helps you set a stop and size. The 54% tells you very little by itself.
""",
    mistakes=(
        "Treating a lean as a guarantee.",
        "Believing any app that claims high direction accuracy.",
        "Ignoring the range.",
    ),
    verdict=Verdict.MIXED,
    evidence=f"Volatility clustering is well documented, and direction is known to be hard to forecast. The system's own direction record is unproven and recently weak. {_LIVE_NOTE}",
    try_it="Find today's forecast range, and compare with what actually happened tomorrow.",
    quiz=(
        Q(
            "Which is more forecastable?",
            ("Direction", "The size of the next move", "Both equally"),
            1,
            "Volatility clusters. Direction is close to random.",
        ),
    ),
    takeaways=(
        "Direction is hard.",
        "Volatility is more predictable.",
        "A forecast is odds, not a verdict.",
    ),
    figures=(("honest-thesis", "What is more predictable, and what is less."),),
)

_DATA = _app(
    slug="under-the-hood/where-the-data-comes-from",
    title="Where the numbers come from",
    summary="Four kinds of data and how they are cleaned.",
    concepts=("data", "failover", "FRED", "GDELT", "Twelve Data"),
    goal="Know what data the system uses and how it is prepared.",
    body="""
A forecast is only as good as its data. The system pulls four kinds of real data.

- **Prices** from **Twelve Data**, with **Yahoo Finance** as a backup. If one source is down, the other fills in. This is called **failover**.
- **Interest rates** from the FRED database: US 2-year and 10-year yields and the yield curve.
- **The dollar and fear gauge:** a broad US dollar index and the VIX, from FRED.
- **News mood:** a daily sentiment score from GDELT.

Sources rarely agree perfectly, and different feeds stamp a "daily" bar differently. So the system **aligns** everything to one clock and **de-duplicates** overlaps. Every value is stored so it never has to be downloaded again for training.
""",
    steps=(
        "Know your data sources.",
        "Check Data health before trusting a forecast.",
        "Expect sources to disagree slightly.",
    ),
    example="""
Twelve Data returns an error at 14:02. The system asks Yahoo instead. Nothing else changes for the user, and the failover is recorded in the logs.
""",
    mistakes=(
        "Assuming two data sources agree.",
        "Ignoring a failing data feed.",
        "Believing a chart you have not checked.",
    ),
    verdict=Verdict.FACT,
    evidence="A description of the app's data. Clean data does not create an edge, but dirty data can create false ones. One lesson later covers a real data bug in this system.",
    try_it="Open Data health and note which sources are currently being used.",
    quiz=(
        Q(
            "What is failover?",
            ("Using a backup source when the first fails", "A kind of order", "Selling at a loss"),
            0,
            "It keeps data flowing when one source breaks.",
        ),
    ),
    takeaways=(
        "Data comes from several sources.",
        "Failover keeps it running.",
        "Data needs cleaning.",
    ),
    figures=(("data-pipeline", "From several sources to one clean history."),),
)

_FEAT = _app(
    slug="under-the-hood/what-the-model-sees",
    title="What the model looks at, with no peeking at the future",
    summary="A short list of features, built only from the past.",
    concepts=("features", "lookahead", "overfitting", "point-in-time"),
    goal="Understand the model's inputs, and how the system prevents lookahead bias.",
    body="""
The model reads a short list of **features**: numbers that summarise the recent past. They come in three small families:

- **Price and indicators:** returns, distance from moving averages, RSI, MACD, ATR.
- **News mood:** the GDELT sentiment score and its trend.
- **Macro drivers:** changes in US rates, the yield curve, the dollar index and the VIX.

The list is kept small on purpose. More inputs let a model memorise noise.

### The golden rule: no peeking

The most common way backtests lie is **lookahead bias**: using information from the future to "predict" the past. This system forbids it by design. A feature can be built only from bars on or before that moment. That is why its honest accuracy numbers are lower than a naive backtest would show.
""",
    steps=(
        "List what a model uses.",
        "Check that each input was known at the time.",
        "Prefer few, meaningful inputs.",
    ),
    example="""
A rule that uses "today's close" to make a decision that is filled at today's close is peeking. The system only uses bars that had already finished.
""",
    mistakes=(
        "Adding features until accuracy rises.",
        "Using revised data.",
        "Standardising with the full sample.",
    ),
    verdict=Verdict.FACT,
    evidence="A description of the design. Avoiding lookahead does not make the forecasts good; it stops them from being falsely good.",
    try_it="Pick a feature in your own idea. Ask when it would actually have been known.",
    quiz=(
        Q(
            "Why keep the feature list small?",
            ("To reduce overfitting", "To save electricity", "Regulators require it"),
            0,
            "Fewer inputs give less room to fit noise.",
        ),
    ),
    takeaways=("Few, meaningful inputs.", "No peeking at the future.", "Honest numbers are lower."),
    figures=(
        ("feature-families", "Three families of features."),
        ("point-in-time", "Features use only what was known at the time."),
    ),
)

_DIRECTION = _app(
    slug="under-the-hood/predicting-direction",
    title="Predicting direction: rules, then trees, then humility",
    summary="How the direction forecast works and how it is checked.",
    concepts=("rule model", "gradient boosting", "regime", "baseline"),
    goal="Understand the direction forecast and the honesty gate around it.",
    body="""
For the direction question the system runs a small pipeline.

1. **A transparent rule model:** a few if-this-then-that rules you could check by hand. This is the **baseline**.
2. **A gradient-boosting model:** many small decision trees, each fixing the last one's mistakes, producing a probability of "up".
3. **A regime check:** before trusting the model, it asks whether today's conditions look like those it trained on. If they do not, it shrinks confidence or abstains.

### The honesty gate

The fancy model is only used if it beats the simple rule out of sample. On EUR/USD direction, it barely does, because direction is nearly random. The system reports the real number and never dresses a coin flip up as a signal.
""",
    steps=(
        "Compare a model with a simple baseline.",
        "Check that conditions match training.",
        "Report probabilities, not certainties.",
    ),
    example="""
Today's volatility is well above its training range. The regime check lowers the confidence, and the ticket shows STAND ASIDE, even though the raw model leaned up.
""",
    mistakes=(
        "Assuming machine learning is automatically better.",
        "Ignoring regime warnings.",
        "Forgetting that the baseline may be just as good.",
    ),
    verdict=Verdict.WEAK,
    evidence=f"The evidence for direction forecasting at this horizon is weak in general, and this system has not proven an edge. {_LIVE_NOTE}",
    try_it="On the Forecast page, find the regime information for today, and note whether it changed the call.",
    quiz=(
        Q(
            "When is the gradient-boosting model used?",
            ("Only if it beats the simple rule out of sample", "Always", "Never"),
            0,
            "It must prove itself against the baseline.",
        ),
    ),
    takeaways=(
        "Rule model first.",
        "ML only if it proves better.",
        "Direction is close to random.",
    ),
    figures=(("direction-model", "Rules, then trees, then a regime check."),),
)

_RANGE = _app(
    slug="under-the-hood/predicting-the-range",
    title="Predicting the range, not the arrow",
    summary="Why volatility can be forecast, and how the band is built.",
    concepts=("volatility", "EWMA", "conformal prediction", "range"),
    goal="Understand the range forecast and how to use it.",
    body="""
Direction is nearly random, but **volatility clusters**: big days tend to follow big days. So the system predicts a **range**.

- **The baseline (EWMA):** a formula that gives recent moves more weight. This is a strong volatility forecast by itself.
- **A machine-learning model:** it only ships if it beats the EWMA baseline on proper scores.
- **A coverage band,** from a method called **conformal prediction**: a range with a stated hit rate, for example "the move lands between 13 and 179 pips about 90% of the time."

Knowing the expected range tells you how far to place a stop, and whether today is a "sit on your hands" kind of day.
""",
    steps=("Read the expected range.", "Set your stop outside it.", "Size for that stop."),
    example="""
The forecast says the 24-hour expected move is ±50 pips. A stop at 1.5× that is 75 pips. Your position size then follows from your risk per trade.
""",
    mistakes=(
        "Reading the range as a forecast of direction.",
        "Using a stop inside the normal range.",
        "Treating the band as a guarantee.",
    ),
    verdict=Verdict.MIXED,
    evidence="Volatility clustering is one of the best-established findings in finance. Whether the app's particular forecasts remain good live is still being measured, and the band's stated coverage should be checked against realised results.",
    try_it="For a week, write the app's expected range each morning, and compare it with what the market did.",
    quiz=(
        Q(
            "Why can the system honestly forecast a range but not direction?",
            (
                "Volatility clusters; direction is close to random",
                "It has a secret indicator",
                "Ranges are easier to draw",
            ),
            0,
            "Big moves follow big moves.",
        ),
    ),
    takeaways=("Range, not arrow.", "EWMA is a strong baseline.", "A band with a stated hit rate."),
    figures=(("vol-cone", "The expected range widens with the horizon."),),
)

_PROBA = _app(
    slug="under-the-hood/trustworthy-probabilities",
    title="Making 60% actually mean 60%",
    summary="Calibration, and how the system checks it.",
    concepts=("calibration", "reliability diagram", "ECE", "isotonic regression"),
    goal="Understand what calibration is and why it matters.",
    body="""
A probability is only useful if it is honest. If the model says 60% a hundred times, up should happen about 60 of those times. Raw model scores usually are not honest in this way.

### How it is checked

A **reliability diagram** plots what the model said against what actually happened. Perfect honesty is a diagonal line. One number sums up the gap: the **expected calibration error (ECE)**. Lower is better.

### How it is fixed

The system fits a small correction called **isotonic regression** on data the model did not see. It only keeps this correction if it lowers the ECE without hurting accuracy. On this system's data, it has roughly halved the calibration error.

Calibration makes the numbers trustworthy. It does not by itself make them profitable.
""",
    steps=(
        "Look at the reliability diagram.",
        "Compare predicted and actual.",
        "Judge in batches.",
    ),
    example="""
Over 100 calls at about 60% up, the market rose 53 times. The model was overconfident by about 7 points. A calibration step would pull 60% closer to 53%.
""",
    mistakes=(
        "Thinking calibration means profit.",
        "Judging calibration on a few calls.",
        "Skipping the check.",
    ),
    verdict=Verdict.MIXED,
    evidence=f"Calibration is measurable and standard. A well-calibrated forecast can still be unprofitable. {_LIVE_NOTE}",
    try_it="Open the post-mortem and find the calibration chart. Are the points near the diagonal?",
    quiz=(
        Q(
            "What does a reliability diagram show?",
            (
                "What was predicted against what happened",
                "A candlestick pattern",
                "Account balance",
            ),
            0,
            "The diagonal means perfect honesty.",
        ),
    ),
    takeaways=(
        "60% should mean 60%.",
        "Calibration is checked on unseen data.",
        "Calibration is not the same as profit.",
    ),
    figures=(("reliability", "Predicted probability against what actually happened."),),
)

_LOOP_SELF = _app(
    slug="under-the-hood/the-self-learning-loop",
    title="The system that grades itself",
    summary="Predict, resolve, post-mortem, and champion against challenger.",
    concepts=("audit log", "post-mortem", "champion", "challenger"),
    goal="Understand how the system checks its own work.",
    body="""
A forecaster that never checks its own work cannot be trusted. This one runs a loop.

1. **Predict.** Each forecast is written to an audit log immediately.
2. **Resolve.** Once the outcome is known, it is marked a hit or a miss.
3. **Post-mortem.** Hits and misses are combined: how accurate, how well calibrated, what conditions went with the errors?
4. **Champion against challenger.** Periodically a fresh **challenger** is trained. It replaces the **champion** only if it is measurably better on held-out data.

The loop steadily improves **calibration and robustness**. It does not manufacture a market-beating edge on direction, and the system does not pretend it does.
""",
    steps=(
        "Look up a past prediction in the audit log.",
        "Check whether it resolved correctly.",
        "Read the retrain decisions.",
    ),
    example="""
Each week the system trains a new challenger. In most weeks the page reads 'champion kept'. That is the loop working as designed.
""",
    mistakes=(
        "Expecting every retrain to help.",
        "Thinking a loop creates an edge.",
        "Skipping the post-mortem.",
    ),
    verdict=Verdict.MIXED,
    evidence=f"The grading is real and logged. The loop has not shown a durable direction edge. {_LIVE_NOTE}",
    try_it="Find one old prediction in the audit log and check its result.",
    quiz=(
        Q(
            "When does a challenger replace the champion?",
            (
                "When it is measurably better on held-out data",
                "Every week",
                "When a human likes it",
            ),
            0,
            "No model is promoted on hope.",
        ),
    ),
    takeaways=(
        "Log first, grade later.",
        "A new model must prove itself.",
        "The loop builds trust, not edge.",
    ),
    figures=(("learning-loop", "Predict, resolve, post-mortem, retrain."),),
)

_SIZE = _app(
    slug="under-the-hood/forecast-to-position-size",
    title="From a forecast to a position size",
    summary="Honest forecast, honest stop, honest size.",
    concepts=("stop", "position size", "event freeze", "risk of ruin"),
    goal="See how a forecast becomes a stop and a position size.",
    body="""
A forecast is worthless if it does not change what you do. The volatility forecast connects straight to the risk engine.

- **A sensible stop.** Placed about 1.5× the expected move, so routine noise does not hit it.
- **A size that respects your budget.** The calculator works out the exact lot size, and always rounds down.
- **An event freeze.** When volatility is forecast to be unusually high, the app warns you to sit out or halve size.
- **Risk of ruin.** A simulator shows the odds of a deep drawdown under your rules.

The whole point: **honest forecast, honest stop, honest size.**
""",
    steps=(
        "Read the expected range.",
        "Set the stop beyond it.",
        "Compute the size.",
        "Check the event freeze.",
    ),
    example="""
Expected 24-hour move: 50 pips. Stop: 75 pips. Risk: 1% of $5,000 = $50. Size: $50 / (75 × $10) = 0.06 lots, rounded down.
""",
    mistakes=(
        "Using a stop inside the expected move.",
        "Ignoring the event freeze.",
        "Rounding up.",
    ),
    verdict=Verdict.MIXED,
    evidence="The arithmetic is exact. The volatility input is the part most supported by evidence. No sizing rule can make a bad forecast into a good one, but it can stop a bad forecast from ruining you.",
    try_it="Use the Trade plan page and check each step of the chain by hand.",
    quiz=(
        Q(
            "Why does the calculator round down?",
            ("The risk budget is a ceiling", "It saves commission", "It is a bug"),
            0,
            "Rounding up would exceed your risk limit.",
        ),
    ),
    takeaways=("Forecast leads to stop.", "Stop leads to size.", "Round down."),
    figures=(("risk-sizing", "Forecast, stop, size."),),
)

_TIPS = _app(
    slug="under-the-hood/tracking-tipsters",
    title="Tracking tipsters: measurement, not advice",
    summary="How the Tips tool measures what actually happened.",
    concepts=("tipster", "scorecard", "risk-adjusted", "expectancy"),
    goal="Understand how the Tips tool works and what it can show you.",
    body="""
Group chats hand out stock tips constantly. This tool does not judge if a tip is good. It **measures** what happened.

1. **Parse:** an assistant pulls out each ticker and what was suggested.
2. **Price:** it records the price on the day the tip was given.
3. **Score:** it tracks the return and builds a scorecard: hit rate, average return, whether "buy on dip" calls really dipped.
4. **Leaderboard:** it ranks tipsters by risk-adjusted return, so one big win does not crown someone reckless.
5. **"What if I had followed?"** a backtest mechanically buys every actionable call, sized by the same 1% risk discipline.

There are no predictions here. Every price already happened. Past calls do not predict future ones, and none of this is advice.
""",
    steps=(
        "Paste a tip.",
        "Check the scorecard.",
        "Look at the equity curve before believing a hit rate.",
    ),
    example="""
A tipster shows 8 wins out of 10, but one loss was 40%. The risk-adjusted ranking and equity curve show that 8 wins out of 10 did not make up for it.
""",
    mistakes=(
        "Ranking tipsters by hit rate alone.",
        "Assuming past tips predict future ones.",
        "Treating the scorecard as advice.",
    ),
    verdict=Verdict.FACT,
    evidence="This is measurement of past results, and it is not a forecast. Survivorship bias applies: the tipsters you see are often the ones who got lucky.",
    try_it="Add one real tip you received. Check how it has done since.",
    quiz=(
        Q(
            "What does the tipster tool do?",
            ("Measures what happened", "Predicts which tips will work", "Gives financial advice"),
            0,
            "It keeps score, nothing more.",
        ),
    ),
    takeaways=(
        "Measure, do not assume.",
        "Risk-adjust before ranking.",
        "Past calls do not predict future ones.",
    ),
    figures=(("tipster", "Parse, price, score and rank."),),
)

_WATCH = _app(
    slug="under-the-hood/the-watchdogs",
    title="The watchdogs: quality gate, drift watch, heartbeats",
    summary="Three guards against the ways an automatic system quietly rots.",
    concepts=("quality gate", "drift", "heartbeats", "events"),
    goal="Understand the three watchdogs that protect the system.",
    body="""
A system that runs unattended needs guards.

- **The quality gate** inspects the recent bars before every prediction. A mid-week hole in the data or a stale feed means **no prediction this hour**, with the reason logged. It knows the FX calendar, so the normal weekend gap does not false-alarm.
- **The drift watch** runs after every grading pass. It compares the error of the last roughly 40 live predictions with the champion's test error. If it degrades past the margin, it triggers a retrain, with a 24-hour cooldown.
- **Heartbeats and events** make it all visible. Every job reports its last run. Nothing important happens silently.

None of this adds predictive edge. It adds **trustworthiness**.
""",
    steps=(
        "Check that heartbeats are green.",
        "Read the events feed for quality skips.",
        "Look for drift events.",
    ),
    example="""
The data feed delivers a 12-hour hole in the middle of Tuesday. The system skips the prediction, logs a quality event, and says so on the Loop page.
""",
    mistakes=(
        "Ignoring red heartbeats.",
        "Thinking watchdogs make the forecasts better.",
        "Being alarmed by the normal weekend gap.",
    ),
    verdict=Verdict.FACT,
    evidence="A description of system safeguards. They prevent known failure modes. They do not create an edge.",
    try_it="Find the most recent event in the Loop's events feed and work out what happened.",
    quiz=(
        Q(
            "The data feed delivers a 12-hour hole in the middle of Tuesday. What does the system do?",
            (
                "Guesses anyway",
                "Skips the prediction loudly and logs a quality event",
                "Stops forever",
            ),
            1,
            "Refusing beats answering from garbage.",
        ),
    ),
    takeaways=(
        "Refuse rather than guess.",
        "Drift triggers retraining.",
        "Nothing important happens silently.",
    ),
    figures=(("drift-watch", "Live error compared with test error."),),
)

_SILENT = _app(
    slug="under-the-hood/knowing-when-to-say-nothing",
    title="Knowing when to say nothing",
    summary="Why the model is allowed to decline, and what that does to its score.",
    concepts=("abstention", "margin", "coverage", "Brier score"),
    goal="Understand abstention and how to read a low coverage number.",
    body="""
For most of its life, this system had to produce a direction every hour. That obligation quietly damaged its score.

Sort every hour by how confident the model was. At the two extremes, it may be picking up something real. In the huge middle, at 51%, 49%, 52%, it is describing noise with a decimal point attached. The middle is most hours, and that is what EUR/USD is over a 24-hour horizon.

So the model now learns a **margin**, the distance from 50/50 a probability must reach before it is willing to call anything. With a margin of 0.06, 58% up is called and 52% up is not.

The system reports **coverage**, the share of hours it speaks. A low coverage number is neutral. What matters is whether the calls it did make scored better than all hours would have.
""",
    steps=(
        "Read the coverage number.",
        "Compare the score of the calls made with all hours.",
        "Treat stand-aside as data.",
    ),
    example="""
The system acts on 30% of hours. Those hours have a hit rate of 54%, and all hours would have been 50.5%. Whether that is enough depends on the breakeven, which is the subject of the next chapter.
""",
    mistakes=(
        "Assuming low coverage is bad.",
        "Forcing a call on every hour.",
        "Ignoring calibration in the tails.",
    ),
    verdict=Verdict.MIXED,
    evidence=f"Abstaining is a measurable design choice. It is not evidence of an edge. {_LIVE_NOTE}",
    try_it="On the Predictions page, look at how often the model abstained in the last week.",
    quiz=(
        Q(
            "The system says it acts on 30% of hours. Is that good or bad?",
            (
                "Bad: it should always act",
                "Good if those 30% score better than all hours would; the number itself is neutral",
                "It is meaningless",
            ),
            1,
            "Coverage by itself is neutral.",
        ),
    ),
    takeaways=(
        "Saying nothing is allowed.",
        "Coverage is neutral.",
        "Judge the calls it does make.",
    ),
    figures=(("abstention", "The model speaks only when it is far enough from 50/50."),),
)

_COST = _app(
    slug="keeping-honest/the-cost-hurdle",
    title="Better than a coin flip is not enough: the cost hurdle",
    summary="A model that is right 51% of the time can still lose money.",
    concepts=("breakeven", "spread", "cost hurdle", "Brier"),
    goal="Know why a forecast has to clear a cost hurdle, and how that hurdle is set.",
    body="""
A model that is right 51% of the time beats a coin flip. It can also lose money on every trade.

You pay the spread and slippage whether you win or lose. The mentor charges **1.2 pips per round trip** on EUR/USD: a 0.8-pip spread plus 0.2 pips of slippage on each leg.

A winning call earns the move minus the cost, and a losing call loses the move plus the cost. So you need to win a little more than half just to stand still.

**Breakeven = 50% + cost ÷ (2 × typical move).**

For the 24-hour forecast with a typical move of about 34 pips, that is about **51.8%**. For the 5-day forecast, about 84 pips, it is about **50.7%**. These numbers are measured from history, not typed in.

The promotion gate uses this as a floor. A challenger must also clear a coverage floor and other rules before replacing the champion.
""",
    steps=(
        "Find the cost per round trip.",
        "Find the typical move.",
        "Compute breakeven.",
        "Compare the record with it.",
    ),
    example="""
100 calls at 51% right on the 24-hour forecast, with a 34-pip typical move:

- 51 wins × 32.8 = +1,673 pips.
- 49 losses × 35.2 = −1,725 pips.
- Net: about **−52 pips**.

A win rate that beats a coin still loses.
""",
    mistakes=(
        "Celebrating anything above 50%.",
        "Using a typical move from a different horizon.",
        "Forgetting slippage.",
    ),
    verdict=Verdict.FACT,
    evidence="The arithmetic is exact, given the stated cost and typical move. As of November 2026, the app's live record on the 24-hour horizon has been below this hurdle in the recent sample.",
    try_it="Compute the breakeven for your own spread and typical move on your market.",
    quiz=(
        Q(
            "A model is right 51% of the time on the 24-hour forecast. What happens after costs?",
            (
                "It makes a small profit",
                "It loses money, because the hurdle is about 51.8%",
                "It breaks even",
            ),
            1,
            "The hurdle is above 50%.",
        ),
        Q(
            "Why is the hurdle lower for the 5-day forecast than the 24-hour one?",
            (
                "The same 1.2-pip cost is a smaller slice of a bigger typical move",
                "Spreads are lower on longer trades",
                "5-day models are better",
            ),
            0,
            "A fixed cost matters less on a larger move.",
        ),
        Q(
            "A challenger has a Brier score of 0.240, speaks on 40% of hours, and is right 50.5% of the time on the 24-hour lane. Is it promoted?",
            (
                "Yes, its Brier score is good",
                "No, it fails the breakeven floor: honest probabilities don't pay the spread",
                "Yes, it beats a coin",
            ),
            1,
            "Calibration alone is not enough.",
        ),
    ),
    takeaways=(
        "Beating a coin is not enough.",
        "Breakeven depends on cost and move size.",
        "The gate enforces this.",
    ),
    figures=(
        ("breakeven-hurdle", "The win rate you need rises above 50% because of costs."),
        ("promotion-floors", "Several floors a challenger must clear."),
    ),
    minutes=8,
)

_ABSTAIN = _app(
    slug="keeping-honest/abstaining-by-profit",
    title="Saying no opinion when a call cannot pay",
    summary="Choosing when to speak by money, not by score.",
    concepts=("margin", "coverage floor", "breakeven", "abstention"),
    goal="Understand how the margin is chosen.",
    body="""
The earlier lesson introduced **abstention**. This one explains how the margin is picked.

At first, the margin was chosen to give the best **Brier score** (a measure of calibration) on the calls kept. Brier knows nothing about the spread, so the model could fall silent on hours that would have paid.

Now the system tries margins from zero upward, and asks two questions for each:

1. Is it still speaking on **at least 15% of hours**?
2. Is the hit rate on those hours **at or above breakeven**?

Among margins that pass both, it picks the **loosest**, because once calls pay, more calls means more money. If none pass, the model does not abstain at all, and the promotion gate judges it as it is.
""",
    steps=(
        "List candidate margins.",
        "Test each against the two rules.",
        "Pick the loosest that passes.",
    ),
    example="""
Breakeven 51.8%, coverage floor 15%:

- Margin 0: 50.6% on all hours. Fails.
- Margin 0.04: 52.3% on 38% of hours. Passes.
- Margin 0.08: 54% on 16% of hours. Passes.
- Margin 0.10: 57% on 9% of hours. Fails coverage.

The system picks **0.04**, the loosest that passes.
""",
    mistakes=(
        "Optimising calibration while ignoring costs.",
        "Picking the tightest margin because its win rate looks best.",
        "Fitting margins on the data used for grading.",
    ),
    verdict=Verdict.FACT,
    evidence="A description of how the margin is chosen. It does not mean any margin produces a profit.",
    try_it="Take a list of probabilities and outcomes. Try two margins and compare the hit rate and how often each speaks.",
    quiz=(
        Q(
            "Breakeven is 51.8% and the coverage floor is 15%. Band 1 speaks on 60% of hours at 52.5% right; band 2 on 25% at 54%; band 3 on 8% at 60%. Which wins?",
            ("Band 1, the loosest band whose calls still clear breakeven", "Band 2", "Band 3"),
            0,
            "It picks the loosest passing band.",
        ),
        Q(
            "No quiet band leaves calls that clear breakeven. What happens?",
            (
                "The model speaks on every hour and the promotion gate judges it as it is",
                "The system shuts down",
                "The model is promoted",
            ),
            0,
            "It does not abstain, and is judged as it is.",
        ),
    ),
    takeaways=(
        "Margins are chosen by profit rules.",
        "At least 15% coverage.",
        "Failing is allowed.",
    ),
    figures=(("abstain-by-profit", "Margins, coverage and breakeven."),),
    minutes=7,
)

_WIN_RATE = _app(
    slug="keeping-honest/honest-win-rates",
    title="Honest win rates: overlap, sample size and the truth emerging",
    summary="Three problems with win rates, and how the mentor handles each.",
    concepts=("independent windows", "overlap", "sample size", "confidence interval"),
    goal="Read the app's win rates correctly, including how little a small sample proves.",
    body="""
A win rate is one of the most persuasive numbers in trading and one of the easiest to get wrong.

### Problem 1: one market day counted 24 times

The 24-hour forecast is made every hour, and adjacent calls share 23 of their 24 hours. If EUR/USD rallies on Tuesday, every 'down' call made on Monday is wrong together. In July 2026 the Loop page once showed a win rate of **11%**. It was one short stance counted about 18 times. Counted honestly, the same stretch was **56%**.

**The fix: independent windows.** Starting from the newest call and walking back, a call is kept only if its window ends before the previously kept call began. That comes to roughly one independent result per trading day.

### Problem 2: a small sample says nothing

Five right out of five happens by chance about once in 32 tries. So the app gives a verdict only after **30 independent windows**, and shows a 95% range.

### Problem 3: the truth emerges slowly

A wide range that still includes breakeven means the edge is not proven. In mid-October 2026 the 24-hour record was **79 independent windows**, a win rate of **59.5%**, and a 95% range of **48.5% to 69.6%**. The range still included breakeven (51.77%), and it needs roughly **161** windows to tell. {live}
""".replace("{live}", _LIVE_NOTE),
    steps=(
        "Find the independent-window count.",
        "Find the 95% range.",
        "Check whether the range includes breakeven.",
    ),
    example="""
79 windows at 59.5% looks strong. Its 95% range is 48.5% to 69.6%, which includes the 51.77% breakeven. So the honest verdict is: **not proven yet**.
""",
    mistakes=(
        "Counting overlapping calls.",
        "Reading a small sample as proof.",
        "Reporting a win rate without its range.",
    ),
    verdict=Verdict.SUPPORTED,
    evidence=f"This is basic statistics. Overlap inflates apparent sample size, and confidence intervals on win rates are wide at small sample sizes. {_LIVE_NOTE}",
    try_it="Take your own record of forecasts. Make them independent. How many results remain?",
    quiz=(
        Q(
            "The 24-hour forecast made about 120 calls this week (5 trading days). Roughly how many independent results does the week add?",
            ("About 120", "About 5, roughly one per trading day", "About 60"),
            1,
            "Overlapping calls count as far fewer independent results.",
        ),
        Q(
            "A forecast is right on 7 of 8 independent windows. What can you conclude?",
            (
                "It has a strong edge",
                "Nothing yet: below 30 independent results no verdict is possible",
                "It is broken",
            ),
            1,
            "A small sample proves very little.",
        ),
        Q(
            "Win rate 59.5% on 79 independent windows, 95% range 48.5% to 69.6%, breakeven 51.77%. Is the edge proven?",
            ("Yes", "No, the range still includes breakeven", "It depends on the weather"),
            1,
            "If the range includes breakeven, it can't be told apart from no edge.",
        ),
    ),
    takeaways=("Count independent windows.", "Show the range.", "Small samples prove little."),
    figures=(
        ("overlapping-windows", "Overlapping forecasts share most of their hours."),
        ("interval-shrink", "The range narrows as the sample grows."),
    ),
    minutes=8,
)

_DATA_NEW = _app(
    slug="keeping-honest/new-data-sources",
    title="New data: a better price feed, and who is positioned where",
    summary="Twelve Data first, and what the COT report adds.",
    concepts=("Twelve Data", "failover", "COT", "publication lag"),
    goal="Understand the app's price feed choice and why COT data needs a publication delay.",
    body="""
Two changes to what the system reads.

**Prices.** Since mid-July 2026 **Twelve Data** has been the primary source, with **Yahoo Finance** as backup, using **failover**. Twelve Data stamps bars cleanly on the hour. The older years of daily history came from Yahoo, and its definition of a "day" differs slightly: this is known and flagged.

**COT.** The CFTC's weekly report shows how different groups are positioned, including large speculators in euro futures. The mentor derives two clues: how crowded speculators are, and how that changed from last week. COT is different in kind from the model's other inputs, which are mostly versions of price.

**The publication lag.** The report shows positions as of Tuesday but appears on Friday. A model can only use it from **Saturday**, after it has been published. Using it earlier would be peeking at the future.

So far, COT has shown no measurable help in this system.
""",
    steps=(
        "Know the source of your prices.",
        "Respect publication dates.",
        "Check whether a new data source actually helps.",
    ),
    example="""
A COT report shows Tuesday's positions, but it arrives on Friday afternoon. If the model used Tuesday's data on Wednesday's prediction, that would be lookahead.
""",
    mistakes=(
        "Using data before it was published.",
        "Assuming more data must help.",
        "Mixing bars from different definitions unknowingly.",
    ),
    verdict=Verdict.FACT,
    evidence="A description of the data. COT is real and published by a regulator, but so far it has not shown measurable help in this system.",
    try_it="Find out what time your favourite data source publishes, and when you can truly use it.",
    quiz=(
        Q(
            "A COT report shows large speculators' positions as of Tuesday. From when may a model use it?",
            ("Tuesday", "From Saturday, after it has been published", "The following month"),
            1,
            "Using it earlier would be lookahead.",
        ),
        Q(
            "Twelve Data returns an error at 14:02. What happens?",
            (
                "The prediction is lost forever",
                "The system asks Yahoo instead and carries on",
                "All data is deleted",
            ),
            1,
            "Failover keeps it running.",
        ),
    ),
    takeaways=(
        "Failover keeps data flowing.",
        "Respect publication delays.",
        "New data must prove itself.",
    ),
    figures=(("cot-publication-lag", "When COT data is actually usable."),),
    minutes=7,
)

_LIVE = _app(
    slug="keeping-honest/learning-from-live-mistakes",
    title="Learning from its own live mistakes",
    summary="Correcting confidence, retraining, and when a champion is demoted.",
    concepts=("recalibration", "stretch factor", "demotion", "champion lifecycle"),
    goal="Understand how live results feed back into the system, and how little they can change.",
    body="""
Live results now do more than trigger retrains.

### Correcting how sure the model sounds

If the model's 60% calls have been landing 53% of the time, the honest thing is to say 53%. The correction is a single **stretch factor**: below 1 pulls calls towards 50%, above 1 pushes them outwards. 50% stays at 50%, and a call can never change sides.

**Safety rules:** only independent live results of the current champion count. Below **30 results** no correction is fitted. The stretch is chosen on the older half of the record and checked on the newer half, in time order, and ships only if it clearly helps.

### Retrains and the champion's lifecycle

A challenger is compared with the champion **re-scored on the same fresh data**, because some periods are easier to predict than others.

### Demotion

A champion that fails its re-check is not demoted immediately. It takes **three failures in a row**, and a pass resets the count, so one bad patch does not kill a good model.
""",
    steps=(
        "Check the live record since promotion.",
        "See if a correction was fitted.",
        "Look at the demotion count.",
    ),
    example="""
Over 40 independent live results, the champion's 65% calls were right about 55% of the time. If the correction also holds on the newer half of the record, the system can stretch those calls down towards 55%.
""",
    mistakes=(
        "Letting recent results change everything.",
        "Comparing with old stored scores.",
        "Demoting after one bad patch.",
    ),
    verdict=Verdict.FACT,
    evidence="A description of the process. These are safeguards. They do not show the model has an edge.",
    try_it="Find the live correction status on the Loop page. Note how many independent results are needed before anything changes.",
    quiz=(
        Q(
            "Over 40 independent live results, the champion's 65% calls were right about 55% of the time. What can live recalibration do?",
            (
                "Change direction of calls",
                "Pull its stated confidence towards 50%, if that holds up on the newer half",
                "Replace the model",
            ),
            1,
            "It only rescales confidence.",
        ),
        Q(
            "The champion fails its re-check on one retrain, passes the next, then fails again. Is it demoted?",
            (
                "Yes",
                "No: it takes three failures in a row, and a pass resets the count",
                "It is deleted",
            ),
            1,
            "Three in a row are needed.",
        ),
        Q(
            "Why is the challenger compared with the champion re-scored on the same fresh data?",
            (
                "Some periods are easier to predict; only the same data makes it a fair race",
                "It is cheaper",
                "To cheat",
            ),
            0,
            "Compare both on the same data.",
        ),
    ),
    takeaways=(
        "Correct confidence, not direction.",
        "30-result floor.",
        "Three strikes before demotion.",
    ),
    figures=(
        ("live-recalibration", "Stretching confidence towards reality."),
        ("champion-lifecycle", "A champion's path from promotion to demotion."),
    ),
    minutes=8,
)

_BARS = _app(
    slug="keeping-honest/finished-bars",
    title="Clean prices: storing and grading only finished bars",
    summary="A real bug, told plainly.",
    concepts=("forming bar", "finished bar", "provisional", "regrading"),
    goal="Understand why only finished bars can be used, and what happened when they were not.",
    body="""
This lesson is about a bug, told plainly, because how a system handles its own mistakes says a lot.

An hourly bar is only final when the hour is over. Until then it is **forming**.

From mid-July to 13 October 2026, the system fetched each bar minutes after it opened, saved it and never updated it. The database was told to ignore later versions, so the finished bar was thrown away.

The audit found **2,310 hourly bars** and **86 daily bars** saved before they finished, typically with only **23%** of the hour's real range. **774** bars were more than 5 pips off, and the worst close was **66.5 pips** wrong. **275** extra Yahoo rows were stamped between hours.

### The fix

Only finished bars are stored, stamped exactly on the hour. A bar saved too early is **provisional**, and the next fetch replaces it. A finished bar is never overwritten, because feeds quietly revise by fractions of a pip.

Predictions already made were re-graded against the correct bars. After the re-grade, the 24-hour win rate on the same 79 windows rose from 53.2% to 59.5%. That shows a measurement fix, not new skill.
""",
    steps=(
        "Check when a bar is treated as final.",
        "Do not save forming bars as final.",
        "Re-grade with corrected data.",
    ),
    example="""
The system saves the 14:00 hourly bar at 14:08. It holds only 8 minutes of a 60-minute bar, so its high, low and close are not final.
""",
    mistakes=("Saving forming bars.", "Treating a re-grade as new skill.", "Hiding a data bug."),
    verdict=Verdict.FACT,
    evidence="An account of a real bug and the fix. The numbers came from the audit. The re-grade did not make the model any better; it corrected the record.",
    try_it="Look at the last bar on your own chart. Is it finished? What would happen if you treated it as final?",
    quiz=(
        Q(
            "The system saves the 14:00 hourly bar at 14:08. What is wrong with that?",
            (
                "Nothing",
                "It holds only 8 minutes of a 60-minute bar, so its high, low and close are not final",
                "The bar is too large",
            ),
            1,
            "A forming bar isn't final.",
        ),
        Q(
            "After the re-grade, the 24-hour win rate on the same 79 windows rose from 53.2% to 59.5%. What does that show?",
            (
                "The model got better",
                "The same calls were graded against the correct bars: a measurement fix, not new skill",
                "A coding error",
            ),
            1,
            "The fix changed the measurement.",
        ),
    ),
    takeaways=(
        "Only finished bars are final.",
        "Mistakes should be told plainly.",
        "A re-grade is not new skill.",
    ),
    figures=(
        ("forming-vs-finished", "A forming bar against a finished one."),
        ("grade-own-bar", "Grading against the bar the forecast was about."),
    ),
    minutes=8,
)

_LAB = _app(
    slug="keeping-honest/strategy-lab-testing",
    title="The strategy lab: testing a trading plan properly",
    summary="Six answers, realistic fills, walk-forward blocks and a held-out period.",
    concepts=("strategy lab", "walk-forward", "held-out", "fills"),
    goal="Understand how the Strategy Lab tests trading plans.",
    body="""
A forecast answers one question. Trading needs several more. The **Strategy Lab**, added in October 2026, tests complete trading plans.

### A plan is six answers

1. **Why might this work?** A plain reason.
2. **Entry:** for example, close above the highest high of the last 20 days.
3. **Stop:** a multiple of ATR or a structural level.
4. **Target:** an R-multiple.
5. **Time limit.**
6. **Size,** from the app's own risk engine, never more than 2% of the account per trade.

Results are in **R**.

### Realistic fills

A signal at a bar's close is filled at the next bar's open, made worse by half the spread plus slippage. If the market opens beyond the stop or target, the order is cancelled. If one bar touches both, the system assumes the worse outcome.

### Walk-forward and held-out

Settings for each time block are chosen using only the blocks before it, and the last section of history is held out. A plan has to be positive on the held-out period by itself, with at least 10 trades.
""",
    steps=("Write the plan as six answers.", "Run it in the Lab.", "Look at the held-out result."),
    example="""
A plan averages +0.3R per trade in development, but loses money in the held-out period. It does **not** pass.
""",
    mistakes=(
        "Writing a plan with no reason.",
        "Tuning on the held-out period.",
        "Believing a backtest with optimistic fills.",
    ),
    verdict=Verdict.MIXED,
    evidence="The Lab uses fair testing rules. As of mid-October 2026, every plan tested had been rejected, so the Lab is not recommending any strategy.",
    try_it="Write a plan as the six answers. If you cannot state the reason, ask yourself why you want to trade it.",
    quiz=(
        Q(
            "Why does the lab choose each block's settings using only the blocks before it?",
            (
                "To make the run faster",
                "That is the only choice a trader could have made at the time; using later data would be peeking",
                "To reduce code",
            ),
            1,
            "It avoids peeking into the future.",
        ),
        Q(
            "A plan averaged +0.3R per trade in development but lost money on the held-out period. Does it pass?",
            (
                "Yes",
                "No: the held-out period must be positive on its own, with at least 10 trades",
                "It depends on the colour",
            ),
            1,
            "Held-out data is the check.",
        ),
    ),
    takeaways=(
        "A plan has six answers.",
        "Fills are deliberately realistic.",
        "The held-out period must stand alone.",
    ),
    figures=(
        ("plan-anatomy", "The parts of a trading plan."),
        ("walk-forward-holdout", "Walk-forward blocks and a held-out section."),
    ),
    minutes=8,
)

_BAR = _app(
    slug="keeping-honest/the-rising-bar",
    title="Why the bar rises with every idea tried",
    summary="Count every try, and raise the standard to match.",
    concepts=("multiple testing", "trial ledger", "deflated Sharpe", "paper trading"),
    goal="Understand why the Strategy Lab's bar gets harder with every test.",
    body="""
Ask 20 people to flip a coin ten times, and someone gets eight heads. They are not skilled. There were just 20 of them. Testing many trading ideas works the same way. The best of 74 settings will look good even if none has any edge.

**The fix: count every try, and raise the bar.**

- The **trial ledger** is append-only. Every setting ever tested is written there and nothing is deleted.
- Each idea gets a **score**: its average R, divided by how much its results vary, times the square root of the number of trades.
- Across many tries, the best score from luck alone climbs: about 2.4 for 70 tries and 3.0 for 500. The lab adds a further margin. This approach is known as the **deflated Sharpe ratio** (Bailey and López de Prado, 2014).

In mid-October 2026, with **74 trials** in the ledger, the bar was about **4.4**. "Buy the dip in a trend" averaged +0.17R on its held-out trades, and was rejected because its score (about 1.0) was far below the bar.

### Paper trading

Plans that pass go to paper trading. Promotion is considered only every **30 trades**, because checking after each trade and stopping at the first pass would find edges in pure noise.
""",
    steps=(
        "Count all your attempts.",
        "Raise your standards to match.",
        "Do not stop testing when it looks good.",
    ),
    example="""
You try 74 settings, and the best has a score of 2.4. That looks strong by itself. The Lab's bar for that many trials was about 4.4, so it is rejected.
""",
    mistakes=(
        "Forgetting failed trials.",
        "Stopping when results look good.",
        "Comparing a best-of-many with a single test.",
    ),
    verdict=Verdict.SUPPORTED,
    evidence="The statistical reasoning is well established (Bailey and colleagues; Harvey et al.). The specific bar is a design choice of this app. No strategy has passed so far.",
    try_it="Write the number of variations you tried for your last trading idea, and how that changes how much you should trust it.",
    quiz=(
        Q(
            "Why does the bar rise with every idea tested, even the ones that failed?",
            (
                "It is a mistake",
                "More tries means a higher best score from luck, and forgetting failures makes survivors look special",
                "Failures earn points",
            ),
            1,
            "Every attempt counts.",
        ),
        Q(
            "'Buy the dip in a trend' averaged +0.17R on its held-out trades. Why was it still rejected?",
            (
                "The code broke",
                "Its overall score (about 1.0) was far below the bar (about 4.4) set by 74 trials",
                "It lost money",
            ),
            1,
            "The bar accounts for how many things were tried.",
        ),
        Q(
            "Why does paper trading only consider promotion every 30 trades?",
            (
                "To save time",
                "Checking after every trade and stopping at the first pass would find edges in pure noise",
                "Regulators require it",
            ),
            1,
            "Stopping when it looks good is a form of cheating.",
        ),
    ),
    takeaways=(
        "Every try counts.",
        "The bar rises with the number of tries.",
        "No idea has passed the bar so far.",
    ),
    figures=(
        ("rising-bar", "The best score from luck climbs with the number of tries."),
        ("lab-lifecycle", "A plan's path through the Lab."),
    ),
    minutes=8,
)

_OPS = _app(
    slug="keeping-honest/running-unattended",
    title="Running unattended: reports, alerts and the maintenance agent",
    summary="How the system runs for months without anyone touching it.",
    concepts=("self-report", "issue code", "alerts", "maintenance agent"),
    goal="Understand the app's self-reporting and maintenance setup.",
    body="""
Trade Mentor is meant to run for months unattended. That takes three layers: the app looks after its models, a maintenance agent looks after the code, and the server's safety net decides whether any change goes live.

### The self-report

Every Saturday at 06:00 UTC the system writes a report on itself, available at `/api/v1/health/report`. It contains summary numbers and never any secrets. It covers health checks, each forecast's live record against its breakeven, week-on-week accuracy, retrain decisions, failing jobs and the strategy lab's status.

Every problem gets a **stable code**, so a reader can tell an old problem from a new one.

### Telegram alerts

Messages are written in three parts: a headline saying what is happening, what the system has already done, and what you should do, if anything.

### The maintenance agent

A daily agent reads the report and either fixes problems within strict rules or writes a log entry saying no change was needed. **Doing nothing is a valid run.**
""",
    steps=(
        "Read the weekly report.",
        "Check whether problems are new or old.",
        "Do not expect a change every day.",
    ),
    example="""
It is Tuesday and the report is all green. The agent changes nothing, and writes a log entry saying so. That is a valid run.
""",
    mistakes=(
        "Assuming green reports mean a profitable system.",
        "Expecting the agent to always change something.",
        "Skipping alerts.",
    ),
    verdict=Verdict.FACT,
    evidence="A description of the operational setup. Health checks are about whether the system is working correctly, not whether it makes money.",
    try_it="Open the health report and find one issue code, or confirm there is none.",
    quiz=(
        Q(
            "It is Tuesday and the report is all green. What does the agent do?",
            (
                "Changes something anyway",
                "Changes nothing and writes a log entry saying so",
                "Restarts the server",
            ),
            1,
            "Doing nothing is a valid run.",
        ),
        Q(
            "What does each problem in the self-report carry, so tomorrow's reader can tell an old problem from a new one?",
            ("A stable issue code", "A random number", "A different colour every day"),
            0,
            "Stable codes let you track issues over time.",
        ),
    ),
    takeaways=(
        "The system reports on itself.",
        "Stable codes track issues.",
        "Doing nothing is a valid run.",
    ),
    figures=(("autonomy-loop", "The self-report, agent and alert cycle."),),
    minutes=7,
)

_SAFETY = _app(
    slug="keeping-honest/the-safety-net",
    title="The safety net: auto-deploy, rollback and protected thresholds",
    summary="What stops a bad change from going live.",
    concepts=("auto-deploy", "rollback", "protected thresholds", "watchdog"),
    goal="Understand the deploy safety net and why some numbers are locked.",
    body="""
An automated maintainer is only safe if something it cannot control checks its work.

### Auto-deploy, every 10 minutes

A program on the server checks for new code. When it finds some, it:

1. **Refuses** the change if it touches a protected file, changes a protected threshold, adds a skipped test or deletes a test file.
2. **Backs up the database** first if the change alters its structure.
3. **Builds and starts** the new version.
4. **Demands proof of health:** the health page and the report page must answer within five minutes, and the logs must be clean.
5. **Rolls back** to the previous version if anything fails.
6. **Reports** on Telegram and in the self-report.

Between deploys it acts as a **watchdog**, restarting the app if it stops answering.

The running copy of this program sits outside the code repository, so a bad change cannot disable the thing that undoes bad changes.

### Protected thresholds

These numbers stop the system from flattering itself: the promotion margin (0.002), the coin-flip and breakeven floors, the 15% coverage floor, demotion after 3 failures, and the 30-result floor. Only a human can change them, through a deliberate override.
""",
    steps=(
        "Know which numbers are locked.",
        "Trust the rollback process.",
        "Check deploy results in the report.",
    ),
    example="""
A change deploys, but the report page does not answer within five minutes. The server rolls back to the previous version and tells you on Telegram.
""",
    mistakes=(
        "Lowering a threshold to get a verdict sooner.",
        "Assuming a passing deploy means better results.",
        "Editing protected files casually.",
    ),
    verdict=Verdict.FACT,
    evidence="A description of the deployment process. It protects against bad code and self-flattering changes. It does not prove the system earns money.",
    try_it="Look at the latest deploy status in the health report and note the result.",
    quiz=(
        Q(
            "A change deploys, but the report page doesn't answer within five minutes. What happens?",
            (
                "Nothing",
                "The server rolls back to the previous version and tells you on Telegram",
                "The database is deleted",
            ),
            1,
            "Rollback is automatic.",
        ),
        Q(
            "The agent tries to lower the 30-result floor to 15 'to get verdicts sooner'. What happens?",
            (
                "It is accepted",
                "The server refuses it: it is a protected threshold, and lowering it would let noise pass as proof",
                "Nothing checks this",
            ),
            1,
            "Protected thresholds cannot be changed automatically.",
        ),
        Q(
            "Why does the copy of the deploy program that actually runs live outside the code repository?",
            (
                "So a bad change cannot disable the very thing that undoes bad changes",
                "To save space",
                "It runs faster",
            ),
            0,
            "The safety net must not depend on the code it guards.",
        ),
    ),
    takeaways=(
        "Refuse, back up, build, verify, roll back.",
        "Protected numbers stop self-flattery.",
        "The safety net sits outside the code.",
    ),
    figures=(
        ("deploy-gate", "The deploy gate."),
        ("protected-thresholds", "The numbers only a human can change."),
    ),
    minutes=8,
)

_SUMMARY = _app(
    slug="keeping-honest/what-it-can-and-cannot-do",
    title="What the mentor can and cannot do, honestly",
    summary="The plain summary.",
    concepts=("honesty", "limits", "scorecard"),
    goal="Hold the correct picture of what this app can do.",
    body=f"""
After all of the above, here is the plain summary.

### What it does well

- **Measuring risk.** How far EUR/USD is likely to move is more predictable than which way. The volatility forecast sets the stop distance, and that sets position size.
- **Refusing to fool itself.** The cost hurdle, independent windows, the 30-result floor, held-out tests, the rising bar and thresholds only a human can change.
- **The risk engine and the journal,** which size every trade from the stop and keep you honest about your own behaviour.

### What is not proven

- **Direction.** In mid-October 2026 the 24-hour champion's record was 79 independent windows with a plausible range that still included breakeven. {_LIVE_NOTE}
- **Trading plans.** The Strategy Lab has tested 8 ideas and rejected all 8. Nothing is recommended.
- **Positioning data.** COT has so far shown no measurable help.

### What it will never do

Place a trade or connect to a broker. It advises and you act. Promise returns: "62% up" means *probably*, under the conditions it was measured in, never *certainly*.

### What this means for you

Treat the direction forecast as **one input**, never the only reason for a trade. Treat **stand aside** as a good result. Size from your stop, journal your behaviour, and remember the system cannot do your discipline for you.

**Education only. Not financial advice. Most retail traders lose money.**
""",
    steps=(
        "Use forecasts as one input.",
        "Treat stand aside as a complete answer.",
        "Use the risk engine.",
        "Keep your journal.",
    ),
    example="""
The direction forecast says 62% up, confidence 40%. You size from the stop, you check the news freeze, you remember the live record is unproven, and you decide accordingly.
""",
    mistakes=(
        "Treating forecasts as signals to obey.",
        "Assuming the app will make you money.",
        "Ignoring the honesty checks.",
    ),
    verdict=Verdict.MIXED,
    evidence=f"Risk measurement has the firmest footing. Direction is unproven and has recently been weak. {_LIVE_NOTE}",
    try_it="Write three sentences: what you will rely on the app for, what you will not, and what you must do yourself.",
    quiz=(
        Q(
            "Which part of the system stands on the firmest ground?",
            (
                "The direction forecast",
                "The volatility forecast and risk sizing, plus the honesty checks",
                "Telegram alerts",
            ),
            1,
            "Risk measurement and honesty checks are firmest.",
        ),
        Q(
            "The direction forecast says 62% up. How should you use it?",
            (
                "Trade it at full size",
                "As one input: size from your stop, and remember its record isn't proven",
                "Ignore everything else",
            ),
            1,
            "One input among many, and unproven.",
        ),
    ),
    takeaways=(
        "Risk measurement is firmest.",
        "Direction is unproven.",
        "The system cannot do your discipline for you.",
    ),
    figures=(("honest-scorecard", "An honest scorecard of what the system can do."),),
    minutes=7,
)

CHAPTERS = (
    chapter(
        "mentor",
        "using-mentor",
        "Trading with Mentor, day to day",
        "How to use this app like a professional.",
        (_DAY, _TICKET, _ODDS, _LOOP, _CLOSE, _WHOLE, _TABS_1, _TABS_2),
    ),
    chapter(
        "mentor",
        "under-the-hood",
        "Under the hood: how the mentor predicts",
        "Every data source, prediction method and watchdog.",
        (
            _WHAT,
            _DATA,
            _FEAT,
            _DIRECTION,
            _RANGE,
            _PROBA,
            _LOOP_SELF,
            _SIZE,
            _TIPS,
            _WATCH,
            _SILENT,
        ),
    ),
    chapter(
        "mentor",
        "keeping-honest",
        "How the mentor keeps itself honest",
        "The cost hurdle, honest win rates, clean prices, the strategy lab and the safety net.",
        (_COST, _ABSTAIN, _WIN_RATE, _DATA_NEW, _LIVE, _BARS, _LAB, _BAR, _OPS, _SAFETY, _SUMMARY),
    ),
)
