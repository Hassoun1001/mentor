"""Stage 6, additions: company numbers, the yield curve, cycles and who holds what."""

from __future__ import annotations

import math

from mentor.domain.curriculum.book._kit import Bar, Chart, Evidence, Lesson, Q, Series, Verdict

# ---------- financial statements ----------

STATEMENTS = Lesson(
    slug="fundamentals/financial-statements",
    title="Reading financial statements",
    summary="The three reports every company publishes, and the numbers that matter most.",
    est_minutes=10,
    key_concepts=("income statement", "balance sheet", "cash flow", "EPS", "free cash flow", "net debt"),
    goal="Read the three statements, and spot when profit and cash do not agree.",
    body_md="""
Companies report their results in three statements.

### 1. Income statement: did it make a profit?

Revenue, minus costs, gives profit. Profit per share is called **EPS**, earnings per share.

### 2. Balance sheet: what does it own and owe?

A snapshot on one date: **assets = liabilities + shareholders' equity.**

**Net debt** is debt minus cash. Net debt divided by EBITDA (profit before interest, tax, depreciation and amortisation) is a common test of how heavy the debt is.

### 3. Cash flow statement: did cash actually arrive?

- **Operating cash flow:** cash from running the business.
- **Capital spending:** cash spent on equipment and buildings.
- **Free cash flow** = operating cash flow − capital spending.

### Why cash matters

Profit includes estimates. Cash is harder to fake. If profit rises for years while operating cash flow stays flat, ask why.

### A short checklist

- Is revenue growing?
- Are margins (profit as a share of revenue) steady?
- Can the company pay its interest easily?
- Does cash flow roughly follow profit?
- Are there many new shares being issued?
""".strip(),
    charts=(
        Chart(
            title="From revenue to net profit",
            caption="Calculated from the made-up company in the worked example. Figures are in millions.",
            data_kind="calculated",
            kind="bars",
            y_format="usd",
            bars=(
                Bar("Revenue", 1000, "accent"),
                Bar("Cost of goods", -600, "danger"),
                Bar("Gross profit", 400, "accentSoft"),
                Bar("Running costs", -250, "danger"),
                Bar("Operating profit", 150, "accentSoft"),
                Bar("Interest", -20, "danger"),
                Bar("Tax", -26, "danger"),
                Bar("Net profit", 104, "accent"),
            ),
        ),
    ),
    steps=(
        "Find the income statement and note revenue, operating profit and net profit.",
        "Find the balance sheet and calculate net debt.",
        "Find the cash flow statement and calculate free cash flow.",
        "Compare profit with operating cash flow.",
        "Look at the last five years, not just one.",
    ),
    example_md="""
A made-up company, in millions:

| Line | Amount |
|---|---|
| Revenue | 1,000 |
| Cost of goods | −600 |
| Running costs | −250 |
| **Operating profit** | **150** |
| Interest | −20 |
| Tax at 20% of 130 | −26 |
| **Net profit** | **104** |

With 50 million shares, **EPS = 104 ÷ 50 = $2.08**.

Debt is 400 and cash is 100, so **net debt = 300**. Depreciation is 50, so EBITDA = 150 + 50 = 200, and net debt ÷ EBITDA = **1.5 times**.

Operating cash flow is 170 and capital spending is 70, so **free cash flow = 100**. Here cash is close to profit, which is a good sign.
""".strip(),
    mistakes=(
        "Looking at one year only.",
        "Trusting 'adjusted' profit without checking what was left out.",
        "Ignoring the growing number of shares.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Piotroski built a nine-point accounting score from financial statements. Among cheap US shares from 1976 to 1996, it helped separate the winners from the losers. The benefit was concentrated in small and less-followed companies.

Reading statements is a basic skill. It is no guarantee of beating the market.
""".strip(),
    ),
    try_it="Download the last annual report of one company. Calculate its net debt and free cash flow, and compare them with the year before.",
    quiz=(
        Q(
            "What is free cash flow?",
            (
                "Operating cash flow minus capital spending",
                "Revenue minus tax",
                "Cash held at the bank",
            ),
            0,
            "It is the cash left over after investing in the business.",
        ),
        Q(
            "If profit keeps rising but cash flow stays flat, you should…",
            ("Ask why they disagree", "Ignore it", "Assume it's a good sign"),
            0,
            "Cash is harder to fake than profit, so a gap needs an explanation.",
        ),
    ),
    takeaways=(
        "Three statements: profit, position and cash.",
        "Compare profit with cash flow.",
        "Look at several years together.",
    ),
    sources=("piotroski-2000",),
)

# ---------- DCF ----------


def _dcf(growth: float, discount: float, terminal: float = 0.02) -> float:
    """Value per share: FCF 100 growing for 5 years, net debt 300, 50 million shares."""
    flows = [100 * (1 + growth) ** year for year in range(1, 6)]
    present = sum(f / (1 + discount) ** i for i, f in enumerate(flows, start=1))
    terminal_value = flows[-1] * (1 + terminal) / (discount - terminal)
    return (present + terminal_value / (1 + discount) ** 5 - 300) / 50


_RATES = (0.08, 0.09, 0.10, 0.11, 0.12)

DCF = Lesson(
    slug="fundamentals/dcf-and-relative-valuation",
    title="DCF and relative valuation",
    summary="Two ways to estimate what a share is worth, and how much they depend on guesses.",
    est_minutes=10,
    key_concepts=("DCF", "discount rate", "terminal value", "P/E", "relative valuation", "EV/EBITDA"),
    goal="Build a small DCF by hand, compare a share with its peers, and see how sensitive both are.",
    body_md="""
### Discounted Cash Flow

A **DCF** estimates all the cash a company will produce, then converts it into today's money. Money later is worth less than money now, so each future amount is reduced using a **discount rate**.

**Value today = cash next year ÷ (1 + rate), plus cash the year after ÷ (1 + rate)², and so on.**

Beyond the forecast years, a **terminal value** stands in for everything after:

**Terminal value = final cash × (1 + long-run growth) ÷ (discount rate − long-run growth)**

Subtract net debt, divide by the number of shares, and you have a value per share.

### Relative valuation

The quicker way: compare with similar companies.

- **P/E** = share price ÷ earnings per share.
- **EV/EBITDA** compares the whole business value with its operating profit before depreciation.

If peers trade at 18 times earnings and this share trades at 14, it looks cheaper. But there might be a good reason.

### The honest point about both

The terminal value is often **most** of a DCF. So the answer depends on a few guesses. Think of a DCF as a way to ask, **"What would I need to believe for this price to make sense?"**
""".strip(),
    charts=(
        Chart(
            title="A small change in the discount rate moves the answer a lot",
            caption="Calculated from the worked example: free cash flow 100, growing 5% for five years, then 2%. Net debt 300 and 50 million shares.",
            data_kind="calculated",
            kind="bars",
            y_format="usd",
            bars=tuple(
                Bar(f"Discount rate {round(r * 100)}%", round(_dcf(0.05, r), 2), "accent")
                for r in _RATES
            ),
        ),
    ),
    steps=(
        "Estimate free cash flow for the next five years.",
        "Discount each year's cash to today.",
        "Add a terminal value, also discounted.",
        "Subtract net debt and divide by the number of shares.",
        "Change the discount rate and growth, and see how the answer moves.",
        "Compare the result with a simple P/E check against peers.",
    ),
    example_md="""
Free cash flow is **100**, growing **5%** a year for five years. The discount rate is **10%**.

| Year | Cash | Value today |
|---|---|---|
| 1 | 105.00 | 95.45 |
| 2 | 110.25 | 91.12 |
| 3 | 115.76 | 86.97 |
| 4 | 121.55 | 83.02 |
| 5 | 127.63 | 79.25 |
| **Sum** | | **435.81** |

Terminal value with 2% long-run growth: 127.63 × 1.02 ÷ 0.08 = **1,627.3**. Today's value of that: 1,627.3 ÷ 1.61051 = **1,010.4**.

Total: 435.81 + 1,010.4 = **1,446.2**. Subtract net debt of 300 and divide by 50 million shares: **$22.92** per share.

Notice that the terminal value is about **70% of the total**. A 1 point change in the discount rate moves the answer by several dollars, as the chart shows.

**Relative check:** EPS is $2.08. At a peer P/E of 18, the share would be $37.44. The two methods disagree, and that is normal.
""".strip(),
    mistakes=(
        "Trusting one precise answer.",
        "Using a terminal growth rate that is too close to the discount rate.",
        "Comparing P/E across companies that are not really similar.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Pinto, Robinson and Stowe surveyed investment professionals and found that market multiples and present-value models dominate practice. That shows these tools are popular. It does not show they are accurate.

Cheap shares have tended to beat expensive ones over long periods, but with long and painful spells of underperformance.
""".strip(),
    ),
    try_it="Build a five-year DCF in a spreadsheet for one company. Change the discount rate by one point either way and write down the new value per share.",
    quiz=(
        Q(
            "What usually makes up a large part of a DCF?",
            ("The terminal value", "Last year's profit", "The share price"),
            0,
            "That is why a DCF depends so heavily on long-run guesses.",
        ),
        Q(
            "If a share has a lower P/E than its peers, it means…",
            (
                "It is definitely a bargain",
                "It looks cheaper, but there may be a good reason",
                "Its earnings must be false",
            ),
            1,
            "Cheap can be cheap for a reason.",
        ),
    ),
    takeaways=(
        "A DCF turns future cash into today's value.",
        "Its answer depends on a few sensitive guesses.",
        "Relative valuation is quick, but only as good as its comparison.",
    ),
    sources=("pinto-valuation-2019",),
)

