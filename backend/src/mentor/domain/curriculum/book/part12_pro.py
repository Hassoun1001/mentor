"""Stage 12 — Running it as a professional."""

from __future__ import annotations

from mentor.domain.curriculum.book._kit import (
    Bar,
    Chart,
    Evidence,
    Figure,
    Lesson,
    Q,
    Verdict,
    chapter,
    fact,
)
from mentor.domain.curriculum.charts import equity_paths

_PLATFORMS = Lesson(
    slug="toolkit/charts-and-platforms",
    title="Charts and platforms",
    summary="Analysis and execution are two different jobs.",
    est_minutes=5,
    key_concepts=("TradingView", "MetaTrader", "broker platform", "charting", "alerts"),
    figures=(Figure("charts-platforms", "One tool for analysis, one tool for execution."),),
    goal="Pick tools that fit each job, and keep your setup simple.",
    body_md="""
Trading needs two kinds of tool, and they are often different.

- **Charting and analysis:** platforms such as **TradingView** offer fast charts, indicators, drawing tools and alerts.
- **Execution:** your **broker's platform** or **MetaTrader**. Orders are placed here. Its job is reliable fills, clear tickets and correct margin.

### How to use them

- Keep charts simple: mark major levels and the trend, and resist stacking ten indicators.
- Set **alerts** instead of watching all day. Staring leads to overtrading.
- Always confirm the spread and your stop on the order ticket before you click. The chart is analysis. The ticket is real money.

This app is your analysis and risk layer: forecasts, volatility range, position-size calculator and journal, alongside whatever platform you execute on.
""".strip(),
    charts=(
        Chart(
            title="A simple chart beats a busy one",
            caption="Illustrative: how a beginner's and an experienced trader's chart might differ in tools used. This is a judgement and not data.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Number of tools on chart",
            bars=(Bar("New trader", 12, "danger"), Bar("Experienced trader", 3, "accentSoft")),
        ),
    ),
    steps=(
        "Choose one charting tool.",
        "Choose one execution platform.",
        "Reduce your charts to the tools your plan needs.",
        "Set alerts for your key levels.",
    ),
    example_md="""
A new trader has twelve indicators on screen, and every one disagrees.

They replace them with: one moving average, ATR and two marked levels. Decisions become easier and calmer. Results do not improve overnight, but the chart stops being a source of confusion.
""".strip(),
    mistakes=(
        "Believing better tools will fix the problem.",
        "Using a platform you have not tested.",
        "Ignoring the spread on the ticket.",
    ),
    evidence=fact("These are practical suggestions. No tool produces an edge."),
    try_it="Remove every indicator from your chart that your written plan does not need.",
    quiz=(
        Q(
            "What is the main job of an execution platform?",
            ("Reliable orders", "Pretty charts", "News"),
            0,
            "Execution is where money actually moves.",
        ),
        Q(
            "Why use alerts?",
            ("So you can stop staring at the chart", "To increase spreads", "To replace stops"),
            0,
            "Alerts reduce the temptation to overtrade.",
        ),
    ),
    takeaways=(
        "Separate analysis from execution.",
        "Keep charts simple.",
        "Check the ticket before clicking.",
    ),
)

