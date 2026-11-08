"""Stage 6 — Fundamentals and macro."""

from __future__ import annotations

from mentor.domain.curriculum.book._kit import (
    Bar,
    Chart,
    Evidence,
    Figure,
    Lesson,
    Mark,
    Q,
    Series,
    Verdict,
    candle_chart,
    chapter,
    fact,
)
from mentor.domain.curriculum.charts import path

_SCHOOLS = Lesson(
    slug="market-study/schools-of-analysis",
    title="The four ways people read a market",
    summary="Technical, fundamental, quantitative and sentiment analysis, and how they fit together.",
    est_minutes=6,
    key_concepts=("technical", "fundamental", "quantitative", "sentiment"),
    figures=(Figure("schools-of-analysis", "Four lenses on one market."),),
    goal="Know the four main approaches, what each is good for, and how they combine.",
    body_md="""
Every method of studying a market falls into one of four groups. None is "the truth". Each answers a different question.

- **Technical analysis** reads price itself: trend, levels, volatility. It is good for timing and risk, and weak at explaining *why* something moves.
- **Fundamental analysis** reads the drivers: interest rates, growth, inflation and trade. It is good for direction over weeks or months and poor at timing.
- **Quantitative analysis** reads statistics: does this signal have a repeatable edge after costs? It is the honesty check on the other three.
- **Sentiment and positioning** read the crowd: are traders already heavily positioned one way? Extremes can matter, but they can stay extreme for a long time.

### How they fit together

Fundamentals give the **bias**, technicals give the **where and when**, quant tells you **whether it actually works**, and sentiment warns you when **everyone already agrees**.

This app leans quantitative and risk-first on purpose, because untested technical or fundamental "edges" are how most accounts die.
""".strip(),
    charts=(
        Chart(
            title="Each lens answers a different question",
            caption="Illustrative: a rough judgement of how useful each approach tends to be for a trading horizon, 1 (weak) to 5 (strong). Not measured.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Usefulness for timing an entry",
            bars=(
                Bar("Technical", 4, "accent"),
                Bar("Quantitative", 3, "accentSoft"),
                Bar("Sentiment", 2, "warn"),
                Bar("Fundamental", 2, "muted"),
            ),
        ),
    ),
    steps=(
        "Write down the question you are trying to answer.",
        "Pick the lens that answers it.",
        "Use a second lens to look for disagreement.",
        "Ask the quantitative question last: does this actually work with costs?",
    ),
    example_md="""
A trader looks at EUR/USD:

- **Fundamental:** the Fed is cutting faster than the ECB, which favours the euro.
- **Technical:** price is in an uptrend and near support.
- **Sentiment:** positioning is already heavily long the euro, which is a warning.
- **Quantitative:** the trader checks their journal: in this kind of setup, they have a 0.1R expectancy, which is small but positive.

Three of four agree, and one warns. The trader takes a smaller position than usual.
""".strip(),
    mistakes=(
        "Treating one lens as the only truth.",
        "Reading fundamentals to justify a position you already hold.",
        "Skipping the quantitative check.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Researchers have long found exchange rates hard to forecast from fundamentals (the Meese-Rogoff puzzle), and Rossi's 2013 review concluded that predictability depends on the model, horizon and sample. Different lenses each have some evidence, and none of them is reliable alone.
""".strip(),
    ),
    try_it="Take one market. Write one sentence for each of the four lenses. Which disagrees with the others?",
    quiz=(
        Q(
            "Which lens is the honesty check on the others?",
            ("Technical", "Quantitative", "Sentiment"),
            1,
            "Quantitative analysis tests whether an idea holds up after costs.",
        ),
        Q(
            "Fundamentals are usually best for…",
            ("Exact timing of an entry", "Direction over weeks or months", "Choosing a stop"),
            1,
            "They are poor at timing and useful for longer-term bias.",
        ),
    ),
    takeaways=(
        "There are four main ways to read a market.",
        "Each answers a different question.",
        "Quant is the honesty check.",
    ),
    sources=("rossi-2013",),
)

_WHAT_MOVES = Lesson(
    slug="macro/what-moves-prices",
    title="What really moves prices",
    summary="Surprises, expectations and who has to act.",
    est_minutes=7,
    key_concepts=("expectations", "surprise", "priced in", "flows"),
    goal="Understand that prices move on surprises compared to expectations, not on news itself.",
    body_md="""
Prices do not move because news is good or bad. They move because the news is **better or worse than expected**.

If everyone expects a 0.5% rate rise and the central bank raises rates 0.5%, the market often barely moves. The rise was **priced in**, meaning it was already reflected in the price.

### Four things that move prices

1. **Surprises** in data and decisions compared with expectations.
2. **Changes in expectations** for the future, even without new data.
3. **Flows:** who has to buy or sell, such as hedgers, funds or central banks.
4. **Positioning:** when many people are on the same side, they can all rush for the exit.

### Why this is hard

You can be right about the news and still lose money, because it was already in the price. "Buy the rumour, sell the fact" describes this.
""".strip(),
    charts=(
        candle_chart(
            path(
                [(0, 1.0800), (6, 1.0830), (7, 1.0860), (9, 1.0840), (20, 1.0820)],
                seed=135,
                noise=0.2,
            ),
            title="A good number, and the price falls anyway",
            caption="Illustrative prices. A spike on the release, then a reversal as traders who were already long take profits. The news was good, and it was already expected.",
            marks=(Mark(7, 1.0860, "Release", "warn"),),
        ),
    ),
    steps=(
        "Before a release, find the consensus forecast.",
        "Decide what result would be a surprise.",
        "Ask how much is already priced in.",
        "Consider who is positioned on each side.",
        "Decide whether to trade, wait or stay out.",
    ),
    example_md="""
US jobs were expected to rise by **180,000**. They rise by **200,000**. That looks good.

But the market had already moved in anticipation, and the unemployment rate rose. The dollar falls.

The headline was good, and the *full picture compared to expectations* was not. You cannot predict such reactions reliably. Plan for them with sizing and stops.
""".strip(),
    mistakes=(
        "Trading the headline without knowing the consensus.",
        "Assuming good news must mean a rising price.",
        "Believing a narrative written after the fact explains what happened.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Research shows macro announcements move markets. Evans and Lyons found that order flow explains much of daily exchange rate moves, and Lucca and Moench found an unusual pattern of US stock gains before Fed meetings, which a later update showed was mainly around meetings with press conferences. Still, knowing the data does not mean you can predict the reaction.
""".strip(),
    ),
    try_it="Pick one upcoming data release. Write the consensus, and two scenarios. After it, compare what happened with what you expected.",
    quiz=(
        Q(
            "Prices usually move on…",
            (
                "Whether news is good or bad",
                "How news compares with expectations",
                "The time of day",
            ),
            1,
            "Surprise relative to expectation drives the reaction.",
        ),
        Q(
            "A rate rise that everyone expected often causes…",
            ("A huge move", "Little move, because it was priced in", "A market closure"),
            1,
            "The expected part is already in the price.",
        ),
    ),
    takeaways=(
        "Markets react to surprises, not to news itself.",
        "You can be right about the news and still lose.",
        "Positioning changes how the market reacts.",
    ),
    sources=("lucca-2015", "evans-lyons-2002"),
)

