"""Stage 10 — Testing and statistics."""

from __future__ import annotations

import math

from mentor.domain.curriculum.book._kit import (
    Bar,
    Chart,
    Evidence,
    Figure,
    Lesson,
    Q,
    Series,
    Verdict,
    chapter,
    fact,
)
from mentor.domain.curriculum.charts import equity_paths

_LOOKAHEAD = Lesson(
    slug="backtesting/lookahead-bias",
    title="Lookahead bias: the subtlest fatal bug",
    summary="Using information you could not have had at the time.",
    est_minutes=6,
    key_concepts=("lookahead", "point-in-time", "data leakage"),
    figures=(Figure("lookahead", "A backtest must only use data from before the decision."),),
    goal="Spot lookahead bias and build tests that cannot have it.",
    body_md="""
**Lookahead bias** happens when a test uses information you could not have had at the moment of the trade.

Common examples:

- Using today's close to decide today's entry.
- Adjusting data using the full sample, including the future.
- Using a number before the date it was actually published.

The result is a backtest that looks wonderful and a live system that loses. There is no warning. The live curve simply goes the other way.

### The defence

Test **event by event**: at each step the system can only see data with a timestamp earlier than that step. The app's backtester is built this way. Every signal must pass this test before it can appear on the dashboard.

Use point-in-time data: the value as it was known then, not as revised later.
""".strip(),
    charts=(
        Chart(
            title="What lookahead does to a backtest",
            caption="Illustrative: a test that peeks at the future usually looks far better than the same rule tested honestly.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Account",
            x_label="Trades",
            series=(
                Series("With lookahead", tuple(100 + i * 0.9 for i in range(60)), "danger"),
                Series(
                    "Honest test",
                    tuple(100 + i * 0.1 + (2 if i % 9 == 0 else 0) for i in range(60)),
                    "accentSoft",
                ),
            ),
        ),
    ),
    steps=(
        "Write down what data your rule uses at each step.",
        "Ask whether each piece was known at that moment.",
        "Enter on the next bar, not the signal bar.",
        "Use point-in-time data for anything that gets revised.",
    ),
    example_md="""
A rule: "If today closes above the 20-day high, buy at today's close."

Testing this with a fill at today's close uses today's close to decide, and assumes you can buy at it. You can only act after the close, so the honest fill is **tomorrow's open**. Fixing that one detail can remove much of the apparent profit.
""".strip(),
    mistakes=(
        "Buying at the same bar used for the signal.",
        "Using revised economic data.",
        "Standardising with the full dataset.",
    ),
    evidence=fact(
        "A testing error rather than a claim. Lookahead can make almost any idea look profitable, so it is the first thing to check."
    ),
    try_it="Take a rule you believe in. Find one place where it might be using information from the future. Fix it and test again.",
    quiz=(
        Q(
            "Which of these is lookahead bias?",
            (
                "Using today's closing price to decide today's entry",
                "Paying the spread on every trade",
                "Holding only one position at a time",
            ),
            0,
            "Today's close was not known when today began.",
        ),
        Q(
            "Which fill is realistic for a signal based on today's close?",
            ("Today's close", "Tomorrow's open", "Yesterday's close"),
            1,
            "You can only act after the close.",
        ),
    ),
    takeaways=(
        "Only use data known at the time.",
        "Lookahead makes bad ideas look great.",
        "Enter on the next bar.",
    ),
)

