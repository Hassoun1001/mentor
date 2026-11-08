"""Stage 5, order-flow additions: Market Profile, CVD and footprints, tape and depth."""

from __future__ import annotations

from mentor.domain.curriculum.book._kit import (
    Bar,
    Chart,
    Evidence,
    Lesson,
    Mark,
    Q,
    Series,
    Verdict,
    candle_chart,
)
from mentor.domain.curriculum.charts import Tone, bar_delta, cumulative, path

_TPOS: tuple[tuple[int, int], ...] = (
    (109, 1),
    (108, 2),
    (107, 3),
    (106, 5),
    (105, 7),
    (104, 9),
    (103, 6),
    (102, 4),
    (101, 2),
    (100, 1),
)
_VALUE_AREA = range(102, 107)


def _tpo_tone(price: int) -> Tone:
    if price == 104:
        return "warn"
    return "accent" if price in _VALUE_AREA else "muted"


MARKET_PROFILE = Lesson(
    slug="flow/market-profile-and-auction-theory",
    title="Market Profile and Auction Market Theory",
    summary="Markets as auctions, and a chart that shows where they spent their time.",
    est_minutes=9,
    key_concepts=("Market Profile", "TPO", "value area", "point of control", "auction", "balance"),
    goal="Read a Market Profile, work out a value area, and explain balance and imbalance.",
    body_md="""
### Auction Market Theory

**Auction Market Theory** says a market behaves like an auction. Price moves up to find sellers and down to find buyers. It is looking for a level where both sides are willing to trade.

- **Balance:** price moves sideways, and both sides are satisfied.
- **Imbalance:** one side is in control, so price moves away to find a new area.

### Market Profile

Peter Steidlmayer developed **Market Profile** at the Chicago Board of Trade in the 1980s.

It gives each 30-minute period a letter. Every price traded during that period receives that letter. The letters stack up sideways at each price, so you can see where the market spent the most time.

One letter at one price is called a **TPO**, which stands for Time Price Opportunity.

### Three key parts

- **Point of Control (POC):** the price with the most TPOs.
- **Value Area:** the band holding about **70%** of the TPOs. The number is a convention.
- **Tails:** thin areas at the edges where price was rejected quickly.

### What it does not do

The profile is a **description** of what happened. It is not a forecast. Rules such as "price entering value will travel through it" are widely repeated, but we have not found any good test of them.
""".strip(),
    charts=(
        Chart(
            title="A one-day profile",
            caption="Illustrative counts. Each bar is the number of 30-minute letters at that price. The POC has its own colour, the value area is the second colour, and the rest are grey.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            bars=tuple(Bar(str(price), count, _tpo_tone(price)) for price, count in _TPOS),
        ),
    ),
    steps=(
        "Count the TPOs at each price and find the total.",
        "Mark the price with the most TPOs. That is the POC.",
        "Add neighbouring rows, largest first, until you have about 70% of the total.",
        "Note the top and bottom of that band.",
        "Ask whether today's market is in balance or moving away from value.",
    ),
    example_md="""
A day has **40 TPOs** in total, using the counts in the chart. 70% of 40 is **28**.

Start at the POC, **104**, with 9. Then keep adding the larger neighbouring row:

| Add | TPOs added | Running total |
|---|---|---|
| 104 (POC) | 9 | 9 |
| 105 | 7 | 16 |
| 103 | 6 | 22 |
| 106 | 5 | 27 |
| 102 | 4 | 31 |

The total first passes 28 at row 102, so the value area runs from **102 to 106**, with **31 TPOs**, which is 78% of the day.

If tomorrow opens at 108, it is outside yesterday's value. That is a fact. What happens next is not.
""".strip(),
    mistakes=(
        "Treating the 70% as something a market must obey.",
        "Using it in thin or unusual sessions, where the profile has little meaning.",
        "Accepting rules taught as facts with no test behind them.",
    ),
    evidence=Evidence(
        Verdict.UNTESTED,
        """
Market Profile and Auction Market Theory give a useful way to describe a day. We found **no reliable, independent success rate** for value-area rules. Most claims come from educators and vendors.

The 70% comes from the idea of a normal distribution, where about 68% falls within one standard deviation. It is a convention.
""".strip(),
    ),
    try_it="Take a day of 30-minute candles. Count how many periods touched each price level, and work out the POC and the value area by hand.",
    quiz=(
        Q(
            "What is the Point of Control?",
            ("The price with the most time or activity", "The day's highest price", "The opening price"),
            0,
            "It is the single most active price in the profile.",
        ),
        Q(
            "What does Auction Market Theory say price is doing?",
            (
                "Following a fixed cycle",
                "Searching for a level where buyers and sellers will trade",
                "Moving at random only",
            ),
            1,
            "Price moves to find both sides of the auction.",
        ),
    ),
    takeaways=(
        "Markets can be viewed as auctions seeking balance.",
        "The profile shows where time was spent.",
        "It describes the past and its rules are unproven.",
    ),
    sources=("steidlmayer",),
)

