"""Stage 3 — Charts and candles."""

from __future__ import annotations

from mentor.domain.curriculum.book._kit import (
    Bar,
    Chart,
    Evidence,
    Figure,
    HLine,
    Lesson,
    Mark,
    Path,
    Q,
    Verdict,
    Zone,
    candle_chart,
    chapter,
    fact,
)
from mentor.domain.curriculum.charts import path, random_walk

_hourly = path(
    [(0, 100), (12, 104), (20, 101), (32, 107), (45, 103), (60, 110)], seed=3, noise=0.35
)

_TIMEFRAMES = Lesson(
    slug="charts/timeframes-and-chart-types",
    title="Timeframes and chart types",
    summary="Lines, bars and candles, and why the same market can look different on each timeframe.",
    est_minutes=6,
    key_concepts=("timeframe", "line chart", "bar chart", "candlestick chart", "top-down"),
    goal="Choose a chart type and timeframe on purpose rather than by habit.",
    body_md="""
A **chart** is a picture of price over time. Three kinds are common.

- A **line chart** joins the closing prices. It is simple and hides the detail inside each period.
- A **bar chart** shows open, high, low and close as lines on a bar.
- A **candlestick chart** shows the same four numbers but makes the body easy to see. Most traders use it.

A **timeframe** is how much time one candle covers: 1 minute, 1 hour, 1 day, and so on. The same market can look completely different across timeframes. A small dip on the daily chart can be a huge fall on the 5-minute chart.

### What changes as you zoom in

- Smaller timeframes contain much more random noise.
- Spreads and fees are the same in money but much larger compared with small moves.
- Screen time needed goes up a lot.

### What people usually do

They look at a higher timeframe to see the bigger picture and a lower one to choose the entry. This is called **top-down analysis**, and Stage 5 has a full lesson on it. Beginners do best on **4-hour or daily charts**, where there is less noise and more time to think.
""".strip(),
    charts=(
        candle_chart(
            _hourly,
            title="Same data, one candle per period",
            caption="Illustrative prices. If each candle is one day this is two months of trading. If each candle is one minute it is an hour. The picture alone does not tell you which.",
        ),
    ),
    steps=(
        "Pick a timeframe that matches how long you intend to hold a trade.",
        "Use a higher timeframe, about 4 to 6 times longer, to see the larger picture.",
        "Set your chart to candlesticks and show the timeframe label clearly.",
        "Check how many hours a day that timeframe needs you to watch.",
        "Stick to one or two timeframes while you learn.",
    ),
    example_md="""
A swing trader holds for about 3–10 days.

- Uses the **daily chart** to see trend and big levels.
- Uses the **4-hour chart** to pick an entry and a stop.
- Checks charts twice a day and has no need to watch all day.

A 1-minute scalper needs to watch nonstop, and pays the spread on every trade. A 1-pip spread on a 3-pip target is a third of the profit. On a 50-pip daily target, it is 2%.
""".strip(),
    mistakes=(
        "Flicking between many timeframes until one agrees with what you want to do.",
        "Starting on 1-minute charts, because they look exciting.",
        "Comparing a move on the hourly chart with a level taken from the weekly chart without noting the difference.",
    ),
    evidence=fact(
        "These are ways of displaying the same data. A practical point: shorter timeframes need much more accurate timing to overcome the same costs, which is why Stage 7 treats scalping as a specialised job."
    ),
    try_it="Open the same market on the 5-minute, 1-hour and 1-day charts. Write one sentence on what each one seems to be saying. Notice how often they disagree.",
    quiz=(
        Q(
            "Which chart type shows open, high, low and close with a visible body?",
            ("Line chart", "Candlestick chart", "Neither"),
            1,
            "Candlesticks show the four prices and make the body easy to see.",
        ),
        Q(
            "Why are short timeframes harder for beginners?",
            (
                "They contain more noise and costs matter more",
                "Spreads are always illegal on them",
                "They need more leverage",
            ),
            0,
            "More noise, and the same spread is a much bigger share of a small move.",
        ),
    ),
    takeaways=(
        "A timeframe is how long one candle lasts.",
        "Smaller timeframes have more noise and a bigger cost burden.",
        "Use a higher timeframe for context and a lower one for the entry.",
    ),
)

