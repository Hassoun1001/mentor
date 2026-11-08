"""Stage 5 — Technical analysis, each tool tested honestly."""

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
    Segment,
    Series,
    Verdict,
    Zone,
    candle_chart,
    chapter,
)
from mentor.domain.curriculum.charts import atr, bollinger, macd, path, random_walk, rsi, sma, vwap

# ---------- levels and lines ----------

_sr = path(
    [(0, 100), (6, 105), (11, 100.8), (17, 105.2), (23, 101), (29, 105.1), (34, 108.5)],
    seed=31,
    noise=0.2,
)

_SUPPORT = Lesson(
    slug="reading-charts/support-resistance",
    title="Support and resistance as memory, not magic",
    summary="Why some prices matter, and how to treat them as zones.",
    est_minutes=7,
    key_concepts=("support", "resistance", "level", "self-fulfilling", "stop hunt"),
    figures=(Figure("sr-zones", "Levels are zones where lots of orders cluster."),),
    goal="Draw support and resistance as zones, and use them for placing risk.",
    body_md="""
**Support** is a price area where falling prices have often stopped. **Resistance** is a price area where rising prices have often stalled. They are not physical laws.

They can matter for a very human reason: people remember prices. Traders who bought at a level may want to get out at breakeven. Stops cluster just beyond levels that everyone can see. Orders pile up there. So levels work partly because **people act on them**.

### How to use them

- Mark **major** levels only: weekly highs and lows, and previous swing extremes.
- Treat them as **zones**, not lines. Price respects areas, not exact numbers.
- Expect brief moves through the level. A small move past a level is often how stops get hit before price reverses. Stops placed with room, using ATR (a measure of how far a market normally moves), survive better than very tight ones.

### Once broken

Old resistance can become new support, and old support can become new resistance. That is called a **role reversal**. It is a common pattern and is also not reliable on its own.
""".strip(),
    charts=(
        candle_chart(
            _sr,
            title="A level that held several times, then broke",
            caption="Illustrative prices. The area around 105 acted as a ceiling three times before price pushed through. It was a zone, not a line.",
            zones=(Zone(104.6, 105.6, "Resistance zone", "danger"),),
            marks=(Mark(34, 108.5, "Break", "accentSoft"),),
        ),
    ),
    steps=(
        "Zoom out to the weekly or daily chart.",
        "Mark the 3 to 5 most obvious highs and lows.",
        "Turn each into a zone, about the width of a normal day's wicks.",
        "Plan trades using these zones for stops and targets.",
        "Remove old levels when they stop being relevant.",
    ),
    example_md="""
EUR/USD has reversed three times between **1.0950 and 1.0965**. You treat that band as resistance.

- If you want to short near it, your stop goes **above 1.0965**, not exactly at it, for example at 1.0985.
- If it breaks and you want to buy a pullback to 1.0960, your stop goes below the zone at 1.0935.

Whatever the idea, the level gave you a place to measure risk. That is the most reliable use of a level.
""".strip(),
    mistakes=(
        "Drawing dozens of lines until something is always 'near a level'.",
        "Placing a stop exactly on the line, where everyone else's is.",
        "Assuming a level must hold because it held before.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
**Tested:** Brock, Lakonishok and LeBaron found trading-range-break rules on the Dow carried information in very long data. Later work (Sullivan et al., Bajgrowicz and Scaillet) found many such rules disappear once you adjust for data snooping and costs.

**Popular belief:** that a level "should" hold because it did before. In reality levels fail often. They are very useful for *placing risk*, less useful as predictions.

Practical gain: a level gives you somewhere sensible to put your stop.
""".strip(),
    ),
    try_it="Mark five levels on a weekly chart with zones instead of lines. Check them next month. Which ones mattered?",
    quiz=(
        Q(
            "What is the best way to think of support and resistance?",
            (
                "Exact lines that hold",
                "Zones where orders tend to cluster",
                "Guaranteed turning points",
            ),
            1,
            "They are zones. They fail often and are best used for risk placement.",
        ),
        Q(
            "Where is a sensible stop, if you buy near a support zone?",
            (
                "Exactly at the support line",
                "Beyond the zone, with room for normal movement",
                "No stop is needed at support",
            ),
            1,
            "Beyond the zone, sized for normal movement. Exact lines get hit often.",
        ),
    ),
    takeaways=(
        "Levels are zones, not lines.",
        "They work partly because people react to them.",
        "Use them to place risk.",
    ),
    sources=("brock-1992", "stw-1999"),
)

_trend = path(
    [(0, 100), (8, 103), (12, 101.2), (20, 105), (24, 103.2), (32, 107), (36, 105.2), (44, 109)],
    seed=37,
    noise=0.2,
)

_TRENDLINES = Lesson(
    slug="ta/trendlines-and-channels",
    title="Trendlines and channels",
    summary="Lines that describe a trend, and why they break so often.",
    est_minutes=6,
    key_concepts=("trendline", "channel", "touch points", "break"),
    goal="Draw trendlines and channels by rule, and know how much weight to give them.",
    body_md="""
A **trendline** is a straight line connecting swing lows in an uptrend, or swing highs in a downtrend. A **channel** adds a parallel line on the other side.

### Drawing them properly

- Use **at least three** touch points. Two points always make a line, so two touches prove nothing.
- Draw from the highest or lowest point of a candle consistently. Wicks or bodies, but pick one and stick to it.
- Use one clear timeframe.

A line drawn by hand is **subjective**. Two traders will often draw different lines on the same chart. So do not depend on a precise line break to make decisions.

### How people use them

- Buy near the lower channel line in an uptrend with a stop just beyond it.
- Treat a clear break of the line as a warning, not a reversal signal.
- Use the line only to help you locate where a pullback might end.
""".strip(),
    charts=(
        candle_chart(
            _trend,
            title="A rising channel",
            caption="Illustrative prices. The lower line joins the swing lows, and a parallel line marks the upper side. Notice how much the line placement depends on which wicks you choose.",
            segments=(
                Segment(0, 100, 44, 106.8, "Lower line", "accent"),
                Segment(0, 103.4, 44, 110.2, "Upper line", "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Find at least three swing lows (uptrend) or swing highs (downtrend).",
        "Connect them with one straight line.",
        "Add a parallel line on the other side to make a channel if you like.",
        "Plan entries at the line and stops beyond it.",
        "When a line breaks, re-check your plan. It may be a warning, nothing more.",
    ),
    example_md="""
EUR/USD has lows at **1.0700, 1.0760 and 1.0820** over six weeks, so the line slopes up by about 60 pips every two weeks.

Next week the line sits around **1.0850**. A pullback to 1.0855 is a possible buy, with a stop at 1.0825, below the line. If price closes clearly below the line, you do not need to flip short. You simply stop looking for buys until a new structure forms.
""".strip(),
    mistakes=(
        "Adjusting a line until it fits what you want.",
        "Treating any tiny poke through a line as a reversal.",
        "Drawing trendlines on very short timeframes, where noise dominates.",
    ),
    evidence=Evidence(
        Verdict.UNTESTED,
        """
Trendlines are hard to test because they are subjective. Lo, Mamaysky and Wang used computers to identify chart shapes and found some information content; that study did not directly test hand-drawn lines.

Treat trendlines as a visual aid. A rule you can write down, such as a moving average, is easier to test. Trend effects measured with simple rules have better support than hand-drawn lines.
""".strip(),
    ),
    try_it="Have a friend, or a second copy of yourself on another day, draw the same trendline. Compare. How far apart are they?",
    quiz=(
        Q(
            "How many touch points do you need before a line means much?",
            ("One", "Two", "At least three"),
            2,
            "Any two points make a line. Three or more means the market has actually respected it.",
        ),
        Q(
            "Why are trendlines hard to test?",
            (
                "They are drawn by hand, and people draw them differently",
                "They are too accurate",
                "Brokers do not allow them",
            ),
            0,
            "Subjectivity makes tests difficult and results easy to fool yourself with.",
        ),
    ),
    takeaways=(
        "Use at least three touches.",
        "A trendline break is a warning, not a verdict.",
        "Hand-drawn lines are subjective.",
    ),
    sources=("lmw-2000",),
)

_FIB_INTRO = Lesson(
    slug="chart-language/fibonacci-and-levels",
    title="Fibonacci, levels and why traders watch them",
    summary="The vocabulary of levels, and the honest reason Fibonacci sometimes seems to work.",
    est_minutes=6,
    key_concepts=("Fibonacci", "retracement", "support", "resistance", "trendline", "pivot"),
    figures=(Figure("fibonacci", "Retracement levels sit between a swing low and swing high."),),
    goal="Know the common level tools and treat them as places to watch, not predictions.",
    body_md="""
Once a market has moved, traders look for where a pullback might stop. They use a handful of level tools.

- **Support and resistance:** areas where buying or selling has appeared before.
- **Trendline and channel:** lines connecting swing points.
- **Fibonacci retracement:** horizontal levels at **23.6%, 38.2%, 50%, 61.8%** of the last swing. The numbers come from a mathematical sequence, and 50% is added by tradition.
- **Fibonacci extension:** projected levels beyond the move, such as **127.2%** and **161.8%**, often used as targets.
- **Pivot points:** levels calculated from the previous period's high, low and close.

### The honest catch

There is no reason in nature for a market to care about the golden ratio. If Fibonacci levels sometimes appear to work, the most likely reason is that **many people watch them** and place orders there, so it can be partly self-fulfilling.

But there is also a big **selection effect**. With several Fibonacci levels on every swing, plus zones around them, price is often near one of them. So a chart can look as though Fibonacci worked when the result is ordinary. The next lessons test this.
""".strip(),
    charts=(
        candle_chart(
            path([(0, 100), (14, 110), (22, 106.2), (32, 112)], seed=43, noise=0.2),
            title="Fibonacci levels of a swing",
            caption="Illustrative prices. From a low of 100 to a high of 110, the retracement levels sit at 107.64, 106.18, 105 and 103.82. Price often sits near one of many levels by chance.",
            hlines=(
                HLine(107.64, "23.6%", "muted"),
                HLine(106.18, "38.2%", "accent"),
                HLine(105.0, "50%", "accent"),
                HLine(103.82, "61.8%", "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Find a clear swing with a low and a high.",
        "Mark the retracement levels between them.",
        "Treat these as zones where you might look for a setup.",
        "Require other reasons as well, such as a trend and a stop you can defend.",
        "Measure your own results on a real, fixed rule.",
    ),
    example_md="""
A rally runs from **1.0700 to 1.0900** (200 pips). Retracement levels:

- 38.2% = 1.0900 − 0.382 × 200 pips = **1.0824**
- 50% = **1.0800**
- 61.8% = 1.0900 − 0.618 × 200 pips = **1.0776**

You could plan to look for buys in the 1.0776–1.0824 zone with a stop below the swing low at 1.0700. That is a tool for organising a trade. It is not a forecast that price will bounce.
""".strip(),
    mistakes=(
        "Treating the golden ratio as a natural law of markets.",
        "Trying every swing until the Fibonacci levels line up.",
        "Using a level with no plan for what happens if it fails.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
Batchelor and Ramyar tested whether Dow Jones trends cluster around Fibonacci or round-fraction ratios. They found a few significant ratios, but no more than chance would produce given how many tests were run.

Some small studies and many blog backtests point the same way. There is no good evidence that the Fibonacci numbers have any special power. Any effect is more likely due to many people watching the same levels, and that is hard to prove either way.
""".strip(),
    ),
    try_it="On a chart with 10 swings, check how often price came within 0.2% of any Fibonacci level. Then do the same with made-up levels at 30%, 45% and 70%. Compare.",
    quiz=(
        Q(
            "Why do Fibonacci retracement levels sometimes seem to work?",
            (
                "The golden ratio has predictive power",
                "Many traders watch them, and price is often near some level by chance",
                "They guarantee a reversal",
            ),
            1,
            "It is partly self-fulfilling and partly chance, not magic.",
        ),
        Q(
            "What did Batchelor and Ramyar find?",
            (
                "Fibonacci ratios strongly predict markets",
                "No more significant ratios than chance would produce",
                "Fibonacci only works in crypto",
            ),
            1,
            "Results were consistent with chance.",
        ),
    ),
    takeaways=(
        "Fibonacci levels are places to watch, not predictions.",
        "Many levels mean price is often near one by chance.",
        "Tests have not found them special.",
    ),
    sources=("batchelor-2006",),
)

_fib_path = path([(0, 100), (12, 110), (20, 104.1), (34, 112.5)], seed=47, noise=0.18)