# ---------- earnings ----------

_DRIFT_DAYS = tuple(range(-5, 41, 5))

EARNINGS = Lesson(
    slug="fundamentals/earnings-and-the-drift",
    title="Earnings surprises and the drift after them",
    summary="Why the result matters less than the surprise, and why prices can keep moving afterwards.",
    est_minutes=8,
    key_concepts=("earnings", "surprise", "guidance", "post-earnings drift", "analyst revisions"),
    goal="Calculate an earnings surprise, and know what the drift research does and does not say.",
    body_md="""
Every quarter, public companies report their results. Analysts have already published forecasts, and the average is known as the **consensus**.

### The surprise matters

**A company can report record profit and still fall**, if people expected even more. The market reacts to the gap between the result and the expectation.

**Surprise = (actual − expected) ÷ expected**

**Guidance**, what the company says about the next period, often matters more than the last quarter.

### The drift

Researchers found that shares with good surprises often **kept rising** for weeks, and shares with bad surprises kept falling. This is called **post-earnings-announcement drift**. One explanation is that investors adjust slowly.

### Analyst revisions

When analysts raise their forecasts, shares have often tended to keep rising for a while too.

### The practical problems

- Earnings can cause large price gaps, and a stop cannot protect you from a gap.
- Options become expensive just before earnings.
- The drift has become smaller over time, especially in large, well-followed companies.
""".strip(),
    charts=(
        Chart(
            title="The shape of the drift",
            caption="Illustrative lines showing the general pattern the research describes. These are not measured returns.",
            data_kind="illustrative",
            kind="lines",
            y_format="pct",
            y_label="Return compared with the market",
            x_label="Trading days from the report",
            x_labels=tuple(str(d) for d in _DRIFT_DAYS),
            series=(
                Series(
                    "Good surprise",
                    tuple(0.0 if d < 0 else round(3 + 0.05 * d, 2) for d in _DRIFT_DAYS),
                    "accent",
                ),
                Series(
                    "Bad surprise",
                    tuple(0.0 if d < 0 else round(-3 - 0.05 * d, 2) for d in _DRIFT_DAYS),
                    "danger",
                ),
            ),
        ),
    ),
    steps=(
        "Find the date of the next report.",
        "Note the consensus estimate before the report.",
        "Calculate the surprise after the report.",
        "Read the guidance section, not only the headline.",
        "Check how large the gap was compared with what options implied.",
    ),
    example_md="""
Analysts expected earnings per share of **$1.00**. The company reported **$1.12**.

Surprise = (1.12 − 1.00) ÷ 1.00 = **+12%**.

Before the report, the at-the-money straddle cost **$8** on a **$100** share, implying a move of about **8%**.

The share rises **5%**. So the surprise was good, yet the actual move was **smaller than the options implied**. A buyer of that straddle in this example would lose money, even though the news was positive.
""".strip(),
    mistakes=(
        "Judging a result without knowing what was expected.",
        "Holding a large position through a report and assuming a stop will protect you.",
        "Believing the drift still works just as it did in the 1980s.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Bernard and Thomas studied the drift and found the gap between good-surprise and bad-surprise shares was positive in 41 of 48 quarters from 1974 to 1985. It is among the oldest and best-documented effects in finance.

The size of the effect has decreased over time. McLean and Pontiff also found published predictors tend to weaken after they are published.
""".strip(),
    ),
    try_it="For three companies reporting this month, write down the expected EPS beforehand. After the report, calculate the surprise and note the share's reaction.",
    quiz=(
        Q(
            "A company reports record profit but the share falls. A likely reason is…",
            (
                "The result was below what was expected",
                "The market is broken",
                "Profit does not matter",
            ),
            0,
            "Prices react to the gap between results and expectations.",
        ),
        Q(
            "What is post-earnings-announcement drift?",
            (
                "Prices continuing to move in the direction of the surprise for a while",
                "A company delaying its report",
                "A type of option",
            ),
            0,
            "It is one of the best-known effects, though it has become smaller.",
        ),
    ),
    takeaways=(
        "Surprise matters more than the headline number.",
        "A drift has been documented but has shrunk.",
        "Earnings gaps can jump over stops.",
    ),
    sources=("bernard-thomas-1989", "mclean-pontiff-2016"),
)

# ---------- yield curve ----------

_TENORS = ("3m", "6m", "1y", "2y", "5y", "10y", "30y")
_NORMAL = (2.0, 2.2, 2.4, 2.7, 3.2, 3.7, 4.1)
_INVERTED = (5.2, 5.1, 4.9, 4.7, 4.3, 4.2, 4.3)

YIELD_CURVE = Lesson(
    slug="macro/yield-curve",
    title="The yield curve",
    summary="What the shape of bond yields says, and why it is poor at timing.",
    est_minutes=7,
    key_concepts=("yield curve", "inversion", "2s10s", "recession", "term spread"),
    goal="Read the yield curve and calculate its key spreads, and know what an inversion does and does not tell you.",
    body_md="""
The **yield curve** plots the yield of government bonds against how long they last, from a few months to 30 years.

### The usual shape

Long-term bonds usually pay **more** than short-term bonds. You are lending for longer, so you want more return. The curve slopes up.

### Inversion

Sometimes short-term yields rise **above** long-term yields. This is called an **inverted curve**. It often happens when a central bank has raised rates and investors expect weaker growth later, followed by cuts.

### The spreads to know

- **10-year minus 3-month:** the one used in the classic recession research.
- **10-year minus 2-year**, known as **2s10s**: the one most often seen in the news.

### Why it matters

An inverted curve has come before most US recessions in modern history. It also affects banks, which borrow short and lend long.

### What it does not do

It is **poor at timing**. The gap between inversion and recession has varied by many months, and shares have often risen for a long time after an inversion.
""".strip(),
    charts=(
        Chart(
            title="A normal curve and an inverted curve",
            caption="Illustrative yields that show typical shapes only, not a particular date.",
            data_kind="illustrative",
            kind="lines",
            y_format="pct",
            y_label="Yield",
            x_label="Bond maturity",
            x_labels=_TENORS,
            series=(
                Series("Normal", _NORMAL, "accent"),
                Series("Inverted", _INVERTED, "danger"),
            ),
        ),
    ),
    steps=(
        "Find today's yields from a free government or central bank source.",
        "Plot them from short to long.",
        "Calculate the 10-year minus 3-month spread.",
        "Calculate the 10-year minus 2-year spread.",
        "Check how the shape has changed compared with a year ago.",
    ),
    example_md="""
Using the inverted curve in the chart:

- 3-month yield: **5.2%**
- 2-year yield: **4.7%**
- 10-year yield: **4.2%**

**10-year minus 3-month** = 4.2 − 5.2 = **−1.0 point**.

**10-year minus 2-year** = 4.2 − 4.7 = **−0.5 point**.

Both are negative, so the curve is inverted. The history says recession risk over the next year or two is higher than normal. It does not say when, and it does not say how shares will behave in the meantime.
""".strip(),
    mistakes=(
        "Treating an inversion as a sell signal for tomorrow.",
        "Mixing up 2s10s and the 3-month spread.",
        "Forgetting that one country's curve mainly describes that country.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Estrella and Mishkin of the New York Fed found that the 10-year minus 3-month spread beat other indicators at predicting US recessions two to six quarters ahead.

**The limits:** it has only a small number of recessions to learn from, and it says little about exact timing or market returns.
""".strip(),
    ),
    try_it="Look up today's US 3-month, 2-year and 10-year yields. Calculate both spreads. Then check the same numbers from one year ago.",
    quiz=(
        Q(
            "What does an inverted yield curve mean?",
            (
                "Short-term yields are above long-term yields",
                "Bond prices are zero",
                "Long-term yields are above short-term yields",
            ),
            0,
            "Short rates are above long rates.",
        ),
        Q(
            "How useful is an inversion for timing a market top?",
            (
                "It is exact to the day",
                "It is poor, because the delay varies widely",
                "It only works on weekends",
            ),
            1,
            "It raises recession risk, but says little about when.",
        ),
    ),
    takeaways=(
        "Long yields usually sit above short yields.",
        "Inversions have often come before US recessions.",
        "It is a poor market-timing tool.",
    ),
    sources=("estrella-mishkin-1996",),
)