_DIRECTION = Lesson(
    slug="chart-language/direction-words",
    title="Bullish, bearish, long, short",
    summary="The vocabulary of direction, and how to name your bias and when it is wrong.",
    est_minutes=5,
    key_concepts=("bullish", "bearish", "long", "short", "rally", "sell-off"),
    figures=(Figure("bull-bear", "Bulls expect up. Bears expect down."),),
    goal="Use direction words correctly and always pair your view with where it would be wrong.",
    body_md="""
Before anything else, traders name the direction.

- **Bullish** means you expect the price to **rise**. A bull attacks upwards with its horns. A **rally** is a strong move up.
- **Bearish** means you expect the price to **fall**. A bear swipes down. A **sell-off** is a sharp move down.
- **Long** means a trade that **gains if the price rises**. You bought.
- **Short** means a trade that **gains if the price falls**. You sold first and plan to buy back cheaper.

### How to use it

Direction words are a **bias**, a leaning, not a forecast. Say it out loud before every trade:

> "I am bullish on EUR/USD, so I am looking for buys on a pullback. I am wrong if it breaks below the last swing low."

Naming your bias *and the place it is wrong* is what separates a plan from a hope.
""".strip(),
    charts=(
        candle_chart(
            path([(0, 1.08), (10, 1.09), (16, 1.085), (30, 1.10)], seed=6, noise=0.25),
            title="A bullish bias, and where it is wrong",
            caption="Illustrative prices. A bias is only useful with a line that says 'I was wrong'.",
            hlines=(HLine(1.0850, "I am wrong below here", "danger"),),
            marks=(Mark(30, 1.10, "Bullish idea", "accentSoft", "down"),),
        ),
    ),
    steps=(
        "Look at the chart and decide: bullish, bearish or neutral.",
        "Write the sentence: 'I am ___, so I am looking for ___, and I am wrong if ___.'",
        "Only then look for a trade.",
        "If you cannot say where you are wrong, stay out.",
    ),
    example_md="""
EUR/USD is at 1.0900 and rising. You write:

> "I am bullish. I want a long on a dip towards 1.0860. I am wrong if it closes below 1.0830."

That sentence gives you an entry idea (a pullback), a place for your stop (1.0830 or a little below), and a reason not to trade if the dip never comes. Compare that with "I think it is going up," which gives you nothing to act on.
""".strip(),
    mistakes=(
        "Treating 'bullish' as a prediction that must come true.",
        "Being bullish on the 5-minute chart while the daily trend is sharply down, without knowing it.",
        "Having no price at which the idea is cancelled.",
    ),
    evidence=fact(
        "Vocabulary only. Being able to name a bias does not make it right. This app's own bullish and bearish calls are unproven, and were recently weak."
    ),
    try_it="Look at three charts and write the bias sentence for each. Then come back in a week and see what happened.",
    quiz=(
        Q(
            "You 'go short' EUR/USD. You make money if…",
            ("The euro rises", "The euro falls", "The price stays flat"),
            1,
            "Short means sell first to buy back cheaper, so you gain when the price falls.",
        ),
        Q(
            "What should every bias sentence include?",
            (
                "A target price of the market",
                "Where the idea would be wrong",
                "The size of your account",
            ),
            1,
            "A view without an exit is just a hope.",
        ),
    ),
    takeaways=(
        "Bullish = up. Bearish = down. Long gains on a rise. Short gains on a fall.",
        "A bias is a leaning, not a forecast.",
        "Always state where you would be wrong.",
    ),
)

_uptrend = path(
    [(0, 100), (6, 104), (10, 102), (16, 108), (20, 105.5), (27, 111), (31, 108.5), (38, 114)],
    seed=9,
    noise=0.2,
)
_ups = _uptrend.closes

