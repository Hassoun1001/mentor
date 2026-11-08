"""Stage 2 — How markets and orders work."""

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
    Series,
    Verdict,
    Zone,
    candle_chart,
    chapter,
    fact,
)
from mentor.domain.curriculum.charts import path

_WHO = Lesson(
    slug="markets/who-is-on-the-other-side",
    title="Who is on the other side of your trade",
    summary="Every trade has someone on the other side. Knowing who helps you stay realistic.",
    est_minutes=7,
    key_concepts=("market maker", "hedger", "speculator", "institution"),
    goal="Know who else is trading, why they trade, and what that means for you.",
    body_md="""
Every time you buy, someone sells. So before asking "will this go up?", it helps to ask "who is selling to me, and why?"

**The main groups**

- **Market makers** quote both a buy price and a sell price all day. They make money on the gap between the two, not by guessing direction. Big banks do this in forex; specialist firms do it in shares and options.
- **Hedgers** trade to reduce a risk they already have. An airline buys fuel futures because it fears oil rising. A European company selling in the US sells dollars ahead of time so a weak dollar will not hurt it. Hedgers are often happy to accept a small loss on the trade, because it protects the business.
- **Institutions** are funds, pension schemes and insurers moving large sums. They often trade slowly and for long-term reasons, and may not care about a few pips.
- **Speculators** trade to make a profit from price changes. Hedge funds and proprietary trading firms are full-time professionals. **Retail traders** like you are also speculators, with far less data and speed.
- **Central banks** sometimes trade to influence their currency, and they set the interest rates that everyone else reacts to.

### Why this matters

Your counterparty is rarely a fool. When you buy from a market maker, it earns the spread and then manages its risk. When you buy from a hedger, you may get a fair deal because the hedger was not trying to win. But when you buy from a well-informed fund, you are probably the one who is about to be wrong.

Most of the short-term money is made by the groups with the best speed and information. That is why a retail trader's edge usually has to come from somewhere else: **longer timeframes, patience, smaller size, or doing what big players cannot do easily.**
""".strip(),
    charts=(
        Chart(
            title="Who trades foreign exchange (by instrument, April 2025)",
            caption="Average daily turnover by product. The headline was $9.6 trillion a day. Most of it is swaps and forwards used for funding and hedging, not speculation on direction.",
            data_kind="published",
            kind="bars",
            y_format="pct",
            y_label="Share of daily turnover",
            source_note="Bank for International Settlements, Triennial Survey 2025.",
            bars=(
                Bar("FX swaps", 42, "accent"),
                Bar("Spot", 31, "accentSoft"),
                Bar("Forwards", 19, "accent"),
                Bar("Options", 7, "warn"),
                Bar("Currency swaps", 2, "muted"),
            ),
        ),
    ),
    steps=(
        "Pick any market you like.",
        "List the groups active in it: hedgers, market makers, funds, retail.",
        "For each one, write why they trade: profit, protection or spread.",
        "Ask what edge you could have that those groups do not already have.",
        "If you cannot name one, treat your trades as practice until you can.",
    ),
    example_md="""
A German car maker expects to receive **$10 million** in three months. It worries the dollar will fall against the euro.

It **sells dollars forward**, which means agreeing today on an exchange rate for three months from now. Say that locks in 1.0900. If EUR/USD later rises to 1.1200, the car maker gets fewer euros on its sales but gains on its hedge. Its income is protected.

A retail trader who bought dollars from that hedge has no such protection. If the trade loses money, that loss is simply a loss. The two sides of the same trade had completely different goals.
""".strip(),
    mistakes=(
        "Imagining the market as 'you against the chart'. It is you against other people and firms.",
        "Assuming every large player is trying to hunt your stop. Most are hedging, funding or managing their own risk.",
        "Thinking you can beat full-time professionals at their fastest game on a retail connection.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Measured facts: the BIS survey reports the product breakdown in the chart above, and the US dollar was on one side of 89.2% of trades.

A measured research result: Evans and Lyons found that signed dealer order flow, meaning who was actively buying versus selling, explained a large part of daily exchange rate changes. Traditional macro models did not. So *who is pressing the trade* matters in the short run. That is useful to know, but retail traders rarely see this data.
""".strip(),
    ),
    try_it="In your journal, write the name of the market you most want to trade and the three kinds of participant most likely to be on the other side of you.",
    quiz=(
        Q(
            "A market maker mainly earns money from…",
            (
                "Predicting direction",
                "The gap between buy and sell prices",
                "Commissions charged to retail traders only",
            ),
            1,
            "Market makers quote both sides and earn the spread, then manage the risk they hold.",
        ),
        Q(
            "Why might a hedger accept a losing trade?",
            (
                "It does not know better",
                "The trade offsets a business risk",
                "Regulators require it",
            ),
            1,
            "A hedge is insurance. Losing on the hedge usually means the underlying business did better.",
        ),
    ),
    takeaways=(
        "Every trade has a counterparty with its own reasons.",
        "Short-term profit tends to flow to the fastest and best informed.",
        "A retail edge usually lives in patience and timeframes, not speed.",
    ),
    sources=("bis-fx-2025", "evans-lyons-2002"),
)

_VENUES = Lesson(
    slug="markets/exchanges-and-otc",
    title="Exchanges, OTC and where your broker fits in",
    summary="The difference between a central exchange and a dealer network, and why it matters to you.",
    est_minutes=7,
    key_concepts=("exchange", "OTC", "broker", "CFD", "clearing"),
    goal="Understand where your order actually goes and who you are trusting when you trade.",
    body_md="""
There are two basic kinds of market.

**An exchange** is a central place with one order book, one set of rules and public prices. Shares, futures and listed options trade on exchanges. A **clearing house** stands in the middle of each trade, so if one side fails the other is still paid.

**Over-the-counter (OTC)** means trades happen directly between parties, with no central exchange. Forex spot is mainly OTC. Prices are quoted by dealers, so two brokers can show slightly different prices at the same moment.

### Where your broker fits

A **broker** gives you access. How they do it matters a lot.

- **An agency broker** sends your order on to the market and charges commission.
- **A market-maker broker** may take the other side of your trade itself. It profits when you lose. This does not make it a cheat, but it does mean a conflict of interest.
- A **CFD** (contract for difference) is a contract with your broker to pay the change in a price. You never own the asset. The contract is only as good as the firm behind it.

### Why it matters

- With an exchange, you can check prices and volumes publicly. In OTC markets, "volume" on your screen is usually only that broker's activity.
- With an exchange and clearing house, the risk that the other side fails is small. With a CFD, you carry the risk of the broker.
- Regulation depends on who is on the other side, so check who your broker is regulated by.
""".strip(),
    charts=(
        Chart(
            title="The dollar is on one side of most currency trades",
            caption="Share of global FX turnover in April 2025 that involved each currency. Each trade has two currencies, so the shares add up to about 200%.",
            data_kind="published",
            kind="bars",
            y_format="pct",
            y_label="Share of FX turnover",
            source_note="Bank for International Settlements, Triennial Survey 2025.",
            bars=(
                Bar("US dollar", 89.2, "accent"),
                Bar("Euro", 28.9, "accentSoft"),
                Bar("Japanese yen", 16.8, "accentSoft"),
                Bar("British pound", 10.2, "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Look up who regulates your broker, and confirm it on the regulator's own website.",
        "Find out if your account is agency or market-maker. Read the order-execution policy.",
        "Find out which products are exchange-traded and which are contracts with the broker.",
        "Check what happens if the broker fails. Are client funds held separately? Is there a compensation scheme?",
        "Keep only the money you actually need for trading at any one broker.",
    ),
    example_md="""
Same idea, two products.

**E-mini S&P 500 future** on CME: one exchange, public volume, a clearing house stands behind each trade, and there is one official price for everyone.

**S&P 500 CFD** at a broker: the broker sets the price, your position exists only in that broker's books, and the 'volume' on the chart is only that broker's data.

Neither is automatically bad. But if your broker runs into trouble, the first position is a claim on a regulated exchange structure, and the second is a claim on one company.
""".strip(),
    mistakes=(
        "Assuming the volume on a forex or CFD chart is the volume of the whole market.",
        "Choosing a broker only because it advertises high leverage.",
        "Trusting a 'regulated' claim without checking the regulator's register yourself.",
    ),
    evidence=fact(
        "These are definitions. One related warning from the CFTC and NASAA: off-exchange retail forex is, at best, very risky and at worst outright fraud, so check registration with the relevant regulator."
    ),
    try_it="Find your broker's name on its regulator's public register. If you cannot find it, write that down and do not deposit money yet.",
    quiz=(
        Q(
            "What does a clearing house do on an exchange?",
            (
                "Sets the price",
                "Stands between buyer and seller so a default does not spread",
                "Provides leverage",
            ),
            1,
            "The clearing house guarantees trades so one side failing does not hit the other.",
        ),
        Q(
            "When you trade a CFD, who are you dealing with?",
            ("The exchange", "Your broker", "A central bank"),
            1,
            "A CFD is a contract with your broker. Its reliability depends on that firm.",
        ),
    ),
    takeaways=(
        "Exchanges have one central price and a clearing house.",
        "OTC and CFDs depend much more on the firm you trade with.",
        "Check regulation yourself, on the regulator's own site.",
    ),
    sources=("cftc-forex-alert",),
)

_ORDER_TYPES = Lesson(
    slug="becoming-pro/order-types",
    title="Market, limit and stop orders",
    summary="The three order types that every broker offers, and when to use each.",
    est_minutes=7,
    key_concepts=("market order", "limit order", "stop order", "stop-loss", "take-profit"),
    figures=(
        Figure(
            "order-types",
            "Market orders take the price now. Limits wait. Stops wake up at a level.",
        ),
    ),
    goal="Know the three basic orders and choose the right one on purpose.",
    body_md="""
Every broker gives you the same three tools. An order is simply an instruction.

- A **market order** says *"fill me now, at whatever price is available."* It is instant, but you pay the spread. In a fast market you can also get **slippage**, which means a worse price than the one you saw.
- A **limit order** says *"fill me only at this price or better."* A **buy limit** sits below the current price; a **sell limit** sits above it. You choose the price, and the market chooses whether you get filled.
- A **stop order** says *"when price reaches this level, send a market order."* A **buy stop** sits above the price; a **sell stop** sits below it. Most stop-losses are this type.

### Two orders every trade should have

From the moment you are in a position, two orders should be waiting:

1. A **stop-loss**: the exit that limits your loss to the amount you chose *before* you entered.
2. A **take-profit**: the exit that banks your gain at your target. It is a limit order.

Beginners enter on a whim and then "manage" the trade by feel. Every trade becomes an emotion test. A better way is to decide the whole exit plan first, place all the orders together, and then leave them alone.

This app's Trade plan page works out both exits for you before any money is at risk.
""".strip(),
    charts=(
        candle_chart(
            path([(0, 1.0820), (10, 1.0850), (16, 1.0832), (28, 1.0880)], seed=33, noise=0.25),
            title="Where each order sits",
            caption="Illustrative prices. The price is at 1.0850. A buy limit waits below it, a buy stop waits above it, and each fills only if price gets there.",
            hlines=(
                HLine(1.0870, "Buy stop (breakout)", "accent"),
                HLine(1.0832, "Buy limit (better price)", "accentSoft"),
                HLine(1.0812, "Stop-loss", "danger"),
            ),
            marks=(Mark(10, 1.0850, "Price now", "fg"),),
        ),
    ),
    steps=(
        "Ask: do I need to be in right now? If yes, use a market order.",
        "If you only want a better price, use a limit order and accept you may miss the trade.",
        "If you only want to enter once price breaks a level, use a stop order.",
        "Place your stop-loss and take-profit with the entry, not afterwards.",
        "Once they are placed, do not move your stop further from the entry.",
    ),
    example_md="""
EUR/USD trades at **1.0850**, and you want to buy on a dip to 1.0832.

1. Place a **buy limit** at 1.0832.
2. Attach a **stop-loss** at 1.0812, which is 20 pips below entry.
3. Attach a **take-profit** at 1.0872, which is 40 pips above entry.

At 0.10 lots (roughly $1 per pip) you risk **$20** to make **$40**. If price never drops to 1.0832, you do nothing and lose nothing. That is the point of a limit order: you pay with the chance of missing the trade instead of paying the spread and a poor entry.
""".strip(),
    mistakes=(
        "Using a market order during a news spike and getting a much worse price.",
        "Putting a buy limit above the current price by mistake. It usually fills instantly at the market.",
        "Having no stop-loss because 'I will watch it'. Screens freeze, phones die, and plans change under pressure.",
    ),
    evidence=fact(
        "These are the rules of how orders work. Note that a stop order becomes a market order, so a stop can fill worse than its level. That is called slippage, and it is common around news and gaps."
    ),
    try_it="In a demo account, place one of each: a buy limit below the price, a buy stop above it, and a position with an attached stop-loss. Check where each fills.",
    quiz=(
        Q(
            "You want to buy EUR/USD, but only if it first drops to a cheaper price. Which order?",
            (
                "Market order",
                "Buy limit below the current price",
                "Buy stop above the current price",
            ),
            1,
            "A buy limit rests below the market and fills only if price comes down to it. A buy stop triggers when price rises through a level.",
        ),
        Q(
            "What is a stop-loss usually?",
            (
                "A limit order that guarantees your price",
                "A stop order that becomes a market order at your level",
                "An instruction to your broker to call you",
            ),
            1,
            "Once triggered it trades at the market, so in a fast move your fill can be worse than the stop level.",
        ),
    ),
    takeaways=(
        "Market = now. Limit = at this price or better. Stop = once price gets here.",
        "Place stop-loss and take-profit when you enter.",
        "A stop order can slip. It limits loss, but not perfectly.",
    ),
)

_UNITS = Lesson(
    slug="chart-language/units-and-orders",
    title="Stop, target and reward: a whole trade in one sentence",
    summary="Pips, lots, stop-loss, take-profit and reward-to-risk combined into one complete plan.",
    est_minutes=6,
    key_concepts=("pip", "lot", "spread", "stop-loss", "take-profit", "R:R"),
    figures=(
        Figure(
            "trade-anatomy", "A trade is an entry, a stop that says you are wrong, and a target."
        ),
    ),
    goal="Be able to describe any trade completely in one clear sentence.",
    body_md="""
You have seen most of these words. Now we join them.

- **Pip** is the standard step of price (0.0001 on most pairs). A **pipette** is a tenth of a pip. A **tick** is the smallest move a market can make. A **point** is used loosely, so always check what it means in the market you trade.
- **Lot** is the trade size. One standard lot is 100,000 units.
- **Stop-loss** is the price that proves your idea wrong.
- **Take-profit** is where you bank the gain.
- **R:R** means **reward-to-risk**: your reward distance divided by your risk distance. A stop 30 pips away with a target 60 pips away is **2:1**.
- **R** on its own means *one unit of your risk*. If you risk $50 and make $100, you made **2R**.

A complete trade fits in one sentence:

> *"Go long at 1.0850, stop-loss 30 pips below (−1R), take-profit 60 pips above (2:1), sized so that −1R is 1% of my account."*

If you cannot say your trade that way, you do not yet have a trade. You have an opinion.
""".strip(),
    charts=(
        candle_chart(
            path([(0, 1.0820), (12, 1.0850), (22, 1.0838), (34, 1.0910)], seed=44, noise=0.22),
            title="A full trade plan, drawn",
            caption="Illustrative prices. The risk is 30 pips, the reward is 60 pips, so the reward-to-risk is 2:1.",
            zones=(
                Zone(1.0850, 1.0910, "Reward: +60 pips (+2R)", "accentSoft", 12, 34),
                Zone(1.0820, 1.0850, "Risk: -30 pips (-1R)", "danger", 12, 34),
            ),
            hlines=(HLine(1.0850, "Entry 1.0850", "fg"),),
        ),
    ),
    steps=(
        "Choose the entry price.",
        "Choose the price at which your idea is proven wrong. That is your stop.",
        "Measure the distance in pips.",
        "Choose your target and divide reward by risk. If it is less than your plan requires, skip the trade.",
        "Size the position so a stop-out costs no more than your risk limit.",
    ),
    example_md="""
Say your account holds **$5,000**, and you risk **1%** ($50) per trade.

- Entry 1.0850, stop 1.0820: 30 pips of risk.
- $50 / 30 pips = **$1.67 per pip**.
- At $1 per pip for 0.10 lots, that is about **0.17 lots**.
- Target 1.0910 is 60 pips: the win is 60 × $1.67 ≈ **$100**, which is 2R.

If you win, you make about $100. If you lose, you lose about $50. Note that the size came from your risk and your stop, not from your feelings about the trade.
""".strip(),
    mistakes=(
        "Picking the lot size first and the stop afterwards.",
        "Writing 'target 2:1' without checking whether price can realistically get there.",
        "Forgetting the spread when working out your real reward-to-risk.",
    ),
    evidence=fact(
        "Arithmetic, nothing to test. A high reward-to-risk ratio does not by itself make a trade good. The chance of reaching the target falls as the target gets further away. Lesson 'Why a 40%-win system can pay' explains this."
    ),
    try_it="Write three past or demo trades as one sentence each, using this exact format. If a trade cannot be written this way, note what was missing.",
    quiz=(
        Q(
            "A stop 30 pips away and a target 60 pips away gives what reward-to-risk?",
            ("2:1", "1:2", "1:1"),
            0,
            "Reward divided by risk: 60 ÷ 30 = 2, so you risk 1 to make 2.",
        ),
        Q(
            "You risked $40 and made $120. How many R did you make?",
            ("1R", "2R", "3R"),
            2,
            "$120 / $40 = 3R. R is measured against what you risked.",
        ),
    ),
    takeaways=(
        "A complete trade fits in one sentence: entry, stop, target, size.",
        "R is one unit of your risk.",
        "The size comes from the stop, not from how you feel.",
    ),
)

_ORDER_REF = Lesson(
    slug="orders-conditions/order-types-reference",
    title="Every order type, and exactly when to use it",
    summary="The four combinations, plus stop-limit orders, explained so they stay in your memory.",
    est_minutes=7,
    key_concepts=("buy limit", "sell limit", "buy stop", "sell stop", "stop limit order", "OCO"),
    figures=(Figure("order-grid", "Limits wait for a better price. Stops wait for a breakout."),),
    goal="Pick the right order for any situation without having to think about it.",
    body_md="""
There are four resting orders. They confuse beginners because the words "buy" and "sell" do not tell you where they sit. The simple trick is this:

**Limits want a better price. Stops want a breakout.**

| Order | Where it rests | What it means |
|---|---|---|
| Buy limit | Below the price | Buy the dip, at a discount |
| Sell limit | Above the price | Sell the rally, at a premium |
| Buy stop | Above the price | Buy only if it breaks upwards |
| Sell stop | Below the price | Sell only if it breaks downwards |

A buy stop is also how you exit a short trade if the price rises. A sell stop is how you exit a long trade if the price falls.

### Stop-limit orders

A **stop-limit** order triggers at one price and then places a limit order at another. It stops you from getting a terrible fill. But in a fast market it may not fill at all, so you can stay stuck in a losing position. For a must-exit stop-loss, a plain stop is safer.

### Linked orders

- **OCO** means *one cancels the other*. Your stop and target are usually linked this way, so filling one cancels the other.
- **Trailing stop** moves your stop as the price moves in your favour.
- **Time in force** says how long an order lasts. **GTC** means good till cancelled. **Day** means it ends with the session.
""".strip(),
    charts=(
        candle_chart(
            path([(0, 1.0800), (14, 1.0850), (28, 1.0842)], seed=52, noise=0.3),
            title="The four resting orders around the current price",
            caption="Illustrative prices. Above the price: sell limit and buy stop. Below it: buy limit and sell stop.",
            hlines=(
                HLine(1.0880, "Sell limit (sell higher)", "danger"),
                HLine(1.0865, "Buy stop (breakout up)", "accent"),
                HLine(1.0820, "Buy limit (buy cheaper)", "accentSoft"),
                HLine(1.0805, "Sell stop (breakdown)", "warn"),
            ),
        ),
    ),
    steps=(
        "Say the idea in plain words: 'I want to buy cheaper', or 'I want to sell if it breaks down'.",
        "Choose a limit if you want a better price. Choose a stop if you want confirmation.",
        "Check which side of the current price the order must sit on.",
        "Set how long the order should last.",
        "Link your exits so one cancels the other.",
    ),
    example_md="""
EUR/USD is at **1.0850**. You think that if it breaks **1.0865** it could run. You place a **buy stop at 1.0866** with a stop-loss at 1.0846 (20 pips) and a take-profit at 1.0906 (40 pips).

Two hours later a release pushes price to 1.0870 in seconds. Your buy stop triggers, and because it became a market order you fill at **1.0868**, two pips of slippage. Your risk is now 22 pips, not 20. A sell-side stop in the same spike may have slipped even more.

If you had used a stop-limit at 1.0866 limit 1.0867, you might not have been filled at all.
""".strip(),
    mistakes=(
        "Using a stop-limit as a must-exit protection and watching it skip past your limit.",
        "Leaving old orders live, forgetting them, and getting filled weeks later.",
        "Mixing up buy limit and buy stop and entering at the wrong moment.",
    ),
    evidence=fact(
        "Order types are rules, not claims. Check your broker's documentation, because the exact behaviour of stops and trailing stops can differ between platforms."
    ),
    try_it="Write these four sentences in your own words: buy limit, sell limit, buy stop, sell stop. Then place each one on a demo account and watch what happens.",
    quiz=(
        Q(
            "You want to SELL only if price rises to a better, higher level first. Which order rests above the market?",
            ("Sell stop", "Sell limit", "Buy limit"),
            1,
            "A sell limit rests above the price: 'sell, but only at this higher price or better'. A sell stop rests below and fires on a breakdown.",
        ),
        Q(
            "What is the main danger of a stop-limit used as a stop-loss?",
            (
                "It costs more commission",
                "It may not fill in a fast market",
                "It cannot be cancelled",
            ),
            1,
            "If price jumps past your limit there may be no fill, and you stay in the trade.",
        ),
    ),
    takeaways=(
        "Limits want a better price. Stops want a breakout.",
        "Plain stops are safer for must-exit protection than stop-limits.",
        "Link exits so one cancels the other.",
    ),
)

_BOOK = Lesson(
    slug="markets/order-book-and-slippage",
    title="The order book and slippage",
    summary="Why the price you see is not always the price you get.",
    est_minutes=7,
    key_concepts=("order book", "depth", "slippage", "market impact", "liquidity"),
    goal="Understand how orders meet, and why slippage happens.",
    body_md="""
An **order book** is a list of all the limit orders waiting at each price. Buy orders sit on one side and sell orders on the other. The size available at each price is the book's **depth**.

When you send a market order, it matches against those waiting orders, starting at the best price. If the best price has only a small amount waiting, your order uses all of it and moves to the next price, and the next. So a big market order fills at several prices and pushes the price against you. That is **market impact**.

**Slippage** is the difference between the price you expected and the price you actually got.

### What makes slippage worse

- **Thin liquidity**, meaning little size waiting in the book.
- **Fast markets**, such as the moments after big news.
- **Large orders** relative to what is waiting.
- **Weekends and holidays**, when books are thin or closed.

**Liquidity** simply means how easily you can trade without moving the price. A deep market lets you trade a lot quietly. A thin market moves as soon as you touch it.

Stop orders are the most exposed. When price falls through your sell stop, the stop becomes a market order at a moment when everyone else is selling too. A stop limits your loss. It does not guarantee your price. If a market gaps from 1.0850 to 1.0800 over a weekend, a stop at 1.0830 can fill at 1.0800.
""".strip(),
    charts=(
        Chart(
            title="A small order book, and how far a market order walks",
            caption="Illustrative sizes. Buying 100 units fills across the first levels at worse and worse prices: 40 at 1.0851, 30 at 1.0852 and 30 at 1.0853. Average fill: about 1.08519, not the 1.0851 on your screen.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Units waiting at each ask price",
            bars=(
                Bar("Ask 1.0851", 40, "danger"),
                Bar("Ask 1.0852", 30, "danger"),
                Bar("Ask 1.0853", 80, "danger"),
                Bar("Bid 1.0850", 35, "accentSoft"),
                Bar("Bid 1.0849", 60, "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Before trading, look at the size waiting near the current price, if your market shows it.",
        "Compare your order size with that depth.",
        "Assume at least one or two ticks of slippage on every market or stop order when you test a plan.",
        "Avoid market orders in the seconds around a major release.",
        "For large orders, split them up over time.",
    ),
    example_md="""
You buy **100 units** with a market order and the book looks like the chart:

- 40 units at 1.0851
- 30 units at 1.0852
- 30 units at 1.0853

**Average fill:** (40 × 1.0851 + 30 × 1.0852 + 30 × 1.0853) / 100 = **1.08519**.

The screen said 1.0851. You paid almost one extra tick on average, because your order walked up the book. For small retail orders in major markets this is usually tiny. On a thin instrument or around news, it can be many times that.
""".strip(),
    mistakes=(
        "Testing a plan with a fill at the exact trigger price every time.",
        "Reading a stop as a guarantee.",
        "Trading thin markets with position sizes that move the price.",
    ),
    evidence=fact(
        "This is how order matching works. Published research such as Almgren and Chriss treats large-order trading as a trade-off: trade fast and pay more impact, or trade slowly and carry more price risk. Stage 11 returns to this."
    ),
    try_it="Open a depth view if your platform has one. Note the size at the best bid and ask for two instruments, and compare at a busy hour and a quiet hour.",
    quiz=(
        Q(
            "What is slippage?",
            (
                "The broker's commission",
                "The difference between expected and actual fill price",
                "The spread",
            ),
            1,
            "Slippage is a worse (occasionally better) fill than the price you saw.",
        ),
        Q(
            "A stop at 1.0830 and a weekend gap to 1.0800. Where does the stop likely fill?",
            ("Exactly 1.0830", "Near 1.0800", "It cannot fill"),
            1,
            "A stop becomes a market order, and the market is now near 1.0800.",
        ),
    ),
    takeaways=(
        "The order book shows what is waiting at each price.",
        "Thin books and fast markets create slippage.",
        "A stop limits loss, but it does not guarantee your price.",
    ),
    sources=("almgren-chriss",),
)

_SESSION_HOURS = (
    ("00", 15),
    ("02", 15),
    ("04", 20),
    ("06", 40),
    ("08", 75),
    ("10", 65),
    ("12", 100),
    ("14", 95),
    ("16", 70),
    ("18", 35),
    ("20", 25),
    ("22", 15),
)

_CLOCK = Lesson(
    slug="becoming-pro/sessions-clock",
    title="The 24-hour market: sessions and when to trade",
    summary="Open is not the same as alive. When each market is really active.",
    est_minutes=7,
    key_concepts=("Sydney", "Tokyo", "London", "New York", "session overlap", "liquidity", "gap"),
    figures=(Figure("sessions-clock", "Forex follows the sun: Sydney, Tokyo, London, New York."),),
    goal="Know when your market is active, and why that changes your costs and your signals.",
    body_md="""
Forex trades 24 hours a day, five days a week. But "open" is not the same as "alive". The day is really a series of overlapping **sessions**, following the sun: **Sydney, Tokyo, London, New York**.

Times below are roughly in UTC and shift by an hour with daylight saving.

- **Asian hours (about 23:00–07:00 UTC):** quiet for EUR/USD. Ranges are small and spreads can be wider.
- **London open (about 07:00–08:00 UTC):** the day wakes up. The first burst of real volume often sets the direction, or fakes it.
- **London–New York overlap (about 12:00–16:00 UTC):** the main event. Most of the day's range, most of the big US data releases at 12:30 and 14:00 UTC, and the tightest spreads.
- **Late New York (about 20:00 UTC on):** winding down. Friday afternoons are mostly noise.

### Why a professional cares

1. **Trade where the liquidity is.** The same 20-pip signal means something in the overlap and very little at 3 a.m.
2. **Costs change.** Spreads widen when fewer people are quoting.
3. **The weekend gap is real.** The market closes Friday around 22:00 UTC and reopens Sunday around 22:00 UTC. Price can jump right over your stop. Holding through the weekend is a decision, not a default.

### Other markets have different clocks

US shares officially trade **09:30–16:00 New York time**, with thinner trading before and after. Major US share futures trade almost 24 hours from Sunday to Friday. Crypto trades all the time, including weekends, when liquidity is often thinner.

**Do this for your market.** Stage 8 covers each one in detail.
""".strip(),
    charts=(
        Chart(
            title="A typical day of EUR/USD activity",
            caption="Illustrative shape. Real activity varies by day and season, and it is highest in the London–New York overlap. Hours are approximately UTC.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Relative activity",
            x_label="UTC hour",
            x_labels=tuple(h for h, _ in _SESSION_HOURS),
            series=(
                Series("Activity", tuple(float(v) for _, v in _SESSION_HOURS), "accent", "area"),
            ),
        ),
    ),
    steps=(
        "Write down the hours your market is most active in your own time zone.",
        "Mark the hours of major data releases for your market.",
        "Decide which hours you will trade and which you will never trade.",
        "Compare spreads at a busy hour and at a quiet hour.",
        "Decide your rule for holding positions over weekends.",
    ),
    example_md="""
You live in Dubai, which is UTC+4.

- London–New York overlap, 12:00–16:00 UTC, is **16:00–20:00 Dubai time**.
- US data at 12:30 UTC lands at **16:30 Dubai time**.
- The Sunday reopen, about 22:00 UTC, is **02:00 Monday Dubai time**.

So a person with a day job in Dubai can reasonably trade EUR/USD from about 17:00 to 20:00. A rule like "no new EUR/USD trades after 21:00 Dubai time" is a sensible start, and it could go straight into your written plan.
""".strip(),
    mistakes=(
        "Treating every hour of the day as equally good for trading.",
        "Holding a full-size position into the weekend without a rule.",
        "Assuming times are fixed when daylight saving shifts them twice a year.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
It is well established that activity and volatility follow a daily pattern, and that spreads are wider when liquidity is thin. The BIS survey shows the UK and US are the two largest forex trading centres, and four centres (UK, US, Singapore, Hong Kong) account for 75% of trading.

What is **not** established is a universal rule like "the London open always sets the direction". Treat such claims as hypotheses to test on your own market.
""".strip(),
    ),
    try_it="Draw a 24-hour bar in your local time. Shade the active hours of your market and the time you can actually be at a screen. Trade only where they overlap.",
    quiz=(
        Q(
            "When does EUR/USD typically move the most?",
            (
                "During the Sydney session",
                "During the London–New York overlap",
                "Exactly at midnight UTC",
            ),
            1,
            "Roughly 12:00–16:00 UTC, when European and American desks are both active.",
        ),
        Q(
            "Why are spreads often wider in quiet hours?",
            (
                "Brokers charge more at night",
                "Fewer participants are quoting prices",
                "The exchange closes",
            ),
            1,
            "Less liquidity means less competition among quotes, so the gap widens.",
        ),
    ),
    takeaways=(
        "Open does not mean active.",
        "Liquidity and costs change through the day.",
        "Weekend gaps can jump over your stop.",
    ),
    sources=("bis-fx-2025",),
)