_OVERFIT = Lesson(
    slug="backtesting/overfitting",
    title="Overfitting and how to spot it",
    summary="Tuning rules to noise. The most common way good-looking backtests fail.",
    est_minutes=7,
    key_concepts=("overfitting", "out-of-sample", "walk-forward", "complexity"),
    figures=(
        Figure(
            "overfitting", "A model fitted to noise looks great in the past and fails on new data."
        ),
    ),
    goal="Recognise overfitting and use out-of-sample testing to reduce it.",
    body_md="""
**Overfitting** is when you tune a model or rule so closely to past data that it matches the noise, the coincidences that will not repeat. The fit looks perfect. The live results collapse.

### Warning signs

- A backtest with implausibly low drawdown.
- Parameters that look too precise, such as "buy on a 13.7-day average".
- Results that collapse on data not used for tuning.
- Many rules and exceptions.

### Defences

- Hold back part of your data, and do not touch it until the end. This is **out-of-sample** testing.
- **Walk forward:** roll a training and test window through time.
- **Penalise complexity:** when two models perform similarly, prefer the simpler one.
- Compare with a simple baseline rule. If the complicated one does not beat it clearly out of sample, it loses.
""".strip(),
    charts=(
        Chart(
            title="Better in the past, worse in the future",
            caption="Illustrative. As rules are added, the fit to past data keeps improving, while performance on unseen data peaks early and then falls.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Performance score",
            x_label="Complexity (number of rules)",
            x_labels=tuple(str(i) for i in range(1, 11)),
            series=(
                Series("Past data", (1.0, 1.4, 1.8, 2.1, 2.4, 2.7, 2.9, 3.1, 3.3, 3.5), "danger"),
                Series(
                    "Unseen data", (0.8, 1.1, 1.3, 1.4, 1.3, 1.1, 0.9, 0.7, 0.5, 0.3), "accentSoft"
                ),
            ),
        ),
    ),
    steps=(
        "Split your data into in-sample and out-of-sample before you start.",
        "Develop your rules on in-sample data only.",
        "Run the final rules on the unseen sample once.",
        "If it fails, do not tune again on that sample.",
        "Prefer rules with few parameters.",
    ),
    example_md="""
A rule tuned over many settings shows a backtest Sharpe ratio of 2.5 on 2015–2022 data. (The **Sharpe ratio** measures return divided by the size of the swings; higher is smoother.)

On unseen 2023–2024 data it scores **0.1**. The drop tells you most of the in-sample result came from fitting noise.
""".strip(),
    mistakes=(
        "Peeking at the out-of-sample data and then tweaking.",
        "Using very specific parameters that have no reason behind them.",
        "Believing that more rules means better results.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Backtest overfitting is well documented. Bailey, Borwein, López de Prado and Zhu showed that it takes surprisingly few variations to find an impressive backtest by chance, and they warn that simple holdouts alone are not enough.

Harvey, Liu and Zhu argue that a new finding should clear a much higher statistical bar because so many ideas have been tried.
""".strip(),
    ),
    try_it="Take a rule you tuned on one period. Test it on a period you have not used. How does it change?",
    quiz=(
        Q(
            "What is out-of-sample data?",
            (
                "Data you did not use for building the rule",
                "Data from another broker",
                "Very old data",
            ),
            0,
            "It simulates the future.",
        ),
        Q(
            "What is a sign of overfitting?",
            ("Great past results and poor results on new data", "A simple rule", "Few parameters"),
            0,
            "Fitted noise fails on new data.",
        ),
    ),
    takeaways=(
        "Overfitting fits noise.",
        "Reserve data for the final test.",
        "Simple rules often survive better.",
    ),
    sources=("bailey-2014", "harvey-2016"),
)

_COSTS_TEST = Lesson(
    slug="backtesting/transaction-costs",
    title="Transaction costs erase paper edges",
    summary="A backtest without costs is not a backtest.",
    est_minutes=5,
    key_concepts=("spread", "commission", "slippage", "frictionless"),
    figures=(Figure("costs-erase-edge", "Costs turn a paper edge into a small or negative one."),),
    goal="Include realistic costs in every test you run.",
    body_md="""
A frictionless backtest assumes you buy at the close and sell at the close. Live, you cross the spread, you pay a commission, and your fill is rarely the price you saw.

On EUR/USD that might be 1–2 pips per round trip: small per trade, and enormous over a thousand trades.

### The rule

Every test must model spread, commission and slippage. If a strategy needs frictionless costs to be profitable, it is not profitable. Do not trade it.

Be pessimistic. Assume your live costs will be worse than your test, and check how much the results degrade if you double the costs.
""".strip(),
    charts=(
        Chart(
            title="An edge shrinking as costs rise",
            caption="Calculated: a strategy earning +0.20R per trade before costs, over 500 trades.",
            data_kind="calculated",
            kind="bars",
            y_format="r",
            y_label="Total R over 500 trades",
            x_label="Cost per trade",
            bars=(
                Bar("Free", 100, "accentSoft"),
                Bar("0.05R", 75, "accent"),
                Bar("0.10R", 50, "accent"),
                Bar("0.15R", 25, "warn"),
                Bar("0.20R", 0, "danger"),
            ),
        ),
    ),
    steps=(
        "Measure your real spread, commission and slippage.",
        "Include them in every simulated trade.",
        "Then double them, and test again.",
        "Do not trade a strategy that fails the doubled-cost test.",
    ),
    example_md="""
A strategy makes +0.20R per trade over 500 trades: +100R gross.

With costs of 0.08R per trade, that is +60R. If real costs turn out to be 0.16R, it is only +20R. Costs have now taken 80% of the gross.
""".strip(),
    mistakes=(
        "Testing with zero spread.",
        "Using your broker's advertised best spread.",
        "Forgetting costs on exits.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Many technical trading results fall apart when costs are included, a point made in the surveys and tests cited in this book (for example Park and Irwin; Bessembinder and Chan, as cited in later work). Treat cost-free claims as worthless.
""".strip(),
    ),
    try_it="Re-run a test with double your assumed costs. How much of the result remains?",
    quiz=(
        Q(
            "A rule only works with zero costs. What should you do?",
            ("Do not trade it", "Trade it carefully", "Use more leverage"),
            0,
            "If it needs free trading to work, it does not work.",
        ),
        Q(
            "Why double costs in a test?",
            ("To check how robust the result is", "Regulators require it", "It raises returns"),
            0,
            "Real costs are usually worse than you expect.",
        ),
    ),
    takeaways=(
        "A backtest without costs is fiction.",
        "Be pessimistic about costs.",
        "Test the double-cost case.",
    ),
    sources=("park-irwin-2007",),
)

