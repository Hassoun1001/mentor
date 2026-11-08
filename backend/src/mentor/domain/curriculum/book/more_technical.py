"""Stage 5, second batch: Dow Theory, more indicators, harmonics and ICT terms."""

from __future__ import annotations

from mentor.domain.curriculum.book._kit import (
    Evidence,
    HLine,
    Lesson,
    Mark,
    Q,
    Segment,
    Series,
    Verdict,
    Zone,
    candle_chart,
)
from mentor.domain.curriculum.charts import adx, anchored_vwap, donchian, mfi, obv, path, stochastic

# ---------- Dow Theory ----------

_dow_path = path(
    [(0, 100), (6, 104), (10, 102), (17, 108), (21, 105.5), (28, 111), (33, 107.8), (38, 109.8), (45, 104.5)],
    seed=61,
    noise=0.18,
)

DOW = Lesson(
    slug="ta/dow-theory",
    title="Dow Theory: where trend reading began",
    summary="The oldest ideas about trends, what they got right, and why the signals come late.",
    est_minutes=8,
    key_concepts=("Dow Theory", "primary trend", "confirmation", "higher highs", "Hamilton"),
    goal="Know the six ideas of Dow Theory, and how the theory decides that a trend has ended.",
    body_md="""
**Dow Theory** comes from the writing of Charles Dow, who started the Wall Street Journal, around the year 1900. William Hamilton and later Robert Rhea turned his notes into a set of rules. Most of today's trend vocabulary comes from this work.

### The six ideas

1. **Prices reflect the news.** What people know is already in the price.
2. **There are three trends.** A *primary* trend lasts months or years. A *secondary* move goes against it for weeks. *Minor* moves last days.
3. **A big trend has three phases.** Careful buyers come first, then the public joins, then people get too excited.
4. **Two indexes must agree.** Dow compared industrial shares with transport shares. If factories are busy, goods must also be moving.
5. **Volume should support the trend.** Volume tends to grow in the direction of the main trend.
6. **A trend continues until it clearly ends.** An uptrend makes higher highs and higher lows. It ends only when both a lower high and a lower low appear.

### Why it matters today

When someone says "higher highs and higher lows", they are using Dow Theory. It also teaches a useful habit: **assume a trend is still in place until there is clear proof that it stopped.**

### The price you pay

Waiting for proof means you are late. A Dow signal comes well after the top or the bottom.
""".strip(),
    charts=(
        candle_chart(
            _dow_path,
            title="How a Dow trend ends",
            caption="Illustrative prices. Higher highs and higher lows, then a lower high at 109.8, and then a close below the last low at 107.8 (the dashed line). The trend is called over only at that last step, far below the top.",
            hlines=(HLine(107.8, "", "warn"),),
            marks=(
                Mark(28, 111, "Top", "fg", "down"),
                Mark(38, 109.8, "Lower high", "warn", "down"),
                Mark(33, 107.8, "Last low", "warn", "up"),
                Mark(41, 107.6, "Trend over", "danger", "up"),
            ),
        ),
    ),
    steps=(
        "Open a weekly chart of a broad stock index.",
        "Mark each swing high and swing low.",
        "Name the primary trend from the pattern of swings.",
        "Open a chart of a related index and check that it agrees.",
        "Call a trend over only when there is a lower high and then a lower low, or the opposite.",
    ),
    example_md="""
An index peaks at **4,700**, falls to **4,480**, and rallies to only **4,620**. That is a lower high. Nothing has ended yet.

Then it closes at **4,450**, below the 4,480 low. A second, related index closes below its own last low in the same week. Now both agree, so a Dow reader says the primary trend has turned down.

The cost: the signal came at 4,450, which is **250 points, or about 5.3%, below the top** (250 ÷ 4,700). The theory tells you the trend changed. It does not get you out near the top.
""".strip(),
    mistakes=(
        "Using it on five-minute charts. The theory was built for long trends in broad markets.",
        "Calling a trend over after the first lower high.",
        "Forgetting that the transport index no longer means what it did in 1900, so agreement between indexes is weaker today.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
**Tested:** in 1934 Alfred Cowles studied Hamilton's editorials and said he did worse than simply holding the market. Later, Brown, Goetzmann and Kumar went back to the same editorials and adjusted for risk. They found Hamilton's calls did have useful timing value from 1902 to 1929. After 1929, the idea showed some predictive power, but trading frictions remove most of the benefit.

**Honest reading:** the core idea, that trends tend to persist, has decent modern support. The exact Dow rules are slow, and a century-old result does not tell you much about today.
""".strip(),
    ),
    try_it="On a weekly chart of any index, find the last bull market top. Mark where the first lower high and then the first lower low came. How far below the top was the signal?",
    quiz=(
        Q(
            "According to Dow Theory, when has an uptrend ended?",
            (
                "At the first red candle",
                "After a lower high and then a lower low",
                "When the news turns bad",
            ),
            1,
            "The theory waits for proof: both a lower high and a lower low.",
        ),
        Q(
            "What is the main cost of waiting for that proof?",
            (
                "The signal comes late, far from the top",
                "The signal is never right",
                "It costs a data fee",
            ),
            0,
            "Dow signals are slow on purpose, so a large part of the move has already happened.",
        ),
    ),
    takeaways=(
        "Most trend words come from Dow Theory.",
        "A trend is assumed to continue until there is clear proof that it ended.",
        "That proof comes late.",
    ),
    sources=("brown-dow-1998",),
)

# ---------- Stochastic ----------

_stoch_path = path(
    [(0, 100), (6, 103), (12, 100.2), (18, 103.1), (24, 100.4), (30, 103), (44, 112)],
    seed=67,
    noise=0.22,
)
_stoch_k, _stoch_d = stochastic(_stoch_path)

STOCHASTIC = Lesson(
    slug="ta/stochastic",
    title="The Stochastic oscillator",
    summary="Where the close sits inside the recent range, and why it fails in a strong trend.",
    est_minutes=7,
    key_concepts=("Stochastic", "%K", "%D", "oscillator", "Williams %R", "overbought"),
    goal="Calculate the Stochastic by hand, and know when it can help and when it misleads.",
    body_md="""
The **Stochastic oscillator** answers a simple question: *where is today's close compared with the recent high and low?*

- A reading near **100** means the close is near the top of the recent range.
- A reading near **0** means the close is near the bottom.

### The formula

**%K = (Close − Lowest low) ÷ (Highest high − Lowest low) × 100**

The period is usually 14 candles. **%D** is just a 3-candle average of %K, so it is smoother.

Traders commonly call a reading above **80** "overbought" and below **20** "oversold". These words sound like a promise that price will fall or rise. They are not. They only say where the close sits.

### Where it can help

In a market moving sideways, a reading near one end often means price is near the edge of the range.

### Where it misleads

In a strong trend, price keeps closing near the top. The reading can **stay above 80 for a long time** while the price keeps rising. Anyone selling because it is "overbought" gets hurt.

### Its twin

**Williams %R** is the same sum drawn upside down, from 0 to −100. Adding it to a chart with the Stochastic adds no new information.
""".strip(),
    charts=(
        candle_chart(
            _stoch_path,
            title="Useful in the range, stuck in the trend",
            caption="Illustrative prices, with a real 14-period Stochastic worked out from them. In the sideways part the line swings between the bands. In the trend at the end it stays high.",
            series=(
                Series("%K", _stoch_k, "accent", panel="lower"),
                Series("%D", _stoch_d, "warn", "dashed", panel="lower"),
            ),
            hlines=(HLine(80, "80", "muted", "lower"), HLine(20, "20", "muted", "lower")),
            zones=(Zone(100, 103.4, "Sideways", "accentSoft", 0, 30),),
            lower_title="Stochastic (14,3)",
        ),
    ),
    steps=(
        "Find the highest high and lowest low of the last 14 candles.",
        "Subtract the low from the close.",
        "Divide by the full range and multiply by 100.",
        "Decide first whether the market is in a range or a trend.",
        "Treat the reading as a description, and never as a signal by itself.",
    ),
    example_md="""
Over 14 days, the highest high on EUR/USD is **1.1000** and the lowest low is **1.0800**. The range is 0.0200.

- Close at **1.0970**: (1.0970 − 1.0800) ÷ 0.0200 × 100 = **85**. The close is near the top of the range.
- Close at **1.0880**: (1.0880 − 1.0800) ÷ 0.0200 × 100 = **40**. The close is below the middle.

If the market is in a sideways range, 85 tells you price is near the top of it. If the market is in a strong uptrend, 85 is simply normal.
""".strip(),
    mistakes=(
        "Selling just because the reading is above 80.",
        "Using Stochastic, RSI and Williams %R together and calling it three confirmations. They are nearly the same information.",
        "Changing the period until past signals look good.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
Fang, Jacobsen and Qin tested well-known technical rules on fresh data from 1987 to 2011 and found no evidence that they predicted stock markets over that period. We did not find a strong study of this one indicator alone.

A study of Dutch online-broker clients by Hoffmann and Shefrin found those using technical analysis tended to do worse, above all heavy options traders. That was one sample, and it did not test this tool directly.

Treat the Stochastic as a way to describe a range, not as a source of edge.
""".strip(),
    ),
    try_it="Calculate the 14-day Stochastic by hand for one market, using the last 14 daily highs, lows and closes. Then check your answer on a chart.",
    quiz=(
        Q(
            "A Stochastic reading of 90 tells you…",
            (
                "Price will fall soon",
                "The close is near the top of the recent range",
                "Volume is high",
            ),
            1,
            "It is only a location inside the range, not a forecast.",
        ),
        Q(
            "Why is adding Williams %R next to Stochastic not helpful?",
            (
                "Because it is the same calculation shown a different way",
                "Because it uses volume",
                "Because it only works on stocks",
            ),
            0,
            "Williams %R is simply the Stochastic drawn upside down.",
        ),
    ),
    takeaways=(
        "Stochastic shows where the close sits in the recent range.",
        "It can stay extreme for a long time in a trend.",
        "Similar oscillators do not confirm each other.",
    ),
    sources=("fang-2014", "hoffmann-shefrin-2014", "park-irwin-2007"),
)