_CB = Lesson(
    slug="macro/central-banks-and-rates",
    title="Central banks and interest rates",
    summary="The single most important driver for currencies and bonds.",
    est_minutes=8,
    key_concepts=("central bank", "policy rate", "hawkish", "dovish", "rate differential"),
    goal="Understand how central banks move markets, and how to follow them.",
    body_md="""
A **central bank**, such as the US Federal Reserve (the **Fed**) or the European Central Bank (the **ECB**), sets short-term **interest rates** to manage inflation and support the economy.

### Why rates matter so much

Money tends to flow towards higher interest rates, all else equal. So when one country's rates rise compared to another's, its currency often strengthens. The difference between two interest rates is the **rate differential**.

For **EUR/USD**, the difference between US and euro-area rates, especially 2-year government yields, is widely watched.

### Words you will hear

- **Hawkish:** leaning towards higher rates, usually to fight inflation.
- **Dovish:** leaning towards lower rates, usually to support growth.
- **Forward guidance:** what a central bank says it expects to do.
- **Pause, hike, cut:** hold, raise or lower rates.

### How to follow them

Read the **statement** and watch the **press conference**. Compare what is said with what the market expected. The Fed and ECB publish their schedules well ahead.

### Effects in other markets

Higher rates tend to weigh on stocks, especially high-growth ones. Bond prices fall when yields rise. Gold can suffer because holding it earns no interest.
""".strip(),
    charts=(
        Chart(
            title="An illustrative rate gap and a currency",
            caption="Illustrative data of how a wider rate gap can line up with a stronger currency. Real relationships are looser, and they change over time.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Index",
            x_label="Months",
            x_labels=tuple(str(i) for i in range(1, 13)),
            series=(
                Series(
                    "Rate gap (scaled)",
                    (100, 101, 103, 104, 106, 108, 107, 109, 111, 110, 112, 113),
                    "accent",
                ),
                Series(
                    "Currency",
                    (100, 100.5, 102, 104, 105, 107, 108, 108, 110, 111, 111, 114),
                    "accentSoft",
                ),
            ),
        ),
    ),
    steps=(
        "Find your central bank's meeting schedule.",
        "Note what the market currently expects.",
        "Read the statement when it is released.",
        "Compare it with expectations, not with your opinion.",
        "Avoid trading the moment of the release unless your plan covers it.",
    ),
    example_md="""
The Fed is expected to hold rates at 4.50%. It does hold, but the chair says inflation "remains a concern" and that cuts are further away. That is hawkish compared to expectations.

Result: US yields rise, and the dollar strengthens. EUR/USD falls 60 pips.

The decision itself was unchanged. The **tone** was the surprise.
""".strip(),
    mistakes=(
        "Trading on the headline rate decision without reading the guidance.",
        "Forgetting the central bank has a calendar you can look up.",
        "Assuming a rate rise will always strengthen a currency.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Links between interest rates and currencies are widely observed. But Meese and Rogoff's puzzle still stands: over short periods, a simple random walk is very hard to beat with economic models. Rossi's review notes that Taylor-rule fundamentals, which are based on central-bank behaviour, are among the more successful predictors, but that results depend heavily on period and method.
""".strip(),
    ),
    try_it="Read the latest statement of the central bank that matters most for your market. Write one sentence: was it hawkish or dovish compared to what was expected?",
    quiz=(
        Q(
            "A hawkish central bank leans towards…",
            ("Higher rates", "Lower rates", "No change at all"),
            0,
            "Hawkish means inclined to raise or hold rates high.",
        ),
        Q(
            "A central bank holds rates as expected but sounds hawkish. A likely reaction is…",
            ("No effect", "The currency strengthens", "Bonds rally strongly"),
            1,
            "The message moved expectations.",
        ),
    ),
    takeaways=(
        "Interest rates drive currencies and bonds.",
        "The surprise relative to expectations matters most.",
        "Read the words, not just the number.",
    ),
    sources=("rossi-2013",),
)

_DATA_TYPES = Lesson(
    slug="macro/inflation-jobs-growth",
    title="Inflation, jobs and growth",
    summary="The big three of economic data, and what each does.",
    est_minutes=7,
    key_concepts=("inflation", "CPI", "employment", "NFP", "GDP"),
    goal="Know the main economic reports, what each measures and why traders care.",
    body_md="""
Three kinds of data matter most.

**Inflation** is the speed at which prices rise. The main report is the **Consumer Price Index (CPI)**. In the US, the Fed also watches **PCE**, a related measure. High inflation pushes central banks towards higher rates.

**Employment** data shows how well the economy is doing. In the US, the **Non-Farm Payrolls (NFP)** report, usually out on the first Friday of the month, is a major market event.

**Growth** is measured by **GDP**, the total value of what an economy produces. Business surveys called **PMIs** give earlier hints.

### How to think about them

- Strong inflation or strong jobs usually pushes rate expectations up.
- Weak data pushes them down.
- A surprising figure can move markets quickly, then reverse.

### Be careful

Reports are revised later. The first figure is an estimate, and revisions can be large.
""".strip(),
    charts=(
        candle_chart(
            path([(0, 1.0820), (10, 1.0830), (12, 1.0880), (20, 1.0860)], seed=141, noise=0.25),
            title="A typical data release",
            caption="Illustrative prices. A sudden move on the release, and spreads often widen for a short time.",
            marks=(Mark(12, 1.0880, "Data out", "warn"),),
        ),
    ),
    steps=(
        "Check the economic calendar each morning.",
        "Find the data that matters for your market.",
        "Note the previous number and the forecast.",
        "Decide your plan for the release in advance.",
        "Check whether the first number is later revised.",
    ),
    example_md="""
CPI is expected at **0.2%** month-on-month and comes in at **0.4%**.

Inflation was higher than expected, so traders raise their expectations for interest rates. The dollar rises. A trader long EUR/USD with a stop 20 pips away and a position sized for a normal day takes a loss.

The professional response was to reduce position size or stand aside before the release.
""".strip(),
    mistakes=(
        "Forgetting about scheduled data until the price jumps.",
        "Reading only the headline number.",
        "Treating an early estimate as final.",
    ),
    evidence=fact(
        "These are descriptions of economic reports. The evidence on using them to trade is in the news-trading lesson. Scheduled data usually moves prices, but predicting the direction reliably remains very hard."
    ),
    try_it="Find the three most important releases for your market next week and write down when each comes out, in your own time zone.",
    quiz=(
        Q(
            "Which report is the main US jobs number?",
            ("CPI", "NFP", "GDP"),
            1,
            "Non-Farm Payrolls is the headline US employment report.",
        ),
        Q(
            "Stronger than expected inflation usually pushes rate expectations…",
            ("Up", "Down", "Nowhere"),
            0,
            "Higher inflation tends to push central banks towards higher rates.",
        ),
    ),
    takeaways=(
        "Inflation, jobs and growth are the big three.",
        "The surprise matters more than the number.",
        "Early estimates can be revised.",
    ),
)

_RISK_ON = Lesson(
    slug="macro/risk-on-risk-off",
    title="Risk-on and risk-off",
    summary="When the whole market changes mood at once.",
    est_minutes=6,
    key_concepts=("risk-on", "risk-off", "safe haven", "VIX"),
    goal="Recognise when markets are in a risk-on or risk-off mood, and what tends to move.",
    body_md="""
Markets sometimes move as a group, based on how much risk investors want to take.

**Risk-on** means investors are confident. Stocks and higher-risk currencies tend to rise.

**Risk-off** means investors are afraid. Money tends to go to **safe havens**: usually the US dollar, Japanese yen, Swiss franc and government bonds. Gold often benefits, but not always.

The **VIX** is an index built from S&P 500 option prices, and it shows how much volatility traders expect over the next month. A rising VIX often accompanies risk-off moods.

### Why it matters

During a risk-off move, positions you thought were separate can all lose at once. Correlations jump. Look at your whole book.

### Use with care

"Risk-on" and "risk-off" are convenient labels used after the fact. Relationships change. The dollar is not always a safe haven, and in some crises gold has sold off too, as people raised cash.
""".strip(),
    charts=(
        Chart(
            title="Stress period: how a risk-off move often looks",
            caption="Illustrative, showing the broad pattern of a risk-off period. Real moves differ a great deal across events.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Index (start = 100)",
            x_label="Days",
            x_labels=tuple(str(i) for i in range(1, 11)),
            series=(
                Series("Stocks", (100, 99, 97, 94, 90, 88, 90, 91, 92, 93), "danger"),
                Series(
                    "US dollar index",
                    (100, 100, 101, 102, 103, 104, 103, 103, 102, 102),
                    "accentSoft",
                ),
                Series(
                    "Government bonds",
                    (100, 100, 101, 102, 103, 104, 103, 103, 102, 102),
                    "accent",
                    "dashed",
                ),
            ),
        ),
    ),
    steps=(
        "Check stocks, bonds, the dollar and VIX together.",
        "Decide if the mood is risk-on, risk-off or mixed.",
        "Check whether your open positions all depend on the same mood.",
        "Reduce exposure if they do.",
    ),
    example_md="""
You hold long AUD/USD, long S&P 500 futures and short USD/JPY. A sudden shock hits and risk appetite collapses.

All three lose together, because they share one mood bet. A risk limit based on these being three separate trades would have been too generous.
""".strip(),
    mistakes=(
        "Assuming a safe haven always behaves the same way.",
        "Using risk-on and risk-off as forecasts.",
        "Forgetting your positions share the same mood.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Carry research supports the idea that risk appetite matters: Brunnermeier, Nagel and Pedersen link carry trade crashes to sudden falls in risk appetite and funding. But risk-on and risk-off are descriptions. Forecasting the switch from one to the other is much harder.
""".strip(),
    ),
    try_it="Watch stocks, bonds, gold and the dollar for a week. Each day write whether the mood seemed risk-on, risk-off or mixed.",
    quiz=(
        Q(
            "In risk-off, money often moves to…",
            (
                "Small-company shares",
                "Safe havens like the yen and government bonds",
                "Crypto only",
            ),
            1,
            "Safe havens tend to benefit, though not always.",
        ),
        Q(
            "What does the VIX measure?",
            ("Expected S&P 500 volatility from option prices", "Stock prices", "Bond yields"),
            0,
            "It comes from S&P 500 option prices.",
        ),
    ),
    takeaways=(
        "Moods can move many markets together.",
        "Your positions can all share one mood.",
        "These are labels, not forecasts.",
    ),
    sources=("brunnermeier-2008",),
)