_cvd_path = path(
    [(0, 100), (10, 103), (14, 101.8), (24, 104.6), (30, 104.2), (38, 104.9), (46, 102.5)],
    seed=101,
    noise=0.2,
)
# The last push to a new high is given weak delta on purpose, so the chart shows a
# real divergence. The caption says these delta numbers are made up.
_delta = tuple(
    round(value * (0.25 if 30 < i <= 38 else 1.0), 1)
    for i, value in enumerate(bar_delta(_cvd_path))
)

CVD_FOOTPRINT = Lesson(
    slug="flow/cvd-and-footprint",
    title="Delta, CVD and footprint charts",
    summary="Counting who was aggressive, and how far you can trust that count.",
    est_minutes=9,
    key_concepts=("delta", "cumulative volume delta", "CVD", "footprint", "aggressor", "absorption"),
    goal="Read delta and a footprint table, and know how the data can mislead you.",
    body_md="""
Every trade has a buyer and a seller, so "more buyers than sellers" makes no sense. What can differ is **who was in a hurry**.

- A **market buy** hits the ask price. It is an aggressive buy.
- A **market sell** hits the bid price. It is an aggressive sell.

### The three tools

- **Delta** is aggressive buying volume minus aggressive selling volume in one period.
- **Cumulative Volume Delta (CVD)** is a running total of delta.
- A **footprint chart** shows that split at each price inside a candle.

### What people look for

- **Agreement:** price rises and CVD rises.
- **Divergence:** price makes a new high and CVD does not.
- **Absorption:** heavy aggressive selling, but price does not fall. Someone is taking the other side.

### Why you should be careful

**Your data may be guessed.** Many feeds do not record who was aggressive. Software estimates it from whether a price ticked up or down, and that is sometimes wrong.

**Spot forex has no central record.** Any delta from a retail forex broker covers only that broker's flow.

**Hidden orders exist.** A large resting order can hide much of its size, which changes how the numbers should be read.
""".strip(),
    charts=(
        candle_chart(
            _cvd_path,
            title="A rough picture of delta and CVD",
            caption="Illustrative prices, volume and delta: the delta numbers are made up to show the idea. Real delta needs a record of every trade. On the last push price makes a new high, but CVD stays below its earlier peak.",
            series=(
                Series("Delta", tuple(_delta), "muted", "bars", "lower"),
                Series("CVD", cumulative(_delta), "accent", "line", "lower"),
            ),
            marks=(Mark(38, 104.9, "New high, CVD lower", "warn", "down"),),
            lower_title="Delta and cumulative delta",
        ),
    ),
    steps=(
        "Check that your data comes from a central market and records trade direction.",
        "Read delta at each candle or price level.",
        "Compare the running CVD with price.",
        "Mark places of absorption and record what followed.",
        "Count the failures too, before you trust a pattern.",
    ),
    example_md="""
One 5-minute candle in an index future, shown as a footprint:

| Price | Sold at bid | Bought at ask | Delta |
|---|---|---|---|
| 100.50 | 20 | 45 | +25 |
| 100.25 | 60 | 120 | +60 |
| 100.00 | 90 | 85 | −5 |
| 99.75 | 110 | 40 | −70 |

The total delta is 25 + 60 − 5 − 70 = **+10**. The whole candle was nearly balanced. But the split inside it tells a clearer story: aggressive buying at the top and aggressive selling at the bottom.

Now suppose the next candles show CVD falling while price holds flat. That might be absorption. It might also be noise. One example tells you very little.
""".strip(),
    mistakes=(
        "Using a retail forex 'delta' as if it were the whole market.",
        "Reading one divergence as a signal.",
        "Paying for a tool before you know how it labels trades.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
**Research supports the basic idea.** Cont, Kukanov and Stoikov show that order flow imbalance drives very short-term price changes in US stocks. Evans and Lyons found signed dealer flow explains much of daily currency movement.

**The retail version is much less proven.** We found no strong test showing that people reading footprints by eye profit after costs. Professional firms use this information at speeds no retail trader can match.
""".strip(),
    ),
    try_it="Find a free crypto chart with CVD. Mark five divergences from the past, before looking at what came after. Then check how many led to a reversal.",
    quiz=(
        Q(
            "What does positive delta mean?",
            (
                "More aggressive buying than aggressive selling",
                "More buyers than sellers overall",
                "The price must rise",
            ),
            0,
            "Each trade has both a buyer and a seller. Delta measures which side was aggressive.",
        ),
        Q(
            "Why might your delta numbers be wrong?",
            (
                "Many feeds estimate trade direction, and forex shows only one broker",
                "Delta does not exist in markets",
                "Candle colours are wrong",
            ),
            0,
            "Check how your feed labels trades before you trust it.",
        ),
    ),
    takeaways=(
        "Delta measures aggression, not the number of buyers.",
        "CVD is a running total of delta.",
        "The research is real, but the retail use is less proven.",
    ),
    sources=("cont-ofi-2014", "evans-lyons-2002"),
)

TAPE_DOM = Lesson(
    slug="flow/tape-reading-and-dom",
    title="Tape reading and depth of market",
    summary="Watching orders and trades directly, and why speed changes everything.",
    est_minutes=8,
    key_concepts=("tape reading", "depth of market", "DOM", "time and sales", "iceberg", "spoofing"),
    goal="Read a depth ladder, work out what a large order would cost, and see the limits of doing this by eye.",
    body_md="""
### Time and sales: the tape

The **tape** is a live list of every trade: its time, price and size. In the past it was printed on paper, which is where the name comes from.

**Tape reading** means watching this stream and judging who is pressing harder.

### Depth of market: the ladder

**Depth of market**, or DOM, shows the orders waiting at each price. Bids are below the market and offers are above it.

### What they can tell you

- How much you can trade before the price moves.
- Whether big orders keep trading at one price.
- Whether the market is thin at this moment.

### What can fool you

- **Spoofing:** placing large orders with no plan to trade them, to mislead others. It is illegal in many markets, but it still happens.
- **Iceberg orders:** large orders showing only a small visible piece.
- **Vanishing orders:** many orders are cancelled in moments.

### The speed problem

In modern markets most orders come from software that reacts in millionths of a second. By the time a human eye reads the screen, the moment may be gone.

Reading depth is still useful for one thing: **understanding what your own order will cost.**
""".strip(),
    charts=(
        Chart(
            title="A depth ladder",
            caption="Illustrative sizes. Offers are above the market, and bids below. Thin levels let a large order move the price quickly.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            bars=(
                Bar("Ask 100.75", 80, "danger"),
                Bar("Ask 100.50", 60, "danger"),
                Bar("Ask 100.25", 40, "danger"),
                Bar("Bid 100.00", 55, "accent"),
                Bar("Bid 99.75", 90, "accent"),
                Bar("Bid 99.50", 120, "accent"),
            ),
        ),
    ),
    steps=(
        "Check the spread and how much is available at the best prices.",
        "Work out how many levels your order would use.",
        "Calculate the average fill.",
        "Watch whether the displayed sizes stay or vanish.",
        "If you are slower than the market, use this only to plan your own orders.",
    ),
    example_md="""
Using the ladder in the chart, you want to buy **150 contracts** at the market.

| Level | Taken | Cost |
|---|---|---|
| 100.25 | 40 | 4,010.00 |
| 100.50 | 60 | 6,030.00 |
| 100.75 | 50 | 5,037.50 |

Total cost: **15,077.50** for 150 contracts.

Average price: 15,077.50 ÷ 150 = **about 100.52**.

Compared with the best ask of 100.25, you paid about **0.27 more per contract**. This is what slippage looks like, even with no news at all.
""".strip(),
    mistakes=(
        "Believing large resting orders are real and will stay.",
        "Trying to out-react software by hand.",
        "Using a CFD platform's depth as if it were the exchange.",
    ),
    evidence=Evidence(
        Verdict.UNTESTED,
        """
Order book changes clearly affect very short-term prices, according to Cont, Kukanov and Stoikov. But we found almost no direct test of humans reading depth or tape in today's markets.

Aquilina, Budish and O'Neill found speed races are a large part of UK share trading, and a handful of firms win most of them. That is the competition any tape reader faces.
""".strip(),
    ),
    try_it="Open any exchange's depth display. Choose a size and work out your average fill if you bought at the market right now. Repeat at a quiet hour and compare.",
    quiz=(
        Q(
            "If you buy 100 contracts and only 40 are at the best ask, what happens?",
            (
                "Only 40 will fill and the rest are cancelled, always",
                "The remainder fills at higher prices",
                "All of it fills at the best ask",
            ),
            1,
            "A market order works through the levels, so the average price worsens.",
        ),
        Q(
            "What is spoofing?",
            (
                "A large order with no plan to trade, placed to mislead others",
                "A type of candlestick",
                "A broker's fee",
            ),
            0,
            "It is illegal in many markets, and it is one reason depth can mislead.",
        ),
    ),
    takeaways=(
        "The tape shows trades, and the ladder shows waiting orders.",
        "Displayed orders may vanish.",
        "The clearest use is estimating your own costs.",
    ),
    sources=("cont-ofi-2014", "aquilina-2022"),
)