_FIB_RETRACE = Lesson(
    slug="ta/fibonacci-retracements",
    title="Fibonacci retracements: how people trade them",
    summary="Step-by-step rules for trading retracements, with the evidence alongside.",
    est_minutes=9,
    key_concepts=("Fibonacci", "retracement", "golden ratio", "swing"),
    goal="Be able to apply Fibonacci retracements correctly, and test whether they help you.",
    body_md="""
A **retracement** is a pullback against a recent move. Fibonacci retracement tools draw levels between the low and the high of that move.

The common levels are **23.6%, 38.2%, 50% and 61.8%**. 61.8% is sometimes called the golden ratio. The 50% level is not a Fibonacci ratio at all; it just became a tradition.

### How traders commonly use them

1. Find a clear, strong swing in the direction of the larger trend.
2. Draw the tool from the swing low to the swing high (in an uptrend).
3. Watch the 38.2% to 61.8% area for a pullback to stop.
4. Look for confirmation there, such as a rejection candle.
5. Put the stop beyond the swing low or the 78.6% level.
6. Set the first target at the previous high.

### What really matters

The key decision is **which swing you pick**. Two people can choose different swings and draw different levels. There is no neutral way to pick the swing, so it is very easy to fool yourself by choosing the swing that makes the levels look perfect.

A testable rule requires a fixed definition of a swing, such as "the highest and lowest closes in the last 50 bars, with the highest after the lowest".
""".strip(),
    charts=(
        candle_chart(
            _fib_path,
            title="A retracement into the 38–62% zone",
            caption="Illustrative prices. A rally from 100 to 110, a pullback to about 104 (near the 61.8% level), and a rise to a new high. Real markets are much messier, and many pullbacks go deeper.",
            zones=(Zone(103.82, 106.18, "38–62% zone", "accent", 12, 34),),
            hlines=(HLine(100, "Swing low: invalidation", "danger"),),
            marks=(Mark(20, 104.1, "Pullback ends", "accentSoft", "up"),),
        ),
    ),
    steps=(
        "Define your swing with a rule, not by eye, for example the highest and lowest closes in the last 50 bars.",
        "Draw the levels from low to high in an uptrend, and high to low in a downtrend.",
        "Plan entries in the 38.2%–61.8% zone, only with the larger trend.",
        "Place the stop beyond the swing's origin, or beyond 78.6%.",
        "Record the setup every time it appears, including those you skipped.",
    ),
    example_md="""
EUR/USD rallied from **1.0700 to 1.0900** over 3 weeks. Levels: 38.2% = **1.0824**, 50% = **1.0800**, 61.8% = **1.0776**.

**Plan:** buy limit at 1.0805. Stop at 1.0760 (below the 61.8% level). Target 1.0900.

- Risk: 45 pips. Reward: 95 pips. About 2.1:1.
- If you risk 1% on a $10,000 account ($100), position size = $100 / (45 × $10) = **0.22 lots**.

Two outcomes:

1. Price dips to 1.0805 and rallies. You make about $209.
2. Price falls to 1.0760. You lose about $99, and the level did not hold. That is normal, and one reason you sized the trade first.
""".strip(),
    mistakes=(
        "Picking the swing after seeing where the price turned.",
        "Using retracements against the larger trend.",
        "Having no stop because the level 'should hold'.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
**Tested:** in the one serious test we found (Batchelor and Ramyar, on Dow Jones data), Fibonacci ratios did not show up more often than chance predicts.

**Popular belief:** that retracement levels are where markets 'naturally' turn. Blog tests differ, and most have unclear methods.

**What can be said:** a pullback in a trend is a sensible place to look for entries. The Fibonacci numbers themselves add little that you can prove.

To find out for yourself, test the same setup with Fibonacci levels against the same setup with simple levels such as 33% and 66%, using fixed rules, and compare.
""".strip(),
    ),
    try_it="Use a rule to define a swing, and record 30 retracements on one market. Note the depth reached each time. Do they cluster at Fibonacci levels, or spread out evenly?",
    quiz=(
        Q(
            "Which level is NOT really a Fibonacci ratio but is commonly included?",
            ("38.2%", "50%", "61.8%"),
            1,
            "50% is tradition, not a Fibonacci ratio.",
        ),
        Q(
            "What is the biggest weakness when people test Fibonacci?",
            (
                "It needs too much maths",
                "They choose the swing after seeing the outcome",
                "Brokers block it",
            ),
            1,
            "Selecting swings afterwards is what makes the tool look better than it is.",
        ),
    ),
    takeaways=(
        "Define the swing with a rule.",
        "Plan the stop before the level.",
        "The best evidence so far says the levels are not special.",
    ),
    sources=("batchelor-2006",),
)

_FIB_EXT = Lesson(
    slug="ta/fibonacci-extensions",
    title="Fibonacci extensions and targets",
    summary="Projecting targets beyond the last swing, and how to treat them.",
    est_minutes=6,
    key_concepts=("extension", "target", "127.2%", "161.8%"),
    goal="Be able to project extension levels and use them sensibly as targets.",
    body_md="""
**Extensions** project levels beyond a move. The common ones are **127.2%** and **161.8%**.

In an uptrend, take the swing from low **A** to high **B**, and the pullback to **C**. A projection for the next move is often measured as:

**Target = C + (B − A) × ratio.** The ratio is often 1.0, 1.272 or 1.618.

### How to use them

Many traders use extensions to plan where to **take profit**. Others use them to decide whether a trade offers enough reward for the risk.

### A simple, better habit

Do not treat an extension as a place where price will stop. A target should come from your own reward-to-risk rule, the location of major levels, and what your own testing shows.
""".strip(),
    charts=(
        candle_chart(
            path([(0, 100), (10, 110), (16, 105), (28, 121.5)], seed=51, noise=0.18),
            title="Extensions measured from a swing and pullback",
            caption="Illustrative prices. Swing A=100 to B=110, pullback to C=105. Extensions: 1.0 = 115, 1.272 = 117.72, 1.618 = 121.18.",
            hlines=(
                HLine(115, "1.0 extension", "muted"),
                HLine(117.72, "1.272", "accent"),
                HLine(121.18, "1.618", "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Identify points A (start), B (end) and C (pullback low).",
        "Compute Target = C + (B − A) × ratio.",
        "Compare the target with major levels nearby.",
        "Check that the reward-to-risk meets your plan.",
        "Decide in advance if you will exit in one piece or in parts.",
    ),
    example_md="""
Swing up from A = 1.0700 to B = 1.0800, pullback to C = 1.0750, and you enter at 1.0755 with a stop at 1.0725 (30 pips).

- 1.0 extension: 1.0750 + 0.0100 = **1.0850** (95 pips of reward, about 3.2R).
- 1.618 extension: 1.0750 + 0.01618 = **1.0912** (157 pips, about 5.2R).

If a large resistance zone sits at 1.0870, the 1.618 target is unlikely to be reached before a serious test. Most traders would take at least part of the position off around 1.0850–1.0870.
""".strip(),
    mistakes=(
        "Treating an extension as a level where price must turn.",
        "Using far-off targets that are rarely reached.",
        "Ignoring major levels on the way to the target.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
There is little direct testing of extension levels themselves. The Dow study that tested Fibonacci ratios in trends (Batchelor and Ramyar) found no special clustering. No strong evidence shows that markets respect these numbers. Use them as a way to plan, not to predict.
""".strip(),
    ),
    try_it="Find three swings and pullbacks. Compute a 1.0 and 1.618 target for each. Then see how often each target was reached before the swing origin was hit.",
    quiz=(
        Q(
            "With A=1.20, B=1.30, C=1.25, what is the 1.0 extension target?",
            ("1.30", "1.35", "1.40"),
            1,
            "C + (B − A) = 1.25 + 0.10 = 1.35.",
        ),
        Q(
            "Which matters more for choosing a target?",
            (
                "A fixed Fibonacci number",
                "Your risk-reward rule and nearby major levels",
                "The colour of the candle",
            ),
            1,
            "Targets should fit your plan and the actual chart.",
        ),
    ),
    takeaways=(
        "Extensions are projected targets.",
        "Treat them as plans, not predictions.",
        "Check nearby levels and your risk-reward.",
    ),
    sources=("batchelor-2006",),
)