_TREND = Lesson(
    slug="chart-language/trend-structure",
    title="Trend, uptrend, downtrend and range",
    summary="A trend has an exact definition. Here it is.",
    est_minutes=6,
    key_concepts=("trend", "uptrend", "downtrend", "range", "higher high", "higher low"),
    figures=(Figure("trend-structure", "Trend is a staircase of highs and lows."),),
    goal="Be able to label any chart as an uptrend, a downtrend or a range using a clear rule.",
    body_md="""
A **trend** is the market's direction over time. It has a definition you can check, and it is not a feeling.

- **Uptrend:** a series of **higher highs** and **higher lows**. Each rise goes further, and each dip stops higher. A rising staircase.
- **Downtrend:** **lower highs** and **lower lows**. A falling staircase.
- **Range:** highs and lows are roughly level. Price bounces between a floor and a ceiling.

### How to use it

- The trend holds while the pattern holds. In an uptrend, a dip that stops above the previous low and turns up is a continuation.
- The warning is a **broken structure**. The first time an uptrend makes a lower low, the uptrend is in doubt. That is your signal to tighten stops or stand aside, not to buy the dip without thinking.

"The trend is your friend" really means "trade with the staircase until it stops climbing." Trend and momentum are among the few effects with real evidence, but they are not guarantees, and a lesson in Stage 7 tests them properly.
""".strip(),
    charts=(
        candle_chart(
            _uptrend,
            title="An uptrend is a rising staircase",
            caption="Illustrative prices. Each high is higher than the last, and each low is higher than the last.",
            marks=(
                Mark(6, _ups[6], "HH", "accentSoft"),
                Mark(10, _ups[10], "HL", "accent", "up"),
                Mark(16, _ups[16], "HH", "accentSoft"),
                Mark(20, _ups[20], "HL", "accent", "up"),
                Mark(27, _ups[27], "HH", "accentSoft"),
                Mark(31, _ups[31], "HL", "accent", "up"),
            ),
        ),
    ),
    steps=(
        "Mark the last three swing highs and swing lows.",
        "Are the highs rising and the lows rising? Uptrend.",
        "Are the highs falling and the lows falling? Downtrend.",
        "Are they flat, or mixed? Range or no clear trend.",
        "Mark the most recent higher low. A close below it is your warning.",
    ),
    example_md="""
Swing lows on the daily chart: 1.0700, 1.0760, 1.0820. Swing highs: 1.0880, 1.0950, 1.1010.

Both are rising, so this is an **uptrend**. The most recent higher low is 1.0820.

A week later, price falls and closes at **1.0805**. The structure is broken. That does not prove a downtrend has begun. It proves the uptrend is no longer intact, so your plan should change: fewer longs, tighter stops, or standing aside until a new pattern forms.
""".strip(),
    mistakes=(
        "Calling something a trend because of the last two candles.",
        "Buying dips in a market that has already broken its structure.",
        "Forcing every chart to be a trend. Plenty of the time markets go sideways.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
The definition is a label, but there is real research on trends. Moskowitz, Ooi and Pedersen found significant positive time-series momentum in all 58 liquid futures they tested, across stocks, bonds, currencies and commodities. In plain terms: over the past 12 months, what had been rising tended to keep rising, on average.

Limits to keep in mind: that is an average across many markets over many years, it is not a rule for any single trade, and it does not by itself tell you exactly when to enter.
""".strip(),
    ),
    try_it="Take a daily chart. Mark three swing highs and lows yourself. Label it uptrend, downtrend or range, then name the level that would change your mind.",
    quiz=(
        Q(
            "What actually defines an uptrend?",
            (
                "Price is above a moving average",
                "A series of higher highs and higher lows",
                "RSI is above 70",
            ),
            1,
            "It stays intact until price makes a lower low and breaks that structure.",
        ),
        Q(
            "An uptrend closes below its last higher low. What does this tell you?",
            (
                "The trend has reversed for certain",
                "The uptrend is in doubt and your plan should change",
                "It is a great time to add more",
            ),
            1,
            "A broken structure is a warning. It does not prove a reversal, but it does remove the uptrend reason.",
        ),
    ),
    takeaways=(
        "Uptrend = higher highs and higher lows.",
        "A break of the last higher low is a warning.",
        "Markets also spend long periods in ranges.",
    ),
    sources=("moskowitz-2012",),
)

_range_path = path(
    [(0, 100), (6, 104), (12, 100.5), (19, 103.8), (26, 100.4), (33, 104), (38, 101)],
    seed=14,
    noise=0.25,
)

_DIRECTION_2 = Lesson(
    slug="market-structure/direction-and-trend",
    title="Which way is the market going?",
    summary="Three possible answers, and why 'sideways' is the one most people forget.",
    est_minutes=6,
    key_concepts=(
        "bullish",
        "bearish",
        "neutral",
        "uptrend",
        "downtrend",
        "sideways",
        "range-bound",
    ),
    figures=(Figure("trend-types", "Up, down or sideways: the three shapes every chart takes."),),
    goal="Describe any chart in one of three words, and know when to do nothing.",
    body_md="""
Before anything else, a trader asks one question about a chart: **which way is it going?** There are only three possible answers.

- **Up.** Price keeps making higher peaks and higher dips.
- **Down.** Price keeps making lower peaks and lower dips.
- **Sideways.** Price bounces between a rough ceiling and a rough floor. Traders also call this **range-bound**.

Markets spend a large share of their time going sideways, and that is the condition most beginners ignore.

**Neutral** is also a real position. It means "I have no strong view." For a beginner, neutral often means "not a good time to trade."

### Why this matters

Trading with the direction means the overall current is helping you. Fighting it, buying in a downtrend because it "looks cheap", is how many beginners lose steadily.

In a **range**, the usual trend rules stop working. Breakouts fail often, and trend tools give false signals over and over. Knowing you are in a range is itself a decision: usually stand aside, or use a range plan from Stage 7.

This app measures whether the market is trending or calm, which it calls a **regime**, and it treats direction in choppy markets as close to a coin flip.
""".strip(),
    charts=(
        candle_chart(
            _range_path,
            title="A range: price is going nowhere",
            caption="Illustrative prices. Trend tools give repeated false signals here, because each move stops at the opposite wall.",
            zones=(Zone(103.3, 104.4, "Ceiling", "danger"), Zone(100, 101, "Floor", "accentSoft")),
        ),
    ),
    steps=(
        "Look at the last 30 to 60 candles on your main timeframe.",
        "Decide up, down, or sideways.",
        "If sideways, ask if you have a plan for ranges. If not, stand aside.",
        "If up or down, look for trades in that direction only.",
        "Repeat every session. Direction can change.",
    ),
    example_md="""
You look at the daily EUR/USD chart. For seven weeks the highs have stayed around 1.0950 and the lows around 1.0750. There is no staircase in either direction, so this is a **range** of about 200 pips.

If you buy a breakout at 1.0955, there is a good chance price falls back inside. In this market a trend rule would have you buying highs and selling lows. A range plan would do the opposite, and a no-trade decision is also fine.
""".strip(),
    mistakes=(
        "Assuming the market must be trending because you want to trade.",
        "Calling every small move a new trend.",
        "Ignoring ranges, where most of the frustration happens.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
**Tested:** research shows momentum across many markets on horizons of several months (Moskowitz et al., and Hurst et al. over more than a century).

**Not settled:** identifying a trend *in real time* on your chart is harder than the research suggests, because the research uses mechanical rules. And there is no clean, tested number for how much of the time a market ranges; figures quoted online vary and are usually not properly tested.
""".strip(),
    ),
    try_it="Open five charts. Label each up, down or sideways in one word. If you hesitate, the honest answer is often sideways.",
    quiz=(
        Q(
            "Price keeps making higher peaks and higher dips for weeks. What is this called?",
            ("A downtrend", "An uptrend (bullish)", "A range"),
            1,
            "Higher peaks and higher dips is an uptrend.",
        ),
        Q(
            "You are in a clear range and have no range plan. What is a sensible action?",
            ("Buy the top of the range", "Stand aside", "Double your size"),
            1,
            "Doing nothing is a valid decision. Most trend rules fail in a range.",
        ),
    ),
    takeaways=(
        "Up, down or sideways: there are only three.",
        "Sideways is common, and most beginners ignore it.",
        "No clear direction often means no trade.",
    ),
    sources=("moskowitz-2012", "hurst-2017"),
)

