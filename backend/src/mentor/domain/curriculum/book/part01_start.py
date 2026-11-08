"""Stage 1 — Absolute basics."""

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
from mentor.domain.curriculum.charts import equity_paths, path, random_walk

_WHAT_TRADING_IS = Lesson(
    slug="start/what-trading-is",
    title="What trading really is",
    summary="Buying and selling to profit from price changes, and how that differs from investing and gambling.",
    est_minutes=7,
    key_concepts=("trading", "investing", "speculation", "market"),
    goal="Know what trading is, how it differs from investing and gambling, and what you are signing up for.",
    body_md="""
A **market** is any place where buyers and sellers agree on a price. Today most markets are computer networks.

**Trading** means buying and selling something so you can profit when its price changes. You might hold for seconds, days or months. What matters is that the *price change* is how you plan to make money.

**Investing** is different. An investor buys part of a business, or a bond, and expects to be paid over years by profits and interest. A trader mostly needs the price to move.

**Gambling** is betting when you have no advantage. Here is the uncomfortable part: *trading without an advantage is gambling.* It does not matter how many charts are on your screen.

An **edge** is a real, repeatable advantage that still pays after all your costs. This book teaches you how to look for an edge, how to test whether you really have one, and how to survive while you find out.

### The three jobs of a trader

1. **Decide** what to trade, which way, and when.
2. **Limit** how much you can lose if you are wrong.
3. **Record** what happened so you can learn from it.

Most beginners put all their energy into job 1. Most of the real work is in jobs 2 and 3.

### What this book will not do

This book will not tell you what to trade. It is education only. It is not financial advice. It contains no signals and no promise of profit.
""".strip(),
    charts=(
        Chart(
            title="What trading costs alone do to an account with no edge",
            caption="Calculated: $10,000 with zero market return and zero skill. 'Busy trader' pays 8% of the account each year in costs, as in the example below. 'Low-cost fund' pays 0.1%.",
            data_kind="calculated",
            kind="lines",
            y_format="usd",
            y_label="Account value",
            x_label="Years",
            x_labels=tuple(str(y) for y in range(0, 11)),
            series=(
                Series(
                    "Low-cost fund", tuple(round(10000 * 0.999**y) for y in range(11)), "accentSoft"
                ),
                Series("Busy trader", tuple(round(10000 * 0.92**y) for y in range(11)), "danger"),
            ),
        ),
    ),
    steps=(
        "Write one sentence: why do you want to trade? Be honest. 'Quick money' is an answer you should know you hold.",
        "Decide how much money you could lose completely without it hurting your life. That is the most you should ever put at risk. For many beginners the right number today is zero, and a demo account is the right start.",
        "Read this book in order. The stages are built so each one needs only the ones before it.",
        "Do not place a real-money trade until you finish Stage 4, which covers risk.",
    ),
    example_md="""
Two friends each have $10,000.

**Sara the investor** buys a low-cost fund of many companies. She adds money every month and expects to hold for 20 years. Her return comes from business profits and dividends.

**Yousef the trader** tries to catch moves in EUR/USD that last a few days. He needs to be right often enough, with wins big enough, to beat his costs. If he has no edge, the costs slowly take his money, even if his guesses are right half the time.

Say Yousef makes 200 trades a year and each round trip costs him $4. That is **$800 a year, or 8% of his account**, before he has made a single good decision. Sara's fund might cost her $10 to $50 a year.
""".strip(),
    mistakes=(
        "Thinking a nice-looking chart means you have an edge.",
        "Starting with money you need for rent or family.",
        "Believing you must trade every day to be a trader. Often the best trade is no trade.",
        "Copying someone's calls without knowing their rules or their real record.",
    ),
    evidence=Evidence(
        Verdict.FACT,
        """
The definitions here are not claims to test. But one thing is well measured: **trading a lot tends to hurt ordinary people.** In a large US study of 66,465 households, those who traded the most earned 11.4% a year while the market earned 17.9%. The next lesson gives more of these numbers. Taken together, they are the most important facts in this book.
""".strip(),
    ),
    try_it="Write your 'why' and your 'money I could lose' number on paper. Keep it. You will need it when you build your trading plan in Stage 7.",
    quiz=(
        Q(
            "What makes trading different from gambling?",
            (
                "Trading uses charts and gambling does not",
                "A real, tested edge that pays after costs",
                "Trading happens on regulated exchanges",
            ),
            1,
            "Charts and exchanges do not create an advantage. Without a tested edge, trading is gambling.",
        ),
        Q(
            "A trader makes 200 round trips a year costing $4 each on a $10,000 account. What is the yearly cost?",
            ("0.8%", "4%", "8%"),
            2,
            "200 × $4 = $800, and $800 / $10,000 = 8%. Costs often decide the result.",
        ),
    ),
    takeaways=(
        "Trading means trying to profit from price changes.",
        "Without a tested edge, trading is gambling.",
        "Risk control and record keeping are most of the job.",
    ),
    sources=("barber-odean-2000",),
)