# ---------- ADX ----------

_adx_path = path(
    [(0, 100), (8, 101.5), (15, 100), (22, 101.5), (30, 100.5), (48, 114), (56, 113), (64, 114.5)],
    seed=71,
    noise=0.2,
)
_adx_line, _plus, _minus = adx(_adx_path)

ADX = Lesson(
    slug="ta/adx",
    title="ADX: is there a trend at all?",
    summary="A number for trend strength. It says nothing about direction.",
    est_minutes=7,
    key_concepts=("ADX", "+DI", "-DI", "trend strength", "Wilder", "filter"),
    goal="Read ADX and its two direction lines, and use it only as a filter.",
    body_md="""
**ADX** stands for Average Directional Index. J. Welles Wilder published it in 1978. It tries to answer one question: **how strong is the current trend?**

ADX runs from 0 to 100.

- **Low ADX, often below 20:** weak or no trend.
- **High ADX, often above 25:** a stronger trend.

These numbers are habits, not laws.

### The two helper lines

- **+DI** measures how much of recent movement was upward.
- **−DI** measures how much was downward.

ADX is built from the gap between them, then smoothed. So **ADX rises when one side is dominant, whichever side that is.** A falling market can have a very high ADX.

### How people use it

Mostly as a **filter**. A trend-following rule might only be allowed when ADX is above a chosen level. A range-trading rule might only be allowed when ADX is low.

### The limit

ADX is averaged twice, so it is slow. When it finally climbs, the trend has already been running for a while. And a falling ADX does not mean price must reverse: it may only mean the pace of the trend is slowing.
""".strip(),
    charts=(
        candle_chart(
            _adx_path,
            title="ADX stays low in the range and climbs after the trend starts",
            caption="Illustrative prices, with a real 14-period ADX worked out from them. Notice that ADX only climbs after the trend is well under way.",
            series=(
                Series("ADX", _adx_line, "accent", panel="lower"),
                Series("+DI", _plus, "accentSoft", "dashed", panel="lower"),
                Series("−DI", _minus, "danger", "dashed", panel="lower"),
            ),
            hlines=(HLine(25, "25", "muted", "lower"),),
            marks=(Mark(30, 100.5, "Trend starts", "fg", "up"),),
            lower_title="ADX (14)",
        ),
    ),
    steps=(
        "Add ADX with its +DI and −DI lines to the chart.",
        "Read ADX for strength only.",
        "Read which DI line is on top for the direction of recent movement.",
        "Choose one threshold before you test anything.",
        "Compare your system with and without the filter on data you did not tune on.",
    ),
    example_md="""
Suppose **+DI is 28** and **−DI is 12**.

The daily number, called DX, is the gap divided by the total:

(28 − 12) ÷ (28 + 12) × 100 = **40**

ADX is a slow average of DX. If yesterday's ADX was **25**, today's is:

(25 × 13 + 40) ÷ 14 = 365 ÷ 14 = **about 26.1**

So even a large DX of 40 only moves ADX by about one point in a day. That is why ADX is late.
""".strip(),
    mistakes=(
        "Reading a high ADX as bullish. It can be high in a crash.",
        "Expecting ADX to warn you early about a new trend.",
        "Tuning the threshold until a backtest looks perfect.",
    ),
    evidence=Evidence(
        Verdict.UNTESTED,
        """
ADX is widely used, but we found few strong independent tests of it as a filter. Studies of wide groups of technical rules, reviewed by Park and Irwin, warn about data snooping and find that many results disappear after costs.

The honest position is that you should test it inside your own system, and keep it only if it clearly helps on unseen data.
""".strip(),
    ),
    try_it="Find one strong downtrend on a daily chart. Check the ADX during it. Was the reading high even though the price was falling?",
    quiz=(
        Q(
            "What does a high ADX tell you?",
            (
                "The price will go up",
                "There is a strong trend, in either direction",
                "Volume is unusually high",
            ),
            1,
            "ADX measures strength only. Direction comes from the DI lines.",
        ),
        Q(
            "Why does ADX react slowly?",
            (
                "It is smoothed more than once",
                "It uses only weekly data",
                "It is published with a delay",
            ),
            0,
            "Double smoothing makes the line calm, but late.",
        ),
    ),
    takeaways=(
        "ADX measures trend strength, not direction.",
        "It is a slow filter, not a trigger.",
        "Test whether it really improves your system.",
    ),
    sources=("wilder-1978", "park-irwin-2007"),
)