# ---------- intermarket ----------

INTERMARKET = Lesson(
    slug="macro/intermarket-analysis",
    title="Intermarket analysis and the dollar index",
    summary="How bonds, shares, currencies and commodities affect each other.",
    est_minutes=8,
    key_concepts=("intermarket", "DXY", "dollar index", "correlation", "commodities", "bonds"),
    goal="Check a market move against related markets, and read the dollar index correctly.",
    body_md="""
Markets do not move alone. **Intermarket analysis** studies how they influence each other. John Murphy made the subject popular.

### Classic links

- **Bonds and shares:** rising yields can pressure expensive growth shares.
- **Dollar and gold:** gold is priced in dollars, so a stronger dollar often weighs on it.
- **Oil and inflation:** higher oil can push up inflation expectations.
- **Risk mood:** in fear, money often moves to dollars, yen and government bonds.

**These are tendencies, not rules.** They change over time, and sometimes reverse.

### The dollar index, DXY

**DXY** measures the US dollar against six currencies. Its weights have been the same since the euro began:

The euro is more than half, so **DXY is mostly a euro story**. It leaves out the Chinese yuan and Mexican peso, even though the US trades heavily with those countries.

### A sensible way to use it

Ask one question: **is this move confirmed elsewhere?**

If EUR/USD is rising, is the dollar falling against other currencies too? Then it is a dollar story. If not, it may be a euro story.
""".strip(),
    charts=(
        Chart(
            title="What is inside the dollar index",
            caption="Published weights, redrawn. The euro makes up more than half of the index.",
            data_kind="published",
            kind="bars",
            y_format="pct",
            source_note="ICE US Dollar Index weights, as listed in public summaries.",
            bars=(
                Bar("Euro", 57.6, "accent"),
                Bar("Japanese yen", 13.6, "muted"),
                Bar("British pound", 11.9, "muted"),
                Bar("Canadian dollar", 9.1, "muted"),
                Bar("Swedish krona", 4.2, "muted"),
                Bar("Swiss franc", 3.6, "muted"),
            ),
        ),
    ),
    steps=(
        "Note the move you care about.",
        "Open charts of the two or three markets most linked to it.",
        "Check whether they confirm or disagree.",
        "Measure the correlation over two different periods.",
        "Note the result, and do not assume the link will hold.",
    ),
    example_md="""
Suppose EUR/USD rises **1%** and the other currencies do not move against the dollar.

DXY would fall by about 57.6% × 1% = **about 0.58%**.

Now suppose DXY falls **0.3%** on a day when EUR/USD is up **0.5%**. The euro alone would explain 0.5% × 57.6% = **about 0.29%** of that fall. So almost the entire DXY move is the euro, and it tells you little about the dollar in general.
""".strip(),
    mistakes=(
        "Assuming a past correlation will last.",
        "Treating DXY as the dollar against the world.",
        "Finding a link by looking at many pairs until one appears.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Some links have been measured. Driesprong, Jacobsen and Maat found oil price changes predicted stock returns in many countries, which they explain as under-reaction. The authors note this was in-sample.

Relationships between markets change over time, so it is safer to use them as a check on a view than as a signal on their own.
""".strip(),
    ),
    try_it="Next time EUR/USD moves more than 0.5% in a day, check USD/JPY and GBP/USD. Was it a dollar move or a euro move?",
    quiz=(
        Q(
            "What is the largest part of the DXY?",
            ("The euro", "The Chinese yuan", "The yen"),
            0,
            "The euro makes up 57.6%. The yuan is not in the index at all.",
        ),
        Q(
            "Intermarket relationships are…",
            ("Fixed for all time", "Tendencies that can change", "Set by law"),
            1,
            "They shift with the economy and policy.",
        ),
    ),
    takeaways=(
        "Markets influence each other.",
        "DXY is largely the euro.",
        "Use links as a check, not as a signal.",
    ),
    sources=("driesprong-2008", "dxy-ice"),
)

# ---------- cycles ----------

_T = tuple(range(0, 49))

CYCLES = Lesson(
    slug="macro/business-and-liquidity-cycles",
    title="Business cycles and liquidity cycles",
    summary="The slow waves behind whole markets, and why they are hard to time.",
    est_minutes=8,
    key_concepts=("business cycle", "liquidity cycle", "recession", "credit", "central bank balance sheet"),
    goal="Name the stages of the business cycle, explain the liquidity cycle, and see why neither gives a timing signal.",
    body_md="""
### The business cycle

Economies move in waves.

| Stage | What happens | What has often done better |
|---|---|---|
| **Recovery** | Output starts rising from a low. | Shares, especially smaller and cyclical ones |
| **Expansion** | Jobs and profits grow. | Shares generally |
| **Slowdown** | Inflation rises, and rates go up. | Commodities, defensive shares |
| **Recession** | Output and jobs fall. | Government bonds |

The table shows tendencies, and history has many exceptions.

**The catch:** the official dates of a recession are often announced **months after** it began. By then markets have often already moved.

### The liquidity cycle

The **liquidity cycle** is the idea that money and credit around the world rise and fall in waves. When credit is easy, risky assets often do well. When it dries up, they often fall.

Researchers call this the **global financial cycle**, and US interest rate policy appears to be a major driver of it.

Followers often track:

- Central bank balance sheets
- Credit spreads
- The strength of the dollar

### The honest point

Both cycles are real as descriptions. Both are hard to use for timing. There are few complete cycles to learn from, and each one is different.
""".strip(),
    charts=(
        Chart(
            title="The stylised cycle",
            caption="Illustrative only: a smooth wave to show the idea. Real cycles are irregular, and their turning points are visible only afterwards.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Activity versus trend",
            x_label="Months",
            x_labels=tuple(str(t) for t in _T),
            series=(
                Series(
                    "Economic activity",
                    tuple(round(math.sin(t / 48 * 2 * math.pi), 3) for t in _T),
                    "accent",
                ),
                Series(
                    "Credit and liquidity",
                    tuple(round(math.sin((t + 6) / 48 * 2 * math.pi), 3) for t in _T),
                    "warn",
                    "dashed",
                ),
            ),
        ),
    ),
    steps=(
        "Look at the latest figures for growth, jobs and inflation.",
        "Decide which stage they most resemble, and how sure you are.",
        "Check central bank policy, credit spreads and the dollar.",
        "Write down what would change your mind.",
        "Treat the view as background, and keep risk rules unchanged.",
    ),
    example_md="""
Suppose the data shows:

- GDP growth slowed from **3% to 1%**.
- Unemployment rose from **3.8% to 4.3%**.
- Inflation is at **4%**, and the central bank has raised rates.

That most resembles a **slowdown**. A careful reader would say the risk of recession has gone up. They would not say when it will start.

Suppose also that a yield curve spread is **−0.5 point** and credit spreads have widened from **1.2 to 2.0 points**. These point the same way, and they are still only a change in odds.
""".strip(),
    mistakes=(
        "Assuming you know the current stage for certain.",
        "Using a slow view to make fast decisions.",
        "Looking at one measure of liquidity and calling it the whole story.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Estrella and Mishkin show the yield curve helped predict recessions. Miranda-Agrippino and Rey show US monetary policy drives a global cycle in asset prices and credit.

Turning this into a profitable rule is much harder. We found no strong evidence that rotating between sectors according to the cycle reliably beats a simple approach after costs.
""".strip(),
    ),
    try_it="Find the current GDP growth, unemployment and inflation for your main market. Which stage does it most resemble? Write down how confident you are, and check again in six months.",
    quiz=(
        Q(
            "Why is it hard to trade a recession call?",
            (
                "Recessions are often dated officially long after they begin",
                "Recessions never happen",
                "Recession data is secret",
            ),
            0,
            "By the time the date is known, markets have often moved.",
        ),
        Q(
            "What does the liquidity cycle describe?",
            (
                "Waves in money and credit around the world",
                "How often a broker's spreads change",
                "A pattern of daily candles",
            ),
            0,
            "When credit expands and contracts, risky assets often follow.",
        ),
    ),
    takeaways=(
        "Economies move through recognisable stages.",
        "Credit and money move in waves too.",
        "Both help with background and are poor for timing.",
    ),
    sources=("estrella-mishkin-1996", "miranda-rey-2020"),
)