_DATA_CAL = Lesson(
    slug="toolkit/data-and-calendars",
    title="Data and economic calendars",
    summary="Know what is coming, and where to find trustworthy data.",
    est_minutes=6,
    key_concepts=("economic calendar", "FRED", "data feed", "news"),
    figures=(Figure("data-calendar", "The calendar tells you which days need caution."),),
    goal="Know what is on the calendar and where to find reliable data.",
    body_md="""
You cannot manage risk around events you did not know were coming.

- **Economic calendar:** sites such as ForexFactory list every scheduled release with an expected impact. For EUR/USD, the essentials are central-bank decisions, inflation, jobs and GDP. Around big prints, spreads widen and fills get worse.
- **Macro data:** **FRED**, from the St. Louis Fed, is an excellent free source of US rates, the dollar index, the VIX and many other series. This app pulls rate and volatility data from it.
- **Prices:** Yahoo Finance and Twelve Data offer free historical candles for forex and stocks.
- **News mood:** GDELT turns world news into daily sentiment scores, which this app uses, though news timing is rarely tradable once it is public.

### Rule of thumb

Check the calendar every morning. Quiet days are for setups. Big-release days are for smaller size or sitting out.
""".strip(),
    charts=(
        Chart(
            title="A sample week, marked by risk",
            caption="Illustrative: how a trader might rate a week's days by event risk, 0 (none) to 3 (high), before planning any trades.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Event risk",
            bars=(
                Bar("Mon", 0, "accentSoft"),
                Bar("Tue (CPI)", 3, "danger"),
                Bar("Wed", 1, "accent"),
                Bar("Thu (ECB)", 3, "danger"),
                Bar("Fri (NFP)", 3, "danger"),
            ),
        ),
    ),
    steps=(
        "Check your economic calendar every morning.",
        "Mark high-impact events in your own time zone.",
        "Decide whether to reduce size, or not trade.",
        "Use reliable sources for data you will base decisions on.",
    ),
    example_md="""
Tuesday's CPI is at 12:30 UTC. Your plan:

- No new trades within 15 minutes before or 30 minutes after.
- Any open position has a stop you can live with, because the spread may widen.
- You note in your journal: "Sat out CPI by plan."

If your plan has no rule about CPI, then write one.
""".strip(),
    mistakes=(
        "Getting hit by a release you did not know was scheduled.",
        "Trusting a single data source for everything.",
        "Thinking 'high impact' means a tradable edge.",
    ),
    evidence=fact(
        "These are sources of information. Whether you can profit from news is a different question, covered in Stage 7."
    ),
    try_it="Set up an economic calendar with your time zone and the currencies you care about. Note next week's three biggest events.",
    quiz=(
        Q(
            "What should you do on a day with a major release, if you have no plan for it?",
            ("Trade bigger", "Reduce size or stand aside", "Ignore it"),
            1,
            "No plan for an event means no trade around it.",
        ),
        Q(
            "Which source is widely used for free US macro data?",
            ("FRED", "A trading chat group", "A broker's advert"),
            0,
            "FRED, from the St. Louis Fed, is widely used.",
        ),
    ),
    takeaways=(
        "Know what is scheduled before you trade.",
        "Trust primary data sources.",
        "Big events call for caution, not bigger size.",
    ),
)