_breakout = path(
    [(0, 100), (10, 103), (14, 101.5), (20, 103), (22, 106), (26, 104.2), (34, 109)],
    seed=18,
    noise=0.15,
)

_MOVES = Lesson(
    slug="chart-language/moves-within-a-trend",
    title="Breakout, pullback and reversal",
    summary="The moves that build every trend, and the most expensive confusion in trading.",
    est_minutes=6,
    key_concepts=("breakout", "pullback", "retracement", "reversal", "consolidation", "fakeout"),
    figures=(Figure("moves-in-trend", "Trends are built from pushes, pauses and pullbacks."),),
    goal="Name each kind of move, and tell a pullback from a reversal using a rule.",
    body_md="""
Zoom in and a trend is built from a few repeating moves.

- **Breakout:** price pushes through a level that had been holding. It often starts a new leg. Beware the **fakeout**, a breakout that fails almost at once.
- **Pullback**, also called a **retracement:** a temporary move against the trend. In an uptrend, a pullback into support is the classic lower-risk buy zone.
- **Consolidation:** price pauses and moves sideways in a tight range.
- **Reversal:** the trend actually turns. An uptrend starts making lower lows.

### The trap

A pullback and a reversal look identical at the start. You cannot tell which one you are in until later. So use a rule instead of a feeling:

- A dip that **holds above the last higher low** and turns up is treated as a **pullback**.
- A dip that **breaks below the last higher low** is treated as a **possible reversal**. Step aside or exit.

That is also why your stop-loss goes beyond the last higher low. The stop is simply the line that says: "If this pullback keeps going, it was actually a reversal, and I am out."
""".strip(),
    charts=(
        candle_chart(
            _breakout,
            title="Breakout, then a pullback that holds",
            caption="Illustrative prices. Price breaks above 103, comes back to test it, holds and continues.",
            hlines=(HLine(103, "Old ceiling at 103", "muted"),),
            marks=(
                Mark(22, 106, "Breakout", "accentSoft"),
                Mark(26, 104.2, "Pullback holds", "accent", "up"),
            ),
        ),
    ),
    steps=(
        "Find the last higher low in the trend.",
        "When the price dips, watch whether it holds above that low.",
        "If it holds and turns back up, treat it as a pullback.",
        "If it closes below, treat it as a possible reversal and leave the trade.",
        "Decide the rule before the trade, not during it.",
    ),
    example_md="""
EUR/USD has been making higher lows, the most recent at **1.0820**. Price pulls back to 1.0835.

- If you buy at 1.0838 with a stop at 1.0815, just under the last higher low, your risk is 23 pips.
- If price turns up and reaches 1.0900, you gain 62 pips, about 2.7R.
- If price breaks below 1.0815, you are out for a planned 1R loss, and you now know the structure is in doubt.

Either way you know the outcome in advance, and the rule made the decision rather than your mood.
""".strip(),
    mistakes=(
        "Buying every breakout without asking how often breakouts fail in this market.",
        "Moving a stop lower 'to give it room' when a pullback becomes a reversal.",
        "Calling every dip a pullback because you want it to be one.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
The words are definitions. Whether acting on them makes money depends on the rules. Lo, Mamaysky and Wang found that computer-detected price patterns carried some extra information about the next moves. That is not the same as showing a profit after costs.

Fakeouts are a real phenomenon, but the exact failure rate of a breakout depends heavily on market, timeframe and definition. Treat any number you read as something to check on your own data.
""".strip(),
    ),
    try_it="Find three pullbacks on a chart. For each, decide using only the rule above whether it was a pullback or a possible reversal at that moment. Then look at what happened next.",
    quiz=(
        Q(
            "A dip that holds above the last higher low, then turns back up, is a…",
            ("Reversal", "Pullback (a continuation)", "Breakout"),
            1,
            "That is a pullback. It becomes a possible reversal only if it breaks below the last higher low.",
        ),
        Q(
            "A breakout that fails and reverses almost at once is called a…",
            ("Fakeout", "Rally", "Marubozu"),
            0,
            "A fakeout traps people who bought the break.",
        ),
    ),
    takeaways=(
        "Trends are built from breakouts, pullbacks and pauses.",
        "A pullback and a reversal look the same at first.",
        "Let the last higher low decide, and place your stop beyond it.",
    ),
    sources=("lmw-2000",),
)

_OBVIOUS = Lesson(
    slug="reading-charts/trend-and-obvious-patterns",
    title="Trend and the fallacy of obvious patterns",
    summary="If a pattern is obvious to you, it is obvious to everyone, including computers.",
    est_minutes=5,
    key_concepts=("trend", "pattern recognition", "efficiency", "noise", "context"),
    figures=(
        Figure(
            "trend-context",
            "Use the chart for context: direction, level, and how wild the bars are.",
        ),
    ),
    goal="Use charts for context and risk decisions, not as a machine that tells the future.",
    body_md="""
A chart pattern that is "clearly" a head and shoulders is also clearly a head and shoulders to every computer with a pattern library. Whatever information the pattern held was priced in very quickly. That is the idea behind market **efficiency**: useful information gets reflected in prices fast, so obvious things tend to stop paying.

The chart is best used for **context**, not as a signal on its own. Three good questions:

1. **Direction:** which way has price been moving on the timeframe I care about?
2. **Location:** are we near a level the market obviously remembers?
3. **Mood:** is the bar size calm or wild?

Use the answers to size the trade and pick the stop. Do not use the chart alone to predict where price goes next.

If you find a pattern that "always works", ask what you are missing. Usually it is one of three things: you are remembering only the wins, you tested on too few examples, or you did not include costs.
""".strip(),
    charts=(
        candle_chart(
            random_walk(45, seed=21, start=100, vol=0.7),
            title="Find the pattern in this chart",
            caption="Simulated coin-flip prices. Any head and shoulders or double top you can see here is pure chance, which is exactly why looks are not evidence.",
        ),
    ),
    steps=(
        "Before looking for signals, ask the three questions: direction, location, mood.",
        "Treat any pattern you find as a question, not an answer.",
        "Define the pattern with exact rules before testing it.",
        "Compare with what the market does at random points.",
        "Only then decide if it is worth trading.",
    ),
    example_md="""
Suppose a pattern is profitable in a backtest with a 53% win rate at 1:1 reward-to-risk, and your costs are about 0.06R per trade.

Break-even win rate = (1 + 0.06) / 2 = **53%**.

So the "profitable" pattern earns approximately **nothing** after costs. It could still look great on a screenshot, and it would still fail as a living.
""".strip(),
    mistakes=(
        "Treating a clear pattern as a reason to enter.",
        "Believing obvious setups stay profitable forever.",
        "Forgetting that the chart cannot tell you about the news that is coming.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
The academic survey by Park and Irwin found that many early tests of technical analysis looked profitable, but most had problems such as data snooping, picking the rules after seeing the results, and not counting costs properly.

Sullivan, Timmermann and White tested a very large set of technical rules on 100 years of Dow data, correcting for having searched through so many, and found the best rules did not hold up well in later data. Neely, Weller and Ulrich found that FX rule profits fade as more traders learn them.

Summary: charts are useful for context and risk. Simple visual signals alone have weak support.
""".strip(),
    ),
    try_it="Pick one pattern you believe in. Write an exact rule that a computer could follow. If you cannot, the pattern is not testable yet.",
    quiz=(
        Q(
            "What is the most honest use of a chart for a beginner?",
            (
                "A machine that says what happens next",
                "Context: direction, location and mood",
                "Proof that a trade will work",
            ),
            1,
            "Charts help you size trades and place stops. They are weak predictors on their own.",
        ),
        Q(
            "A pattern looks profitable in a backtest with no costs. What should you do?",
            ("Trade it", "Add realistic costs and test on unseen data", "Ask a friend"),
            1,
            "Costs and fresh data are the two tests that matter most.",
        ),
    ),
    takeaways=(
        "If a pattern is obvious, it is usually already priced in.",
        "Use charts for direction, location and mood.",
        "A pattern must be tested with exact rules and costs.",
    ),
    sources=("park-irwin-2007", "stw-1999", "neely-2009"),
)