_PIVOTS = Lesson(
    slug="ta/pivot-points",
    title="Pivot points",
    summary="A simple level formula used by many intraday traders.",
    est_minutes=6,
    key_concepts=("pivot point", "R1", "S1", "intraday"),
    goal="Be able to calculate pivots and know what they are really used for.",
    body_md="""
**Pivot points** are levels calculated from the previous period's high, low and close. They are popular for short-term trading because everyone gets the same numbers.

The classic daily formula uses yesterday's **high (H)**, **low (L)** and **close (C)**:

- **Pivot (P) = (H + L + C) / 3**
- **R1 = 2P − L** and **S1 = 2P − H**
- **R2 = P + (H − L)** and **S2 = P − (H − L)**

R means resistance, and S means support.

### How they are used

Traders watch whether price is above or below P to judge the day's bias, and treat R1, S1 and so on as places to take profit or to expect a pause. Their appeal is that they are objective and easy.

### Weaknesses

Different versions exist (Woodie, Camarilla, Fibonacci-based pivots), and each gives different levels. And since there are always several pivots nearby, price will often touch some of them by chance.
""".strip(),
    charts=(
        candle_chart(
            path([(0, 1.0800), (10, 1.0830), (22, 1.0815), (34, 1.0850)], seed=55, noise=0.3),
            title="Classic daily pivots",
            caption="Illustrative prices. Using yesterday's H 1.0850, L 1.0790, C 1.0820: P = 1.0820, R1 = 1.0850, S1 = 1.0790, R2 = 1.0880, S2 = 1.0760.",
            hlines=(
                HLine(1.0880, "R2", "danger"),
                HLine(1.0850, "R1", "danger"),
                HLine(1.0820, "Pivot", "accent"),
                HLine(1.0790, "S1", "accentSoft"),
                HLine(1.0760, "S2", "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Get yesterday's high, low and close from your broker's session.",
        "Compute P, R1, S1, R2, S2.",
        "Note whether today's price is above or below P.",
        "Use the levels as possible targets, not automatic entries.",
        "Check how much your broker's session times change the numbers.",
    ),
    example_md="""
Yesterday: H = **1.0900**, L = **1.0820**, C = **1.0870**.

- P = (1.0900 + 1.0820 + 1.0870) / 3 = **1.0863**
- R1 = 2 × 1.0863 − 1.0820 = **1.0906**
- S1 = 2 × 1.0863 − 1.0900 = **1.0826**

A trader might say: above 1.0863 I favour buys, with 1.0906 as a target. That is a simple way to structure a day. It is not an edge in itself.
""".strip(),
    mistakes=(
        "Treating pivots as certain turning points.",
        "Mixing different pivot formulas.",
        "Forgetting that different session cut-offs change every level.",
    ),
    evidence=Evidence(
        Verdict.UNTESTED,
        """
Pivot points are popular, but we found no strong independent tests showing they beat random levels after costs. Be suspicious of statistics quoted without sample sizes.

If you want to use them, treat them as a neutral way to mark the day, and test them on your own market.
""".strip(),
    ),
    try_it="Compute pivots for the last 10 days of one market. Count how often price actually reached R1 and S1. Compare with arbitrary levels of similar distance.",
    quiz=(
        Q(
            "Pivot point P is calculated as…",
            ("(H + L + C) / 3", "(H + L) / 2", "C only"),
            0,
            "The classic pivot averages yesterday's high, low and close.",
        ),
        Q(
            "Why might pivots seem to work?",
            (
                "Because many people watch them, and price is often near several levels",
                "They are based on company earnings",
                "They predict news",
            ),
            0,
            "With many nearby levels, price is often close to one by chance.",
        ),
    ),
    takeaways=(
        "Pivots are simple, formula-based levels.",
        "They are a neutral framework, not proof of an edge.",
        "Test on your own market.",
    ),
)

# ---------- patterns ----------

_hs = path(
    [(0, 100), (7, 106), (11, 102), (18, 109), (24, 102.3), (31, 105.6), (37, 98)],
    seed=61,
    noise=0.15,
)

_REVERSAL = Lesson(
    slug="ta/chart-patterns-reversal",
    title="Reversal patterns: head and shoulders, double tops and more",
    summary="The classic reversal shapes, with what the evidence says.",
    est_minutes=9,
    key_concepts=("head and shoulders", "double top", "double bottom", "neckline", "measured move"),
    goal="Identify the main reversal patterns and know how little to trust them alone.",
    body_md="""
Chart patterns are recurring shapes that traders use to anticipate what comes next. Reversal patterns are said to warn of the end of a trend.

- **Head and shoulders:** three peaks, the middle one highest, with a horizontal or sloping support line called the **neckline**. A break of the neckline is the classic signal.
- **Inverse head and shoulders:** the same pattern upside down.
- **Double top:** two peaks at about the same level. A **double bottom** is two troughs.
- **Triple top or bottom:** three tests of a level.
- **Rounding top or bottom:** a slow curve.

### The classic trading rule

1. Wait for the neckline to break, with a close beyond it.
2. Enter on the break or on a retest.
3. Put the stop above the last peak (right shoulder).
4. The **measured move** target is the height of the pattern projected from the neckline.

### Do not skip this

A pattern is only complete when the neckline breaks. Until then, it is just a guess about a shape that is not finished yet.
""".strip(),
    charts=(
        candle_chart(
            _hs,
            title="Head and shoulders",
            caption="Illustrative prices. Three peaks, with a neckline at about 102. Target by measured move: 102 − (109 − 102) = 95.",
            hlines=(HLine(102.1, "Neckline", "warn"),),
            marks=(
                Mark(7, 106, "Left shoulder", "muted"),
                Mark(18, 109, "Head", "danger"),
                Mark(31, 105.6, "Right shoulder", "muted"),
                Mark(37, 98, "Break", "accentSoft", "up"),
            ),
        ),
    ),
    steps=(
        "Check that there was a clear trend before the pattern.",
        "Mark the neckline.",
        "Wait for a close beyond the neckline. Do not anticipate.",
        "Plan entry, and a stop beyond the right shoulder.",
        "Project the measured-move target, then check whether the reward-to-risk is worth it.",
    ),
    example_md="""
A head and shoulders on the daily chart of a stock: head at **$109**, neckline at **$102**.

- Height = 109 − 102 = **$7**.
- Target = 102 − 7 = **$95**.
- Entry on a close at $101.50, stop above the right shoulder at $106.

Risk per share: **$4.50**. Reward: $6.50. Reward-to-risk is about 1.4:1 before costs, which is not very attractive on its own. Many traders never check this and take the trade because the pattern is 'textbook'.
""".strip(),
    mistakes=(
        "Trading the pattern before the neckline breaks.",
        "Seeing patterns because you want a trade.",
        "Forgetting that patterns fail, and failures can be sharp.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Lo, Mamaysky and Wang used computer algorithms to detect patterns in US stocks and concluded that several add incremental information. That is a real and careful finding. It does not by itself mean a trading strategy using those patterns beat the market after costs and risk.

Popular claims of very high pattern success rates usually come from small samples or from counting only the clear examples. Later critical work shows how much data snooping can inflate these results.

Practical view: patterns are useful for organising your thinking. They are not reliable as stand-alone signals.
""".strip(),
    ),
    try_it="Write a precise rule that defines a double top. Apply it to 2 years of daily data on one market. Then count how many confirmed and how many failed.",
    quiz=(
        Q(
            "When is a head and shoulders pattern complete?",
            ("When the head forms", "When the neckline breaks", "When the right shoulder starts"),
            1,
            "Until the neckline breaks, the pattern has not confirmed.",
        ),
        Q(
            "A head at 109, neckline at 102. What is the measured-move target?",
            ("95", "102", "109"),
            0,
            "Height 7, projected below 102: 95.",
        ),
    ),
    takeaways=(
        "Wait for the neckline break.",
        "Check reward-to-risk before trusting a textbook pattern.",
        "Patterns have some information content, but no proven stand-alone edge.",
    ),
    sources=("lmw-2000", "park-irwin-2007", "stw-1999"),
)

_flag = path([(0, 100), (10, 108), (20, 106.5), (27, 106.8), (35, 114)], seed=64, noise=0.15)

_CONTINUATION = Lesson(
    slug="ta/chart-patterns-continuation",
    title="Continuation patterns: flags, triangles and ranges",
    summary="Shapes that are said to pause a trend before it continues.",
    est_minutes=8,
    key_concepts=("flag", "pennant", "triangle", "wedge", "rectangle"),
    goal="Identify continuation patterns, and plan a trade around them with a defined risk.",
    body_md="""
**Continuation patterns** are pauses that are said to come before the trend continues.

- **Flag:** a strong move up, then a small channel that drifts down.
- **Pennant:** like a flag, but the small pause forms a triangle shape.
- **Ascending triangle:** a flat top and rising lows.
- **Descending triangle:** a flat bottom and falling highs.
- **Symmetrical triangle:** falling highs and rising lows, narrowing to a point.
- **Rectangle:** a sideways box.
- **Wedges** slope in one direction and are often considered reversal patterns too, depending on context.

### The usual rule

1. Identify a strong move before the pattern, known as the **pole**.
2. Wait for a break of the pattern in the direction of the pole.
3. Stop on the other side of the pattern.
4. Target the height of the pole, projected from the break.

### Beware

A triangle is often drawn after the fact. In a live market, a triangle can break in either direction. It also takes judgement to decide where it starts and ends.
""".strip(),
    charts=(
        candle_chart(
            _flag,
            title="A flag: pause in a strong move",
            caption="Illustrative prices. A strong move up to 108, a small drift lower, then a break out of the pause.",
            zones=(Zone(106, 108, "Flag", "warn", 10, 27),),
            marks=(Mark(35, 114, "Breakout", "accentSoft"),),
        ),
    ),
    steps=(
        "Find a strong move in the trend direction.",
        "Identify a pause with a clear top and bottom.",
        "Wait for a close outside the pause in the trend direction.",
        "Place the stop on the other side of the pattern.",
        "Measure the target from the pole, and check the reward-to-risk ratio.",
    ),
    example_md="""
EUR/USD rallies **100 pips** in 2 days, then drifts down 20 pips in a small channel for a day and a half.

Plan: buy stop 3 pips above the top of the channel at 1.0850. Stop at 1.0825 below the channel. Target: 1.0850 + 100 pips = **1.0950**.

Risk 25 pips, reward 100 pips. If the channel breaks downward instead, the order simply never triggers. A good plan has a way of not taking the trade.
""".strip(),
    mistakes=(
        "Drawing the pattern after the breakout and treating that as evidence.",
        "Trading flags in choppy markets, where they fail often.",
        "Forgetting that the same shape can appear on random data.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
The evidence on continuation patterns is similar to reversal patterns. Careful research finds some extra information in chart shapes, but evidence that they pay after costs is much thinner. Compression before expansion has more support, because volatility clusters, than any particular shape does.
""".strip(),
    ),
    try_it="Take 10 candidate flags from a chart and write down which direction each broke and how far it went.",
    quiz=(
        Q(
            "What is the 'pole' in a flag?",
            ("The pause", "The strong move before the pause", "The stop"),
            1,
            "The pole is the strong move used to project the target.",
        ),
        Q(
            "Why are triangles risky to trust?",
            (
                "They can break either way and are often clearest in hindsight",
                "They are illegal",
                "They only occur in crypto",
            ),
            0,
            "They can break either way, so plan for both.",
        ),
    ),
    takeaways=(
        "Continuation patterns are pauses inside a trend.",
        "Wait for the break.",
        "Do not count hindsight as evidence.",
    ),
    sources=("lmw-2000",),
)

# ---------- indicators ----------

_ma_path = path(
    [(0, 100), (15, 112), (30, 118), (45, 112), (60, 100), (75, 92)], seed=68, noise=0.3
)
_ma_close = _ma_path.closes

_MA = Lesson(
    slug="indicators/moving-averages",
    title="Moving averages and why they lag",
    summary="Simple and exponential averages, what they do, and how they fail.",
    est_minutes=8,
    key_concepts=("SMA", "EMA", "lag", "trend filter", "whipsaw", "golden cross"),
    figures=(Figure("ma-lag", "A moving average follows price, always a little behind."),),
    goal="Use moving averages as a trend filter, and know why crossovers disappoint.",
    body_md="""
A **moving average** is the average price over the last N candles, drawn as a line.

- A **simple moving average (SMA)** weights each candle equally.
- An **exponential moving average (EMA)** weights recent candles more.

By design, a moving average is a slow summary of recent price. Its job is to **lag**. That makes it useful as a **trend filter**: "above the 200, I only look for buys; below it, only sells." It is poor as a turning-point signal, since by the time it crosses, much of the move has happened.

### Popular uses

- **Filter:** only trade in the direction of the long moving average.
- **Dynamic support:** pullbacks to a 20 or 50 average.
- **Crossovers:** a short average crossing a long one. A 50 crossing above the 200 is called a **golden cross**.

### How they fail

- **Whipsaw:** in sideways markets, every cross is a false signal.
- The choice of length is arbitrary, and small changes can flip the signal.
- Crossover systems look great in cherry-picked backtests.

The simple crossover is also the benchmark any fancy system should beat.
""".strip(),
    charts=(
        candle_chart(
            _ma_path,
            title="Fast and slow moving averages lag behind price",
            caption="Illustrative prices, real calculations of the 10 and 30-period averages on those prices. The slow average turns well after the top.",
            series=(
                Series("10-period average", sma(_ma_close, 10), "accent"),
                Series("30-period average", sma(_ma_close, 30), "warn"),
            ),
        ),
    ),
    steps=(
        "Pick one long average as a trend filter, such as the 100 or 200.",
        "Only look for trades in the direction of that filter.",
        "Do not use crossovers on their own in a sideways market.",
        "Test any rule you use, including costs, on data you did not tune it on.",
        "Keep the number of averages on your chart small.",
    ),
    example_md="""
Your rule: buy only if the daily close is above the 200-day moving average.

- Price 1.0950, 200-day average 1.0800: buys are allowed.
- Price falls to 1.0780: your rule says stop looking for buys.

The filter stops you from buying into a falling market. It costs you some of the early part of a recovery. That trade-off is what the moving average is: fewer bad trades, later entries.
""".strip(),
    mistakes=(
        "Treating a moving average as a signal that price will reverse.",
        "Using the crossover that looks best in hindsight.",
        "Stacking many averages on a chart until none of them is useful.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
**Tested:** Brock, Lakonishok and LeBaron found that moving-average rules on the Dow from 1897 to 1986 were informative. Time-series momentum research using similar trend signals (Moskowitz et al.; Hurst et al.) has held up across many markets and over more than a century.

**Disputed:** Sullivan et al. and others show that much of the apparent profit of many technical rules shrinks after adjusting for data mining and costs. Neely et al. found FX trading rule profits have tended to fade over time.

Summary: a moving-average trend filter on longer timeframes has real, modest support. Short-term crossover signals have much less.
""".strip(),
    ),
    try_it="On a chart, count how many times the 20 and 50 averages crossed in the last two years. How many crossings were followed by a big move, and how many were whipsaws?",
    quiz=(
        Q(
            "A moving average is best used as…",
            ("A precise turning-point signal", "A trend filter", "A forecast"),
            1,
            "It lags by design, so it filters direction instead of timing turns.",
        ),
        Q(
            "In a sideways market, moving-average crossovers tend to…",
            ("Whipsaw", "Work perfectly", "Disappear"),
            0,
            "Each crossing tends to be followed by a reversal.",
        ),
    ),
    takeaways=(
        "Moving averages lag by design.",
        "Use them as a filter on longer timeframes.",
        "Short-term crossovers have weaker support.",
    ),
    sources=("brock-1992", "moskowitz-2012", "hurst-2017", "stw-1999", "neely-2009"),
)

_rsi_path = path(
    [(0, 100), (15, 112), (30, 123), (40, 118), (55, 130), (70, 124)], seed=72, noise=0.35
)
_rsi_vals = rsi(_rsi_path.closes)

_RSI = Lesson(
    slug="indicators/rsi-and-the-overbought-trap",
    title="RSI and the overbought trap",
    summary="What RSI measures and why 'overbought' does not mean 'about to fall'.",
    est_minutes=7,
    key_concepts=("RSI", "momentum", "divergence", "regime", "overbought", "oversold"),
    figures=(Figure("rsi-regime", "RSI can stay high for a long time in a strong trend."),),
    goal="Read RSI correctly and avoid the most common mistake traders make with it.",
    body_md="""
The **Relative Strength Index (RSI)** compares recent gains to recent losses on a scale from 0 to 100.

- Above **70** is often called **overbought**.
- Below **30** is often called **oversold**.

Here is the trap. *Overbought does not mean about to fall.* In a range, high readings may hint at a pullback. In a strong trend, RSI can stay above 70 for a long time while the price keeps rising. Selling because RSI is high is one of the most common ways to fight a strong trend.

### Uses that survive

- **Regime tag:** extreme readings tell you the move is strong, and possibly that it is trending.
- **Divergence** at a major level: price makes a new high, but RSI does not. This is worth noticing, not sufficient alone.
- **Range tool:** in a clear range, extreme readings can hint at mean reversion.

The standard setting is 14 periods, and small changes to the number change the readings.
""".strip(),
    charts=(
        candle_chart(
            _rsi_path,
            title="RSI can stay high in a strong trend",
            caption="Illustrative prices, real RSI calculation on those prices. RSI spends long stretches above 70 while the price keeps rising.",
            series=(Series("RSI (14)", _rsi_vals, "accent", "line", "lower"),),
            lower_title="RSI (14)",
            hlines=(HLine(70, "70", "danger", "lower"), HLine(30, "30", "accentSoft", "lower")),
        ),
    ),
    steps=(
        "Check whether the market is trending or ranging.",
        "In a trend, treat extreme RSI as a sign of strength, not a reversal.",
        "In a range, consider extreme readings as a hint only.",
        "Treat divergence as one input at a level you already care about.",
        "Test any RSI rule on your market with costs included.",
    ),
    example_md="""
EUR/USD rallies for two weeks and daily RSI reaches **78**. A trader who sells because "it is overbought" keeps a tight stop and is stopped out twice as the rally continues.

Another trader reads the same 78 and concludes: the trend is strong. Buying near a major high with a tight stop may not be wise, but neither is shorting because of one number. That trader waits for a pullback in the direction of the trend.
""".strip(),
    mistakes=(
        "Selling just because RSI is above 70.",
        "Buying just because RSI is below 30 in a downtrend.",
        "Optimising the RSI period until the backtest looks good.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
We did not find a strong, independent, out-of-sample study showing that RSI rules beat a benchmark after costs. Many practitioner tests disagree, and most test only a single market and period without correcting for how many settings were tried.

The general results in this chapter apply: simple rules can look good until you allow for costs and data mining. RSI's most reliable role is descriptive.
""".strip(),
    ),
    try_it="Find the last 5 times RSI went above 70 on one market. Note what price did over the next 20 candles. Did it fall, or keep going?",
    quiz=(
        Q(
            "RSI is at 80 in a strong uptrend. The most accurate reading is…",
            (
                "A reversal is due",
                "The move is strong, and this is not by itself a reversal signal",
                "RSI is broken",
            ),
            1,
            "RSI can stay high for a long time in a strong trend.",
        ),
        Q(
            "Divergence is best treated as…",
            (
                "One input at a level you already care about",
                "A guaranteed reversal",
                "A sign to double your size",
            ),
            0,
            "It is a hint, not enough alone.",
        ),
    ),
    takeaways=(
        "Overbought does not mean about to fall.",
        "RSI behaves differently in trends and ranges.",
        "Evidence for RSI as a trading signal is weak.",
    ),
    sources=("stw-1999",),
)

_macd_path = path([(0, 100), (20, 112), (35, 108), (50, 118), (70, 103)], seed=78, noise=0.3)
_macd_line, _macd_sig, _macd_hist = macd(_macd_path.closes)

_MACD = Lesson(
    slug="ta/macd",
    title="MACD",
    summary="A momentum indicator made of moving averages.",
    est_minutes=7,
    key_concepts=("MACD", "signal line", "histogram", "momentum", "divergence"),
    goal="Understand what MACD is made of and what it can tell you.",
    body_md="""
**MACD** stands for Moving Average Convergence Divergence. It is built from moving averages.

- **MACD line** = the 12-period EMA minus the 26-period EMA.
- **Signal line** = the 9-period EMA of the MACD line.
- **Histogram** = MACD line minus signal line.

When the MACD line is above zero, the short average is above the long average, which is a sign of upward momentum.

### How people use it

- **Crossovers:** MACD crossing above its signal line is read as bullish.
- **Zero-line:** moves above or below zero can act as a trend filter.
- **Divergence:** price makes a new high but MACD does not.

### Limits

MACD is a difference of moving averages, so it is a lagging tool like them. It generates many crossover signals in sideways markets. The default numbers (12, 26, 9) are just conventions. Do not treat them as special.
""".strip(),
    charts=(
        candle_chart(
            _macd_path,
            title="MACD below the price",
            caption="Illustrative prices, real MACD calculation on those prices. The bars in the lower panel show the histogram.",
            series=(
                Series("MACD", _macd_line, "accent", "line", "lower"),
                Series("Signal", _macd_sig, "warn", "line", "lower"),
                Series("Histogram", _macd_hist, "muted", "bars", "lower"),
            ),
            lower_title="MACD (12, 26, 9)",
        ),
    ),
    steps=(
        "Look at whether MACD is above or below zero.",
        "Use that as a broad momentum filter, not as an entry signal.",
        "Be careful with crossovers in a range.",
        "Compare MACD with price at major levels for divergence.",
        "Test on your own market, with costs.",
    ),
    example_md="""
A daily chart of gold shows MACD crossing above its signal line on Monday. Price rose for the previous five days.

A trader enters at the crossover and pays the spread. Because MACD lags, a lot of the move has already happened. Within days price pulls back, and the signal reverses.

If the same trader uses MACD above zero only as a filter ("I only look for pullback buys while MACD is positive"), the indicator has a smaller job and fewer false signals.
""".strip(),
    mistakes=(
        "Using every crossover as a trade signal.",
        "Thinking MACD predicts rather than describes.",
        "Tuning the three numbers to a past period.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
MACD has been tested mostly in small studies and practitioner backtests, with mixed and often unconvincing results. We did not find strong out-of-sample evidence of an edge after costs.

Because it is built from moving averages, some of the evidence on moving averages applies. Long-horizon trend signals have stronger support than short-term crossover signals.
""".strip(),
    ),
    try_it="Compare, on one market, how many MACD crossovers occurred in the last year and how many were followed by a move of at least 2 ATR.",
    quiz=(
        Q(
            "What is the MACD line?",
            ("12 EMA minus 26 EMA", "RSI minus 50", "The average true range"),
            0,
            "MACD is the difference of two exponential moving averages.",
        ),
        Q(
            "MACD is above zero. The honest reading is…",
            ("A buy signal", "Recent momentum has been upward", "Price is guaranteed to rise"),
            1,
            "It describes recent momentum. It does not forecast the future.",
        ),
    ),
    takeaways=(
        "MACD is built from moving averages.",
        "It describes momentum and lags.",
        "Use it as a filter rather than a trigger.",
    ),
    sources=("moskowitz-2012",),
)

_bb_path = path(
    [(0, 100), (12, 104), (22, 101), (35, 103), (42, 110), (55, 106)], seed=81, noise=0.3
)
_bb_u, _bb_m, _bb_l = bollinger(_bb_path.closes)

_BOLLINGER = Lesson(
    slug="ta/bollinger-bands",
    title="Bollinger Bands",
    summary="Bands set by recent volatility, and how traders use them.",
    est_minutes=7,
    key_concepts=("Bollinger Bands", "standard deviation", "squeeze", "mean reversion"),
    goal="Read Bollinger Bands correctly and know what they do and do not tell you.",
    body_md="""
**Bollinger Bands** draw a moving average (usually 20 periods) with one line above and one below it. The upper and lower lines sit a set number of **standard deviations** away. A standard deviation is a measure of how spread out recent prices have been. The usual setting is 2.

- When price moves a lot, the bands widen.
- When price is calm, the bands narrow, which is called a **squeeze**.

### Common uses

- **Mean reversion:** in a range, price near the outer band may return towards the middle.
- **Breakout:** a squeeze may come before a larger move.
- **Trend:** in strong trends, price can stick to, or "ride", the upper band for a long time.

### The trap

Being at the upper band does **not** mean "too high". Like RSI, it just means price has been strong recently.
""".strip(),
    charts=(
        candle_chart(
            _bb_path,
            title="Bollinger Bands on a squeeze and breakout",
            caption="Illustrative prices, real 20-period Bollinger calculation on those prices. The bands narrow in the quiet period, then price breaks out.",
            series=(
                Series("Upper band", _bb_u, "accent", "dashed"),
                Series("Average", _bb_m, "muted"),
                Series("Lower band", _bb_l, "accent", "dashed"),
            ),
        ),
    ),
    steps=(
        "Check if the market is trending or ranging.",
        "In a range, an outer band may hint at a fade, with a stop outside the range.",
        "In a trend, do not sell only because price touches the upper band.",
        "Treat a squeeze as 'volatility may expand', not as a direction.",
        "Test your rules on your market.",
    ),
    example_md="""
EUR/USD daily bands narrow to about **80 pips** wide, the narrowest in months. That suggests that volatility is low and may expand.

A breakout plan: buy on a close above the upper band, stop at the middle band, or sell on a close below the lower band with the stop at the middle band. Each trade risks about 40 pips. You will probably get some false starts.
""".strip(),
    mistakes=(
        "Selling simply because the upper band was touched.",
        "Treating a squeeze as if it says which direction the next move will take.",
        "Assuming bands with 2 standard deviations contain 95% of prices. Market returns have fat tails.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
We did not find strong out-of-sample academic tests of Bollinger Bands after costs in our research pass. Practitioner tests are mixed, often negative, and usually lack proper out-of-sample checks.

Volatility clustering, which is well supported, gives the squeeze idea its grounding: quiet periods do tend to be followed by more movement eventually. It does not tell you the direction.
""".strip(),
    ),
    try_it="Find three squeezes on a chart. Before looking at what came next, predict up or down and write your reasons. Check how often you were right.",
    quiz=(
        Q(
            "What does a Bollinger squeeze suggest?",
            ("A move may come, direction unknown", "Price will rise", "Trend is ending"),
            0,
            "It points to possible volatility expansion. It does not give the direction.",
        ),
        Q(
            "Price sits on the upper band in a strong trend. This means…",
            ("It must fall", "Recent strength, not necessarily a reversal", "The band is broken"),
            1,
            "Price can ride a band for a long time in a trend.",
        ),
    ),
    takeaways=(
        "Bands widen and narrow with volatility.",
        "A touch of a band is not a signal by itself.",
        "A squeeze says something about size, not direction.",
    ),
    sources=("mandelbrot-1963",),
)

_atr_path = path([(0, 100), (20, 105), (35, 102), (55, 110)], seed=84, noise=0.4)
_atr_values = atr(_atr_path)

_ATR = Lesson(
    slug="indicators/atr-and-volatility",
    title="ATR and volatility-aware stops",
    summary="Measuring how far a market normally moves, and setting stops that survive it.",
    est_minutes=7,
    key_concepts=("ATR", "volatility", "stop", "noise floor"),
    figures=(Figure("atr-stop", "A stop closer than normal noise gets hit by randomness."),),
    goal="Use ATR to place stops that respect how far a market normally moves.",
    body_md="""
**Average True Range (ATR)** measures the average size of the last N candles, usually 14. It does not show direction. It shows how much the market has been moving.

Think of it as the market's noise level. A stop closer than about 1× ATR sits inside everyday wiggle and will be hit by randomness.

### Practical rules

- Many swing traders use **2 to 3 × ATR** for stops.
- In calm markets (low ATR), stops can be tighter and sizes larger for the same money risk.
- In wild markets (high ATR), stops must be wider, which means smaller sizes. The position-size calculator handles this automatically.

This is a key link in your plan: ATR tells you how far the stop should be, your stop tells you the position size, and your position size keeps your risk constant.
""".strip(),
    charts=(
        candle_chart(
            _atr_path,
            title="ATR rises and falls with the size of candles",
            caption="Illustrative prices, real 14-period ATR on those prices.",
            series=(Series("ATR (14)", _atr_values, "warn", "line", "lower"),),
            lower_title="ATR (14)",
        ),
    ),
    steps=(
        "Compute ATR(14) on your timeframe.",
        "Choose a multiple (for example 2×) from your testing.",
        "Stop distance = ATR × multiple.",
        "Stop price = entry − stop distance, for a long.",
        "Compute position size from that distance.",
    ),
    example_md="""
EUR/USD daily ATR is **70 pips**. You use 2× ATR.

- Stop distance = **140 pips**.
- Entry 1.0900 long: stop at **1.0760**.
- Account $10,000, risk 1% ($100): lots = $100 / (140 × $10) = **0.07 lots**.

Last month ATR was only 40 pips, so 2× was 80 pips and you could have traded about 0.12 lots for the same dollar risk. The ATR adjusted your size to fit the market.
""".strip(),
    mistakes=(
        "Using a fixed pip stop whatever the market is doing.",
        "Forgetting that ATR is measured in price units and changes over time.",
        "Taking the same lot size when volatility doubles.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
It is well established that volatility clusters: big moves tend to follow big moves (Mandelbrot; Engle's ARCH). So a stop based on recent volatility has a real basis.

The evidence is less clear on which exact multiple of ATR to use, or that this lifts returns. Its strongest role is keeping your risk stable.

Note: this app forecasts a volatility range, and its live forecasting record overall is still too short to count as proven.
""".strip(),
    ),
    try_it="Find today's ATR on two different markets and compute the stop distance for 2× ATR. How much smaller would your position have to be in the more volatile one?",
    quiz=(
        Q(
            "ATR measures…",
            ("Direction", "How much price has been moving", "Trade volume"),
            1,
            "ATR measures the typical size of candles, regardless of direction.",
        ),
        Q(
            "Daily ATR doubles. To keep the same dollar risk you should…",
            (
                "Use a wider stop and a smaller position",
                "Keep the same stop and size",
                "Double your position",
            ),
            0,
            "Wider stops mean smaller sizes for the same risk.",
        ),
    ),
    takeaways=(
        "ATR measures market noise.",
        "Set stops based on volatility.",
        "Wider stops mean smaller size.",
    ),
    sources=("mandelbrot-1963",),
)

_vwap_path = path([(0, 100), (10, 103), (20, 101.5), (32, 105), (40, 103.5)], seed=88, noise=0.3)

_VWAP = Lesson(
    slug="ta/vwap",
    title="VWAP",
    summary="The average price paid, and why big traders care about it.",
    est_minutes=6,
    key_concepts=("VWAP", "volume-weighted", "benchmark", "execution"),
    goal="Understand what VWAP is and how it is used by both traders and institutions.",
    body_md="""
**VWAP** means **volume-weighted average price**. It is the average price of everything traded so far today, with busy moments counting more.

**VWAP = total value traded ÷ total volume traded.**

It usually resets each day. Unlike a normal moving average, it uses volume.

### Who uses it

- **Institutions** use VWAP as a benchmark. A big fund that buys a stock below that day's VWAP has done better than the average buyer.
- **Execution algorithms** may split a large order to match VWAP.
- **Day traders** often treat price above VWAP as a bullish backdrop and price below it as bearish, and watch for pullbacks to VWAP.

### Limits

VWAP is built from real traded volume, so it is more meaningful where volume is measured on a central exchange. In spot forex there is no central volume, so a "VWAP" is usually built from one broker's data or tick counts.
""".strip(),
    charts=(
        candle_chart(
            _vwap_path,
            title="VWAP as an intraday reference",
            caption="Illustrative prices and volumes, real VWAP calculation on them.",
            series=(Series("VWAP", vwap(_vwap_path), "accent"),),
        ),
    ),
    steps=(
        "Add VWAP to an intraday chart of a market with real volume data.",
        "Note whether price is mostly above or below it.",
        "Treat VWAP as context for the day.",
        "If you test pullbacks to VWAP, use fixed rules.",
        "Avoid building decisions on VWAP from single-broker forex data.",
    ),
    example_md="""
You buy 1,000 shares of a stock at an average of $50.10. Today's VWAP was $50.25.

A fund manager would say your execution was $0.15 **better than VWAP**, a saving of $150. If you had bought at $50.40, that would be a poor execution of 15 cents per share.

For retail traders, this mindset is useful. Instead of asking only "did I make money?", you can ask "did I get a good price?".
""".strip(),
    mistakes=(
        "Treating VWAP as a signal rather than a benchmark.",
        "Using forex VWAP built from a single broker as if it were true market volume.",
        "Forgetting that VWAP is meant to reset each day.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
VWAP's role as an execution benchmark is standard among institutions. As a retail trading signal, we found no strong independent evidence of an edge after costs. Practitioner claims of reliable 'bounces' at VWAP are usually untested on data that was not used to pick the rule.
""".strip(),
    ),
    try_it="On a stock or futures market, note today's VWAP and your hypothetical entry from earlier in the day. Was it better or worse than the average buyer?",
    quiz=(
        Q(
            "VWAP stands for…",
            (
                "Volume-weighted average price",
                "Volatility-weighted average price",
                "Very wide average price",
            ),
            0,
            "It weights the average by traded volume.",
        ),
        Q(
            "Why is VWAP less meaningful in spot forex?",
            ("There is no central volume", "It does not work on Mondays", "Forex has no price"),
            0,
            "Spot forex is decentralised, so true total volume is not available.",
        ),
    ),
    takeaways=(
        "VWAP is the average price paid today.",
        "Institutions use it to judge execution quality.",
        "It needs real volume to mean much.",
    ),
    sources=("almgren-chriss",),
)

# ---------- volume and order flow ----------

_vol = path([(0, 100), (10, 101), (20, 100.5), (24, 106), (40, 110)], seed=92, noise=0.3)

_VOLUME = Lesson(
    slug="candles-volume/volume-and-profile",
    title="Volume, delta and the volume profile",
    summary="Reading how much traded and where it traded.",
    est_minutes=9,
    key_concepts=(
        "volume",
        "delta",
        "volume profile",
        "point of control",
        "value area",
        "open interest",
    ),
    figures=(Figure("volume-profile", "A horizontal view of how much traded at each price."),),
    goal="Read volume, delta and a volume profile, and know where the data is reliable.",
    body_md="""
Price tells you where the market went. **Volume** tells you how much traded on the way.

### Volume basics

- **Volume:** the number of units traded in a period, usually drawn as bars under the chart.
- **Volume spike:** a sudden, unusually tall bar. Often news or a breakout.
- **Delta:** the difference between aggressive buying (trades at the ask) and aggressive selling (trades at the bid). Positive delta means buyers were the more aggressive side.

### The confirmation idea

- A breakout on **high volume** is often considered more convincing.
- A breakout on **low volume** is often considered suspect.
- A trend on **shrinking volume** may be losing support.

### Volume profile

A **volume profile** flips the view sideways: a horizontal histogram of how much traded at each price.

- **Point of Control (POC):** the price with the most volume. A centre of activity.
- **Value area:** the band of prices where about 70% of the volume happened.
- **Value Area High and Low:** the edges of that band.

### Open interest

In futures and options, **open interest** counts contracts still open. Rising open interest during a trend means new positions are being added.

### The honest caveat

Volume is meaningful in **central exchanges**, where every trade is reported. In **spot forex**, it is murky: "volume" is usually only your broker's slice.
""".strip(),
    charts=(
        candle_chart(
            _vol,
            title="A breakout on rising volume",
            caption="Illustrative prices and volumes. Volume rises as price breaks out, which many traders read as confirmation. It is not a guarantee.",
            series=(Series("Volume", _vol.volume, "muted", "bars", "lower"),),
            lower_title="Volume",
            marks=(Mark(24, 106, "Breakout", "accentSoft"),),
        ),
    ),
    steps=(
        "Check whether your market has real, centrally reported volume.",
        "Compare the current bar's volume with the average of the last 20 bars.",
        "Look at whether large volume agrees with the direction of the price move.",
        "Use a volume profile to find the price areas where most trading happened.",
        "Treat all of this as context, and test before you rely on it.",
    ),
    example_md="""
A stock breaks above $50 on volume **three times** its 20-day average. Two days later, it pulls back to $50 on **half** its average volume.

A volume-based reading: buyers committed on the breakout, and sellers were not active on the pullback. A plan could be a buy near $50 with a stop at $48.50.

Now the honest check: test how often this pattern on this stock was followed by a further rise, and compare that to any two-day pullback. Volume alone does not tell you.
""".strip(),
    mistakes=(
        "Reading a retail forex 'volume' bar as if it were the whole market.",
        "Using volume profile levels as magic prices.",
        "Treating a single volume spike as proof of a trend.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
**Reasonably supported:** Evans and Lyons found that signed order flow explains much of daily exchange rate moves, so *who is pressing the market* matters in the short term. But that study used dealer data retail traders cannot see.

**Less supported:** claims like "POC acts as a magnet" or "buy at the value area low" have little independent testing. They may work partly because everyone watches the same levels.
""".strip(),
    ),
    try_it="Pick a market with real volume, and note volume on the last five breakouts. Did the high-volume ones go further than the low-volume ones?",
    quiz=(
        Q(
            "On a volume profile, the price with the most volume is the…",
            ("Value Area High", "Point of Control", "Delta"),
            1,
            "The Point of Control is the price where the most volume changed hands.",
        ),
        Q(
            "Why is spot forex volume unreliable?",
            (
                "There is no central exchange reporting all trades",
                "Forex has no buyers",
                "It is banned",
            ),
            0,
            "Your platform shows only its own slice of activity.",
        ),
    ),
    takeaways=(
        "Volume is most useful on central exchanges.",
        "A volume profile shows where trading happened.",
        "Treat volume as context, not proof.",
    ),
    sources=("evans-lyons-2002",),
)

_FLOW = Lesson(
    slug="ta/order-flow",
    title="Order flow basics",
    summary="Watching who is pressing the buttons, and why retail traders see so little of it.",
    est_minutes=7,
    key_concepts=("order flow", "footprint", "absorption", "tape reading"),
    goal="Understand what order flow is, and be realistic about what you can see.",
    body_md="""
**Order flow** means the stream of actual buy and sell orders hitting the market. If more aggressive buyers are hitting the ask than aggressive sellers hitting the bid, the flow is positive.

### Common tools

- **Depth of market** (or order book): the orders waiting at each price.
- **Time and sales** (the "tape"): each trade as it happens.
- **Footprint charts:** volume at each price inside a candle, split by buyers and sellers.
- **Delta:** net buying minus net selling.

### Concepts you may hear

- **Absorption:** heavy selling hits a level, but price does not fall, suggesting a large buyer is absorbing it.
- **Iceberg orders:** large orders hidden behind a small visible size.

### Reality for a retail trader

Order flow has real value when you have fast, complete data on a centralised market. Retail traders usually have delayed data, thin views, and can't see where a dark pool or an OTC trade happened. In forex especially, no retail trader sees the whole flow.

**Spoofing**, placing large orders with no intention of letting them fill, is illegal in many markets. But it means a book can show orders that disappear.
""".strip(),
    charts=(
        Chart(
            title="Net buying pressure through a session",
            caption="Illustrative data of net buying (delta) over 12 periods of a day. A rising sum suggests aggressive buyers are in control. It describes the past.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Cumulative net buying",
            x_label="Periods",
            x_labels=tuple(str(i) for i in range(1, 13)),
            series=(
                Series("Cumulative delta", (0, 3, 6, 4, 9, 14, 13, 18, 22, 20, 26, 30), "accent"),
            ),
        ),
    ),
    steps=(
        "Ask what data you actually have, and how complete it is.",
        "If you trade a central market, learn to read the book and the tape.",
        "Practise on a demo account for weeks before risking money.",
        "Use order flow as a final check at a level you already care about.",
        "Be sceptical of indicators claiming to show 'institutional flow' on retail forex.",
    ),
    example_md="""
A futures trader plans to buy a dip at a support zone at 4,800. As price reaches 4,801, the tape shows heavy selling, but the price is not going lower and the visible bids keep refilling. That is **absorption**, a hint that a large buyer may be there.

The trader enters with a stop at 4,795. It may work, or the buyer may stop and the level may break. Order flow gave a clue, and the stop handles the case where the clue was wrong.
""".strip(),
    mistakes=(
        "Paying for 'order flow' indicators on retail forex that cannot see true flow.",
        "Reading one absorption event as a guarantee.",
        "Forgetting that market makers and bots can change what you see in an instant.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Order flow has serious academic support in explaining *prices* (Evans and Lyons), and it is central to professional market making. Whether a retail trader with partial data can turn it into profit after costs is much less clear, and we found no independent evidence that retail order-flow tools beat simple alternatives.
""".strip(),
    ),
    try_it="Watch a depth-of-market view for 30 minutes on a demo. Write down what you can and cannot figure out from it.",
    quiz=(
        Q(
            "What is absorption?",
            (
                "A large player taking heavy opposite-side flow without price moving",
                "A type of fee",
                "A candle shape",
            ),
            0,
            "It hints at a large player, but it is not a guarantee.",
        ),
        Q(
            "Why is order flow less useful for retail forex?",
            (
                "Forex has no central exchange, so retail sees only a slice",
                "Forex is too slow",
                "It is illegal",
            ),
            0,
            "Flow data is partial and broker-specific.",
        ),
    ),
    takeaways=(
        "Order flow shows who is pressing the market.",
        "It needs fast, complete data.",
        "Retail views are usually partial.",
    ),
    sources=("evans-lyons-2002",),
)

# ---------- structure and retail theories ----------

_swing = path(
    [
        (0, 100),
        (6, 104),
        (10, 102),
        (16, 106),
        (20, 103.5),
        (26, 108),
        (32, 104.5),
        (38, 103),
        (44, 100),
    ],
    seed=96,
    noise=0.15,
)
_swc = _swing.closes

_STRUCTURE = Lesson(
    slug="market-structure/swings-bos-choch",
    title="Market structure: swings, BOS and CHoCH",
    summary="Read the trend from the shape of the swings.",
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
    figures=(Figure("market-structure-swings", "Swings labelled HH, HL, LH and LL."),),
    goal="Label market structure and tell the difference between a warning and a confirmation.",
    body_md="""
"Market structure" simply means reading the trend from the shape of the zig-zags.

- A **swing high** is a peak: a candle higher than the ones around it.
- A **swing low** is a trough: a candle lower than the ones around it.

Compare each swing with the one before it:

- **HH**, a higher high. **HL**, a higher low.
- **LH**, a lower high. **LL**, a lower low.

**Uptrend = HH and HL. Downtrend = LH and LL. Mixed = no clear structure.**

### BOS and CHoCH

- A **Break of Structure (BOS)** is when price breaks past the last swing in the direction of the trend. In an uptrend, pushing above the previous higher high. It says the trend continues.
- A **Change of Character (CHoCH)** is the first crack in the pattern. In an uptrend, the first lower low.

Note the honest order: a **CHoCH is an early warning**. Only a follow-up **BOS in the new direction** suggests a reversal. Many CHoCHs are just deep pullbacks.

Reading structure tells you the trend's *shape*, not its *future*.
""".strip(),
    charts=(
        candle_chart(
            _swing,
            title="Structure turning from up to down",
            caption="Illustrative prices. Higher highs and lows until the first lower low at 104.5 breaks the pattern. A later lower low confirms the new direction.",
            marks=(
                Mark(6, _swc[6], "HH", "accentSoft"),
                Mark(10, _swc[10], "HL", "accent", "up"),
                Mark(16, _swc[16], "HH", "accentSoft"),
                Mark(20, _swc[20], "HL", "accent", "up"),
                Mark(26, _swc[26], "HH", "accentSoft"),
                Mark(32, _swc[32], "CHoCH", "warn", "up"),
                Mark(44, _swc[44], "BOS down", "danger", "up"),
            ),
        ),
    ),
    steps=(
        "Mark the swing highs and lows with a fixed rule.",
        "Label each one HH, HL, LH or LL.",
        "State the current structure in one sentence.",
        "Note the level that would be a CHoCH, and the level that would be a BOS.",
        "Plan your trade around those levels.",
    ),
    example_md="""
EUR/USD daily: last swings were HL 1.0750, HH 1.0900, HL 1.0820. The uptrend is intact.

A **CHoCH** would be a close below 1.0820. You note: "If that happens, I stop buying dips."

If after a CHoCH a rally fails at 1.0880 and price then breaks 1.0760, that is a **BOS** down. You now consider sell setups. The labels organise your thinking, and they do not tell you what happens next.
""".strip(),
    mistakes=(
        "Marking swings by feel, in a way that fits your bias.",
        "Treating every CHoCH as a confirmed reversal.",
        "Forgetting that swings depend on the timeframe you use.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
These labels are a way of describing trend, and the evidence for trends in the broad sense (momentum) is good. "BOS" and "CHoCH" as specific signals have, to our knowledge, not been tested in reliable independent studies. Use them as descriptions.
""".strip(),
    ),
    try_it="Mark the swings on 60 candles and write 'HH', 'HL', etc. Then state the structure and the level that would change your mind.",
    quiz=(
        Q(
            "In a healthy uptrend, price suddenly makes a LOWER low for the first time. This is called a…",
            (
                "Break of Structure confirming the uptrend",
                "Change of Character (an early warning)",
                "Marubozu",
            ),
            1,
            "A first lower low is a warning. A later BOS down would confirm.",
        ),
        Q(
            "What is a Break of Structure in an uptrend?",
            ("A break above the previous higher high", "Any red candle", "Volume dropping"),
            0,
            "It confirms the trend is continuing.",
        ),
    ),
    takeaways=(
        "Structure is the shape of the swings.",
        "CHoCH is a warning; BOS is a confirmation.",
        "Structure describes, it does not predict.",
    ),
    sources=("moskowitz-2012",),
)

_SMC = Lesson(
    slug="smart-money/what-smc-is",
    title="Smart Money Concepts: the honest introduction",
    summary="A popular way of talking about charts, and what can and cannot be claimed for it.",
    est_minutes=7,
    key_concepts=(
        "smart money",
        "institutional",
        "narrative",
        "unfalsifiable",
        "honest skepticism",
    ),
    figures=(Figure("risk-vs-predict", "A good story is not the same as a measurable edge."),),
    goal="Understand the language of Smart Money Concepts without believing it blindly.",
    body_md="""
**Smart Money Concepts (SMC)** is a popular online way of reading charts. You will hear words such as *order blocks*, *liquidity* and *fair value gaps*. This book teaches them so you understand the language.

### The story SMC tells

Big institutions ("smart money") cannot buy or sell huge positions without moving price, so they supposedly engineer moves to trap small traders, take their orders as **liquidity**, and fill their own positions at good prices. SMC is a set of names for the footprints those institutions supposedly leave.

### What is useful about it

- It makes you think about **where other traders' stops sit**.
- It gives you precise words for chart features.
- It pushes you to wait for confirmation.

### The honest warning

- Most SMC ideas are **descriptive, not predictive**. After a move, you can always point at an "order block" that "caused" it. Doing that before the move, reliably, is the part nobody has proved.
- Many SMC claims are **unfalsifiable**: vague enough that any outcome can be explained. That is a red flag in any field.
- We know of no published, independent study showing SMC beats a simple baseline after costs.

Use SMC as vocabulary. Treat it as context. Combine it with risk management, which *is* proven to matter.
""".strip(),
    charts=(
        candle_chart(
            random_walk(40, seed=33, start=100, vol=0.8),
            title="Random data still has 'order blocks'",
            caption="Simulated coin-flip prices. Any dip before a rally can be labelled an 'order block' after the fact. A label after a move is not a prediction.",
        ),
    ),
    steps=(
        "Learn the vocabulary, so you understand what others are saying.",
        "For any SMC idea, write a rule that could be tested.",
        "Test it on data you have not used to learn the idea.",
        "Compare with a simple benchmark such as a moving-average trend filter.",
        "Treat what remains as context, or discard it.",
    ),
    example_md="""
A popular video says: "Buy the last down candle before a strong rally. That is the order block."

Turn that into a rule: *In an uptrend on the 4-hour chart, when a candle closes above the prior 5-candle high, the last down candle before it is the order block. Place a buy limit at its high. Stop at its low.*

Now you can count the outcomes on 500 instances. Many order-block claims quietly disappear once they have to be written down this way.
""".strip(),
    mistakes=(
        "Treating SMC as a secret method because it uses technical words.",
        "Labelling the past and calling it prediction.",
        "Paying for SMC signal groups without seeing audited, complete results.",
    ),
    evidence=Evidence(
        Verdict.UNTESTED,
        """
We found no independent study showing SMC methods beat a simple benchmark after costs. Many of its ideas restate older concepts: support and resistance, stop clustering, buying low within a range. Those older concepts have mixed evidence. The SMC branding adds new words, and adds no proven predictive power.
""".strip(),
    ),
    try_it="Find one SMC 'setup' on social media. Write it as a precise rule. Could you test it, or is it too vague? That answer is useful either way.",
    quiz=(
        Q(
            "What is the honest way to treat Smart Money Concepts?",
            (
                "As a secret system that guarantees wins",
                "As useful vocabulary, helpful for context but unproven as an edge",
                "As proof that retail traders always lose",
            ),
            1,
            "SMC offers useful words, not proven edge.",
        ),
        Q(
            "Why are vague SMC explanations a problem?",
            (
                "They can explain any outcome, so they cannot be tested",
                "They are too long",
                "They use too many colours",
            ),
            0,
            "A claim that cannot fail cannot be tested.",
        ),
    ),
    takeaways=(
        "SMC is vocabulary, not a proven method.",
        "A label after the fact is not a prediction.",
        "Turn any claim into a testable rule.",
    ),
)

_sweep = path(
    [(0, 100), (10, 103), (16, 101.5), (22, 103), (24, 103.6), (28, 100.8), (38, 98)],
    seed=101,
    noise=0.15,
)

_SWEEP = Lesson(
    slug="smart-money/liquidity-sweeps-stophunts",
    title="Liquidity, sweeps and stop hunts",
    summary="The SMC idea with the most real substance behind it.",
    est_minutes=7,
    key_concepts=("liquidity", "liquidity sweep", "stop hunt", "equal highs", "equal lows"),
    figures=(Figure("liquidity-pools", "Stops cluster just beyond obvious levels."),),
    goal="Know where stops tend to cluster, and how a sweep can trap traders.",
    body_md="""
This is the SMC idea with the most real substance, because it rests on a true point: **stop orders cluster in obvious places.**

**Liquidity** here means orders waiting to be filled. Where do lots of orders wait?

- Above an obvious **swing high** or **resistance**: the stops of everyone who sold, and the buy orders of breakout traders.
- Below an obvious **swing low** or **support**: the stops of those who bought, plus breakout sellers.
- **Equal highs or lows:** when two peaks sit at nearly the same level, stops pile up especially thickly beyond them.

A big player who needs to buy a lot wants many sell orders to trade against, and stop orders provide them.

### The sweep

A **liquidity sweep** or **stop hunt** is when price makes a brief, sharp poke beyond an obvious level, triggering those stops, and then reverses.

### How to use this carefully

- Be suspicious of clean breakouts through obvious levels, especially on a spike that immediately reverses.
- Place your stop a little further from the obvious level than everyone else.
- Wait for the snap-back and confirmation, rather than chasing the poke.

### The honest limit

You can usually only name a sweep **afterwards**. At the time, a sweep and a real breakout look identical. So this is risk awareness rather than a signal.
""".strip(),
    charts=(
        candle_chart(
            _sweep,
            title="A sweep above an obvious high",
            caption="Illustrative prices. Equal highs at 103 attract stop orders. Price pokes through and reverses. At the time, this looks the same as a real breakout.",
            hlines=(HLine(103, "Equal highs", "warn"),),
            marks=(Mark(24, 103.6, "Sweep", "danger"),),
        ),
    ),
    steps=(
        "Identify the most obvious highs and lows on your timeframe.",
        "Ask where most stops would be placed.",
        "Place your own stop further away, if your size still allows it.",
        "Treat clean spikes through obvious levels with suspicion.",
        "Plan your response before it happens.",
    ),
    example_md="""
Two equal highs at **1.0900** on the 4-hour chart. You are short from 1.0870. Most people would place their stops at 1.0905 or 1.0910.

You place yours at **1.0930**, accepting a smaller position size to keep the same dollar risk. Price spikes to 1.0918 and reverses. You survive the sweep.

But if the breakout is real, you lose more per unit, which is why your position had to be smaller in the first place.
""".strip(),
    mistakes=(
        "Treating every reversal as a stop hunt aimed at you.",
        "Placing your stop exactly where everyone else does.",
        "Selling every breakout because 'it might be a sweep'.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Stop clustering around obvious levels is a reasonable and widely reported idea, and brief spikes through such levels do happen. What is not established is that any retail trader can reliably distinguish a sweep from a real breakout in real time. We found no independent test of this as a profitable strategy.
""".strip(),
    ),
    try_it="Find the last few spikes above obvious highs on a chart. For each, write what happened next. How many reversed? How many continued?",
    quiz=(
        Q(
            "Price spikes just above an obvious resistance where many stops sat, triggers them, then immediately drops back. This is a…",
            ("Breakout to buy into", "Liquidity sweep", "Marubozu"),
            1,
            "A quick poke that triggers stops and reverses is called a sweep.",
        ),
        Q(
            "What is the best use of this idea?",
            (
                "A reliable entry signal",
                "Risk awareness when placing stops",
                "A way to predict news",
            ),
            1,
            "It helps you place stops. You usually can only name it afterwards.",
        ),
    ),
    takeaways=(
        "Stops cluster beyond obvious levels.",
        "Sweeps look like breakouts until after the fact.",
        "Use this to place stops better.",
    ),
)

_BLOCKS = Lesson(
    slug="smart-money/blocks-fvg-premium",
    title="Order blocks, fair value gaps and premium/discount",
    summary="The rest of the SMC dictionary, with the old ideas underneath.",
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
    figures=(Figure("smc-blocks", "Blocks, gaps and the premium/discount map."),),
    goal="Know what each SMC term means, and see which older idea it restates.",
    body_md="""
### The block family

- **Order block:** the last candle or cluster before a big, sharp move. The idea is that big players placed orders here and may defend it.
- **Breaker block:** an order block that failed and was broken. It is expected to flip role.
- **Mitigation block:** a zone where a big player supposedly returns to manage a position.

All three are variations of one familiar idea: **old areas where price reacted can matter again.** That is support and resistance.

### Fair value gap (FVG)

A **fair value gap**, or **imbalance**, appears when price moves so fast that three consecutive candles leave a gap between the wicks of the first and third. The theory says markets often return to "fill" the gap. Sometimes that happens. Often it does not.

### Premium and discount

Take any recent swing and find its midpoint, called **equilibrium**. The upper half is **premium** and the lower half is **discount**. SMC traders prefer to sell in premium and buy in discount. This is a tidy version of an old instinct: buy low, sell high within the range.

### The through-line

Strip away the branding and most SMC tools reduce to three older ideas: support and resistance zones matter, stops cluster at obvious levels, and it is better to buy low and sell high inside a range than to chase. Those ideas have mixed but real discussion behind them.
""".strip(),
    charts=(
        candle_chart(
            path([(0, 100), (8, 102), (12, 106), (22, 104), (36, 112)], seed=107, noise=0.12),
            title="An 'order block' and an imbalance, labelled",
            caption="Illustrative prices. The base before a sharp rise is what SMC calls an order block. Labelling it after the rise is easy.",
            zones=(
                Zone(101.2, 102.6, "'Order block'", "accent", 7, 12),
                Zone(103, 105.5, "'Imbalance'", "warn", 10, 13),
            ),
        ),
    ),
    steps=(
        "Learn the names of the zones.",
        "Translate each into support and resistance, gaps or range position.",
        "Define the idea as a rule you can test.",
        "Require a tested reason before you trade it.",
        "Keep your risk sizing the same no matter what you call the zone.",
    ),
    example_md="""
A trader sees a sharp rally from 1.0800 to 1.0870, then a pullback. They label the last down candle before the rally at 1.0800–1.0810 as an order block and buy a limit at 1.0810 with a stop at 1.0795.

An older description of this is: "buy a pullback into the base of the last strong move." The trade is exactly the same either way. Whether it has an edge can only be measured, and renaming it does not change that.
""".strip(),
    mistakes=(
        "Assuming a new word means a new edge.",
        "Marking every candle as some kind of block.",
        "Believing gaps must always be filled.",
    ),
    evidence=Evidence(
        Verdict.UNTESTED,
        """
We found no independent testing of order blocks, breaker blocks or fair value gaps as predictive tools. They are close relatives of support and resistance, which has mixed evidence.

If you want to use one, test it. Compare with a simple level and a random level, including costs.
""".strip(),
    ),
    try_it="Find one 'fair value gap' on a chart. Write down how many of them in the last 100 bars got filled within 20 bars. Then decide if this is useful.",
    quiz=(
        Q(
            "A fast move leaves a gap between the wicks of three candles. SMC calls this…",
            ("Order block", "Fair value gap", "Point of control"),
            1,
            "A fast move skipping prices creates a fair value gap.",
        ),
        Q(
            "What older idea do order blocks mostly restate?",
            ("Support and resistance", "Moving averages", "Carry"),
            0,
            "An old area that price reacted to may matter again.",
        ),
    ),
    takeaways=(
        "SMC terms restate older ideas in new words.",
        "None have strong independent testing.",
        "Renaming a level does not create an edge.",
    ),
)

_wy = path(
    [(0, 110), (10, 100), (20, 104), (30, 100.5), (40, 104), (48, 101), (58, 112)],
    seed=112,
    noise=0.2,
)

_WYCKOFF = Lesson(
    slug="ta/wyckoff",
    title="Wyckoff: accumulation and distribution",
    summary="An old framework that SMC borrows heavily from.",
    est_minutes=7,
    key_concepts=("Wyckoff", "accumulation", "distribution", "spring", "upthrust"),
    goal="Understand the Wyckoff framework and where it is useful.",
    body_md="""
**Richard Wyckoff** developed his market method in the early 1900s. He described markets as if run by a single **composite operator**: an imagined big player who buys cheaply and sells dear.

He said prices move through four phases:

1. **Accumulation:** a sideways range after a fall, where big players are said to be buying.
2. **Markup:** an uptrend.
3. **Distribution:** a sideways range after a rise, where big players are said to be selling.
4. **Markdown:** a downtrend.

### The key events

- A **spring** is a brief drop below the bottom of an accumulation range that quickly reverses.
- An **upthrust** is the opposite: a brief rise above the top of a distribution range that fails.

If that sounds familiar, you have seen it in the SMC lesson under the name **liquidity sweep**. Wyckoff described similar ideas long ago.

### The problem

The method needs judgement. Two skilled readers can label the same chart differently. The "composite operator" is a teaching story and not a real person.
""".strip(),
    charts=(
        candle_chart(
            _wy,
            title="Wyckoff accumulation, labelled",
            caption="Illustrative prices. A range after a fall, a spring below the range, and a markup. Labels are easy to apply afterwards.",
            zones=(Zone(100, 104, "Range", "accent", 10, 48),),
            marks=(
                Mark(30, 100.5, "Spring", "accentSoft", "up"),
                Mark(58, 112, "Markup", "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Identify a clear range after a strong move.",
        "Ask whether volume and price action suggest buying or selling.",
        "Look for a spring or upthrust near the edge of the range.",
        "Plan a trade with the stop beyond the extreme.",
        "Test your rules on past ranges, including the failures.",
    ),
    example_md="""
A stock falls from $40 to $25, then trades between $25 and $28 for three months. It briefly drops to $24.60, then closes back above $25 on rising volume. A Wyckoff reader calls this a **spring**.

A trade: buy at $25.20, stop at $24.40. Target the top of the range at $28, and then look to hold for more if price breaks out.

If it instead falls through $24.40, you take a planned loss. A range can resolve downward just as easily.
""".strip(),
    mistakes=(
        "Labelling a range as accumulation just because you want it to go up.",
        "Assuming a composite operator is really steering the market.",
        "Using Wyckoff labels without a stop.",
    ),
    evidence=Evidence(
        Verdict.UNTESTED,
        """
We did not find rigorous independent tests of the Wyckoff method as a whole. Most sources are teaching materials or practitioner reports. It is useful as a way to organise what you see, and the risk approach it teaches is sensible. It is not a proven predictive system.
""".strip(),
    ),
    try_it="Take a range on a chart. Decide if you think it is accumulation or distribution, before looking at what happened next. Then check.",
    quiz=(
        Q(
            "In Wyckoff's framework, what is a spring?",
            ("A brief drop below a range that reverses", "A strong uptrend", "A type of indicator"),
            0,
            "A spring is a false breakdown of an accumulation range.",
        ),
        Q(
            "What is the main weakness of Wyckoff analysis?",
            (
                "It is subjective and hard to test",
                "It is too mathematical",
                "It is banned by regulators",
            ),
            0,
            "Different readers can label the same chart differently.",
        ),
    ),
    takeaways=(
        "Wyckoff describes accumulation, markup, distribution and markdown.",
        "SMC reuses many Wyckoff ideas.",
        "It is useful for organising your thinking, unproven as a predictive system.",
    ),
)

# ---------- grand theories ----------

_ew = path(
    [
        (0, 100),
        (6, 106),
        (10, 103),
        (20, 114),
        (24, 110.5),
        (32, 118),
        (36, 113),
        (40, 116),
        (48, 108),
    ],
    seed=117,
    noise=0.12,
)
_ew_c = _ew.closes

_ELLIOTT = Lesson(
    slug="ta/elliott-wave",
    title="Elliott Wave",
    summary="A beautiful theory that is hard to test and easy to fit to any chart.",
    est_minutes=8,
    key_concepts=("Elliott Wave", "impulse", "corrective wave", "wave count"),
    goal="Understand Elliott Wave and why you should be careful with its predictions.",
    body_md="""
**Elliott Wave theory**, proposed by R. N. Elliott in the 1930s, says markets move in repeating wave patterns driven by crowd psychology.

### The basic pattern

- A **five-wave impulse** in the direction of the trend: waves 1, 3 and 5 advance; waves 2 and 4 pull back.
- A **three-wave correction**, usually labelled A, B and C, against the trend.

Common rules: wave 2 cannot retrace beyond the start of wave 1, wave 3 cannot be the shortest impulse wave, and wave 4 should not overlap wave 1. Fibonacci ratios are often used to project wave lengths.

### The central problem

Waves are identified by a person, and several valid "counts" can exist at the same moment. When a forecast fails, the usual response is to change the count. A theory that can always be re-counted to fit any price path is very hard to test.

### How to use it sensibly

If you find it helps you think about phases, treat it as a story. The real decisions should still come from defined risk, levels, and a plan.
""".strip(),
    charts=(
        candle_chart(
            _ew,
            title="A textbook wave count",
            caption="Illustrative prices. Five waves up, three waves down. Real charts almost never look this clean, and several counts usually fit.",
            marks=(
                Mark(6, _ew_c[6], "1", "accent"),
                Mark(10, _ew_c[10], "2", "muted", "up"),
                Mark(20, _ew_c[20], "3", "accent"),
                Mark(24, _ew_c[24], "4", "muted", "up"),
                Mark(32, _ew_c[32], "5", "accent"),
                Mark(36, _ew_c[36], "A", "danger", "up"),
                Mark(40, _ew_c[40], "B", "warn"),
                Mark(48, _ew_c[48], "C", "danger", "up"),
            ),
        ),
    ),
    steps=(
        "Learn the basic pattern, so you understand what people mean.",
        "If you use a count, write down the exact price at which it would be wrong.",
        "Always keep a stop that does not depend on the count.",
        "Keep a record of your predictions.",
        "Check how often your count needed to change.",
    ),
    example_md="""
A trader counts five waves up in EUR/USD finishing at **1.1000** and expects an ABC correction to about 1.0850.

They short at 1.0980 with a stop at 1.1030. A week later price reaches 1.1050. The count was wrong. Many traders would now simply "re-label" the waves and keep the same trade. A disciplined trader takes the 1R loss: the stop was the plan, the wave count was only a guess.
""".strip(),
    mistakes=(
        "Re-counting waves whenever the forecast fails.",
        "Treating a wave count as a fact.",
        "Trading without a stop because 'wave 5 still has to come'.",
    ),
    evidence=Evidence(
        Verdict.UNTESTED,
        """
We did not find a rigorous, independent test showing Elliott Wave forecasts beat chance. The main difficulty is that waves are identified subjectively, and there are usually several legitimate counts. The Fibonacci part of the theory is also weakly supported (see the Fibonacci lessons).

Elliott Wave may give a story that helps some traders organise what they see. It should not be treated as a method for predicting markets.
""".strip(),
    ),
    try_it="Before you look at the next month of a chart, count waves and write your forecast. Then check. Also count how many alternative counts you considered.",
    quiz=(
        Q(
            "Why is Elliott Wave so hard to test?",
            (
                "It needs special data",
                "Several counts can fit, and counts are changed when wrong",
                "It only works on weekends",
            ),
            1,
            "A theory that can always be re-counted is hard to test.",
        ),
        Q(
            "What should be independent of a wave count?",
            ("Your stop-loss", "Your chart colour", "Your broker"),
            0,
            "If the count is wrong, the stop limits the damage.",
        ),
    ),
    takeaways=(
        "Elliott Wave is a popular story of market waves.",
        "Counts can be changed after failures, so it is hard to test.",
        "Keep your risk independent of the count.",
    ),
    sources=("batchelor-2006",),
)

_ichi = path([(0, 100), (15, 106), (25, 103), (40, 112), (55, 106)], seed=121, noise=0.25)
_ichi_high = _ichi.highs
_ichi_low = _ichi.lows


def _mid(highs: tuple[float, ...], lows: tuple[float, ...], n: int) -> tuple[float | None, ...]:
    out: list[float | None] = []
    for i in range(len(highs)):
        if i + 1 < n:
            out.append(None)
        else:
            out.append((max(highs[i + 1 - n : i + 1]) + min(lows[i + 1 - n : i + 1])) / 2)
    return tuple(out)


_ICHIMOKU = Lesson(
    slug="ta/ichimoku",
    title="Ichimoku",
    summary="An all-in-one Japanese indicator, explained clearly.",
    est_minutes=7,
    key_concepts=("Ichimoku", "tenkan-sen", "kijun-sen", "senkou span", "kumo"),
    goal="Understand the parts of the Ichimoku chart and how it is used.",
    body_md="""
**Ichimoku Kinko Hyo** means roughly "one glance equilibrium chart". It was developed in Japan and puts several lines on one chart.

- **Tenkan-sen:** midpoint of the last 9 periods' high and low.
- **Kijun-sen:** midpoint of the last 26 periods.
- **Senkou Span A:** the average of Tenkan and Kijun, plotted 26 periods ahead.
- **Senkou Span B:** the midpoint of the last 52 periods, also plotted 26 periods ahead.
- The area between the two Senkou lines is the **cloud** (Kumo).
- **Chikou span:** the current close plotted 26 periods back.

### Common reading

- Price above the cloud: bullish backdrop.
- Price below the cloud: bearish backdrop.
- Thick clouds are seen as stronger areas of support or resistance.
- A Tenkan cross above Kijun is treated as a signal.

### Limits

The settings were developed for a six-day Japanese week many decades ago. The chart is busy. And in choppy markets, signals flip often.
""".strip(),
    charts=(
        candle_chart(
            _ichi,
            title="Tenkan and Kijun on price",
            caption="Illustrative prices, real 9 and 26-period midpoint calculations. The cloud is omitted here for clarity.",
            series=(
                Series("Tenkan-sen (9)", _mid(_ichi_high, _ichi_low, 9), "accent"),
                Series("Kijun-sen (26)", _mid(_ichi_high, _ichi_low, 26), "warn"),
            ),
        ),
    ),
    steps=(
        "Add the Ichimoku tool to your chart.",
        "Note whether price is above, below or inside the cloud.",
        "Use that as a broad filter.",
        "Do not trade cross signals on their own.",
        "Test with fixed rules, and be sceptical of the default settings.",
    ),
    example_md="""
On a daily chart, EUR/USD trades above the cloud and Tenkan has crossed above Kijun.

A trader treats this as permission to look for buys only. They do not buy immediately. They wait for a pullback to the Kijun-sen line and place a stop below the cloud.

Note the filter here does the same kind of job as a moving average: it tells you which side to prefer, without telling you when to enter.
""".strip(),
    mistakes=(
        "Using all five lines as five separate signals.",
        "Assuming old default settings fit every market.",
        "Taking cross signals in sideways markets.",
    ),
    evidence=Evidence(
        Verdict.UNTESTED,
        """
We found no strong peer-reviewed out-of-sample tests of Ichimoku. One retail backtest on EUR/USD showed a good result but was a single market and period with no out-of-sample check, so it is very weak evidence. Treat claims about Ichimoku as unproven.
""".strip(),
    ),
    try_it="Add Ichimoku to a chart of your market. Compare, over the last year, how often 'above the cloud' agreed with a 100-period moving average filter. Was the extra complexity needed?",
    quiz=(
        Q(
            "Price above the Ichimoku cloud is usually read as…",
            ("A bullish backdrop", "A certain buy", "A market closure"),
            0,
            "It is treated as a broad filter, like a moving average.",
        ),
        Q(
            "Why be careful with the default Ichimoku settings?",
            (
                "They were designed for a six-day Japanese week and may not fit your market",
                "They are illegal",
                "They only suit crypto",
            ),
            0,
            "Defaults are history, not science.",
        ),
    ),
    takeaways=(
        "Ichimoku is a set of midpoint lines and a cloud.",
        "It works as a broad filter.",
        "Independent evidence is thin.",
    ),
)

# ---------- together ----------

_CONDITIONS = Lesson(
    slug="orders-conditions/market-conditions",
    title="Reading the weather: market conditions",
    summary="Match your plan to the market. The same plan can win or lose in different weather.",
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
    figures=(Figure("market-conditions", "A map of market weather: volatility and trend."),),
    goal="Label the market's current condition and pick the right approach for it.",
    body_md="""
A good plan in the wrong conditions can still lose. Before entering, look at the market's "weather".

### How much it is moving

- **Volatility:** how much price moves, whatever the direction. It decides how far your stop must be and so how big your position can be.
- **Momentum:** how forcefully price is moving one way.

### How it behaves

- **Trend:** a persistent drift. Trend strategies assume moves continue.
- **Mean reversion:** price stretched far from its average tends to snap back. It is the **opposite** bet to trend, and the skill is knowing which you are in.

### How markets relate

- **Correlation:** how markets move together.

### The frictions

- **Liquidity:** how easily you can trade without moving the price.
- **Spread:** the gap you pay. It widens when liquidity is thin.
- **Slippage:** getting a worse fill than expected, especially around news.

### Match strategy to conditions

Breakouts do best in expanding volatility and die in quiet ranges. Mean reversion prints in a range and gets flattened by a trend. This is why the mentor measures the **regime**, and why it will tell you to stand aside.
""".strip(),
    charts=(
        Chart(
            title="Which plan fits which weather",
            caption="Illustrative judgement, not data: how well each style tends to suit each market condition, 1 (poor) to 5 (good).",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Fit (1–5)",
            bars=(
                Bar("Trend follow: in a trend", 5, "accentSoft"),
                Bar("Trend follow: in a range", 1, "danger"),
                Bar("Mean reversion: in a range", 4, "accentSoft"),
                Bar("Mean reversion: in a trend", 1, "danger"),
                Bar("Breakout: expanding", 4, "accentSoft"),
                Bar("Breakout: quiet", 1, "danger"),
            ),
        ),
    ),
    steps=(
        "Is the market trending or ranging?",
        "Is volatility high, low, rising or falling?",
        "Is liquidity good at this hour?",
        "Choose a plan built for these conditions, or stand aside.",
        "Re-check at the start of each session.",
    ),
    example_md="""
It is Friday afternoon, the market has been in a 60-pip range all week, and a major central bank decision comes next week.

- Trend strategy: poor fit.
- Breakout strategy: wait.
- Spread is wider than usual.

A professional's choice is often "no trade", and writing this in a journal as a decision still counts as work done.
""".strip(),
    mistakes=(
        "Using a trend plan in a range because it worked last month.",
        "Treating 'no trade' as failure.",
        "Ignoring liquidity at the time you trade.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Regime-based thinking is widely used and has some academic backing (Hamilton's regime-switching models; volatility clustering). The evidence that a retail trader can identify regimes early enough to help is less clear. Stage 11 covers regime models.
""".strip(),
    ),
    try_it="Each day for a week, write one line: 'trending or ranging, and volatility high or low'. At the end of the week, check how often you changed your mind.",
    quiz=(
        Q(
            "A strategy that bets price will snap back toward its average is exploiting…",
            ("Momentum", "Mean reversion", "Correlation"),
            1,
            "Mean reversion is the opposite bet to momentum.",
        ),
        Q(
            "Which strategy often struggles in a quiet range?",
            ("Breakout", "Mean reversion", "Standing aside"),
            0,
            "Without volatility, breakouts often fail.",
        ),
    ),
    takeaways=(
        "Match the plan to the conditions.",
        "Trend and mean reversion are opposite bets.",
        "Standing aside is a real choice.",
    ),
    sources=("hamilton-regimes", "mandelbrot-1963"),
)

_TOP_DOWN = Lesson(
    slug="market-study/top-down-workflow",
    title="Top-down: zoom out before you zoom in",
    summary="A simple four-step way to analyse any market.",
    est_minutes=6,
    key_concepts=("multi-timeframe", "context", "setup", "trigger"),
    figures=(Figure("top-down", "From the big picture to the precise entry."),),
    goal="Use a repeatable, top-down process each time you look at a chart.",
    body_md="""
Staring at a 5-minute chart is how you get chopped up. Work top-down.

1. **Higher timeframe (monthly or weekly):** what is the dominant trend? Only fight it with a very good reason.
2. **Daily:** what is the current context? Trending, ranging, near a big level, calm or wild?
3. **Setup:** a location worth trading, such as a pullback into support in an uptrend. A candidate, not yet a trade.
4. **Trigger:** the precise entry and, more importantly, the stop that proves it wrong.

### Why the order matters

Each level sets the context for the next. If the weekly trend is up, a daily pullback is a place to look for buys, not sells. Start from the 5-minute chart and you trade noise with no context.

This app's volatility reading tells you how wide step 4's stop should be today.
""".strip(),
    charts=(
        candle_chart(
            path([(0, 100), (20, 108), (35, 104), (55, 113)], seed=129, noise=0.2),
            title="Top-down on one chart",
            caption="Illustrative prices. The trend is up (step 1), price pulls back to a level (step 2), and a setup forms (step 3).",
            hlines=(HLine(104, "Pullback area", "accent"),),
            marks=(Mark(35, 104, "Setup", "accentSoft", "up"),),
        ),
    ),
    steps=(
        "Write the weekly trend in one word.",
        "Write the daily context in one sentence.",
        "Mark the level where you would look for a trade.",
        "Define the entry and the stop.",
        "Check the size, and decide if it is worth taking at all.",
    ),
    example_md="""
**Weekly:** EUR/USD has made higher highs for 3 months. Trend: up.

**Daily:** pulled back 2% to the area around 1.0850.

**Setup:** near the 1.0850 zone, the last higher low is 1.0820.

**Trigger:** bullish rejection candle on the 4-hour chart, buy 1.0870, stop 1.0815, target 1.1000.

Risk: 55 pips. Reward: 130 pips. 2.4:1 before costs. You now have a plan you can write in a journal, and you know where it fails.
""".strip(),
    mistakes=(
        "Starting on a small timeframe.",
        "Treating the trigger as more important than the plan's context.",
        "Fighting a higher timeframe trend without a very good reason.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Using a larger trend as a filter is supported in general by the time-series momentum research cited earlier. The specific four-step process is a practical habit, and we found no controlled study proving it improves returns. Its main value is making you think in the same order every time.
""".strip(),
    ),
    try_it="Run this four-step process on one market every day this week. Write each step in one short line.",
    quiz=(
        Q(
            "Which step comes first?",
            ("The entry trigger", "The higher timeframe trend", "Choosing your lot size"),
            1,
            "Start with the big picture.",
        ),
        Q(
            "A setup is…",
            (
                "A trade already placed",
                "A location worth watching, not yet a trade",
                "A type of order",
            ),
            1,
            "A setup is a candidate. The trigger makes it a trade.",
        ),
    ),
    takeaways=(
        "Zoom out first, then zoom in.",
        "Each level sets the context for the next.",
        "The stop is part of the trigger.",
    ),
    sources=("moskowitz-2012",),
)

CHAPTERS = (
    chapter(
        "technical",
        "levels-and-lines",
        "Levels and lines",
        "Support, resistance, trendlines, Fibonacci and pivots.",
        (_SUPPORT, _TRENDLINES, _FIB_INTRO, _FIB_RETRACE, _FIB_EXT, _PIVOTS),
    ),
    chapter(
        "technical",
        "chart-patterns",
        "Chart patterns",
        "Reversal and continuation shapes, and what is actually known about them.",
        (_REVERSAL, _CONTINUATION),
    ),
    chapter(
        "technical",
        "indicators",
        "Indicators",
        "Moving averages, RSI, MACD, Bollinger, ATR and VWAP.",
        (_MA, _RSI, _MACD, _BOLLINGER, _ATR, _VWAP),
    ),
    chapter(
        "technical",
        "volume-and-flow",
        "Volume and order flow",
        "How much traded, where it traded, and who pressed the buttons.",
        (_VOLUME, _FLOW),
    ),
    chapter(
        "technical",
        "market-structure",
        "Market structure and retail theories",
        "Swings, Smart Money Concepts and Wyckoff.",
        (_STRUCTURE, _SMC, _SWEEP, _BLOCKS, _WYCKOFF),
    ),
    chapter(
        "technical",
        "grand-theories",
        "Grand theories",
        "Elliott Wave and Ichimoku.",
        (_ELLIOTT, _ICHIMOKU),
    ),
    chapter(
        "technical",
        "putting-it-together",
        "Putting it together",
        "Reading market conditions and working top-down.",
        (_CONDITIONS, _TOP_DOWN),
    ),
)