_ci = [(n, round(1.96 * math.sqrt(0.25 / n) * 100, 1)) for n in (20, 50, 100, 300, 1000)]

_SAMPLE = Lesson(
    slug="testing/sample-size-and-luck",
    title="Sample size and luck",
    summary="How many trades it really takes to know anything.",
    est_minutes=8,
    key_concepts=("sample size", "confidence interval", "standard error", "luck"),
    goal="Know how many trades you need before a result means anything.",
    body_md="""
A win rate from 20 trades tells you very little. Why? Because luck alone moves the number around.

A **confidence interval** is a range that probably contains the true value. For a win rate near 50%, the 95% range is roughly the sample's win rate plus or minus:

**1.96 × √(0.25 / n)**

The table in the chart shows what this means. With 20 trades the range is about ±22 percentage points. With 300 trades, about ±6 points. With 1,000 trades, about ±3 points.

So a 55% win rate over 100 trades could easily be a true 50% or lower. Most traders do not have nearly enough trades to know what they think they know.

### How to use this

Do not change your plan after 20 trades. Compare your record with what a coin would do. And ask "could this be luck?" before asking "how do I scale this?".
""".strip(),
    charts=(
        Chart(
            title="How wrong your win rate could be, by sample size",
            caption="Calculated half-width of the 95% confidence interval for a win rate near 50%. Assumes independent trades, so reality is usually worse.",
            data_kind="calculated",
            kind="bars",
            y_format="pct",
            y_label="± percentage points",
            x_label="Number of trades",
            bars=tuple(Bar(f"{n} trades", w, "danger" if w > 8 else "accent") for n, w in _ci),
        ),
    ),
    steps=(
        "Record the sample size next to any statistic.",
        "Compute the confidence interval.",
        "Check whether the interval still includes the break-even win rate.",
        "Collect more data before changing anything big.",
    ),
    example_md="""
You have won **58 of 100** trades. Win rate 58%.

95% range: ±1.96 × √(0.25 / 100) = ±9.8%, so roughly **48% to 68%**.

Your break-even win rate is 52%. Your true win rate might be below that. You do not have proof of an edge yet, even though 58% feels strong.
""".strip(),
    mistakes=(
        "Treating 30 trades as proof.",
        "Stopping a test once the results look good.",
        "Ignoring that trades can be correlated, which makes the true uncertainty larger.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
This is basic statistics. The interval above assumes independent trades, and real trades are often correlated, so the true uncertainty is larger. It is why honest forecasting records, including this app's, need large samples before they mean much.

This app's own recent forecasts (18 windows at 38.9% since 14 October 2026) are nowhere near a sample that could show a real edge, and they are currently below break-even.
""".strip(),
    ),
    try_it="Compute the 95% confidence range for your own win rate. Does it include your break-even win rate?",
    quiz=(
        Q(
            "At 100 trades, roughly how wide is the 95% range around a 50% win rate?",
            ("±2%", "±10%", "±40%"),
            1,
            "About ±9.8%.",
        ),
        Q(
            "Your range includes your break-even win rate. This means…",
            ("You do not yet have proof of an edge", "You have an edge", "You have no edge"),
            0,
            "It may or may not be an edge; you cannot tell yet.",
        ),
    ),
    takeaways=(
        "Small samples are mostly luck.",
        "Always show your confidence range.",
        "Do not conclude too early.",
    ),
)

_WALK = Lesson(
    slug="testing/walk-forward",
    title="Walk-forward testing",
    summary="Test a strategy the way you would actually run it.",
    est_minutes=7,
    key_concepts=("walk-forward", "training window", "test window", "reoptimise"),
    goal="Understand walk-forward testing and why it is a better test than one split.",
    body_md="""
**Walk-forward testing** repeats this pattern through history:

1. Train or tune on one window of data.
2. Test on the next unseen window.
3. Move forward and repeat.

It imitates real life, where you would adjust your strategy periodically and trade it on data you have never seen.

### What to watch

- Keep the training and test windows fixed in advance.
- Do not change the rules because of a bad test window.
- Combine all the test windows to judge the strategy.
- Keep a final untouched period, because repeated testing can still overfit.

This is close to how the app's Strategy Lab and retraining loops work.
""".strip(),
    charts=(
        Chart(
            title="Walk-forward windows",
            caption="Illustrative schedule. Each row trains on an older window and tests on the next new one.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Test window (months)",
            bars=(
                Bar("Round 1: train 2018-20, test 2021", 12, "accent"),
                Bar("Round 2: train 2019-21, test 2022", 12, "accent"),
                Bar("Round 3: train 2020-22, test 2023", 12, "accent"),
                Bar("Round 4: train 2021-23, test 2024", 12, "accent"),
            ),
        ),
    ),
    steps=(
        "Choose a training window and a test window.",
        "Tune only on the training window.",
        "Record the test-window result.",
        "Move forward and repeat.",
        "Judge the strategy on the combined test results.",
    ),
    example_md="""
Your rule has one parameter, the lookback length. Each year you pick the best lookback from the prior three years and trade it the next year.

Combined out-of-sample results: 6 years, +18R total, max drawdown 11R. That is far more informative than one large in-sample test that said +60R.
""".strip(),
    mistakes=(
        "Changing rules after a bad test window.",
        "Using very short test windows.",
        "Using the final test data again and again.",
    ),
    evidence=fact(
        "A testing procedure. Bailey and colleagues warn that even hold-out and walk-forward testing can be gamed if you repeat them enough times, so the number of attempts still matters."
    ),
    try_it="Split your history into four test windows. Run a simple rule through a walk-forward using a one-parameter setting.",
    quiz=(
        Q(
            "In walk-forward testing, the test window is…",
            ("Data never seen during tuning", "The same as the training window", "Random data"),
            0,
            "That mimics the unknown future.",
        ),
        Q(
            "Which is true?",
            (
                "Walk-forward cannot be overfitted at all",
                "Repeated attempts can still overfit",
                "It is only for crypto",
            ),
            1,
            "The more variations you try, the more luck you can find.",
        ),
    ),
    takeaways=(
        "Walk-forward mimics real life.",
        "Tune only on past windows.",
        "Keep track of how many attempts you make.",
    ),
    sources=("bailey-2014",),
)

_fp = [(n, round((1 - 0.95**n) * 100, 1)) for n in (1, 5, 10, 20, 50, 100)]

_MULTI = Lesson(
    slug="testing/multiple-testing",
    title="Multiple testing",
    summary="Try enough ideas and something will look great by chance.",
    est_minutes=7,
    key_concepts=("multiple testing", "false discovery", "data snooping", "Sharpe haircut"),
    goal="Understand why trying many ideas raises the bar for believing any of them.",
    body_md="""
Test one idea, and you have a fair chance of knowing if it is real. Test a hundred, and some will look great **by chance**.

If each test has a 5% chance of a false positive, the chance of at least one false positive across N independent tests is:

**1 − 0.95ᴺ**

At 14 tests it is already about 50%. At 100 tests it is over 99%.

So a strategy found by trying a thousand combinations is not comparable to one found on the first attempt. You have to raise your standards to reflect how many things you tried. This is often called **data snooping** or a **multiple testing** correction.

### What to do

- Keep a record of every test you run.
- Raise your bar for significance according to how many you tried.
- Prefer ideas with a good reason to exist.
- Remember that "the best of many" will usually disappoint later.

This is the thinking behind the Strategy Lab's rising bar in this app.
""".strip(),
    charts=(
        Chart(
            title="Chance of at least one false discovery",
            caption="Calculated: 1 − 0.95ᴺ, assuming independent tests at a 5% significance level.",
            data_kind="calculated",
            kind="bars",
            y_format="pct",
            y_label="Chance of a false positive",
            x_label="Number of tests",
            bars=tuple(Bar(f"{n} tests", v, "danger" if v > 50 else "warn") for n, v in _fp),
        ),
    ),
    steps=(
        "Count every test you ran, including the ones you threw away.",
        "Raise your significance bar accordingly.",
        "Prefer economic reasons over statistical findings.",
        "Hold out data that you test only once.",
    ),
    example_md="""
You try 200 combinations of moving averages. The best shows a t-statistic of 2.4. Taken alone, that would look significant at the 5% level.

Harvey, Liu and Zhu argue that a new finding should have a t-statistic above about 3. Your best result, picked from 200 tries, does not clear that bar.
""".strip(),
    mistakes=(
        "Reporting only the best test.",
        "Treating every backtest as independent.",
        "Forgetting the tests you discarded.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
This is established statistics, and it is an active topic in finance. Harvey, Liu and Zhu conclude a t-statistic above about 3.0 is needed for a new finding. McLean and Pontiff found that published predictors of stock returns shrink after publication. Sullivan, Timmermann and White applied this thinking directly to technical trading rules.
""".strip(),
    ),
    try_it="Count how many settings you tried the last time you tested a strategy. Write that number next to the result.",
    quiz=(
        Q(
            "With 100 independent tests at the 5% level, the chance of at least one false positive is about…",
            ("5%", "50%", "99%"),
            2,
            "1 − 0.95^100 ≈ 99.4%.",
        ),
        Q(
            "What should you do about many tests?",
            ("Raise the bar for significance", "Report only the best", "Ignore them"),
            0,
            "Standards must rise with the number of attempts.",
        ),
    ),
    takeaways=(
        "More tests create more lucky results.",
        "Count every attempt.",
        "Raise the bar accordingly.",
    ),
    sources=("harvey-2016", "mclean-pontiff-2016", "stw-1999"),
)