_compression = path(
    [(0, 100), (8, 104), (14, 102), (22, 102.6), (28, 102.3), (32, 107)], seed=25, noise=0.12
)

_PRICE_ACTION = Lesson(
    slug="market-structure/price-action-moves",
    title="How price actually moves: the price-action words",
    summary="Every word traders use for how price pushes, pauses and turns.",
    est_minutes=7,
    key_concepts=(
        "support",
        "resistance",
        "breakout",
        "breakdown",
        "pullback",
        "continuation",
        "consolidation",
        "expansion",
        "compression",
    ),
    figures=(Figure("price-action-map", "The full map of price-action words on one chart."),),
    goal="Know the full vocabulary of how price moves, so that charts become readable.",
    body_md="""
Price never moves in a straight line. It pushes, pauses, pulls back and sometimes turns around. Here is the vocabulary, grouped by what it describes.

### Floors and ceilings

- **Support:** a price floor, where falling prices have often stopped.
- **Resistance:** a price ceiling, where rising prices have often stalled.
- They are **zones**, not exact lines.

### Breaking through

- **Breakout:** price pushes up through a ceiling.
- **Breakdown:** price falls down through a floor.
- Once broken, old support often acts as new resistance, and the other way round.

### Pauses

- **Pullback** or **retracement:** a temporary move against the trend.
- **Continuation:** price resumes the trend after a pause.
- **Consolidation:** a sideways pause in a tight range.

### Energy

- **Expansion:** big wide candles, as volatility rises.
- **Compression:** small tight candles, as volatility falls. Compression often comes before expansion, like a spring winding up.

### The trap

The most expensive confusion is **pullback versus reversal**. They look identical at the start. That is why you never bet the whole account on one call, and why a stop-loss exists.
""".strip(),
    charts=(
        candle_chart(
            _compression,
            title="Compression, then expansion",
            caption="Illustrative prices. Candles get small before a big move. This is a common shape, but compression does not tell you the direction of the next move.",
            zones=(Zone(101.8, 103.2, "Compression", "warn", 14, 28),),
            marks=(Mark(32, 107, "Expansion", "accentSoft"),),
        ),
    ),
    steps=(
        "Identify the main floor and ceiling on your chart.",
        "Label the current phase: trend, pullback, consolidation or expansion.",
        "Ask what would have to happen for the phase to change.",
        "Plan your trade around that change.",
    ),
    example_md="""
Say the daily range for the past month averaged **70 pips**. For the last eight days it has been **30 pips**. That is compression.

A plan could be: "Do nothing inside this box. On a break of the high or low, look for a trade in the break's direction, with the stop on the other side of the box."

The box is 60 pips tall, so if price breaks up and your stop sits below the box, you risk 60 pips plus a buffer. If that is too large for your account at your risk, you take a smaller size or skip the trade.
""".strip(),
    mistakes=(
        "Treating support and resistance as exact lines.",
        "Assuming compression tells you the direction. It only tells you a move may be coming.",
        "Calling everything a reversal because the last two candles went against you.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Volatility clustering is well documented: large moves tend to follow large moves and quiet periods tend to follow quiet periods (Mandelbrot, and later Engle's ARCH models). So the idea of compression and expansion has a real basis.

Whether support and resistance hold *better than chance* is much less settled. Some of their power may come from people reacting to the same lines. Stage 5 covers this.
""".strip(),
    ),
    try_it="On one chart, write a label on each phase: trend, pullback, consolidation, expansion, breakout. Use only these words.",
    quiz=(
        Q(
            "Price is in an uptrend, drifts down a bit, then continues up. That dip was a…",
            ("Reversal", "Pullback (or retracement)", "Breakdown"),
            1,
            "A temporary dip against the trend that then resumes is a pullback.",
        ),
        Q(
            "What does compression tell you?",
            (
                "Which way the next move goes",
                "That a larger move may be coming",
                "That the market is broken",
            ),
            1,
            "Compression can precede expansion. It does not tell you the direction.",
        ),
    ),
    takeaways=(
        "Support and resistance are zones.",
        "Compression often comes before expansion.",
        "Pullback and reversal look the same at the start.",
    ),
    sources=("mandelbrot-1963",),
)

_anatomy = Path(
    candles=(
        (100, 104, 99, 103),
        (103, 104.5, 100, 101),
        (101, 101.5, 97, 100.5),
        (100.5, 104.5, 100, 103.8),
    ),
    volume=(100.0, 100.0, 100.0, 100.0),
)

_CANDLES = Lesson(
    slug="reading-charts/candlesticks",
    title="Candlesticks: what they show and what they do not",
    summary="One candle is four numbers. Everything else is a name for a shape.",
    est_minutes=6,
    key_concepts=("OHLC", "wick", "body", "context"),
    figures=(Figure("candle-anatomy", "Body = open to close. Wicks = the extremes."),),
    goal="Read any candle correctly and know what it can and cannot tell you.",
    body_md="""
A candle compresses a period of price into four numbers: **open, high, low, close**. People often write this as **OHLC**.

- The **body** is the part between open and close.
- The **wicks** (or **shadows**) go up to the high and down to the low.
- Green usually means the close was above the open. Red means it closed below.

That is all a candle is.

**Pin bars, engulfing patterns and dojis** are names for shapes. Names are not evidence. A doji at the top of a long run-up may matter. A doji in the middle of nowhere probably does not.

### What a candle is useful for

- Reading recent volatility from the size of the bars.
- Seeing where price spent time and where it only visited.
- Noticing mismatch. A candle that closes near its low after pushing up is a rejection, not a buy signal.

This app's forecasting does not use candle patterns as inputs, because their statistical edge after costs looks small.
""".strip(),
    charts=(
        candle_chart(
            _anatomy,
            title="Four candles, four stories",
            caption="Illustrative prices. Wicks show the highs and lows that price reached but could not hold.",
            marks=(
                Mark(0, 104, "Long body up", "accentSoft"),
                Mark(1, 104.5, "Closed low", "danger"),
                Mark(2, 97, "Long lower wick", "accent", "up"),
            ),
        ),
    ),
    steps=(
        "Look at the body: did price close up or down, and by how much?",
        "Look at the wicks: which side was rejected?",
        "Compare the size of this candle to the last 20.",
        "Check the location: near a level you care about, or in the middle?",
        "Only then ask if the candle matters at all.",
    ),
    example_md="""
A daily candle has open 1.0820, high 1.0900, low 1.0790, close 1.0815.

- It closed slightly below the open (**body of 5 pips**).
- It reached up to 1.0900 and fell back, so buyers were rejected at the top (**wick of 80 pips above the open**).
- It went down to 1.0790 and recovered (**wick of 25 pips**).

The market explored both sides and went nowhere. That is what the candle said. It did not say what happens next.
""".strip(),
    mistakes=(
        "Treating a named candle as a signal without checking its location.",
        "Forgetting that a candle's shape can change completely before it closes.",
        "Reading a meaning into every single candle.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
Studies of candlestick patterns have been mostly negative after costs. Later researchers summarise the US and Japanese evidence, including Marshall, Young and Rose's work, as finding little value. A study of the Stock Exchange of Thailand found most reversal patterns earned mean returns not statistically different from zero. A separate study of Taiwanese stocks found results that depended strongly on the exit rule used.

So candles are good for describing what happened. As stand-alone predictors, the evidence is weak.
""".strip(),
    ),
    try_it="Take any day's candle and write three sentences: what the body did, what the wicks did, and how big it was compared with recent days.",
    quiz=(
        Q(
            "What do the four numbers OHLC stand for?",
            ("Open, high, low, close", "Open, half, low, change", "Order, hold, loss, count"),
            0,
            "A candle shows these four prices for one period.",
        ),
        Q(
            "Tested alone and after costs, single candlestick patterns generally…",
            ("Beat the market strongly", "Show little reliable edge", "Are impossible to test"),
            1,
            "Most studies find small or no effect after costs.",
        ),
    ),
    takeaways=(
        "A candle is four numbers.",
        "Names of shapes are not evidence.",
        "Location and size matter more than the shape alone.",
    ),
    sources=("marshall-candles-2006", "thai-candles-2017"),
)