_WEEK = Lesson(
    slug="toolkit/weekly-workflow",
    title="A weekly workflow",
    summary="Plan, trade, journal, review. A loop that turns trades into learning.",
    est_minutes=6,
    key_concepts=("routine", "preparation", "review", "process"),
    figures=(Figure("weekly-routine", "A weekly loop of plan, trade, journal and review."),),
    goal="Set up a simple weekly loop that fits your life.",
    body_md="""
Tools only help inside a routine. A simple weekly loop beats sporadic brilliance.

- **Plan (weekend):** mark the higher-timeframe trend and major levels, read next week's calendar, and write the few setups you will wait for. Decide your risk per trade.
- **Trade (during the week):** take only the planned setups. Size with the calculator, set the stop from the volatility read, and log the entry before you click.
- **Journal (daily):** a two-minute entry per trade: what you saw, what you did, how you felt. Tag mistakes honestly.
- **Review (weekend):** sort the journal by R, read your best and worst five, tag patterns, adjust **one** thing. Then plan again.

Markets are mostly noise. Your process is the only part you fully control. This loop is the same predict, resolve, review cycle the app runs on its own forecasts.
""".strip(),
    charts=(
        Chart(
            title="Hours in a realistic trading week",
            caption="Illustrative schedule for a swing trader with a full-time job.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Hours per week",
            bars=(
                Bar("Weekend plan", 1.0, "accent"),
                Bar("Trading", 2.5, "accent"),
                Bar("Journal", 0.5, "accentSoft"),
                Bar("Weekend review", 0.5, "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Block an hour for planning at the weekend.",
        "Trade only the setups you planned.",
        "Journal the same day.",
        "Review at the weekend.",
        "Change only one thing per week.",
    ),
    example_md="""
Sunday, 30 minutes: EUR/USD weekly uptrend, level at 1.0850, CPI on Wednesday. Setup: pullback to 1.0850 after CPI with a stop below 1.0810.

Monday and Tuesday: no setup. No trades. That is success.

Wednesday: CPI causes a spike, the setup is invalidated. No trade. Friday: a clean setup appears; you trade at planned size.

Sunday: review shows you took one trade and followed your rules.
""".strip(),
    mistakes=(
        "Planning nothing and then improvising.",
        "Trading setups that are not in the plan.",
        "Skipping the weekend review.",
    ),
    evidence=fact(
        "A habit rather than a claim. There is little controlled research on this. It works by making your choices visible and repeatable."
    ),
    try_it="Put your four weekly blocks in your calendar for next week.",
    quiz=(
        Q(
            "Which is part of the weekly loop?",
            ("Planning, trading, journaling, reviewing", "Only trading", "Only news reading"),
            0,
            "Each step feeds the next.",
        ),
        Q(
            "If no setup appeared this week, you…",
            (
                "Were successful, if you followed your plan",
                "Should invent one",
                "Should change strategy",
            ),
            0,
            "No setup means no trade.",
        ),
    ),
    takeaways=(
        "Plan, trade, journal, review.",
        "No setup is a good result.",
        "Change one thing at a time.",
    ),
)

_DAY = Lesson(
    slug="becoming-pro/daily-routine",
    title="A professional's trading day",
    summary="Short, repeatable and calm.",
    est_minutes=6,
    key_concepts=("routine", "preparation", "execution window", "review", "screen time"),
    figures=(Figure("daily-routine-timeline", "A short daily routine beats all-day watching."),),
    goal="Build a short daily routine that makes bad hours impossible.",
    body_md="""
The image of a trader glued to six monitors is a movie prop. A good retail day is short and almost a ritual.

**Before the session (15–20 minutes)**

- Read the calendar. This app's dashboard shows high-impact events.
- Check the system's read: direction lean, volatility regime, expected range.
- Decide in advance: am I trading today? Which setup? Where would the stop go? If nothing qualifies, that is a **complete, successful trading day**.

**During your window (30–60 minutes)**

- Watch only for the setup you chose. It appears, you run the checklist, place entry, stop and target together, and walk away.
- If it does not appear, you are done.

**After the close (10 minutes)**

- Journal the trade or the no-trade.
- Check the system's scoreboard.

**Weekly (30 minutes)**

- Read the week's journal. Tag mistakes. Pick **one** thing to do differently.

Almost everything that loses beginners money happens outside those windows: the bored lunchtime entry, the revenge trade, the 11 p.m. "one more".
""".strip(),
    charts=(
        Chart(
            title="Where a day's minutes go",
            caption="Illustrative schedule of a focused retail trading day.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Minutes per day",
            bars=(
                Bar("Preparation", 20, "accent"),
                Bar("Trading window", 45, "accent"),
                Bar("Journal and review", 10, "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Write your daily schedule, in your local time.",
        "Set your trading window.",
        "Close the platform when the window ends.",
        "Journal each day, including no-trade days.",
    ),
    example_md="""
A trader in Dubai with a job:

- 16:30: read the calendar, check the app, decide on setups (15 minutes).
- 17:00–18:00: trading window.
- 18:00: journal (10 minutes).
- The rest of the day: no chart.

Total: about 1 hour 25 minutes, at most. The time you spend away from the chart protects your account.
""".strip(),
    mistakes=(
        "Watching all day.",
        "Trading outside your window.",
        "Treating a no-trade day as wasted.",
    ),
    evidence=fact(
        "A practice, not a tested claim. More screen time generally leads to more trades and more costs, and research on overtrading gives good reason to keep it short."
    ),
    try_it="Write your daily routine on one page. Follow it for five days and note any time you broke it.",
    quiz=(
        Q(
            "How much screen time does a process-driven day need?",
            ("All day", "Roughly 1–2 focused hours around your session", "None, ever"),
            1,
            "More screen time usually means more mistakes.",
        ),
        Q(
            "Your setup did not appear. Today was…",
            ("Wasted", "Successful, if you followed your plan", "A reason to force a trade"),
            1,
            "Doing nothing is a real decision.",
        ),
    ),
    takeaways=("Keep the day short.", "Decide before the session.", "No setup means no trade."),
    sources=("barber-odean-2000",),
)

_DEMO = Lesson(
    slug="becoming-pro/from-demo-to-real",
    title="From demo to real money: the ladder",
    summary="Nobody should start at full size. Each rung has an exam.",
    est_minutes=7,
    key_concepts=("demo account", "micro lots", "graduation criteria", "drawdown"),
    figures=(Figure("account-ladder", "Each rung has its own exam."),),
    goal="Move from practice to real money in stages, using numbers rather than feelings.",
    body_md="""
Nobody should start at full size. The path is a ladder, and each rung has an exam.

**Rung 1 — Demo (1–3 months).** Practice with fake money. The goal is **mechanics**, not profit: 50 or more trades placed exactly as your written plan says, a complete journal, and no rule violations.

**Rung 2 — Tiny live (3–6 months).** Real money, micro lots, risking cents to a few dollars per trade. This rung exists to meet the **feelings**. The heartbeat on a real stop-out cannot be simulated. Exam: positive expectancy across 50 or more live trades, and your rules survive.

**Rung 3 — Meaningful size, stepwise.** Increase risk only after each 50-trade block stays disciplined. A common rule: double size only after a profitable, rule-clean quarter, and **halve** it after a 10% drawdown. Sizing down after losses is what professionals do and gamblers do not.

A word on the numbers: 50 trades is a useful starting exam, but not proof of an edge. Stage 10 shows why.

### Where this app fits

It can help through rungs 0–2. Paper-trade its calls, size by rules and journal everything, and let its honest scoreboards tell you when your numbers justify the next rung. Remember the app's own record is unproven.
""".strip(),
    charts=(
        Chart(
            title="A sensible ladder of risk per trade",
            caption="Illustrative example of how risk per trade might step up over time, conditional on passing each exam.",
            data_kind="illustrative",
            kind="bars",
            y_format="pct",
            y_label="Risk per trade",
            bars=(
                Bar("Demo", 0, "muted"),
                Bar("Tiny live", 0.1, "accent"),
                Bar("Small live", 0.25, "accent"),
                Bar("Normal", 0.75, "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Trade 50 demo trades by the rules.",
        "Move to tiny real money.",
        "Trade 50 live trades with a complete journal.",
        "Increase size in steps, only after clean blocks.",
        "Reduce size after drawdowns.",
    ),
    example_md="""
A trader passes the demo rung with 60 rule-following trades. They go live with 0.01 lots, risking about $3 per trade on a $2,000 account.

Their first live losing streak of five trades costs about $15 and feels awful. They keep following the rules. After 50 trades, expectancy is slightly positive and they raise risk a step. Nothing about this is exciting, which is the point.
""".strip(),
    mistakes=(
        "Skipping demo because it feels fake.",
        "Jumping to full size after a good week.",
        "Not reducing size after a large drawdown.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
There is no controlled study proving any particular ladder. But there is plenty of evidence that most retail traders lose quickly (ESMA; Barber et al.; Chague et al.). Going slowly is a way to limit the cost of finding out whether you are one of the few who can do this.
""".strip(),
    ),
    try_it="Write down your own rungs, with an exam for each and the size of your risk at each rung.",
    quiz=(
        Q(
            "What is the test for moving from demo to tiny live?",
            (
                "Doubling the demo account fast",
                "50+ trades following the written plan",
                "One month without any losses",
            ),
            1,
            "The test is rule-following.",
        ),
        Q(
            "What should you do after a 10% drawdown?",
            ("Halve size", "Double up", "Open a new account"),
            0,
            "Reducing size after losses protects you.",
        ),
    ),
    takeaways=(
        "Trade through rungs: demo, tiny, then larger.",
        "Each rung has an exam.",
        "Reduce size after drawdowns.",
    ),
    sources=("esma-cfd-2018", "barber-day-2014", "chague-2020"),
)

_PROP = Lesson(
    slug="pro/prop-firm-challenges",
    title="Prop-firm challenges",
    summary="How they work, what they cost, and how few pass.",
    est_minutes=9,
    key_concepts=("prop firm", "challenge", "daily loss limit", "max drawdown", "profit target"),
    goal="Understand how prop-firm challenges work, and make an informed decision about them.",
    body_md="""
A **proprietary trading firm**, or prop firm, offers to let you trade its money if you pass a test. You usually pay a fee for the test, known as a **challenge**.

### Typical rules

- A **profit target**, such as 8–10%.
- A **daily loss limit**, such as 4–5%.
- A **maximum drawdown**, such as 8–12%.
- Sometimes a minimum number of trading days, or rules on news trading.

Break a rule and the challenge is over. Many firms simulate the trading rather than use real market capital.

### How firms make money

Their income comes in large part from challenge fees. Industry-reported figures suggest only about **12–14% of challenges pass** and about **7% of buyers are ever paid**. Those figures are unaudited estimates, but they fit what firms report.

### Before you pay

- Read every rule carefully.
- Check whether trading is simulated.
- Size small. A 5% daily limit means you need to risk much less than you might.
- Treat the fee as tuition, not an investment.

### Regulation

The rules are unsettled. The CFTC sued one firm, My Forex Funds, in 2023, and the case was dismissed in 2025. Many firms operate from offshore. Check the firm's status and the rules where you live.
""".strip(),
    charts=(
        Chart(
            title="Prop-firm funnel (industry estimates)",
            caption="Share of challenge buyers reaching each stage. These figures are unaudited and vary by source and firm.",
            data_kind="published",
            kind="bars",
            y_format="pct",
            y_label="Share of challenge buyers",
            source_note="Industry-reported, e.g. Track360 (2026). Treat as rough estimates.",
            bars=(
                Bar("Buy a challenge", 100, "muted"),
                Bar("Pass the challenge", 13, "warn"),
                Bar("Ever paid", 7, "danger"),
            ),
        ),
        Chart(
            title="Sizing for a 5% daily loss limit",
            caption="Calculated: consecutive full losses that would break a 5% daily limit.",
            data_kind="calculated",
            kind="bars",
            y_format="plain",
            y_label="Losses in a row before limit",
            x_label="Risk per trade",
            bars=(
                Bar("0.5% risk", 10, "accentSoft"),
                Bar("1% risk", 5, "accent"),
                Bar("2% risk", 2.5, "warn"),
                Bar("5% risk", 1, "danger"),
            ),
        ),
    ),
    steps=(
        "Read all the rules before buying.",
        "Compute how many losses fit your daily limit.",
        "Keep risk per trade small.",
        "Avoid news if the rules restrict it.",
        "Decide in advance how many challenges you will pay for.",
    ),
    example_md="""
A $100,000 challenge costs **$500**. The target is 10%, the daily limit is 5%, and the maximum drawdown is 10%.

At 1% risk per trade, five losses in a day end the challenge. So at 0.5% risk per trade, you need about 20 net wins of 1R to reach the target, and you have room for 10 losses in a day.

If you pass and receive 80% of profits, your first $5,000 of profit pays you $4,000. But if you fail three challenges first, you have paid $1,500. The honest expected value depends on your real pass rate.
""".strip(),
    mistakes=(
        "Risking too much per trade to hit the target quickly.",
        "Not reading the rules.",
        "Buying challenge after challenge.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
Pass rates are estimates from industry sources and vary widely, with figures from 5% to 25% reported. Most sources agree that most buyers do not get paid. Published research on this is thin.

The legal position is unsettled in many countries. Do not assume a firm is regulated.
""".strip(),
    ),
    try_it="Find one challenge's rules. Compute how many losses in a row you could take, and the expected cost of failing twice.",
    quiz=(
        Q(
            "Where do prop firms get a large part of their income?",
            ("Challenge fees", "Bank interest", "Advertising only"),
            0,
            "Fees are a major source.",
        ),
        Q(
            "A 5% daily limit and 1% risk per trade means…",
            ("Five full losses in a day end the challenge", "You cannot lose", "No limit applies"),
            0,
            "Size small relative to the limits.",
        ),
    ),
    takeaways=(
        "Most challenge buyers do not get paid.",
        "Size small to fit the limits.",
        "Treat the fee as tuition.",
    ),
    sources=("prop-stats", "prop-mff"),
)

_TAX = Lesson(
    slug="pro/taxes-and-regulation",
    title="Taxes and regulation, at a general level",
    summary="What to find out before trading seriously. Not legal or tax advice.",
    est_minutes=7,
    key_concepts=("tax", "regulation", "record keeping", "licensing"),
    goal="Know what questions to ask about tax and regulation where you live.",
    body_md="""
Rules differ by country and change often. This lesson only tells you what to find out. It is not legal or tax advice.

### Questions to answer

- **Who regulates the products you trade?** Your broker's regulator and your own.
- **How are gains taxed where you live?** It may depend on the product, your holding period, and whether you are a resident.
- **What records must you keep?** Keep every trade, every deposit and withdrawal.
- **What are the leverage limits?** They differ by country and product.
- **What rules apply to sharing trading ideas?** Giving advice publicly can be regulated.

### Examples of how rules differ

- In the EU, leverage on retail CFDs is capped, and there are risk warnings and negative balance protection.
- In the US, forex leverage is limited, and the $25,000 pattern-day-trader minimum has been replaced by new intraday margin rules from June 2026.
- In the UAE, individuals who give financial recommendations on social media may need a licence under SCA Resolution No. 10 of 2025. The UAE does not generally tax individuals' income, but you should check your own situation with a qualified adviser.

### Keep records

Good records protect you whatever the rules are. Your journal and broker statements are a start.

This book is education only and does not give recommendations.
""".strip(),
    charts=(
        Chart(
            title="EU retail CFD leverage limits",
            caption="ESMA's 2018 caps, shown as maximum leverage ratios. Check for current rules where you live, as they may differ.",
            data_kind="published",
            kind="bars",
            y_format="plain",
            y_label="Maximum leverage",
            source_note="ESMA, 2018.",
            bars=(
                Bar("Major FX pairs", 30, "accent"),
                Bar("Other FX, gold, major indices", 20, "accentSoft"),
                Bar("Crypto", 2, "danger"),
            ),
        ),
    ),
    steps=(
        "Find out who regulates your broker and your products.",
        "Find out how gains are taxed where you live.",
        "Set up a record-keeping system.",
        "Talk to a qualified professional before trading large amounts.",
    ),
    example_md="""
A trader in the UAE trades forex through a broker regulated in another country.

Questions to answer: Is that broker allowed to serve UAE residents? Are any gains taxable, either here or elsewhere? What records should be kept? If they begin posting trade ideas on social media, do they need a licence?

Each answer depends on current law and personal circumstances. That is why a qualified adviser is worth it once real money is involved.
""".strip(),
    mistakes=(
        "Assuming the rules are the same as in another country.",
        "Keeping no records.",
        "Publishing trade calls without checking the local licensing rules.",
    ),
    evidence=fact(
        "General information only. Rules change: the UAE regulator has reportedly been renamed, and US rules changed in 2026. Always check primary sources or a qualified professional."
    ),
    try_it="Write one paragraph on how gains on your intended product are taxed where you live, and name where you found that information.",
    quiz=(
        Q(
            "Who should you ask about your specific tax situation?",
            ("A qualified adviser", "A trading group chat", "A broker's sales team"),
            0,
            "Tax depends on your personal circumstances.",
        ),
        Q(
            "What does good record keeping protect you from?",
            ("Problems with tax and disputes", "Losing trades", "Market gaps"),
            0,
            "Records are useful whatever the rules are.",
        ),
    ),
    takeaways=(
        "Rules vary by country and change often.",
        "Keep complete records.",
        "Ask a professional.",
    ),
    sources=("esma-cfd-2018", "finra-pdt-2026", "uae-finfluencer"),
)

_BUSINESS = Lesson(
    slug="pro/running-it-like-a-business",
    title="Running it like a business",
    summary="Income, costs, drawdowns and the honest maths of trading for a living.",
    est_minutes=8,
    key_concepts=("trading business", "income", "capital", "drawdown"),
    goal="Work out honestly what it would take to live off trading.",
    body_md="""
Many beginners imagine trading for a living. It is a business, and it should be judged like one.

### The maths

To earn an income, you need **capital**. If you have $20,000 and make a very good 20% in a year, that is $4,000. That is not an income.

Suppose you need $40,000 a year to live, and you aim for 20% a year (an excellent result that few sustain). You would need **$200,000 of capital**, and you would still have to withdraw from it in losing periods.

### Costs that a business has

Data, platforms, software, professional advice, tax, insurance and your own time.

### Risks a business has to plan for

Drawdowns that last for months; rule changes at your broker; health; technology failures; and the fact that your edge may stop working.

### A sensible approach

Keep your job while you build a record. Only consider leaving when you have **at least two years of audited or broker-verified results**, and enough savings to cover a long drawdown. Most people should not do this. That is a useful thing to know before you start.
""".strip(),
    charts=(
        Chart(
            title="Capital needed for $40,000 income a year",
            caption="Calculated at the annual return shown, before tax and drawdowns.",
            data_kind="calculated",
            kind="bars",
            y_format="usd",
            y_label="Capital needed",
            x_label="Annual return",
            bars=(
                Bar("10%", 400000, "accentSoft"),
                Bar("20%", 200000, "accent"),
                Bar("40%", 100000, "warn"),
                Bar("100%", 40000, "danger"),
            ),
        ),
        Chart(
            title="A real business has flat years",
            caption="Simulated, a small positive edge: 12 possible 3-year paths. Even a real edge produces long flat or losing stretches.",
            data_kind="calculated",
            kind="lines",
            y_format="plain",
            y_label="Account (start = 100)",
            x_label="Trades",
            series=equity_paths(
                n_paths=12, n_trades=150, win_rate=0.48, win_r=1.3, risk_pct=1.0, seed=37
            ),
        ),
    ),
    steps=(
        "Work out your yearly living cost.",
        "Compute the capital needed at a realistic return.",
        "Build a verified record for at least two years.",
        "Keep your job while you do.",
        "Plan for the worst year, not the average one.",
    ),
    example_md="""
Yousef needs $36,000 a year. He has $30,000 of savings.

If he could make 20% a year, trading would bring in $6,000. Withdrawing for living costs would drain the account.

Better plan: keep his job, trade the $30,000 at small risk, and aim to build a two-year verified record. If that works, he has options. If it does not, he still has his salary and has limited his losses.
""".strip(),
    mistakes=(
        "Quitting a job after a good month.",
        "Using leverage to meet an income target.",
        "Forgetting taxes and drawdowns.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
Studies of those who attempt to trade for a living are not encouraging. In Brazil, only about 3% of persistent day traders were profitable after fees, and fewer still earned a living wage. Regulators report that most retail CFD accounts lose money.

Some people do it. Do not assume you will be one of them without strong evidence.
""".strip(),
    ),
    try_it="Calculate your yearly costs, and the capital you would need at 15% a year. Write down whether that is realistic for you.",
    quiz=(
        Q(
            "If you need $40,000 a year and earn 20% annually, how much capital do you need?",
            ("$40,000", "$100,000", "$200,000"),
            2,
            "$40,000 / 0.20 = $200,000.",
        ),
        Q(
            "When should you consider leaving a job to trade?",
            (
                "After a strong month",
                "After a long, verified record and with enough savings",
                "After reading this book",
            ),
            1,
            "A long record and savings are the minimum.",
        ),
    ),
    takeaways=(
        "Trading for a living needs capital.",
        "Plan for bad years, not average ones.",
        "Most people should not try to do this.",
    ),
    sources=("chague-2020", "esma-cfd-2018"),
)

CHAPTERS = (
    chapter(
        "pro",
        "daily-practice",
        "Daily practice",
        "Tools, routines, and moving from demo to real money.",
        (_PLATFORMS, _WEEK, _DAY, _DEMO),
    ),
    chapter(
        "pro",
        "as-a-business",
        "As a business",
        "Prop firms, tax and regulation, and the maths of trading for a living.",
        (_PROP, _TAX, _BUSINESS),
    ),
)