_MC = Lesson(
    slug="testing/monte-carlo",
    title="Monte Carlo simulation",
    summary="Reshuffling your trades to see what might happen next.",
    est_minutes=7,
    key_concepts=("Monte Carlo", "resampling", "drawdown", "scenario"),
    goal="Use simulation to see the range of results your strategy might produce.",
    body_md="""
A backtest gives you one path. In real life, the order of your trades could have been different. **Monte Carlo simulation** generates many possible futures by resampling your trade results or simulating from your win rate and payoffs.

### Why bother

- It shows the **range** of possible drawdowns, not just the single one in your test.
- It shows how often you would have had a long losing period.
- It helps you choose a position size that survives the bad paths.

### The catch

Simple reshuffling assumes each trade is independent. Real results can cluster in bad regimes, so real drawdowns are often worse than the simulation.
""".strip(),
    charts=(
        Chart(
            title="Many possible paths from one strategy",
            caption="Simulated: 12 paths of 100 trades, 48% win rate, 1.6R winners, risking 1% per trade. All have the same edge, and their drawdowns are very different.",
            data_kind="calculated",
            kind="lines",
            y_format="plain",
            y_label="Account (start = 100)",
            x_label="Trades",
            series=equity_paths(
                n_paths=12, n_trades=100, win_rate=0.48, win_r=1.6, risk_pct=1.0, seed=29
            ),
        ),
    ),
    steps=(
        "Collect your trade results.",
        "Resample them many times, in random order.",
        "Record the maximum drawdown of each simulated path.",
        "Look at the worst 5%.",
        "Choose your risk so that this worst case is survivable.",
    ),
    example_md="""
Your backtest's maximum drawdown is **12%**. A Monte Carlo reshuffle of its trades shows that 5% of paths have a drawdown of **24%** or worse.

If you plan to quit at 15%, you will probably be forced out by bad luck. Either cut your risk per trade, or accept a deeper drawdown as normal.
""".strip(),
    mistakes=(
        "Believing the single backtest drawdown.",
        "Assuming independence without thinking.",
        "Using simulation as proof that a strategy works.",
    ),
    evidence=fact(
        "A tool for understanding risk under assumptions. It does not prove an edge exists. If the input trades are overfitted, the simulation is too."
    ),
    try_it="Run a simple reshuffle of your last 50 trades in a spreadsheet, 20 times, and write down the worst drawdown you saw.",
    quiz=(
        Q(
            "What does Monte Carlo mainly show?",
            ("The range of possible outcomes", "The exact future", "Whether your broker is safe"),
            0,
            "A range of outcomes, given your assumptions.",
        ),
        Q(
            "Why might simulated drawdowns be too small?",
            ("Real losses can cluster", "Computers are slow", "Spreads are fixed"),
            0,
            "Independence assumptions usually understate risk.",
        ),
    ),
    takeaways=(
        "One backtest is one possible path.",
        "Plan for the bad paths.",
        "Clustering makes reality worse.",
    ),
)