_shapes = Path(
    candles=(
        (100, 103, 99.5, 102.5),
        (102.5, 103, 98.6, 102.8),
        (103, 103.3, 101, 101.1),
        (101, 101.2, 100.9, 101.1),
        (101.2, 104.5, 101.1, 102),
    ),
    volume=(100.0, 100.0, 100.0, 100.0, 100.0),
)

_VOCAB = Lesson(
    slug="chart-language/candles-vocabulary",
    title="Candle words: body, wick, doji, pin bar",
    summary="The names of candle shapes, and how to use them carefully.",
    est_minutes=6,
    key_concepts=("candle", "body", "wick", "doji", "engulfing", "pin bar", "gap"),
    figures=(Figure("candle-types", "Common shapes: body, wick, doji, hammer, engulfing."),),
    goal="Know the common candle words and use them to describe, not to predict.",
    body_md="""
Candle words describe the shape, and the shape hints at who won the period.

- **Body:** the part from open to close. A big body means one side clearly won.
- **Wick**, or shadow: the thin lines to the high and low. These prices were tried and rejected.
- **Doji:** open and close almost the same. A tiny body with wicks. It shows indecision.
- **Engulfing:** a candle whose body completely covers the previous body. A bullish engulfing after a fall means buyers took over that period.
- **Pin bar** or **hammer:** a small body with one long wick. A long lower wick means the market tried lower and got pushed back.
- **Gap:** a jump between one candle's close and the next one's open, common after weekends or news.

### How to use them carefully

Candles are best as **confirmation at a level you already care about**, and never alone. A hammer at support in an uptrend is worth noticing. The same hammer in the middle of nowhere is noise. Use them to read the fight, not as buy buttons.
""".strip(),
    charts=(
        candle_chart(
            _shapes,
            title="Candle shapes side by side",
            caption="Illustrative prices. From left: a strong up candle, a hammer with a long lower wick, a strong down candle, a doji, and a shooting star with a long upper wick.",
            marks=(
                Mark(0, 103, "Up", "accentSoft"),
                Mark(1, 98.6, "Hammer", "accent", "up"),
                Mark(2, 103.3, "Down", "danger"),
                Mark(3, 100.9, "Doji", "muted", "up"),
                Mark(4, 104.5, "Star", "warn"),
            ),
        ),
    ),
    steps=(
        "Identify the body and the wicks.",
        "Name the shape, if it has a common name.",
        "Check where it appeared: at a level, or in the middle of nowhere.",
        "Check whether it agrees with the larger trend.",
        "Treat it as one small input.",
    ),
    example_md="""
EUR/USD has been rising and dips into a support zone at 1.0820–1.0830.

A 4-hour candle opens at 1.0845, falls to 1.0822, and closes at 1.0843, a long lower wick and small body. That is a hammer **at a level**, in the direction of the trend.

It is a reason to *pay attention*, not a reason to buy automatically. You would still need an entry, a stop below 1.0820, and a position size that risks only your planned amount.
""".strip(),
    mistakes=(
        "Buying every hammer you see.",
        "Forgetting that the same shape means nothing without context.",
        "Reading patterns before the candle has closed.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
Single-candle signals have shown little reliable edge after costs in academic tests of stock markets. A hammer may hint at a short-term reversal, but no large test has shown it to be dependable.

Use these words to communicate what happened. Do not treat them as buy signals.
""".strip(),
    ),
    try_it="Mark every hammer on a chart over a month. For each, note what the next five candles did. Count how often the move continued in the hoped-for direction.",
    quiz=(
        Q(
            "A small-bodied candle with a long lower wick, at support, hints that…",
            (
                "Sellers are firmly in control",
                "Buyers rejected the lower prices",
                "Nothing, candle shapes are random",
            ),
            1,
            "A long lower wick means price was pushed down and bought back up. It is only worth noting at a level you already care about.",
        ),
        Q(
            "What is a doji?",
            (
                "A candle with open and close almost the same",
                "A candle with no wicks",
                "A kind of gap",
            ),
            0,
            "A doji shows that neither side won that period.",
        ),
    ),
    takeaways=(
        "Body shows who won. Wicks show what was rejected.",
        "A shape matters only at a level you already care about.",
        "Use candles to describe, not to predict.",
    ),
)

_ZOO = Lesson(
    slug="candles-volume/candlestick-zoo",
    title="The candlestick zoo: every pattern that matters",
    summary="Hammers, stars, engulfing, inside bars and more, with an honest health warning.",
    est_minutes=8,
    key_concepts=(
        "doji",
        "hammer",
        "hanging man",
        "shooting star",
        "engulfing",
        "inside bar",
        "outside bar",
        "pin bar",
        "marubozu",
    ),
    figures=(Figure("candle-zoo", "The full set of named candle shapes."),),
    goal="Recognise every common candle pattern and know how little each one proves.",
    body_md="""
Every candle is a story about a fight between buyers and sellers. These shapes are named outcomes of that fight.

### Indecision

- **Doji:** tiny body. Neither side won.

### Rejection candles (one long wick)

- **Hammer:** small body at the top, long wick below, appearing after a fall. A possible bottom.
- **Hanging man:** looks identical to a hammer but appears after a rise. A possible top warning.
- **Shooting star:** small body at the bottom, long wick above, after a rise. A possible top.
- **Pin bar:** the general name for any candle with one long wick and a small body.

### Power candles

- **Marubozu:** big body with almost no wicks. One side dominated.
- **Engulfing:** a two-candle pattern where a big body swallows the previous body.

### Two-candle relationships

- **Inside bar:** a candle that fits entirely inside the previous candle's range. A pause.
- **Outside bar:** a candle whose range covers the previous one, with a higher high and a lower low.

### The honest truth

Candlestick patterns are useful vocabulary and mild hints, not magic. Tested on their own, most single patterns barely beat a coin flip, and many do not beat it at all after costs. Pros use them as one small input.

**What about multi-candle patterns** like morning star and three white soldiers? The same applies. They are stories that need testing.
""".strip(),
    charts=(
        Chart(
            title="What a small edge leaves after costs",
            caption="Calculated from the worked example below: a pattern that gains 2 pips on average before costs, at different round-trip costs.",
            data_kind="calculated",
            kind="bars",
            y_format="plain",
            y_label="Average pips left per trade",
            bars=(
                Bar("Before costs", 2.0, "accent"),
                Bar("Cost 0.6 pips", 1.4, "accentSoft"),
                Bar("Cost 1.2 pips", 0.8, "warn"),
                Bar("Cost 2.0 pips", 0.0, "danger"),
            ),
        ),
    ),
    steps=(
        "Learn the shapes so you can read what people mean.",
        "Pick at most one or two shapes to study.",
        "Define them with exact rules (body size, wick length, location).",
        "Test them on your market against random points.",
        "Keep them only if they beat costs on unseen data.",
    ),
    example_md="""
You define a hammer precisely: lower wick at least twice the body, and the close in the top third of the candle, after three falling candles.

Across 300 hammers on EUR/USD 4-hour data, you check the next 5 candles. Say the price rose by an average of **2 pips**, and your round-trip cost is **1.2 pips**, leaving **0.8 pips** on average.

That is not nothing. But with so little remaining, a slightly wider spread or a bad few months could erase it, so it needs testing on data you have not seen. (These numbers are an example of how to test, not results.)
""".strip(),
    mistakes=(
        "Learning 40 patterns instead of learning what any one of them is worth.",
        "Taking a pattern out of its context.",
        "Assuming patterns that worked in old books still work in today's markets.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
Academic results are mostly negative. A Thai study found most patterns earned returns not different from zero, and later researchers describe the US evidence as similarly unconvincing.

Be careful with practitioner statistics that quote high success rates. They often come from small samples, or from choosing the time period after seeing the data.

This app does not trade candle patterns.
""".strip(),
    ),
    try_it="Pick your favourite candle pattern. Find 20 examples of it on a chart including the failed ones. Calculate how many worked by a rule you wrote down first.",
    quiz=(
        Q(
            "A candle with a tiny body at the top and a long lower wick appears after a fall. What is it?",
            ("A shooting star", "A hammer", "A doji"),
            1,
            "A long lower wick after a fall is a hammer: sellers pushed down, and buyers pushed back up.",
        ),
        Q(
            "A hammer shape appears after a rise. What is it usually called?",
            ("Hanging man", "Marubozu", "Inside bar"),
            0,
            "Same shape, different location, different name. This is why location matters.",
        ),
    ),
    takeaways=(
        "The patterns are vocabulary.",
        "Location and context matter more than the shape.",
        "Most single patterns show little edge after costs.",
    ),
    sources=("marshall-candles-2006", "thai-candles-2017"),
)

CHAPTERS = (
    chapter(
        "charts",
        "reading-a-chart",
        "Reading a chart",
        "Timeframes, direction, trends and how price really moves.",
        (_TIMEFRAMES, _DIRECTION, _TREND, _DIRECTION_2, _MOVES, _OBVIOUS, _PRICE_ACTION),
    ),
    chapter(
        "charts",
        "candles",
        "Candles",
        "What a candle tells you, and how little a named shape proves.",
        (_CANDLES, _VOCAB, _ZOO),
    ),
)