# ---------- short interest, insiders, flows ----------

POSITIONS = Lesson(
    slug="macro/short-interest-insiders-flows",
    title="Short interest, insiders and fund flows",
    summary="Public data about what others hold, and how old it is when you see it.",
    est_minutes=8,
    key_concepts=("short interest", "days to cover", "insider trades", "fund flows", "ETF flows", "13F"),
    goal="Use public positioning data correctly, and know how much of it is out of date.",
    body_md="""
You can see part of what others are doing, with a delay.

### Short interest

**Short interest** is the number of shares that have been sold short and not yet bought back. Two simple measures:

- **Percent of float** = shares short ÷ freely tradable shares.
- **Days to cover** = shares short ÷ average daily volume.

Many people expect heavily shorted shares to "squeeze" higher. More often, high short interest is **bad news** for the share, because short sellers tend to be informed.

### Insider trades

Company officers must report when they trade their own shares. **Sales are often routine**, for example for taxes. Unusual buying carries more information.

### Fund and ETF flows

Flows show where money is going. **Retail money moving into a fund has often been a poor sign** for the shares it favours.

### Institutional filings

Large US managers report their holdings every quarter on form **13F**. These filings can be up to 45 days old when published.

### The rule for all of this

Before using any data, ask: **how old is it, and who has already acted on it?**
""".strip(),
    charts=(
        Chart(
            title="How old is the data when you can see it?",
            caption="Calculated from US reporting deadlines and typical schedules, rounded to days. The filing or event may be even older.",
            data_kind="calculated",
            kind="bars",
            y_format="plain",
            y_label="Approximate days",
            bars=(
                Bar("Insider trade (Form 4)", 2, "accent"),
                Bar("COT report", 3, "accent"),
                Bar("Short interest", 11, "warn"),
                Bar("13F holdings, up to", 45, "danger"),
            ),
        ),
    ),
    steps=(
        "Pick one share and note its short interest.",
        "Calculate percent of float and days to cover.",
        "Check recent insider filings, and look for unusual buying.",
        "Check how old each piece of data is.",
        "Treat it as background for a wider view.",
    ),
    example_md="""
A company has **40 million** freely tradable shares. **10 million** are sold short, and daily volume is **2 million**.

- Percent of float = 10 ÷ 40 = **25%**.
- Days to cover = 10 ÷ 2 = **5 days**.

That is high. It could lead to a squeeze. It could also mean informed traders expect bad news, which historically has been the more common outcome.

In the same month, the chief executive buys **$500,000** of shares on the open market, for the first time in years. That is more unusual than a routine sale, and research suggests such trades carry more information.
""".strip(),
    mistakes=(
        "Assuming a high short interest must lead to a squeeze.",
        "Treating every insider sale as bad news.",
        "Copying 13F holdings that may be months old.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
- **Short interest:** Rapach, Ringgenberg and Zhou found total US short interest was a strong predictor of later market returns.
- **Insiders:** Cohen, Malloy and Pomorski found that unusual insider trades carried the useful information, at about 0.8% a month in the working paper, before costs, while routine trades carried none.
- **Fund flows:** Frazzini and Lamont found retail flows tended to precede lower returns for the favoured shares.

Published effects often weaken after being published, so treat these numbers as historical.
""".strip(),
    ),
    try_it="Pick a share with high short interest. Look up insider trades over the last year. Separate routine sales from unusual trades.",
    quiz=(
        Q(
            "If 5 million shares are short and daily volume is 1 million, days to cover is…",
            ("0.2", "5", "50"),
            1,
            "Shares short divided by daily volume: 5 ÷ 1 = 5 days.",
        ),
        Q(
            "What did the research find about insider trades?",
            (
                "Unusual trades were informative, and routine ones were not",
                "All insider sales predict a fall",
                "Insider trades contain no information",
            ),
            0,
            "Separating routine from unusual trades was the key.",
        ),
    ),
    takeaways=(
        "High short interest is more often a warning than a promise of a squeeze.",
        "Unusual insider buying says more than routine sales.",
        "Always check how old the data is.",
    ),
    sources=("rapach-short-2016", "cohen-insiders-2012", "frazzini-lamont-2008"),
)