_COSTS = Lesson(
    slug="becoming-pro/costs-of-trading",
    title="What trading actually costs",
    summary="Spread, commission, swap and slippage add up to the number your edge must beat.",
    est_minutes=7,
    key_concepts=("spread", "swap", "slippage", "commission", "cost per trade", "breakeven"),
    figures=(Figure("spread-anatomy", "The spread is paid the moment you open a trade."),),
    goal="Add up your full cost per trade and know what you must make just to break even.",
    body_md="""
Every trade starts behind. Knowing how far behind is what separates people who survive from people who wonder where the money went.

- **Spread:** the gap between bid and ask. On EUR/USD it is usually 0.5–1.5 pips at retail.
- **Commission:** a fee per trade. Some accounts have a tighter spread plus commission. It is the same cost with a different label.
- **Swap or rollover:** when you hold a leveraged position overnight, you pay or earn the interest-rate difference between the two currencies. It is small per day and meaningful over weeks.
- **Slippage:** the extra you pay when an order fills at a worse price than you saw. Around big news it can be many pips.
- **Data, platform and software fees:** easy to forget, and they count too.

### Your break-even win rate

Costs raise the win rate you need. If you risk 1R to make 1R, and costs take 0.1R per trade, each winner pays 0.9R and each loser costs 1.1R. So you need to win **55%** of the time just to break even, not 50%.

Cost per trade divided by risk per trade is a number you should know for every strategy.
""".strip(),
    charts=(
        Chart(
            title="Win rate needed to break even as costs rise",
            caption="Calculated for trades risking 1R to make 1R. With a cost of c per trade (in R), a winner pays 1−c and a loser costs 1+c, so break-even win rate = (1+c) / 2.",
            data_kind="calculated",
            kind="bars",
            y_format="pct",
            y_label="Win rate needed to break even",
            x_label="Cost per trade",
            bars=(
                Bar("No cost", 50.0, "accentSoft"),
                Bar("0.05R", 52.5, "accent"),
                Bar("0.10R", 55.0, "accent"),
                Bar("0.20R", 60.0, "warn"),
                Bar("0.30R", 65.0, "danger"),
            ),
        ),
    ),
    steps=(
        "List every cost for your market: spread, commission, swap, slippage, fees.",
        "Express the total per round trip in money and in R.",
        "Multiply by how often you trade to get a monthly cost.",
        "Work out your break-even win rate.",
        "Only accept a strategy whose average gain clearly beats this cost.",
    ),
    example_md="""
A strategy risks 1R and targets 1R, and each trade risks 20 pips on 0.10 lots ($1 per pip):

- 1R = 20 pips = $20
- Spread 1 pip + commission 0.3 pip + slippage 0.5 pip = **1.8 pips = $1.80**
- Cost per trade = $1.80 / $20 = **0.09R**

Break-even win rate = (1 + 0.09) / 2 = **54.5%**.

If the strategy really wins 52% of the time, it **loses money** even though it is right more often than wrong. Most small edges die here.
""".strip(),
    mistakes=(
        "Ignoring swap on trades held for weeks.",
        "Believing 'zero commission' means no cost. The spread is still a cost.",
        "Measuring results without counting small fees that add up.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Costs matter measurably. A large study of US investors found the most active traders underperformed by about 6.5 percentage points a year, mostly because of trading costs. Regulators and researchers keep finding the same thing in very different markets.

Research on technical trading rules also shows that many results that look good before costs shrink or disappear once realistic costs are added.

On this app: its own live record is unproven, and the win rate it needs to beat costs was recently about 51.8%. The app has not been beating that reliably.
""".strip(),
    ),
    try_it="Work out your real cost per round trip on your demo account, in money and in pips. Then multiply it by the number of trades you plan to make in a month.",
    quiz=(
        Q(
            "EUR/USD shows bid 1.1000 and ask 1.1001. You buy and instantly sell. What happened?",
            ("You broke even", "You lost one pip: the spread", "You made one pip"),
            1,
            "You bought at 1.1001 and sold at 1.1000. Every round trip starts one spread behind.",
        ),
        Q(
            "A 1:1 strategy with costs of 0.2R per trade must win at least what share of trades to break even?",
            ("50%", "60%", "70%"),
            1,
            "(1 + 0.2) / 2 = 60%. Costs raise the bar quickly.",
        ),
    ),
    takeaways=(
        "Add spread, commission, swap and slippage together.",
        "Costs raise the win rate you need to break even.",
        "A strategy that wins slightly more than half can still lose money.",
    ),
    sources=("barber-odean-2000", "park-irwin-2007"),
)

_LEVERAGE = Lesson(
    slug="becoming-pro/leverage-and-margin",
    title="Leverage and margin, explained properly",
    summary="Leverage is a loan. How to use it without letting it use you.",
    est_minutes=7,
    key_concepts=(
        "leverage",
        "margin",
        "margin call",
        "notional",
        "effective leverage",
        "stop-out",
    ),
    figures=(
        Figure(
            "leverage-seesaw", "The bigger the position, the harder a small move hits your account."
        ),
    ),
    goal="Understand what leverage really does, and find your true leverage on any position.",
    body_md="""
Leverage has ruined more retail accounts than bad predictions ever did. Not because it is evil. Because nobody explained that it is **a loan**.

- **Notional** is the full value of your position.
- **Leverage** means your position can be bigger than your cash. At 30:1, every $1 of cash can control $30.
- **Margin** is the cash set aside while the position is open. It is not a fee. Close the trade and it comes back.
- **Margin call** or **stop-out** is what happens when losses eat your account down to the broker's limit. The broker closes your positions for you, usually at the worst moment. It is not bad luck. It is the receipt for trading too big.

### The number that matters: effective leverage

Forget the maximum your broker offers. Calculate:

*Total position notional ÷ account balance = your effective leverage.*

Professionals tend to run low effective leverage even when 30:1 or more is on offer. At 10 times effective leverage, a normal 1% move against you costs **10% of your account**. Three of those in a row is a normal bad week, and it takes almost a third of your money.

### Leverage caps

Many regulators limit retail leverage. In the EU it is 30:1 on major currency pairs, 20:1 on other pairs, gold and major indices, and 2:1 on crypto. In the US, retail forex is limited to 50:1 on majors and 20:1 on others. Rules change, so check the rules where you live.

This app does not ask you to pick leverage. You pick **risk per trade**, and the Trade plan sizes the position from the stop. The leverage that results is usually small. That is the point.
""".strip(),
    charts=(
        Chart(
            title="What a normal losing run does at different leverage",
            caption="Calculated: account change after four 1% moves against you in a row, using all the leverage shown. Compounded, costs ignored.",
            data_kind="calculated",
            kind="bars",
            y_format="pct",
            y_label="Account after four 1% moves against you",
            bars=(
                Bar("1×", round((0.99**4 - 1) * 100, 1), "accentSoft"),
                Bar("3×", round((0.97**4 - 1) * 100, 1), "accent"),
                Bar("5×", round((0.95**4 - 1) * 100, 1), "warn"),
                Bar("10×", round((0.90**4 - 1) * 100, 1), "danger"),
                Bar("20×", round((0.80**4 - 1) * 100, 1), "danger"),
            ),
        ),
    ),
    steps=(
        "Find your position value (units × price).",
        "Divide by your account balance. That is your effective leverage.",
        "Check how far price can move before you hit a margin call.",
        "Set a personal limit for effective leverage, well below the maximum allowed.",
        "Always work out size from your stop and your risk, not from what leverage you can get.",
    ),
    example_md="""
A **$5,000** account buys **1 mini lot** of EUR/USD at 1.1000.

- Notional: 10,000 × 1.1000 = **$11,000**.
- Margin at 30:1: $11,000 / 30 = **about $367**, set aside but not spent.
- Effective leverage: $11,000 / $5,000 = **2.2 times**.

A 1% move against you is 110 pips, costing about **$110**, which is 2.2% of the account. Painful but survivable.

Now the same account trades **1 standard lot**: $110,000 notional, 22 times effective leverage. The same 1% move costs **$1,100, or 22% of the account**.
""".strip(),
    mistakes=(
        "Treating margin used as money you have not risked.",
        "Thinking high leverage is the same as high return.",
        "Letting your position size grow because 'the broker let me'.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Regulators reached their leverage limits by looking at real account outcomes. ESMA reported that 74–89% of retail CFD accounts lost money before introducing its limits, and capped retail leverage so clients could not lose more than they put in.

Leverage does not cause losses alone. But it shortens the distance between a normal losing run and the end of your account.
""".strip(),
    ),
    try_it="For one open or imaginary trade, compute your effective leverage, the margin needed, and the move that would hit your broker's stop-out level.",
    quiz=(
        Q(
            "With 100:1 leverage available on a $1,000 account, how much should a disciplined trader risk per trade?",
            (
                "The full $100,000 the leverage allows",
                "Whatever the broker's margin call permits",
                "Still about 1% of the account",
            ),
            2,
            "Leverage changes what you can buy, not what you should risk. The stop and your risk rule set the size.",
        ),
        Q(
            "A $4,000 account holds a $20,000 position. What is the effective leverage?",
            ("5×", "20×", "4×"),
            0,
            "$20,000 / $4,000 = 5. That is the number to watch.",
        ),
    ),
    takeaways=(
        "Leverage is a loan. Margin is your deposit.",
        "Watch effective leverage, not the maximum on offer.",
        "Size from your stop and your risk rule, not from available leverage.",
    ),
    sources=("esma-cfd-2018",),
)