_EDGE = Lesson(
    slug="market-study/building-an-edge",
    title="Building an edge you can trust",
    summary="A pipeline designed to kill bad ideas cheaply.",
    est_minutes=7,
    key_concepts=("hypothesis", "backtest", "forward test", "validation"),
    figures=(Figure("edge-pipeline", "Most ideas should die early and cheaply."),),
    goal="Take an idea through a pipeline that kills bad ideas before they cost you money.",
    body_md="""
An **edge** is a rule with a positive expected value after costs. You do not find one by staring at charts. You build it through a pipeline designed to kill bad ideas cheaply.

1. **Hypothesis:** a specific, testable claim, with a reason it might exist. Write it down.
2. **Backtest:** test it honestly on history, with point-in-time data, real costs and a held-out sample.
3. **Forward test:** run it on new data or paper trade it. This is where many "great" backtests fall apart.
4. **Small live:** trade it with tiny size. Real fills and real emotions are data a backtest can't give you.
5. **Scale:** increase size only once it has proved itself, and within your risk rules.

Most ideas die at step 2 or 3. That is the pipeline working. Killing a bad idea for the price of a backtest is the cheapest money you will ever make.

This app's champion/challenger loop follows this discipline automatically. A new model must beat the current one before it replaces it.
""".strip(),
    charts=(
        Chart(
            title="How many ideas survive the pipeline",
            caption="Illustrative funnel. Exact numbers vary, but most ideas should fail cheaply and early.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Ideas remaining",
            bars=(
                Bar("Ideas", 100, "muted"),
                Bar("Pass backtest", 15, "accent"),
                Bar("Pass forward test", 5, "accent"),
                Bar("Pass small live", 2, "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Write the idea as a testable claim.",
        "Backtest it with honest data and costs.",
        "Forward test it on new data.",
        "Trade it small.",
        "Scale only after proof.",
    ),
    example_md="""
Idea: "After a three-day fall inside a weekly uptrend, buying beats random."

Backtest: 12 years, +0.08R per trade after costs, 310 trades, and the 95% range includes zero. So far this is not an edge. You stop here and move on, having spent a few hours and no money. That is a good result.
""".strip(),
    mistakes=(
        "Skipping straight to live trading.",
        "Scaling up too quickly.",
        "Being attached to an idea.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Each stage is a practice recommended widely in testing research. Overfitting research (Bailey et al.) shows why repeated selection is dangerous even with hold-outs. No pipeline guarantees an edge, and this one is designed to filter out bad ideas rather than promise good ones.

The app's own loop is not yet proven to have found a durable edge.
""".strip(),
    ),
    try_it="Write one idea as a testable hypothesis and take it as far through this pipeline as you can.",
    quiz=(
        Q(
            "What is the job of the pipeline?",
            (
                "To kill bad ideas cheaply",
                "To prove that every idea works",
                "To replace risk management",
            ),
            0,
            "Most ideas should fail early.",
        ),
        Q(
            "Where do many strategies fall apart?",
            ("In forward testing", "In writing the idea", "In choosing a colour"),
            0,
            "New data is the real test.",
        ),
    ),
    takeaways=(
        "An edge must survive a pipeline.",
        "Most ideas die early, and that is good.",
        "Scale only after proof.",
    ),
    sources=("bailey-2014",),
)

_PREDICTS = Lesson(
    slug="market-study/what-actually-predicts",
    title="What actually predicts markets, and what does not",
    summary="A short list of effects with real evidence, and a long list without.",
    est_minutes=8,
    key_concepts=("momentum", "mean reversion", "volatility", "carry"),
    figures=(Figure("predictable-vs-not", "A short list with evidence, a long list without."),),
    goal="Know which effects have real evidence, so you do not waste time on the rest.",
    body_md="""
Decades of research point to a short list of effects that hold up, and a long list of popular ideas that mostly do not after costs.

### Has real evidence

- **Trend and momentum:** what has been rising tends to keep rising for a while, across many markets.
- **Volatility clustering:** big moves follow big moves. This is why the size of moves can be forecast even when direction cannot.
- **Carry:** higher-yielding assets have tended to earn a premium, with sharp reversals.

### Partly supported or conditional

- **Mean reversion:** real at some horizons, but small, costly, and exposed to trends.
- **Pairs and statistical arbitrage:** real in the past, but shrinking.
- **Seasonality:** some evidence, and much debate.

### Mostly unproven after costs

Precise chart patterns, Fibonacci levels, single candlesticks, Elliott Wave, RSI or MACD signals on their own, and trading the news after it is public. They feel predictive because people remember the hits and forget the misses.

### The takeaway

Build your study around the effects with evidence, and require everything else to prove itself out of sample before you risk money on it.

This app's own direction forecasts are unproven and have recently been weak. The list above describes what independent research has found, not what this app can do.
""".strip(),
    charts=(
        Chart(
            title="Strength of the evidence, as this book reads it",
            caption="This book's own judgement from the sources cited, 1 (weak) to 5 (strong). It is a summary and not a measurement.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Evidence strength (1–5)",
            bars=(
                Bar("Momentum / trend", 4.5, "accentSoft"),
                Bar("Volatility clustering", 4.5, "accentSoft"),
                Bar("Carry", 4, "accentSoft"),
                Bar("Mean reversion", 2.5, "accent"),
                Bar("Seasonality", 2.5, "accent"),
                Bar("Chart patterns", 2, "warn"),
                Bar("Fibonacci", 1, "danger"),
                Bar("Single candles", 1, "danger"),
            ),
        ),
    ),
    steps=(
        "List the effects your trading depends on.",
        "Next to each, write the evidence you know.",
        "Treat anything not on the evidence list as a hypothesis.",
        "Spend your time testing, not collecting indicators.",
    ),
    example_md="""
A trader's plan uses a moving-average trend filter, a Fibonacci entry and a moon-phase rule.

- Trend filter: reasonable evidence.
- Fibonacci: weak evidence.
- Moon phase: nothing.

The trader keeps the first, tests the second, and drops the third.
""".strip(),
    mistakes=(
        "Treating all techniques as equally valid.",
        "Dismissing all technical analysis because some of it fails.",
        "Citing a study you have not read.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Summarised from sources cited in this book: Moskowitz et al. and Hurst et al. on trend; Koijen et al. and Brunnermeier et al. on carry; Mandelbrot and Engle on volatility clustering; Gatev et al. on pairs; Batchelor and Ramyar on Fibonacci; and Park and Irwin on technical analysis in general.

Every 'yes' has limits: costs, crowding, and periods when it doesn't work.
""".strip(),
    ),
    try_it="Write down the three ideas your trading relies on most. Put a 1–5 score next to each, and name the evidence.",
    quiz=(
        Q(
            "Which of these has strong evidence?",
            ("Time-series momentum", "Moon phases", "Fibonacci levels alone"),
            0,
            "Momentum is well documented across markets.",
        ),
        Q(
            "What does an effect's evidence mean for you?",
            ("It may still fail for you after costs", "It is guaranteed", "It is banned"),
            0,
            "Evidence is about averages, not your individual result.",
        ),
    ),
    takeaways=(
        "A short list has real evidence.",
        "Most popular ideas are unproven after costs.",
        "Evidence is not a guarantee.",
    ),
    sources=(
        "moskowitz-2012",
        "hurst-2017",
        "koijen-2018",
        "brunnermeier-2008",
        "batchelor-2006",
        "park-irwin-2007",
    ),
)

_PROB = Lesson(
    slug="market-study/probabilistic-thinking",
    title="Think in probabilities, not predictions",
    summary="Ask what the odds and payoffs are, not whether this trade will win.",
    est_minutes=7,
    key_concepts=("probability", "base rate", "expected value", "variance"),
    figures=(Figure("distributions", "Each trade is one sample from a range of outcomes."),),
    goal="Replace 'will this win?' with 'what are the odds and the payoff?'",
    body_md="""
The biggest mindset shift is to stop asking "will this trade win?" and start asking "what are the odds, and what is the payoff?"

- **Every trade is one sample** from a range of outcomes. A good trade can lose, and a bad trade can win. Judge the decision, not the single result.
- **Base rates first.** If predicting direction is about 50–53% at best, any claim of being "80% sure" should make you suspicious. Start from the honest base rate, and demand real evidence to move off it.
- **Expected value, not hope.** A 40%-chance trade paying 3:1 can be excellent. A 90%-chance trade paying 1:5 is a slow bleed.
- **Respect variance.** Even a real edge has long losing streaks.

The app hands you probabilities and ranges, not verdicts. Its forecasts are unproven, so read any probability it shows as a calibrated estimate and not as a promise.
""".strip(),
    charts=(
        Chart(
            title="Two trades by expected value",
            caption="Calculated: expected value = chance of win × win − chance of loss × loss. Win rate alone can mislead.",
            data_kind="calculated",
            kind="bars",
            y_format="r",
            y_label="Expected value per trade",
            bars=(
                Bar("40% win, pays 3R", 0.6, "accentSoft"),
                Bar("90% win, pays 0.1R, risks 1.5R", -0.06, "danger"),
            ),
        ),
    ),
    steps=(
        "Estimate the base rate for what you are about to do.",
        "Estimate the payoff if you are right and the loss if you are wrong.",
        "Calculate expected value before costs, then after.",
        "Decide based on the number, not on how it feels.",
    ),
    example_md="""
Trade A: 40% chance of +3R, 60% chance of −1R. Expected value = 1.2 − 0.6 = **+0.6R**.

Trade B: 90% chance of +0.1R, 10% chance of −1.5R. Expected value = 0.09 − 0.15 = **−0.06R**.

Trade B wins almost all the time and still loses money. Many trading "systems" are like Trade B.
""".strip(),
    mistakes=("Being '100% sure'.", "Judging a decision by one outcome.", "Ignoring base rates."),
    evidence=fact(
        "This is arithmetic and basic probability. The hard part is estimating the inputs honestly, which is what this whole stage is about."
    ),
    try_it="Pick an open or hypothetical trade. Write your honest win probability and the expected payoff. Compute the expected value.",
    quiz=(
        Q(
            "A trade has a 90% chance of winning but loses a lot when it fails. It may…",
            ("Still have negative expected value", "Always be good", "Be illegal"),
            0,
            "Win rate alone does not determine expected value.",
        ),
        Q(
            "Someone says they are 80% sure about direction. A good reaction is…",
            ("Ask for evidence from a long record", "Trust them", "Double your size"),
            0,
            "Such claims are rarely supported.",
        ),
    ),
    takeaways=(
        "Think in odds and payoffs.",
        "Judge decisions, not single results.",
        "Start from an honest base rate.",
    ),
)

CHAPTERS = (
    chapter(
        "testing",
        "testing-honestly",
        "Testing honestly",
        "Lookahead, overfitting, costs, sample size, walk-forward, multiple testing and Monte Carlo.",
        (_LOOKAHEAD, _OVERFIT, _COSTS_TEST, _SAMPLE, _WALK, _MULTI, _MC),
    ),
    chapter(
        "testing",
        "finding-an-edge",
        "Finding an edge",
        "How to build an edge, what really predicts markets, and how to think in odds.",
        (_EDGE, _PREDICTS, _PROB),
    ),
)