# ---------- Donchian ----------

_don_path = path(
    [(0, 100), (10, 102), (18, 100.3), (28, 102.1), (34, 101), (48, 110), (54, 108), (66, 115)],
    seed=73,
    noise=0.2,
)
_don_up, _don_low = donchian(_don_path, 20)
_breakout = next(
    i for i, u in enumerate(_don_up) if u is not None and _don_path.closes[i] > u and i > 25
)

DONCHIAN = Lesson(
    slug="ta/donchian-channels",
    title="Donchian channels: the plain breakout rule",
    summary="The highest high and lowest low of the last N candles, and why funds still use it.",
    est_minutes=8,
    key_concepts=("Donchian", "channel", "breakout", "Turtle", "Keltner", "trend following"),
    goal="Build a Donchian channel, and understand what a written breakout rule can and cannot do.",
    body_md="""
A **Donchian channel** has only two lines:

- The **upper line** is the highest high of the last N candles.
- The **lower line** is the lowest low of the last N candles.

The usual N is 20. It is named after Richard Donchian, a pioneer of trend following.

### The basic rule

- A close above the upper line means the market has reached a new high for that period.
- A close below the lower line means it has reached a new low.

That is the heart of many trend systems. The famous "Turtle" traders of the 1980s used rules of this type, along with strict position sizing.

### Why people like it

It is simple and leaves nothing to judgement. Two people will always draw the same lines, so it can be tested honestly.

### What it costs

Most breakouts fail. A breakout system often wins well under half of the time. It only works if the few long trends pay for all the small losses. That is hard to live with.

### Related channels

**Keltner channels** use an average plus or minus some ATR. **Bollinger Bands** use standard deviation. Donchian uses only actual highs and lows.
""".strip(),
    charts=(
        candle_chart(
            _don_path,
            title="A 20-period Donchian channel",
            caption="Illustrative prices, with a real channel worked out from them. Each line uses only the 20 candles before the current one, so it never uses the future.",
            series=(
                Series("20-bar high", _don_up, "accent"),
                Series("20-bar low", _don_low, "danger"),
            ),
            marks=(Mark(_breakout, _don_path.closes[_breakout], "Breakout", "fg", "up"),),
        ),
    ),
    steps=(
        "Pick N, such as 20, and do not change it to suit one chart.",
        "Draw the highest high and lowest low of the last N candles, leaving out the current one.",
        "Write the exact rule for a breakout and for leaving a trade.",
        "Size each trade from an ATR stop.",
        "Test it across many markets, with costs included.",
    ),
    example_md="""
Gold's 20-day high is **$2,050** and its 20-day low is **$1,960**. Today it closes at **$2,052**, a new 20-day high.

A trader following such a rule wants the risk limited to **1% of a $10,000 account, or $100**.

ATR is $30, so a stop 2 × ATR away is **$60** from the entry.

Position size = $100 ÷ $60 = **about 1.67 ounces**.

In this example, if the trade loses at the stop, the loss is about $100. If gold trends a long way, the gain can be several times that amount. Most of the time it will not.
""".strip(),
    mistakes=(
        "Trying this in just one market. The evidence comes from many markets at once.",
        "Giving up after a run of small losses, which is the normal cost of the rule.",
        "Including the current candle in the channel, which makes backtests falsely good.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
**Tested:** Szakmary, Shen and Sharma studied channel and moving-average rules on 28 commodity futures markets over 48 years. The rules had positive average returns after costs in most markets.

**The limits:** a later study of US stocks by Szakmary and Lancaster found that such profits vanished after 2007. The result also holds for a broad portfolio of markets. A single market can lose for years.

Trend evidence is one of the stronger results in technical trading, but it is not a promise.
""".strip(),
    ),
    try_it="On a daily chart, count the last ten 20-day breakouts. How many kept going for more than two ATRs? How many reversed?",
    quiz=(
        Q(
            "What is the upper Donchian line?",
            ("A moving average", "The highest high of the last N candles", "The average price"),
            1,
            "It is simply the highest high, with no averaging.",
        ),
        Q(
            "Why does a breakout system need a few big winners?",
            (
                "Because most breakouts fail and create small losses",
                "Because brokers require it",
                "Because it wins nearly every trade",
            ),
            0,
            "Many small losses must be paid for by rare large gains.",
        ),
    ),
    takeaways=(
        "Donchian channels are simple and testable.",
        "Trend rules have decent evidence across many markets.",
        "Expect many small losses along the way.",
    ),
    sources=("szakmary-2010", "moskowitz-2012"),
)

# ---------- OBV and MFI ----------

_obv_path = path(
    [(0, 100), (10, 104), (15, 102), (25, 106), (30, 104.5), (40, 108)], seed=79, noise=0.24
)

OBV_MFI = Lesson(
    slug="ta/obv-and-mfi",
    title="OBV and MFI: indicators that use volume",
    summary="Two ways to bring volume into a chart, and where they do not work.",
    est_minutes=7,
    key_concepts=("OBV", "MFI", "volume", "typical price", "money flow"),
    goal="Calculate OBV and MFI, and know that they need real volume to mean anything.",
    body_md="""
Most indicators use price only. These two also use **volume**, the amount that was traded.

### On-Balance Volume (OBV)

Joseph Granville made this popular in the 1960s. It is a running total.

- If today's close is **higher**, add today's volume.
- If today's close is **lower**, subtract today's volume.
- If the close is **unchanged**, do nothing.

The exact value means nothing. Only the direction matters. People look to see whether OBV is rising with the price.

### Money Flow Index (MFI)

MFI is like RSI, but it includes volume. It runs from 0 to 100.

1. Find the **typical price**: (high + low + close) ÷ 3.
2. **Money flow** = typical price × volume.
3. Add up the money flow on days the typical price rose, and on days it fell.
4. **MFI = 100 − 100 ÷ (1 + rise total ÷ fall total)**

### The big warning for forex

Spot forex has no central exchange. The "volume" on most forex charts is only how many price changes your broker saw, called **tick volume**. It is not how much was traded. OBV and MFI are far more meaningful on shares and futures.
""".strip(),
    charts=(
        candle_chart(
            _obv_path,
            title="OBV below a rising market",
            caption="Illustrative prices and volume, with a real OBV worked out from them. OBV rises when more volume comes on up days.",
            series=(Series("OBV", obv(_obv_path), "accent", panel="lower"),),
            lower_title="On-Balance Volume",
        ),
        candle_chart(
            _obv_path,
            title="MFI on the same candles",
            caption="Illustrative prices and volume, with a real 14-period MFI worked out from them.",
            place="example",
            series=(Series("MFI", mfi(_obv_path), "accent", panel="lower"),),
            hlines=(HLine(80, "80", "muted", "lower"), HLine(20, "20", "muted", "lower")),
            lower_title="Money Flow Index (14)",
        ),
    ),
    steps=(
        "Check that the market has real volume.",
        "Add OBV and look only at its direction.",
        "Compare OBV with price over the same swings.",
        "Add MFI if you want an RSI-style view that includes volume.",
        "Treat disagreements as a question to investigate, not as a signal.",
    ),
    example_md="""
**OBV over five days**, starting at 0:

| Day | Close vs yesterday | Volume | OBV |
|---|---|---|---|
| 2 | Up | 1,000 | 1,000 |
| 3 | Down | 600 | 400 |
| 4 | Up | 1,200 | 1,600 |
| 5 | Flat | 900 | 1,600 |
| 6 | Down | 700 | 900 |

**MFI:** suppose money flow on up days adds to **$600,000** and on down days to **$200,000** over 14 days.

The ratio is 3. MFI = 100 − 100 ÷ (1 + 3) = 100 − 25 = **75**.
""".strip(),
    mistakes=(
        "Using either indicator on spot forex tick volume and trusting it like real volume.",
        "Reading the exact OBV number as meaningful. Only the direction matters.",
        "Treating a small divergence as a turn in the market.",
    ),
    evidence=Evidence(
        Verdict.UNTESTED,
        """
OBV and MFI appear in large studies of thousands of technical rules, but we could not find a clear result for either one alone. Fang, Jacobsen and Qin found no evidence that well-known technical rules predicted stock markets on fresh data from 1987 to 2011.

We do not know of good evidence that either tool gives a reliable edge. Test before you believe.
""".strip(),
    ),
    try_it="On a stock, compare OBV with the price over the last six months. Find one place where they disagreed, and see what happened next. Then find another example, because one is never enough.",
    quiz=(
        Q(
            "If today's close is lower, what happens to OBV?",
            ("Today's volume is added", "Today's volume is subtracted", "OBV is reset to zero"),
            1,
            "Down closes subtract the day's volume.",
        ),
        Q(
            "Why are these tools weaker on spot forex?",
            (
                "Forex charts usually show tick volume, not true traded volume",
                "Forex has no prices",
                "They only work on crypto",
            ),
            0,
            "There is no central forex exchange, so true total volume is not visible to you.",
        ),
    ),
    takeaways=(
        "OBV is a running total of signed volume.",
        "MFI is an RSI that includes volume.",
        "Both need real volume to be meaningful.",
    ),
    sources=("fang-2014", "park-irwin-2007"),
)

# ---------- Harmonic patterns ----------

_harm_path = path(
    [(0, 100), (10, 110), (18, 103.82), (25, 107.64), (35, 102.14), (45, 107)],
    seed=83,
    noise=0.1,
)

HARMONIC = Lesson(
    slug="ta/harmonic-patterns",
    title="Harmonic patterns: Gartley and friends",
    summary="Shapes defined by Fibonacci ratios, and the flexibility that makes them hard to trust.",
    est_minutes=8,
    key_concepts=("harmonic", "Gartley", "XABCD", "Fibonacci ratios", "Bat", "Butterfly"),
    goal="Identify a Gartley shape by its ratios, and see why many small choices make it hard to test.",
    body_md="""
A **harmonic pattern** is a five-point shape, labelled **X, A, B, C and D**. The swings between the points must match set ratios. Names include Gartley, Bat, Butterfly and Crab.

### The Gartley ratios

These are the usual published ratios for a bullish Gartley:

- **AB** pulls back about **61.8%** of XA.
- **BC** pulls back **38.2% to 88.6%** of AB.
- **CD** extends **127.2% to 161.8%** of BC.
- **D** sits about **78.6%** of the way back along XA.

Followers treat point D as a place where a reversal may start. They put the stop just beyond X, where the shape would be broken.

### What is appealing

Rules are precise, and there is a clear place for risk. That is more than most chart shapes offer.

### The honest problem

Look at how many choices there are:

- Which swing counts as X?
- How much tolerance does each ratio get? Is 58% close enough to 61.8%?
- Which timeframe?
- Which of the many pattern names fits?

Each choice is another chance to find a pattern after the fact. And the ratios come from Fibonacci, which has tested poorly.
""".strip(),
    charts=(
        candle_chart(
            _harm_path,
            title="A bullish Gartley drawn on made-up prices",
            caption="Illustrative prices. X = 100, A = 110, B = 103.82, C = 107.64, D = 102.14. The prices were built to fit the ratios exactly. Real charts almost never fit this cleanly.",
            segments=(
                Segment(0, 100, 10, 110, "", "accent"),
                Segment(10, 110, 18, 103.82, "", "muted"),
                Segment(18, 103.82, 25, 107.64, "", "muted"),
                Segment(25, 107.64, 35, 102.14, "", "warn"),
            ),
            marks=(
                Mark(0, 100, "X", "fg", "up"),
                Mark(10, 110, "A", "fg", "down"),
                Mark(18, 103.82, "B", "fg", "up"),
                Mark(25, 107.64, "C", "fg", "down"),
                Mark(35, 102.14, "D", "accentSoft", "up"),
            ),
        ),
    ),
    steps=(
        "Find a clear swing and label it X to A.",
        "Measure each later swing and write down the ratio.",
        "Check every ratio against a written tolerance you chose beforehand.",
        "Mark point D and the price where the shape fails.",
        "Log every pattern you find, not only the ones that worked.",
    ),
    example_md="""
Take X at **100** and A at **110**, so XA = 10.

- **B** = 110 − (10 × 0.618) = **103.82**. AB = 6.18.
- **C** retraces 61.8% of AB: 103.82 + 3.82 = **107.64**. BC = 3.82.
- **D** at 78.6% of XA: 110 − 7.86 = **102.14**. CD = 5.50, which is 5.50 ÷ 3.82 = **1.44 × BC**. That fits the range.

In this example the invalidation price is X at **100**, which is **2.14** below D.

A common target is 61.8% of AD: 102.14 + (7.86 × 0.618) = **107.00**, which is **4.86** above D. That would be about **2.3 times the risk**, but only if price gets there, and these numbers say nothing about how often it does.
""".strip(),
    mistakes=(
        "Loosening the ratio tolerance until a pattern appears.",
        "Remembering only the examples that worked.",
        "Trusting a scanner without checking how it picks swings.",
    ),
    evidence=Evidence(
        Verdict.UNTESTED,
        """
We found no strong independent test of harmonic patterns after costs. Most claims come from authors or tool sellers.

The ratios themselves are the weak point. Batchelor and Ramyar tested Fibonacci-type ratios in Dow trends and found no more of them than chance would produce.

Treat harmonic patterns as an untested idea with a clear risk point, and nothing more.
""".strip(),
    ),
    try_it="Write down your ratios and tolerances before you look at a chart. Then go through three months of data and record every pattern. Do not skip the failed ones.",
    quiz=(
        Q(
            "In a bullish Gartley, where is the shape broken?",
            ("Beyond point X", "At point C", "At the 50% line"),
            0,
            "If price passes X, the shape no longer fits.",
        ),
        Q(
            "What makes harmonics hard to test fairly?",
            (
                "They have too few rules",
                "Many choices about swings and tolerance allow patterns to be found after the fact",
                "They cannot be drawn on a chart",
            ),
            1,
            "Each choice is another chance to fool yourself.",
        ),
    ),
    takeaways=(
        "Harmonics are ratio-based five-point shapes.",
        "They give a clear point of invalidation.",
        "Their edge is unproven.",
    ),
    sources=("batchelor-2006",),
)

# ---------- ICT terms ----------

_ict_path = path(
    [(0, 105.5), (8, 102), (14, 104.2), (19, 101.8), (24, 105.5), (32, 103), (42, 108)],
    seed=89,
    noise=0.12,
)

ICT = Lesson(
    slug="smart-money/ict-terms",
    title="ICT words in plain English",
    summary="Market structure shift, displacement, kill zones and OTE, and what they really are.",
    est_minutes=8,
    key_concepts=("ICT", "market structure shift", "displacement", "kill zone", "OTE", "judas swing"),
    goal="Translate common ICT words into plain chart language, and know that they remain untested.",
    body_md="""
**ICT** stands for Inner Circle Trader, an online teacher. His words spread widely through Smart Money teaching. Much of it renames older ideas.

### A translation table

| ICT word | What it plainly means |
|---|---|
| **Market Structure Shift (MSS)** | A strong break against the recent swings. Close to a "Change of Character". |
| **Displacement** | A big, fast candle in one direction. |
| **Fair Value Gap** | A gap between the wicks of candles one and three. |
| **Liquidity** | Places where stops probably sit, such as just past old highs or lows. |
| **Kill zone** | A busy time of day, such as the London open or New York open. |
| **Judas swing** | An early false move in the session that reverses. |
| **OTE (Optimal Trade Entry)** | A pullback zone between 62% and 79% of a swing. |
| **Premium / discount** | The top half and bottom half of a range. |

### What these words get right

- Markets really are busiest at certain hours.
- Stops really do cluster beyond obvious levels.
- Fast moves do leave gaps.

### What goes too far

The method says market makers plan each move to trap you. A retail chart cannot show that. And the "Optimal" in OTE is a name, not a proven result.

Be most careful about teaching that rests on a few perfect screenshots.
""".strip(),
    charts=(
        candle_chart(
            _ict_path,
            title="A sweep, a shift, and a pullback into the 'OTE' zone",
            caption="Illustrative prices. Price dips just below an old low, then breaks above the last swing high. Followers would then watch for a pullback between 62% and 79% of that swing.",
            hlines=(HLine(102, "Old low", "warn"),),
            zones=(Zone(102.58, 103.21, "OTE zone", "accentSoft", 24),),
            marks=(
                Mark(19, 101.8, "Sweep", "danger", "up"),
                Mark(22, 104.6, "Shift", "accent", "down"),
            ),
        ),
    ),
    steps=(
        "Translate each word into a plain chart fact.",
        "Write a rule with exact numbers, such as how large displacement must be.",
        "Test the rule on many past cases, with costs.",
        "Compare it with a simple rule, such as a basic pullback entry.",
        "Keep the part that adds something, and drop the story.",
    ),
    example_md="""
Price falls to **101.8**, just under an old low at **102**. Then it rallies to **105.5** and breaks the last swing high at **104.2**. A follower calls this a market structure shift.

The OTE zone is 62% to 79% of the swing from 101.8 to 105.5. The swing is 3.7.

- 62% back: 105.5 − (3.7 × 0.62) = **103.21**
- 79% back: 105.5 − (3.7 × 0.79) = **102.58**

So the zone is **102.58 to 103.21**. This arithmetic is simple. Whether this zone behaves differently from any other pullback zone is what nobody has shown.
""".strip(),
    mistakes=(
        "Treating a new name as a new discovery.",
        "Believing that a retail chart shows what banks are doing.",
        "Copying screenshots without counting failed cases.",
    ),
    evidence=Evidence(
        Verdict.UNTESTED,
        """
We found no audited track record and no strong independent test of ICT models.

Some of the pieces do have support. Osler found that stop orders cluster just beyond round numbers in currency markets. Busy session hours are well known too. That does not show that the full method works.
""".strip(),
    ),
    try_it="Take one ICT idea and write it as a rule with exact numbers. If you cannot do that, you cannot test it.",
    quiz=(
        Q(
            "What is a 'kill zone' in plain language?",
            ("A busy time of the trading day", "A stop-loss level", "A candle pattern"),
            0,
            "It is a name for times like the London or New York open.",
        ),
        Q(
            "Which statement is honest?",
            (
                "ICT has been proven by independent tests",
                "Some pieces, such as stop clusters, have support, but the full method is untested",
                "Retail charts show bank orders",
            ),
            1,
            "Some ingredients are real. The full recipe has not been tested.",
        ),
    ),
    takeaways=(
        "Most ICT terms rename older ideas.",
        "Some pieces describe real behaviour.",
        "The full method has no independent proof.",
    ),
    sources=("osler-2003",),
)

# ---------- Anchored VWAP ----------

_av_path = path(
    [(0, 110), (8, 104), (14, 100), (24, 106), (30, 103.5), (40, 109)], seed=97, noise=0.2
)

ANCHORED_VWAP = Lesson(
    slug="ta/anchored-vwap",
    title="Anchored VWAP",
    summary="The average price paid since an event you choose.",
    est_minutes=6,
    key_concepts=("anchored VWAP", "VWAP", "average cost", "event", "anchor"),
    goal="Calculate an anchored VWAP, and pick an anchor for a reason you can state in advance.",
    body_md="""
Ordinary **VWAP** is the average price paid today, weighted by volume. It resets each day.

An **anchored VWAP** works the same way, but it starts at a moment you choose:

- a company's earnings day
- a major low or high
- a big news event

### What it tells you

It shows the **average price paid by everyone who traded since that moment**. If price is above the line, the average buyer since then is in profit. If price is below it, the average buyer is losing.

Some traders think those average buyers may act when price comes back to their cost. That is a story and not a law.

### The rule that protects you

**Choose the anchor for a reason before you see what happens next.** If you keep moving the start point until the line touches a turning point, you have drawn a line that fits by construction. It then means nothing.

### Where it works poorly

In spot forex, true volume is not available, so the weighting is rough.
""".strip(),
    charts=(
        candle_chart(
            _av_path,
            title="Two anchors, two different average costs",
            caption="Illustrative prices and volume, with real anchored VWAPs worked out from them. One line starts at the low and one at the start of the fall. The anchor changes the answer.",
            series=(
                Series("Anchored at the low", anchored_vwap(_av_path, 14), "accent"),
                Series("Anchored at the start", anchored_vwap(_av_path, 0), "warn"),
            ),
            marks=(Mark(14, 100, "Anchor", "fg", "up"),),
        ),
    ),
    steps=(
        "Choose an event that you can explain.",
        "Start adding price × volume from that candle.",
        "Divide by the total volume since that candle.",
        "Compare the current price with the line.",
        "Write down the anchor rule, and use it the same way every time.",
    ),
    example_md="""
Three candles after an earnings report:

| Candle | Typical price | Volume | Price × volume |
|---|---|---|---|
| 1 | 100 | 1,000 | 100,000 |
| 2 | 104 | 3,000 | 312,000 |
| 3 | 108 | 1,000 | 108,000 |

Total value: 520,000. Total volume: 5,000.

Anchored VWAP = 520,000 ÷ 5,000 = **104**.

A simple average of the three prices is also 104, because the busiest candle was exactly in the middle. If candle 3 had the most volume, the VWAP would be higher.
""".strip(),
    mistakes=(
        "Moving the anchor until it fits the chart.",
        "Treating the line as a wall that price must respect.",
        "Using it on forex tick volume and trusting the exact number.",
    ),
    evidence=Evidence(
        Verdict.UNTESTED,
        """
The sum is plain arithmetic, and the idea of average cost is useful for thinking about who is in profit. We found no strong independent test of anchored VWAP as a trading rule.

The risk of picking anchors after the fact is high, so any informal result is doubtful.
""".strip(),
    ),
    try_it="Pick the last earnings date of one share. Calculate where the anchored VWAP is now. Is the price above or below the average buyer's cost?",
    quiz=(
        Q(
            "What does anchored VWAP show?",
            (
                "The average price paid since a chosen moment",
                "Next week's price",
                "How many stops are nearby",
            ),
            0,
            "It is an average cost since your anchor.",
        ),
        Q(
            "Why must the anchor be chosen for a stated reason?",
            (
                "Because moving it until it fits makes the line meaningless",
                "Because the platform requires it",
                "Because volume is always wrong",
            ),
            0,
            "Fitting an anchor after the fact guarantees a good-looking chart that proves nothing.",
        ),
    ),
    takeaways=(
        "Anchored VWAP is an average cost since an event.",
        "Pick the anchor by rule, in advance.",
        "It is useful for context, not proven as a signal.",
    ),
)