_HONEST_ODDS = Lesson(
    slug="start/the-honest-odds",
    title="The honest odds: most retail traders lose",
    summary="What the best available numbers say about how ordinary traders actually do.",
    est_minutes=7,
    key_concepts=("retail trader", "survivorship bias", "costs", "base rate"),
    goal="See the real numbers on how retail traders do, so you start with clear eyes.",
    body_md="""
A **retail trader** is a person trading their own money, not working for a bank or fund. Almost all trading advertising is aimed at retail traders. So it is worth knowing how they actually do.

### What regulators and researchers have measured

- **Contracts for difference (CFDs)** are contracts with a broker that pay you the change in a price. When European regulators studied them, between **74% and 89%** of retail accounts lost money. Average losses per client ranged from €1,600 to €29,000.
- **Day trading in Brazil:** among people who kept day trading futures, about **3%** came out ahead after costs.
- **Day trading in Taiwan:** fewer than **1%** of day traders could earn reliable profits after fees.
- **Ordinary stock accounts in the US:** the households trading the most earned about 6.5 percentage points a year *less* than the market.

These studies cover different markets and times. They do not agree on one exact number. They all point the same way.

### Why so many lose

1. **Costs.** You pay on every trade. Your wins must beat them.
2. **Competition.** On the other side are firms with better data, faster systems and full-time experts.
3. **Leverage.** Borrowed money makes normal losing streaks fatal.
4. **Behaviour.** Holding losers, cutting winners, and trading more when upset.

### Why it still looks easy

Winners post screenshots. Losers go quiet. This is **survivorship bias**: you only see the people who survived, so the picture looks better than the truth. If a thousand people flip coins, about one will get ten heads in a row. That person looks like a genius and is only lucky.
""".strip(),
    charts=(
        Chart(
            title="Share of retail CFD accounts that lost money (EU regulators)",
            caption="The low and high ends of the range national regulators reported to ESMA. Across firms and countries the share was between these two numbers.",
            data_kind="published",
            kind="bars",
            y_format="pct",
            y_label="Accounts losing money",
            source_note="ESMA, 2018 press release on CFD restrictions.",
            bars=(Bar("Lowest reported", 74, "warn"), Bar("Highest reported", 89, "danger")),
        ),
        Chart(
            title="Luck looks like skill: 12 traders with no edge",
            caption="Simulated: every trade is a coin flip paying 1R, and each risks 2% of the account. No trader has any edge at all, yet some curves look like strong careers and others look like disasters.",
            data_kind="calculated",
            kind="lines",
            y_format="plain",
            y_label="Account (start = 100)",
            x_label="Trades",
            series=equity_paths(
                n_paths=12, n_trades=150, win_rate=0.5, win_r=1.0, risk_pct=2.0, seed=11
            ),
        ),
    ),
    steps=(
        "Assume, as your starting point, that you are in the losing group.",
        "Treat each claim of success as unproven until you see a long, audited record that includes the costs.",
        "Ask of any strategy: what would happen if I took this with no skill at all? Compare with that.",
        "Decide now that you will not risk real money until your own tested results justify it.",
    ),
    example_md="""
A course seller shows a year of winning trades. Take 1,000 people who start trading. Say each one has a 50% chance of a profitable month, purely by luck.

- After 1 month, about 500 are up.
- After 6 months in a row, about 16 are left.
- After 12 months in a row, about **0.24 people** are left, so it might happen or might not.

With 100,000 people trying, about **24** would have a perfect 12-month streak **by luck alone**. Some of those will sell courses. Their record is real. It proves nothing about skill.
""".strip(),
    mistakes=(
        "Thinking 'I am smarter than average, so these numbers do not apply to me'. Most losing traders thought this too.",
        "Trusting screenshots. They are easy to fake and easy to cherry-pick.",
        "Reading 'most lose' as 'nobody wins'. Some do. The point is that you should not assume you will.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
**Well measured:** regulators' CFD data and several large academic studies all find that most retail traders lose after costs.

**Less certain:** the exact percentage. It changes with the market, period and how 'profitable' is defined. The Brazil figure counts persistent futures day traders; the Taiwan figure counts day traders able to earn reliable returns.

**This app's own record:** the mentor's own direction forecasts are unproven. Since 14 October 2026, forecast windows that started while the market was open went 18 calls at 38.9% correct, against about 51.8% needed to break even. Nothing in this book should be read as saying this app can beat the market.
""".strip(),
    ),
    try_it="Find any trader's advert online. Write down what is missing: time period, costs, losing trades, audited results, how many followers lost money. Count the missing items.",
    quiz=(
        Q(
            "European regulators found what share of retail CFD accounts lost money?",
            ("About 30–50%", "About 50–60%", "About 74–89%"),
            2,
            "National regulators reported 74–89% losing money, with average losses of €1,600 to €29,000.",
        ),
        Q(
            "A trader with a perfect 12-month record is proof of…",
            (
                "Skill, because 12 wins in a row is rare",
                "Nothing by itself: with enough people trying, some will do this by luck",
                "A guaranteed future income",
            ),
            1,
            "That is survivorship bias. You need the full group and a much longer record to tell skill from luck.",
        ),
    ),
    takeaways=(
        "Most retail traders lose money after costs. This is measured, not an opinion.",
        "You mostly see the winners, so success looks more common than it is.",
        "Start by assuming you have no edge until tests show otherwise.",
    ),
    sources=("esma-cfd-2018", "chague-2020", "barber-day-2014", "barber-odean-2000"),
)

_HOW_TO_USE = Lesson(
    slug="start/how-to-use-this-book",
    title="How to use this book",
    summary="The map from complete beginner to someone who could trade independently.",
    est_minutes=5,
    key_concepts=("roadmap", "demo account", "lesson format"),
    goal="Understand the path through the book and how each lesson is built.",
    body_md="""
This book moves in stages. Each stage only needs the ones before it.

| Stages | What you get |
|---|---|
| 1–3 | You can read a price, place an order and read a chart |
| 4 | You know how to size a trade so a losing run will not end you |
| 5–6 | You know the tools people use, and which ones have evidence |
| 7–8 | You can follow a full trading plan in any market |
| 9–10 | You can test whether your plan is real or luck |
| 11–12 | You know how models and professionals work |

### How every lesson is built

Each lesson has the same parts, always in the same order:

- **Goal:** one sentence on what you will learn.
- **Explained simply:** the idea, with each new word explained.
- **Step by step:** exactly what to do.
- **Worked example:** the idea with real numbers.
- **Common mistakes:** how people get this wrong.
- **Does it actually work?** what testing shows, and what is only popular belief.
- **Try it yourself:** a small job for you.
- **Check yourself:** a short quiz.
- **Key takeaways:** the few things to remember.

### About the charts

Every chart has a label. **Illustrative** means the prices are made up to show a shape. **Calculated** means exact maths or a simulation, with the assumptions written under it. **Published** means numbers reported by a named source, redrawn here. If a chart looks perfect, it is probably illustrative. Real charts are messier.

### About 'Does it actually work?'

You will see one of these labels:

- **Definition:** nothing to test, just the meaning of a word.
- **Supported:** repeated testing finds it, with limits explained.
- **Mixed:** some tests pass and some fail.
- **Weak evidence:** tests mostly fail, or it only works before costs.
- **Little testing:** popular, but rarely tested properly.

### One market or all markets?

This book teaches any market. Many worked examples use EUR/USD because it is cheap to trade and this app follows it, but Stage 8 shows how to change a plan for stocks, futures, gold, bonds, options and crypto.

Education only. Nothing here is financial advice or a recommendation to trade anything.
""".strip(),
    charts=(
        Chart(
            title="A sensible pace through the book",
            caption="A suggested minimum, not a measurement. Going slower is fine. Going faster usually means skipping the risk and testing stages, which are the ones that protect you.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Weeks of study and demo practice",
            bars=(
                Bar("Stages 1–3", 2, "accent"),
                Bar("Stage 4", 2, "danger"),
                Bar("Stages 5–6", 6, "accent"),
                Bar("Stages 7–8", 8, "accent"),
                Bar("Stages 9–10", 6, "warn"),
                Bar("Demo proof", 12, "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Read one lesson at a time, in order.",
        "Do each 'Try it yourself' task. Reading alone does not build skill.",
        "Answer the quiz from memory, then read the explanation even when you were right.",
        "Open a demo account, which uses pretend money on real prices, once you reach Stage 2.",
        "Use the glossary whenever a word is unclear.",
        "Only when you finish Stage 10 should you think about risking real money. Even then, start small.",
    ),
    example_md="""
A learner studies for 30 minutes on most days.

- A typical lesson takes 6 minutes to read and 10 minutes to practise.
- Two lessons a day is about 30 minutes.
- The whole book is around 150 lessons, so this learner finishes in about **75 study days**, or three to four months with breaks.

Then comes at least **three months of demo trading** with a written plan. That puts the first small real-money trade about six to seven months from day one. That can feel slow. Compare it with the cost of the usual path, which is losing the account in the first few months.
""".strip(),
    mistakes=(
        "Skipping to the strategy chapters. Without Stage 4 a good strategy still loses the account.",
        "Treating a quiz as a test to pass rather than a tool to remember.",
        "Believing a chart in this book is a real market when its label says illustrative.",
    ),
    evidence=fact(
        "This lesson explains the book. There is nothing to test. The pace above is a suggestion, not a research finding."
    ),
    try_it="Pick how many minutes a day you can really give this. Set a fixed time, and find the Learn button so you can come back tomorrow.",
    quiz=(
        Q(
            "Which stage should you finish before risking any real money?",
            ("Stage 3", "Stage 4 at the least, and ideally Stage 10", "Stage 7"),
            1,
            "Stage 4 teaches you to survive. Stage 10 teaches you to tell an edge from luck.",
        ),
        Q(
            "A chart in this book is labelled 'illustrative'. What does that mean?",
            (
                "The prices are made up to show a shape",
                "It is real data from the last year",
                "It is a forecast",
            ),
            0,
            "Illustrative charts teach a shape. They are not real market data and they are not forecasts.",
        ),
    ),
    takeaways=(
        "The stages build on each other, so read them in order.",
        "Every lesson separates tested facts from popular belief.",
        "Check each chart's label to know whether its data is real.",
    ),
)

_pair = path([(0, 1.0850), (10, 1.0900), (20, 1.0870), (34, 1.0950)], seed=21, noise=0.25)

_WHAT_YOU_TRADE = Lesson(
    slug="market-basics/what-you-are-trading",
    title="What you are actually trading",
    summary="Prices, pairs and contracts: what the number on your screen really means.",
    est_minutes=7,
    key_concepts=("pair", "base", "quote", "ratio", "instrument"),
    figures=(Figure("pair-ratio", "A pair is a ratio: how many dollars one euro costs."),),
    goal="Understand what a price means, so you know exactly what moves your profit or loss.",
    body_md="""
An **instrument** is anything you can trade: a currency pair, a share, a futures contract, a coin. Every instrument has a price. But the price means slightly different things in different markets.

### Currency pairs are ratios

In **forex**, the market for currencies, you always trade one currency against another. A **pair** such as **EUR/USD** is a ratio. It tells you how many US dollars one euro costs right now.

The first currency (EUR) is the **base**. The second (USD) is the **quote**. If EUR/USD moves from 1.0850 to 1.0900, one euro now costs half a cent more. That is a rise of about 0.46%.

You are never trading "the euro". You are trading the *relationship* between two currencies. If both become stronger against the world, EUR/USD may not move at all.

So the pair has two stories at once. A great euro story can be cancelled by a great dollar story. Any headline about the dollar is also news about EUR/USD, from the other side.

### Other markets

- A **share** price is what one small piece of a company costs. If it rises from $100 to $101, you made $1 per share.
- A **future** is a contract to buy or sell later at a set price. Its size is fixed by the exchange.
- A **coin** like bitcoin is usually quoted against a dollar or a dollar-like token, so it is really a pair too.

### Who wins when the price moves

A **long** position gains when the price rises. A **short** position gains when the price falls. In forex, when you are long EUR/USD you hold euros and owe dollars.
""".strip(),
    charts=(
        candle_chart(
            _pair,
            title="EUR/USD: each candle is one period's price story",
            caption="Illustrative prices. Up means one euro buys more dollars, so the euro is stronger against the dollar.",
            marks=(
                Mark(0, 1.0850, "1.0850", "fg"),
                Mark(34, 1.0950, "1.0950", "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Read the name: which currency or asset comes first? That is what you are buying or selling.",
        "Read the price as a sentence: 'one [base] costs [price] [quote]'.",
        "Work out what a rise means for you: is your base getting stronger, or your quote weaker?",
        "Before any trade, ask what would have to happen on *both* sides of a pair for you to be wrong.",
    ),
    example_md="""
You buy EUR/USD at **1.0850** with €10,000, so you hold euros and owe dollars. The price rises to **1.0950**.

- Your euros are now worth €10,000 × 1.0950 = **$10,950**.
- They cost you €10,000 × 1.0850 = **$10,850**.
- Profit: **$100**, before costs.

If instead the price falls to 1.0750, your loss is $100. Note that the euro does not have to be "strong" for you to make money. If the dollar weakens because the US economy disappoints, EUR/USD can rise without any good news from Europe.
""".strip(),
    mistakes=(
        "Treating 'the dollar is strong' and 'EUR/USD is falling' as two separate ideas. For this pair they are the same event.",
        "Forgetting that in a pair like USD/JPY the dollar is the base, so a rising price means a *stronger* dollar.",
        "Assuming every market's price works the same. A future's value depends on its contract size, not just its price.",
    ),
    evidence=fact(
        "These are definitions. One related fact from the Bank for International Settlements' 2025 survey: the dollar was on one side of 89.2% of all currency trades, so it really is the centre of the system."
    ),
    try_it="Open any chart. Write the price in words: 'One euro costs ___ dollars'. Do the same for USD/JPY and for one stock. Which way does the price move if the dollar gets stronger in each case?",
    quiz=(
        Q(
            "In EUR/USD, which currency is the base?",
            ("USD", "EUR", "Neither, both count equally"),
            1,
            "The first currency is the base. The price says how much quote currency one unit of base costs.",
        ),
        Q(
            "USD/JPY rises from 150 to 152. What happened?",
            (
                "The dollar got stronger against the yen",
                "The yen got stronger against the dollar",
                "Both got stronger by the same amount",
            ),
            0,
            "In USD/JPY the dollar is the base, so a higher number means one dollar buys more yen.",
        ),
    ),
    takeaways=(
        "A currency pair is a ratio of two currencies.",
        "Every price has two sides. A move can come from either.",
        "Long gains on a rise; short gains on a fall.",
    ),
    sources=("bis-fx-2025",),
)

_LOTS = Lesson(
    slug="market-basics/lots-pips-leverage",
    title="Lots, pips and leverage",
    summary="The three numbers that decide how much each price move is worth to you.",
    est_minutes=8,
    key_concepts=("pip", "lot", "leverage", "margin", "contract size"),
    figures=(
        Figure(
            "leverage", "Leverage turns a small margin into a large exposure, in both directions."
        ),
    ),
    goal="Be able to work out what any price move is worth in money, before you place a trade.",
    body_md="""
Three small words decide how much money you make or lose.

**Pip.** A *pip* is a small step of price in forex. For most pairs it is **0.0001**. For pairs with the Japanese yen it is **0.01**. If EUR/USD moves from 1.0850 to 1.0851, it moved one pip.

**Lot.** A *lot* is a standard size of trade.

| Name | Units of base currency |
|---|---|
| Standard lot (1.00) | 100,000 |
| Mini lot (0.10) | 10,000 |
| Micro lot (0.01) | 1,000 |

**Leverage.** *Leverage* means a small deposit controls a much bigger position. The deposit is called **margin**. With 30:1 leverage, each $1 of margin controls $30 of currency. Gains and losses are both worked out on the big number, not on your deposit.

### Other markets use different words

- **Stocks:** you buy shares. Each share is its own unit.
- **Futures:** you buy *contracts*. The exchange sets the size. The E-mini S&P 500 future is worth $50 for every point the index moves. The Micro version is worth $5.
- **Crypto:** you buy amounts in coins or dollars.

So the question is always the same: *how much is one step of price worth in my money, at this size?*
""".strip(),
    charts=(
        Chart(
            title="Same 1% move, different leverage: your account change",
            caption="Calculated: account change from a 1% move against you if you use all the leverage shown. Costs are ignored, so reality is slightly worse.",
            data_kind="calculated",
            kind="bars",
            y_format="pct",
            y_label="Change in account",
            bars=(
                Bar("1:1", -1, "accentSoft"),
                Bar("5:1", -5, "accent"),
                Bar("10:1", -10, "warn"),
                Bar("30:1", -30, "danger"),
                Bar("100:1", -100, "danger"),
            ),
        ),
    ),
    steps=(
        "Find the size you are trading (for example, 0.10 lots = 10,000 units).",
        "Find the value of one step of price. For EUR/USD, one pip × units = 0.0001 × 10,000 = $1.",
        "Multiply by the number of pips to your stop to see the money at risk.",
        "Work out the position value: units × price. Divide by your account size to see your real leverage.",
    ),
    example_md="""
You have a **$5,000** account. You trade **0.10 lots** of EUR/USD at 1.0800.

- **Position value:** 10,000 × 1.0800 = **$10,800**.
- **Real leverage:** $10,800 / $5,000 = **2.16 times**. Your broker may offer 30:1, but this is what you are using.
- **Pip value:** 0.0001 × 10,000 = **$1 per pip**.
- A move of 50 pips against you costs **$50**, which is **1% of your account**.

Now imagine you trade 1.00 lot instead. Pip value is $10. The same 50 pips costs **$500**, which is 10% of your account. And the position value is $108,000, so you are using 21.6 times leverage. A normal day's move could hurt badly.
""".strip(),
    mistakes=(
        "Looking at the leverage your broker offers rather than the leverage you are using.",
        "Forgetting that pip value changes on pairs where USD is not the quote currency.",
        "Treating margin as the most you can lose. In a fast market you can lose all your margin and, on some accounts, more.",
    ),
    evidence=fact(
        "Definitions and arithmetic. One relevant finding: EU regulators capped retail forex leverage at 30:1 on major pairs and as low as 2:1 on crypto because of how badly leveraged retail accounts did."
    ),
    try_it="Use the app's position-size calculator. Enter a $10,000 account and a 40-pip stop. How many lots make 1% risk? Check the answer by hand.",
    quiz=(
        Q(
            "On EUR/USD, what is one pip worth at 0.10 lots?",
            ("$0.10", "$1", "$10"),
            1,
            "0.10 lots = 10,000 units, and 10,000 × 0.0001 = $1 per pip.",
        ),
        Q(
            "An account of $2,000 holds a $20,000 position. What leverage is being used?",
            ("2:1", "10:1", "20:1"),
            1,
            "$20,000 / $2,000 = 10. The broker's maximum is not what matters; the size you use is.",
        ),
    ),
    takeaways=(
        "Pip, lot and leverage turn a price move into money.",
        "Always compute what one step is worth before you trade.",
        "The leverage you use matters, not the leverage you are offered.",
    ),
    sources=("esma-cfd-2018", "cme-micro"),
)

_SPREAD = Lesson(
    slug="market-basics/spread-is-your-first-expense",
    title="The spread is your first expense",
    summary="Every trade starts slightly in the red. Here is why, and how much it adds up to.",
    est_minutes=6,
    key_concepts=("bid", "ask", "spread", "transaction cost"),
    figures=(
        Figure("spread", "The gap between bid and ask is a fee you pay on every round trip."),
    ),
    goal="Know what the spread is, how much it costs you, and when it becomes dangerous.",
    body_md="""
At any moment a market shows two prices.

- The **bid** is the price at which you can sell.
- The **ask** is the price at which you can buy.

The ask is always higher. The gap between them is the **spread**. It is a real cost that you pay on every trade.

Think of a money changer at an airport. They buy your dollars at one rate and sell at a worse rate. The gap is how they get paid.

If you buy at the ask and sell a second later at the bid, you lose the spread even though the price did not move. So every trade starts slightly in the red.

### When spreads get dangerous

- **Around big news**, spreads can widen a lot, often several times normal.
- **When markets are quiet** or a session is closing, fewer people are quoting.
- **On less popular instruments**, the spread is much wider all the time.

### Why this matters so much

Your strategy's profit per trade has to be bigger than your costs. If you scalp small moves, the spread may be a big share of your target. Many strategies that look good on paper die here. A **backtest** is a test of rules on past data. A backtest that ignores the spread is fiction.
""".strip(),
    charts=(
        Chart(
            title="How the spread eats a small target",
            caption="Calculated: share of a profit target taken by a 0.8-pip spread. The spread is the same each time; the shorter your target, the more it costs you.",
            data_kind="calculated",
            kind="bars",
            y_format="pct",
            y_label="Share of target lost to spread",
            x_label="Profit target (pips)",
            bars=(
                Bar("5", 16, "danger"),
                Bar("10", 8, "warn"),
                Bar("20", 4, "accent"),
                Bar("50", 1.6, "accentSoft"),
                Bar("100", 0.8, "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Look up the live bid and ask for what you plan to trade.",
        "Convert the spread into money at your size: spread in pips × pip value.",
        "Add commission and any other fees to get your total cost per round trip.",
        "Compare with your target. If costs are more than about 10% of your target, reconsider.",
        "Do not trade during the seconds around major news unless your plan is built for it.",
    ),
    example_md="""
You trade 0.10 lots of EUR/USD. The spread is **0.8 pips**. Pip value is $1.

- Cost per round trip: 0.8 × $1 = **$0.80**.
- 30 trades a day = **$24 a day**.
- About 220 trading days a year = **$5,280 a year**.

On a $10,000 account, that is **53% of the account per year in spread alone**, before commission or slippage. You would need to earn over 53% a year just to break even.

Slippage is the gap between the price you expected and the price you got. It would make this worse.
""".strip(),
    mistakes=(
        "Testing a strategy without costs and being surprised when it loses live.",
        "Measuring your win or loss from the mid price instead of the price you can actually trade at.",
        "Choosing a broker on leverage rather than total cost.",
    ),
    evidence=fact(
        "Arithmetic. The spread is a guaranteed cost that exists on every trade. Studies of retail options find an extreme version of this problem, with average spreads around 12.6% on the cheap weekly options retail traders prefer."
    ),
    try_it="Open three instruments in a demo account at a quiet hour. Write down the spread in each. Open them again in the minutes after a major data release. How much did they widen?",
    quiz=(
        Q(
            "Which statement is correct?",
            (
                "You buy at the bid and sell at the ask",
                "You buy at the ask and sell at the bid",
                "You buy and sell at the same price",
            ),
            1,
            "Buy at the higher ask, sell at the lower bid. The difference is your cost.",
        ),
        Q(
            "A 1-pip spread on a 5-pip target costs what share of the target?",
            ("2%", "20%", "50%"),
            1,
            "1 / 5 = 20%. Short-term strategies are especially exposed to spread.",
        ),
    ),
    takeaways=(
        "Every trade pays the spread, so every trade starts in the red.",
        "Small targets lose a large share to costs.",
        "Spreads widen when you most want to trade, such as during news.",
    ),
    sources=("bryzgalova-2023",),
)

_rw = random_walk(60, seed=5, start=100.0, vol=0.9)

_RANDOM = Lesson(
    slug="start/why-it-looks-predictable",
    title="Why charts look predictable even when they are not",
    summary="Your eyes find patterns everywhere. A chart of pure luck shows why that is dangerous.",
    est_minutes=6,
    key_concepts=("random walk", "pattern", "hindsight bias"),
    goal="Learn why a chart can look full of patterns even when nothing in it can be predicted.",
    body_md="""
A **random walk** is a price path where each step is decided by something like a coin flip. Nothing in the past helps you guess the next step.

Now look at the first chart below. It has trends, reversals and what look like support and resistance levels. It was produced by a computer **flipping coins**. There is no information in it.

Human brains are built to find patterns. That helped our ancestors spot danger. On a chart it causes a problem: we see trends and setups even in pure noise. Then, because we know what happened next, we feel we 'would have seen it coming'. This is **hindsight bias**.

### What this does not mean

It does not mean every market is pure noise. Later chapters show some effects, such as momentum, that hold up in long tests. It means **a pattern looking convincing is not evidence**. The only evidence is testing rules on data you did not see when you made the rules.

### A simple rule

From here on, each time you see a clean chart pattern, ask: *what would this look like on random data?* Quite often the answer is: exactly the same.
""".strip(),
    charts=(
        candle_chart(
            _rw,
            title="These candles were made by flipping coins",
            caption="Simulated random walk: each close is the last close plus a random step. Any 'trend' or 'level' you can see here happened by chance.",
        ),
    ),
    steps=(
        "Take any chart pattern you believe in.",
        "Find 50 past examples of it, including the ones that failed.",
        "Write down what happened after each one, using a fixed rule decided in advance.",
        "Compare with what happens at random points in the same market.",
        "Only believe it if it beats random by more than your costs.",
    ),
    example_md="""
You notice that after three red candles in a row, the fourth is often green. You look at a chart and find 10 clear examples. Eight turned green. That looks like 80%.

Now you test it properly on 2,000 cases, with the rule set in advance:

- Green after three reds: **1,020**.
- Red after three reds: **980**.

That is 51%, which is close to chance, and costs would remove it. The first count felt strong only because you noticed the wins. Careful testing removes that.
""".strip(),
    mistakes=(
        "Trusting a pattern because you can remember it working.",
        "Looking only at the winning examples, because those are the ones that stand out.",
        "Thinking that because some effects are real, the one you just noticed must be.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Researchers have long found that exchange rates are very hard to forecast. A large review by Rossi (2013) found that forecasting ability depends on the method, the horizon and the period, and that the random walk is the toughest benchmark to beat.

But random walks are not the whole story. The academic debate is summed up by a paper of Grossman and Stiglitz: if prices held all information, nobody would pay to gather it. So markets can only be *nearly* efficient. There may be small edges, and they are hard to find.
""".strip(),
    ),
    try_it="Use a coin. Start at 100. Heads = up 1, tails = down 1. Plot 60 flips on paper. Can you find a 'support level' or a 'trend'? Could you have used it to predict the next flip?",
    quiz=(
        Q(
            "A chart has a neat-looking trend and a double bottom. What does that prove?",
            (
                "The pattern will work again",
                "Nothing by itself: random data also creates these shapes",
                "The market is efficient",
            ),
            1,
            "A pattern needs testing on data not used to find it. Looks do not count as evidence.",
        ),
        Q(
            "You remember eight recent wins from a rule. What should you do next?",
            (
                "Start trading it right away",
                "Test it on hundreds of cases with rules fixed in advance",
                "Increase your size since it works",
            ),
            1,
            "Memory keeps the wins. Only a pre-defined test on many cases tells you whether it is real.",
        ),
    ),
    takeaways=(
        "Pure coin flips produce charts that look full of patterns.",
        "A convincing shape is not evidence. A fair test is.",
        "Some real effects exist, but only testing can show which.",
    ),
    sources=("rossi-2013", "grossman-stiglitz-1980"),
)

CHAPTERS = (
    chapter(
        "start",
        "start-here",
        "Start here",
        "What trading is, how people really do, and how to use this book.",
        (_WHAT_TRADING_IS, _HONEST_ODDS, _HOW_TO_USE, _RANDOM),
    ),
    chapter(
        "start",
        "first-numbers",
        "Your first numbers",
        "What a price means, and how much each price move is worth.",
        (_WHAT_YOU_TRADE, _LOTS, _SPREAD),
    ),
)