_BROKER = Lesson(
    slug="markets/choosing-a-broker",
    title="Choosing a broker and avoiding scams",
    summary="How to check a broker and how to spot the most common trading scams.",
    est_minutes=7,
    key_concepts=("regulation", "segregated funds", "scam", "signal seller"),
    goal="Know how to check a broker, and recognise the common scams before they cost you money.",
    body_md="""
Picking a broker is your first risk decision. Before you think about features, you need to be confident your money is safe.

### What to check

1. **Regulation.** Look the firm up on the regulator's own public register, by company name and number. Do not rely on a logo on the broker's site.
2. **Client money.** Are client funds held in separate accounts?
3. **Protection.** Is there a compensation scheme? How much does it cover? Is **negative balance protection** offered, which means your losses stop at what you deposited?
4. **Costs.** Compare full round-trip cost on your market, including commissions and overnight fees.
5. **Execution.** Who is on the other side, and what is the execution policy?
6. **Withdrawals.** Read the terms. Test with a small withdrawal early.

### Common scams

- **Guaranteed returns.** Trading has no guaranteed returns. Anyone promising them is wrong or lying.
- **Signal groups** that show only winners, with no audited record of all trades.
- **"Account managers"** who phone you and push you to deposit more.
- **Fake platforms** where the profit on screen is invented, and withdrawals never arrive.
- **Recovery scams** that promise to get back money you lost, for a fee.
- **Pressure** to act fast or in secret.

Regulators keep warning about these. The CFTC and NASAA say off-exchange forex can be outright fraud, and that you should check a firm's registration first.
""".strip(),
    charts=(
        Chart(
            title="What 12% a month would have to mean",
            caption="Calculated: $1,000 compounding at 12% a month against 10% a year over three years. Almost nothing real produces the first line over long periods, which is why this promise is a red flag.",
            data_kind="calculated",
            kind="lines",
            y_format="usd",
            y_label="Value of $1,000",
            x_label="Months",
            x_labels=tuple(str(m) for m in range(0, 37, 3)),
            series=(
                Series(
                    "10% a year",
                    tuple(round(1000 * 1.10 ** (m / 12)) for m in range(0, 37, 3)),
                    "accentSoft",
                ),
                Series(
                    "Promised 12% a month",
                    tuple(round(1000 * 1.12**m) for m in range(0, 37, 3)),
                    "danger",
                ),
            ),
        ),
    ),
    steps=(
        "Find the broker's company name and licence number.",
        "Confirm both on the regulator's official website.",
        "Read the pages on client money and order execution.",
        "Open a small account and test a withdrawal before depositing more.",
        "If anyone pressures you, promises returns or asks for secrecy, stop.",
    ),
    example_md="""
A message offers you "12% a month, managed by a licensed professional", and a chat shows daily profit screenshots.

Check the maths: 12% a month compounds to about **290% a year**. Few real funds have managed anything like that over long periods.

Check the claim: ask for the firm's licence number, then look it up on the regulator's site. If it is not listed, or the name is a near match, walk away. Many victims only find out when they try to withdraw and get asked to pay a "tax" first.
""".strip(),
    mistakes=(
        "Trusting a logo or a certificate shown on the broker's own website.",
        "Depositing more because the on-screen account is 'making money'.",
        "Paying someone to recover money lost to a scam.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Regulators report these fraud patterns repeatedly. In one CFTC case, defendants promised to double participants' money through retail forex trading. Regulator warnings are not a claim that every offer is fraud, but the warning signs here are well documented.

If you live in the UAE, finance-influencer activity is now licensed under SCA Resolution No. 10 of 2025, according to law-firm summaries. Check the regulator's current rules before relying on any such content.
""".strip(),
    ),
    try_it="Pick any broker. Find its licence on the regulator's register. Write down the licence number, the regulator, and whether client money is held separately.",
    quiz=(
        Q(
            "How should you verify a broker is regulated?",
            (
                "By the logo on its website",
                "On the regulator's own public register",
                "By asking in a chat group",
            ),
            1,
            "A logo can be copied. The regulator's register is the authority.",
        ),
        Q(
            "Someone offers guaranteed monthly returns. What is the safest assumption?",
            ("It is a good opportunity", "It is probably a scam", "It depends on the size"),
            1,
            "No real trading account has guaranteed returns. Treat this as a red flag.",
        ),
    ),
    takeaways=(
        "Verify regulation on the regulator's own website.",
        "Guarantees, pressure and secrecy are red flags.",
        "Test a small withdrawal early.",
    ),
    sources=("cftc-forex-alert", "uae-finfluencer"),
)

CHAPTERS = (
    chapter(
        "markets",
        "who-trades",
        "Who is on the other side",
        "The people and firms you are trading with, and where your order actually goes.",
        (_WHO, _VENUES),
    ),
    chapter(
        "markets",
        "orders",
        "Orders",
        "Every order type and what really happens when you send one.",
        (_ORDER_TYPES, _UNITS, _ORDER_REF, _BOOK),
    ),
    chapter(
        "markets",
        "clock-and-costs",
        "The clock and the bill",
        "When markets are alive, what trading costs, and how leverage really works.",
        (_CLOCK, _COSTS, _LEVERAGE, _BROKER),
    ),
)