_COT = Lesson(
    slug="macro/positioning-and-cot",
    title="Positioning and the COT report",
    summary="Who is holding what in futures markets, and how far to trust it.",
    est_minutes=7,
    key_concepts=("Commitments of Traders", "positioning", "crowded trade"),
    goal="Understand what the COT report shows and how to use it without over-trusting it.",
    body_md="""
**Positioning** means which side traders are on. If everyone is already long, there may be few buyers left to push the price higher.

The **Commitments of Traders (COT) report** is published by the US **CFTC**. It shows positions in US futures markets broken down by type of trader, such as commercials (often hedgers) and managed money (funds).

It is usually released on **Friday afternoon** in the US, using positions from the **previous Tuesday**. So it is already a few days old when you see it. There has been talk of more frequent reports, so check the CFTC's current schedule.

### How people use it

- A **crowded trade** is when positions are at extreme levels. Some people treat that as a warning.
- Changes in position can show money moving in or out.

### Limits

Commercials are often hedging, so their position does not tell you direction. "Extreme" levels can stay extreme for a long time.

This app uses COT data as one of its inputs and accounts for the delay when using it. The inputs are not proven to give the app an edge.
""".strip(),
    charts=(
        Chart(
            title="A positioning swing",
            caption="Illustrative data of net fund positions in a futures market. Extreme readings do not reliably mark a turning point.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Net long positions (thousands)",
            x_label="Weeks",
            x_labels=tuple(str(i) for i in range(1, 21)),
            series=(
                Series(
                    "Net long",
                    (
                        10,
                        18,
                        25,
                        40,
                        55,
                        70,
                        92,
                        110,
                        124,
                        130,
                        128,
                        120,
                        112,
                        100,
                        85,
                        70,
                        62,
                        55,
                        48,
                        40,
                    ),
                    "accent",
                ),
            ),
        ),
    ),
    steps=(
        "Find the COT data for your market on the CFTC's website.",
        "Note the date of the positions, not only the release date.",
        "See whether positions are near extremes for the last year.",
        "Use this as a warning sign, not as a trigger.",
    ),
    example_md="""
On Friday you see that funds are at a 3-year high of net long gold. The report is for Tuesday. Gold has fallen since then.

A sensible use: "The crowd is heavily long. I will not add longs on this signal, and I will tighten stops on my existing longs."
""".strip(),
    mistakes=(
        "Treating the COT as real-time data.",
        "Betting on a reversal the moment positions look extreme.",
        "Forgetting that commercial hedgers can be on the 'wrong' side by design.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
The COT data is real and published by a regulator. Its usefulness as a timing signal is unclear; extremes can persist a long time. Moskowitz, Ooi and Pedersen found speculators profit at the expense of hedgers in their momentum study, which fits with hedgers often being on the other side of trends.
""".strip(),
    ),
    try_it="Find the current COT position for one market. Write down its date, and whether positions look extreme compared to the last two years.",
    quiz=(
        Q(
            "COT data usually shows positions as of…",
            ("The moment you read it", "The previous Tuesday", "A year ago"),
            1,
            "It is usually published on Friday using Tuesday's positions.",
        ),
        Q(
            "Extreme positioning means…",
            ("An immediate reversal", "A possible warning, which can persist", "Nothing at all"),
            1,
            "Crowded trades can keep getting more crowded.",
        ),
    ),
    takeaways=(
        "COT shows positioning, with a delay.",
        "Commercial positions are often hedges.",
        "Extremes are a warning, not a trigger.",
    ),
    sources=("cftc-cot", "moskowitz-2012"),
)

_READ_RELEASE = Lesson(
    slug="macro/how-to-read-a-release",
    title="How to read a data release",
    summary="A simple routine for the moments around scheduled news.",
    est_minutes=6,
    key_concepts=("consensus", "previous", "revision", "reaction"),
    goal="Have a routine for scheduled news, so you do not trade on impulse.",
    body_md="""
A scheduled release has four pieces of information.

1. **Previous:** last period's number, sometimes revised.
2. **Forecast:** the consensus of economists.
3. **Actual:** the new number.
4. **Reaction:** how the market responds.

The difference between actual and forecast is the **surprise**.

### A simple routine

- **Before:** know the time and consensus. Check whether your open trades can survive a large move. Decide not to trade in the first moments unless you have a tested plan for that.
- **During:** watch the size of the surprise and which details matter.
- **After:** wait for spreads to normalise. Look at how the price behaves after the first move.

### The first reaction is not the final one

Markets often spike one way and reverse. The first spike is often driven by automated systems reacting to the headline number, and thin liquidity.
""".strip(),
    charts=(
        candle_chart(
            path(
                [(0, 1.0800), (8, 1.0805), (9, 1.0850), (14, 1.0815), (25, 1.0790)],
                seed=147,
                noise=0.2,
            ),
            title="The first reaction, then the real one",
            caption="Illustrative prices. A sharp spike on the number, followed by a reversal. Your stop may fill at a bad price during the spike.",
            marks=(Mark(9, 1.0850, "First spike", "warn"),),
        ),
    ),
    steps=(
        "Note previous, forecast and the release time.",
        "Decide whether to be flat, reduced or holding.",
        "Do not enter in the first seconds.",
        "After the spike, look for a clear structure before acting.",
        "Write down what happened and whether your plan held.",
    ),
    example_md="""
NFP is forecast at +150,000 and comes in at +180,000, but last month's figure is revised down by 60,000. The headline looks strong, but the net two-month picture is weaker.

EUR/USD spikes down 30 pips on the headline and reverses up 50 pips over the next hour.

A trader who waited 15 minutes and read the full report would have had a very different view from one who reacted to the headline.
""".strip(),
    mistakes=(
        "Entering on the first candle after the number.",
        "Reading only the headline.",
        "Leaving wide spreads out of your risk estimate.",
    ),
    evidence=fact(
        "A routine for handling known risk, not a claim about profits. Whether you can trade news profitably is examined in the news and event trading plan."
    ),
    try_it="Choose a release this week and write, before it comes out, what you will do at each stage. Afterwards note whether you followed your plan.",
    quiz=(
        Q(
            "The surprise in a release is…",
            ("Actual minus forecast", "Actual minus previous", "Forecast minus previous"),
            0,
            "The surprise is how far the actual was from the forecast.",
        ),
        Q(
            "Why be careful with the first move after a release?",
            (
                "Liquidity is thin and the first move often reverses",
                "It is always correct",
                "It is illegal",
            ),
            0,
            "Early moves are often unreliable.",
        ),
    ),
    takeaways=(
        "Surprise, not the number, is what matters.",
        "Decide before the release.",
        "Do not trade the first seconds without a tested plan.",
    ),
)

CHAPTERS = (
    chapter(
        "macro",
        "what-moves-markets",
        "What moves markets",
        "The forces behind prices, from central banks to crowd mood.",
        (_SCHOOLS, _WHAT_MOVES, _CB, _DATA_TYPES, _RISK_ON),
    ),
    chapter(
        "macro",
        "using-the-data",
        "Using the data",
        "Calendars, positioning data and how to handle a release.",
        (_DATA_CAL, _COT, _READ_RELEASE),
    ),
)
