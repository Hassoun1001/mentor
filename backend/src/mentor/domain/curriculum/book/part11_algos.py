"""Stage 11 — Algorithms and prediction."""

from __future__ import annotations

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

_HOW = Lesson(
    slug="algos/how-markets-are-forecast",
    title="How markets are forecast",
    summary="The main approaches, and how to tell if a forecast is any good.",
    est_minutes=7,
    key_concepts=("forecast", "baseline", "benchmark", "calibration"),
    goal="Know the main ways markets are forecast and how to judge any forecast.",
    body_md="""
There are many ways to forecast a market, from a person's judgement to machine learning. The important question is not how clever a forecast looks. It is whether it beats a **simple baseline**.

### Common baselines

- **Random walk:** tomorrow's price equals today's. For exchange rates, this is famously hard to beat.
- **Trend or carry rules:** simple rules with a track record.
- **Coin flip:** 50% accuracy before costs.

### How to judge a forecast

- **Accuracy** after costs, not before.
- **Calibration:** when it says 60%, does it happen 60% of the time?
- **Stability:** does it hold across different periods?
- **Costs:** does it survive them?

### The app and you

This app forecasts direction and ranges, and grades itself in public on the Loop page. Its direction record is unproven and recently weak. That honest grading is the point: **a forecast you cannot grade is worthless**.
""".strip(),
    charts=(
        Chart(
            title="Live hit rate against break-even (this app)",
            caption="Windows that started while the market was open, since 14 October 2026: 18 predictions, 38.9% correct, against about 51.8% needed to break even. A very small sample, and currently below break-even.",
            data_kind="published",
            kind="bars",
            y_format="pct",
            y_label="Hit rate",
            source_note="This app's own live record as of early November 2026.",
            bars=(
                Bar("App's live hit rate", 38.9, "danger"),
                Bar("Break-even hit rate", 51.8, "warn"),
            ),
        ),
    ),
    steps=(
        "Write down the baseline you must beat.",
        "Score forecasts on data the model did not see.",
        "Include costs.",
        "Check calibration, not only accuracy.",
        "Keep score forever.",
    ),
    example_md="""
A model says "up" 60% of the time, and is right 53% of the time.

If break-even after costs is 52%, there might be a small edge. But with 500 forecasts the 95% range on that 53% is about ±4.4 points, so the true figure might be below 52%. Keep collecting data before believing it.
""".strip(),
    mistakes=(
        "Judging a model by its accuracy before costs.",
        "Comparing against no baseline.",
        "Trusting a forecaster with no record.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
Meese and Rogoff's work, and Rossi's later survey, show that beating a simple random walk at short horizons is very hard for exchange rates. Forecasting ability depends on predictor, horizon and sample.

Machine learning has shown some success in equities (Gu, Kelly and Xiu) but those results are from researchers using large datasets across thousands of stocks. They do not prove any individual retail forecast works.
""".strip(),
    ),
    try_it="Open the app's record page. Write the sample size and the hit rate. Would you call that proof?",
    quiz=(
        Q(
            "What must a useful forecast beat?",
            ("A simple baseline after costs", "Nothing", "A friend's guess"),
            0,
            "Without a baseline, you cannot know if it is any good.",
        ),
        Q(
            "What does calibration check?",
            (
                "Whether stated probabilities match real frequencies",
                "Whether a chart is colourful",
                "Whether costs are zero",
            ),
            0,
            "If it says 60%, it should happen about 60% of the time.",
        ),
    ),
    takeaways=(
        "Always compare with a baseline.",
        "Score out of sample, after costs.",
        "This app's record is unproven.",
    ),
    sources=("rossi-2013", "gu-kelly-xiu-2020"),
)

_FUND = Lesson(
    slug="algos/fundamental-and-macro-models",
    title="Fundamental and macro models",
    summary="Using economic data to forecast.",
    est_minutes=7,
    key_concepts=("macro model", "Taylor rule", "purchasing power parity", "fair value"),
    goal="Understand macro forecasting models and their well-known limits.",
    body_md="""
**Macro models** use economic variables, such as interest rates and inflation, to estimate fair value or to forecast prices.

### Examples

- **Interest rate differentials:** used to forecast currencies.
- **Purchasing power parity:** the idea that exchange rates should adjust so a basket of goods costs the same across countries, over very long periods.
- **Taylor rule:** an estimate of where a central bank should set rates, given inflation and output.
- **Earnings-based valuation** for stocks.

### Limits

- Macro data arrives late and gets revised.
- Fair value can stay far from price for years.
- Short-horizon results are weak. Models that explain the past often fail on new data.

These models tend to be better for **direction over longer periods** than for short-term trades.
""".strip(),
    charts=(
        Chart(
            title="Fair value versus price, over years",
            caption="Illustrative: a fair-value model can correctly point the way over years, while the price stays far from it for long stretches.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Index",
            x_label="Years",
            x_labels=tuple(str(y) for y in range(1, 11)),
            series=(
                Series(
                    "Model fair value",
                    (100, 101, 102, 103, 104, 105, 106, 107, 108, 109),
                    "accent",
                    "dashed",
                ),
                Series("Price", (100, 92, 88, 95, 112, 118, 108, 101, 106, 110), "danger"),
            ),
        ),
    ),
    steps=(
        "State what the model predicts and over what horizon.",
        "Use only data available at the time.",
        "Compare with a random-walk forecast.",
        "Allow for data revisions.",
    ),
    example_md="""
A macro model suggests EUR/USD is 8% undervalued.

An honest use: a small position over a long horizon, with a wide stop. It tells you little about next week. If you act only on that number and use high leverage, the price can move further against you for a year or more before it corrects, if it ever does.
""".strip(),
    mistakes=(
        "Using a long-term model for short-term timing.",
        "Assuming fair value must be reached.",
        "Using final revised data in a backtest.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
Rossi's survey finds predictability is most visible when using Taylor-rule fundamentals or net foreign assets, with linear models and few parameters. But overall the evidence for short-horizon forecasting from macro data is weak, and predictability depends heavily on the sample.
""".strip(),
    ),
    try_it="Pick one macro variable you think matters for your market, and chart it against the price for 10 years. Does the relationship look stable?",
    quiz=(
        Q(
            "Macro models are generally better for…",
            ("Long-term direction", "Tick-by-tick trading", "Choosing a stop"),
            0,
            "They are weak at short horizons.",
        ),
        Q(
            "Why must you use data as it was at the time?",
            ("Economic data is revised", "Old data is free", "Regulators require it"),
            0,
            "Using revised data introduces lookahead bias.",
        ),
    ),
    takeaways=(
        "Macro models work best over long horizons.",
        "Short-term forecasting from macro is weak.",
        "Use point-in-time data.",
    ),
    sources=("rossi-2013",),
)

_SENT = Lesson(
    slug="algos/sentiment-models",
    title="Sentiment models",
    summary="Trying to measure the crowd's mood from news and positioning.",
    est_minutes=6,
    key_concepts=("sentiment", "text analysis", "contrarian", "positioning"),
    goal="Understand how sentiment is measured and what to expect from it.",
    body_md="""
**Sentiment** tries to measure the mood of the market. Sources include:

- **News text:** counting positive and negative words, or using language models.
- **Social media:** volume and tone.
- **Positioning:** data such as the COT report.
- **Surveys** of investors.

### How it is used

Sometimes sentiment is used directly: positive news leads to buying. Often it is used in reverse: when everyone agrees, the trade may be crowded. This reversal idea is called **contrarian**.

### The catch

News sentiment is often already in the price. Social-media sentiment is noisy and can be manipulated. Results often depend on the source and period.

This app uses GDELT news sentiment as one input. It is not proven to give the app an edge.
""".strip(),
    charts=(
        Chart(
            title="A sentiment signal, over time",
            caption="Illustrative: sentiment often moves together with price, so it is hard to know whether it leads or follows.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Index",
            x_label="Weeks",
            series=(
                Series("Price", (100, 102, 101, 104, 108, 112, 110, 106, 103, 105), "accent"),
                Series(
                    "Sentiment",
                    (100, 101, 103, 103, 106, 110, 112, 108, 104, 104),
                    "warn",
                    "dashed",
                ),
            ),
        ),
    ),
    steps=(
        "Define sentiment precisely, with a data source.",
        "Check if it leads prices or just follows them.",
        "Test against a simple baseline.",
        "Treat extreme readings as warnings, not triggers.",
    ),
    example_md="""
A sentiment index for the euro has been at its highest level for a year.

Contrarian reading: "The trade is crowded." Trend reading: "Strong sentiment supports the rally." Both are stories. Only a test on your market can tell you which, if either, adds value.
""".strip(),
    mistakes=(
        "Trusting sentiment because it seems modern.",
        "Mixing lead and lag.",
        "Overfitting to one news event.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Sentiment research finds some relationships with short-term returns, but they are often small and sensitive to definitions. (We cite Tetlock's work from general knowledge; it was not re-opened during this research pass.) The COT report provides real positioning data, but it is delayed.
""".strip(),
    ),
    try_it="Find one news sentiment chart for your market and overlay the price. Does sentiment lead, lag or move at the same time?",
    quiz=(
        Q(
            "What does 'contrarian' mean?",
            ("Betting against the crowd", "Betting with the crowd", "Trading only at night"),
            0,
            "It treats extremes as a warning sign.",
        ),
        Q(
            "Why is social-media sentiment difficult?",
            ("It is noisy and can be manipulated", "It is illegal", "It is always correct"),
            0,
            "Quality is low and bots are common.",
        ),
    ),
    takeaways=("Sentiment is noisy.", "Check if it leads or follows.", "Use extremes as warnings."),
    sources=("cftc-cot",),
)

_REG = Lesson(
    slug="algos/regression",
    title="Regression",
    summary="The simplest forecasting model, and often good enough.",
    est_minutes=7,
    key_concepts=("regression", "coefficient", "features", "R-squared", "regularisation"),
    goal="Understand what a regression model does and where it fits in forecasting.",
    body_md="""
**Regression** finds the best-fitting relationship between inputs and the thing you want to predict.

**Linear regression** fits a straight line, or a flat surface when there are several inputs: `prediction = a + b₁ × input₁ + b₂ × input₂`.

**Logistic regression** is used when you want a probability, such as the probability that the next period closes up.

### Key ideas

- **Features** are the inputs (for example momentum, volatility, rate differences).
- **Coefficients** show how much each feature matters.
- **R-squared** shows how much of the variation is explained. In financial returns, even a very small R-squared can be valuable, but very large values should make you suspicious.
- **Regularisation** penalises complexity to reduce overfitting.

### Why start here

Regression is cheap, transparent, and hard to fool yourself with. A complicated model should have to beat it clearly on unseen data.

This app uses logistic regression among its direction models.
""".strip(),
    charts=(
        Chart(
            title="A weak but real regression fit",
            caption="Illustrative scatter represented as a noisy line and a fitted line. In finance, a relationship can be real and still explain very little.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Next-period return",
            x_label="Signal",
            series=(
                Series(
                    "Observations",
                    (
                        -2.1,
                        1.2,
                        -0.4,
                        2.0,
                        -1.5,
                        0.8,
                        1.9,
                        -0.9,
                        2.4,
                        0.3,
                        1.1,
                        -0.7,
                        2.8,
                        0.9,
                        1.5,
                    ),
                    "muted",
                    "dashed",
                ),
                Series("Fitted line", tuple(-0.8 + i * 0.16 for i in range(15)), "accent"),
            ),
        ),
    ),
    steps=(
        "Choose a small number of inputs with a reason behind them.",
        "Standardise them using past data only.",
        "Fit the model on training data.",
        "Evaluate it on unseen data.",
        "Compare with a baseline.",
    ),
    example_md="""
A logistic regression predicts next-day up or down from last week's return and current volatility.

On test data it shows 53.2% accuracy, against 50.7% for always predicting 'up'. After 1 pip of costs, it is not clearly better than the baseline. A regression makes this kind of honest comparison simple.
""".strip(),
    mistakes=(
        "Adding features until accuracy rises.",
        "Standardising with future data.",
        "Reading a large R-squared as success.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Rossi's review finds predictability is most visible with simple, linear models with few parameters. Gu, Kelly and Xiu found linear methods were outperformed by more flexible ones when predicting US stock returns, but linear models remain important baselines.
""".strip(),
    ),
    try_it="In a spreadsheet, fit a simple regression of tomorrow's return on today's return. How much does it explain? Now compare it to using no predictor at all.",
    quiz=(
        Q(
            "Which regression gives a probability?",
            ("Logistic", "Linear", "None"),
            0,
            "Logistic regression outputs a probability.",
        ),
        Q(
            "Why compare with a simple baseline?",
            ("Complex models must earn their complexity", "To save electricity", "Regulators ask"),
            0,
            "Complexity needs to pay for itself.",
        ),
    ),
    takeaways=(
        "Regression is simple and transparent.",
        "Small R-squared is normal.",
        "Use it as a baseline.",
    ),
    sources=("rossi-2013", "gu-kelly-xiu-2020"),
)

_TREE = Lesson(
    slug="algos/tree-models",
    title="Tree models",
    summary="Decision trees, random forests and boosting.",
    est_minutes=7,
    key_concepts=(
        "decision tree",
        "random forest",
        "gradient boosting",
        "feature interactions",
        "hyperparameters",
    ),
    goal="Understand tree models, why they often do well, and how they overfit.",
    body_md="""
A **decision tree** asks a sequence of yes-or-no questions: "is momentum positive?", "is volatility high?" and so on, until it reaches a prediction.

One tree is unstable. So we combine many.

- A **random forest** averages many trees built on random subsets of the data.
- **Gradient boosting** builds trees one after another, each correcting the errors of the previous ones.

### Why they are popular

Trees capture **interactions** automatically: for example, momentum may help only when volatility is low. They handle messy data well and need less preparation.

### The risks

- They overfit easily, with many **hyperparameters**, settings chosen before training.
- They can be slow to retrain and hard to explain.

This app's direction models use gradient boosting among others. They are tested with honest walk-forward results, and live results are still unproven.
""".strip(),
    charts=(
        Chart(
            title="How a tree model fits better with more depth",
            caption="Illustrative. Deeper trees fit past data better, but beyond some depth they do worse on unseen data.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Score",
            x_label="Tree depth",
            x_labels=tuple(str(d) for d in range(1, 11)),
            series=(
                Series(
                    "Past data",
                    (0.51, 0.53, 0.55, 0.58, 0.62, 0.66, 0.71, 0.75, 0.80, 0.86),
                    "danger",
                ),
                Series(
                    "Unseen data",
                    (0.50, 0.52, 0.53, 0.53, 0.52, 0.52, 0.51, 0.50, 0.49, 0.49),
                    "accentSoft",
                ),
            ),
        ),
    ),
    steps=(
        "Start with a small, simple model.",
        "Use a walk-forward test.",
        "Limit depth and number of trees.",
        "Compare with logistic regression.",
        "Check which features are doing the work.",
    ),
    example_md="""
A gradient-boosting model is trained on 2015–2021 data, and tested on 2022–2023.

Training accuracy: 68%. Test accuracy: 52.3%. The drop is a warning, though it is common in finance. Compare it with a regression at 52.1% and ask if the added complexity is worth it.
""".strip(),
    mistakes=(
        "Believing high training accuracy.",
        "Tuning hyperparameters on test data.",
        "Using too many features.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Gu, Kelly and Xiu found trees and neural networks performed best in predicting US stock returns across many methods, using broad data. That is meaningful, but it is a large cross-section of stocks, and it does not guarantee results for one currency pair.

Whether a tree model produces a tradable edge on a single market after costs has to be tested.
""".strip(),
    ),
    try_it="Train a small decision tree on past data with a free tool, and check its accuracy on data it did not see. Compare with always predicting up.",
    quiz=(
        Q(
            "What does a random forest do?",
            ("Averages many trees", "Uses one very deep tree", "Plants trees"),
            0,
            "Averaging reduces overfitting.",
        ),
        Q(
            "What is a warning sign?",
            (
                "Training accuracy far above test accuracy",
                "Test accuracy near baseline",
                "A simple model",
            ),
            0,
            "A large gap suggests overfitting.",
        ),
    ),
    takeaways=(
        "Trees capture interactions.",
        "They overfit easily.",
        "Always compare with a simple baseline.",
    ),
    sources=("gu-kelly-xiu-2020",),
)

_NN = Lesson(
    slug="algos/neural-networks",
    title="Neural networks",
    summary="Flexible models that need a lot of data and care.",
    est_minutes=7,
    key_concepts=("neural network", "layers", "deep learning", "noise"),
    goal="Understand what neural networks can and cannot do for trading.",
    body_md="""
A **neural network** passes inputs through layers of simple calculations, with weights learned from data. With enough layers, it can represent very complex relationships. **Deep learning** refers to models with many layers.

### Where they shine

They excel when there is a lot of data with strong structure, such as images and language.

### Why markets are hard

- Financial data has a very low **signal-to-noise ratio**: the true pattern is tiny compared with the random movement.
- Markets change over time.
- There are far fewer independent data points than you might think. Twenty years of daily data is about 5,000 points, tiny for a deep model.

Neural networks can capture useful non-linearities when data is plentiful, such as across thousands of stocks. Applying a large network to one currency pair with limited history is a good way to overfit.
""".strip(),
    charts=(
        Chart(
            title="Signal and noise in daily returns",
            caption="Illustrative: tiny signal compared with large noise, which is why flexible models tend to fit the noise.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Size",
            bars=(
                Bar("Typical daily move", 100, "muted"),
                Bar("Real predictable part", 3, "accentSoft"),
            ),
        ),
    ),
    steps=(
        "Start with simple models.",
        "Use a neural network only with plenty of data.",
        "Use strict walk-forward validation.",
        "Regularise heavily.",
        "Compare after costs.",
    ),
    example_md="""
A trader trains a neural network on 10 years of 1-hour EUR/USD candles. In-sample accuracy is 71%.

On out-of-sample data, it scores 50.2%. After costs, it loses. The network learned the noise.

Researchers have got better results by pooling data across thousands of stocks, which gives far more data for each pattern.
""".strip(),
    mistakes=(
        "Using a big model on a small dataset.",
        "Reading training accuracy as a result.",
        "Believing 'AI' is magic.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Gu, Kelly and Xiu found neural networks performed well in predicting US stock returns using large cross-sections. Evidence for single-market retail trading with neural nets is weak, and most public claims lack proper out-of-sample testing.
""".strip(),
    ),
    try_it="Count how many independent data points your strategy really has. How many weights would a simple neural network have? Compare the two.",
    quiz=(
        Q(
            "Why are markets hard for neural networks?",
            (
                "Very low signal-to-noise and limited data",
                "They cannot do maths",
                "They need candles",
            ),
            0,
            "Flexible models learn the noise.",
        ),
        Q(
            "Where have neural nets shown results?",
            (
                "Across large sets of stocks with lots of data",
                "Single-pair day trading with no costs",
                "Coin flips",
            ),
            0,
            "Large datasets are key.",
        ),
    ),
    takeaways=(
        "Flexible models overfit noise.",
        "Markets have a low signal-to-noise ratio.",
        "Use them only with plenty of data.",
    ),
    sources=("gu-kelly-xiu-2020",),
)

_REGIME = Lesson(
    slug="algos/regime-models",
    title="Regime models",
    summary="Recognising that markets change character.",
    est_minutes=7,
    key_concepts=("regime", "hidden Markov", "volatility clustering", "GARCH"),
    goal="Understand regime models and how they are used to adjust trading.",
    body_md="""
A **regime** is a market's current character: calm and trending, or wild and choppy. Many strategies work in one regime and fail in another.

### Common approaches

- **Rule-based:** for example, ATR above its 200-day average means a high-volatility regime.
- **Hidden Markov models**, developed from Hamilton's work: the model assumes the market is in a hidden state, and estimates the probabilities of being in each state and switching between them.
- **GARCH**, a volatility model that captures clustering: big moves follow big moves.

### What is useful

- **Volatility** is far easier to forecast than direction, thanks to clustering. That makes volatility regimes useful for sizing.
- Regime labels help you know when to stand aside.

### The catch

Regimes are clearest in hindsight. By the time you are sure, it may be changing again.

This app uses a regime indicator to help decide when to stand aside, and to set range expectations.
""".strip(),
    charts=(
        Chart(
            title="Volatility clusters",
            caption="Illustrative: quiet periods and wild periods cluster together, which is why volatility can be forecast better than direction.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Daily volatility",
            x_label="Days",
            series=(
                Series(
                    "Volatility",
                    (
                        1,
                        1.1,
                        0.9,
                        1,
                        1.2,
                        1.1,
                        3.8,
                        4.2,
                        3.5,
                        3.0,
                        2.2,
                        1.8,
                        1.4,
                        1.2,
                        1,
                        1.1,
                        0.9,
                        1,
                        3.2,
                        4.0,
                        3.6,
                        2.5,
                        2.0,
                        1.5,
                        1.2,
                    ),
                    "accent",
                    "area",
                ),
            ),
        ),
    ),
    steps=(
        "Choose a simple regime definition first.",
        "Check if your strategy's results differ by regime.",
        "Decide what to do in each regime.",
        "Test whether the regime signal is available in time.",
    ),
    example_md="""
A trend strategy earned **+0.4R** per trade when volatility was rising from low levels, and **−0.2R** in very choppy markets.

A regime rule: "only trade if ATR(14) is above its 50-day average and the trend filter agrees." That rule removes a poor regime. Test it on data you did not use to find it.
""".strip(),
    mistakes=(
        "Defining regimes after seeing the results.",
        "Using a regime filter that lags too much.",
        "Treating a volatility forecast as a direction forecast.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Volatility clustering is one of the most established facts in finance (Mandelbrot, 1963; Engle's ARCH models, which won a Nobel Prize). Regime-switching models have been widely studied since Hamilton (1989). Whether a retail trader can profit from identifying regimes is less clear; many practical regimes are only obvious in hindsight.
""".strip(),
    ),
    try_it="Split your journal's results into 'high volatility' and 'low volatility' using ATR. Do they differ?",
    quiz=(
        Q(
            "Why can volatility be forecast better than direction?",
            ("Volatility clusters", "Direction is illegal to forecast", "Volatility never changes"),
            0,
            "Big moves tend to follow big moves.",
        ),
        Q(
            "What is the main problem with regimes?",
            ("They are clearest in hindsight", "They do not exist", "They are illegal"),
            0,
            "Knowing the regime in real time is the hard part.",
        ),
    ),
    takeaways=(
        "Markets change character.",
        "Volatility clusters.",
        "Regimes are clearest in hindsight.",
    ),
    sources=("mandelbrot-1963", "hamilton-regimes"),
)

_EXEC = Lesson(
    slug="algos/execution-algorithms",
    title="Execution algorithms: TWAP and VWAP",
    summary="How large orders are split so they do not move the price.",
    est_minutes=7,
    key_concepts=("TWAP", "VWAP", "market impact", "implementation shortfall"),
    goal="Understand how and why large orders are split into pieces.",
    body_md="""
A large order placed all at once pushes the price against you. **Execution algorithms** split it into small pieces.

- **TWAP** (time-weighted average price) splits an order evenly over time.
- **VWAP** (volume-weighted average price) splits an order in line with expected market volume.
- **Implementation shortfall** aims to minimise the total cost, compared with the price when the decision was made.

### The trade-off

Trade fast and you pay a lot of **market impact**. Trade slowly, and the price might move away from you. Almgren and Chriss formalised this trade-off between impact and price risk.

### Why this matters to you

Most retail orders are too small to need this. Knowing about it is useful, because it explains why institutional trades take time and why large moves can continue over several days. It also explains why large players care about VWAP as a benchmark.
""".strip(),
    charts=(
        Chart(
            title="Slicing an order: TWAP and VWAP",
            caption="Illustrative: a parent order divided across a day. TWAP is even. VWAP follows a typical busy-morning-and-close volume pattern.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Share of the order in each interval",
            x_label="Time of day",
            x_labels=("9:30", "10", "11", "12", "1", "2", "3", "4"),
            series=(
                Series("TWAP", (12.5, 12.5, 12.5, 12.5, 12.5, 12.5, 12.5, 12.5), "muted", "dashed"),
                Series("VWAP", (20, 16, 11, 8, 7, 9, 13, 16), "accent"),
            ),
        ),
    ),
    steps=(
        "Compare your order size to normal market volume.",
        "If small, a simple limit or market order is fine.",
        "If large, split it over time.",
        "Measure your fill against VWAP.",
    ),
    example_md="""
A fund wants to buy **$50 million** of a stock that trades $200 million a day. A single order would be 25% of daily volume and would push the price a lot.

Using VWAP over the full day spreads it out: it pays close to the day's average price, and leaves little trace. If you only need to buy $2,000, none of this applies.
""".strip(),
    mistakes=(
        "Assuming a small retail order needs an algo.",
        "Thinking TWAP guarantees a good price.",
        "Ignoring market impact on larger accounts.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Market impact is well documented, and execution algorithms are standard at institutions. The Almgren-Chriss framework is widely used to think about the trade-off. For retail-size orders, the benefit is usually negligible.
""".strip(),
    ),
    try_it="Find your typical order size as a percentage of average volume in your market. Decide if you would need to split it.",
    quiz=(
        Q(
            "TWAP splits an order…",
            ("Evenly over time", "By volume", "Randomly"),
            0,
            "TWAP is time-weighted.",
        ),
        Q(
            "What is the main trade-off in execution?",
            ("Market impact versus price risk", "Colour versus font", "Spread versus swap"),
            0,
            "Trade fast and pay impact; trade slowly and bear price risk.",
        ),
    ),
    takeaways=(
        "Large orders are split up.",
        "Impact and timing risk trade off.",
        "Retail orders rarely need this.",
    ),
    sources=("almgren-chriss",),
)

_AUTOMATION = Lesson(
    slug="toolkit/screening-and-automation",
    title="Screening and automation",
    summary="What to automate, and what to be careful about.",
    est_minutes=6,
    key_concepts=("screener", "alerts", "Python", "backtesting library", "bot risk"),
    figures=(Figure("automation-stack", "Automate analysis first. Execution last."),),
    goal="Automate the boring parts of trading without creating new risks.",
    body_md="""
Once you have a process, tools can remove the boring work.

- **Screeners** filter hundreds of instruments down to the few that fit your rules.
- **Alerts** let the platform watch price and notify you when a level is hit. This is a cure for overtrading from boredom.
- **Code:** Python with `pandas` for data, `backtesting.py` or `vectorbt` for testing, `scikit-learn` for models. You can test an idea on years of data in seconds. This is how this app's backend works.

### The hard line

Automate **analysis, screening, alerts and testing** freely. Be extremely careful automating **execution**: a bot with a sizing bug can empty an account faster than any human can. If you do automate trades, the risk limits must live in the code, not in your intentions.

### A safe path

1. Backtest. 2. Paper-trade automatically. 3. Run live with tiny size. 4. Add safety switches, such as a daily loss limit that stops the bot.
""".strip(),
    charts=(
        Chart(
            title="Risk of automating each task",
            caption="Illustrative judgement, not data: how dangerous a bug in each task can be, 1 (low) to 10 (high).",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Danger of a bug",
            bars=(
                Bar("Screeners", 2, "accentSoft"),
                Bar("Alerts", 2, "accentSoft"),
                Bar("Backtesting", 3, "accent"),
                Bar("Paper trading", 3, "accent"),
                Bar("Live execution", 10, "danger"),
            ),
        ),
    ),
    steps=(
        "Automate your data and alerts first.",
        "Write tests for any code that calculates size.",
        "Paper-trade before going live.",
        "Add a kill switch.",
        "Log everything.",
    ),
    example_md="""
A trader automates a strategy. A bug multiplies lot size by 100 on one instrument because a contract size changed.

With a hard cap in code ("no order bigger than 0.5 lots") the order is rejected and an alert goes out. Without it, the account could be wiped out in seconds.
""".strip(),
    mistakes=(
        "Automating before you have a tested edge.",
        "Running a bot without a kill switch.",
        "Trusting code without tests.",
    ),
    evidence=fact(
        "Automation does not create an edge. It just carries out your rules, including mistakes, very quickly."
    ),
    try_it="Set one price alert on the market you trade. Practise waiting for it instead of watching the chart.",
    quiz=(
        Q(
            "What should you automate first?",
            ("Analysis and alerts", "Live execution", "Nothing ever"),
            0,
            "Automate what is low risk.",
        ),
        Q(
            "Where should risk limits for a bot live?",
            ("In the code", "In your intentions", "In your memory"),
            0,
            "Limits must be enforced automatically.",
        ),
    ),
    takeaways=(
        "Automate analysis first.",
        "Execution automation is the most dangerous.",
        "Build in hard limits.",
    ),
)

CHAPTERS = (
    chapter(
        "algos",
        "forecasting",
        "Forecasting",
        "How markets are forecast, from macro models to machine learning.",
        (_HOW, _FUND, _SENT, _REG, _TREE, _NN, _REGIME),
    ),
    chapter(
        "algos",
        "execution-and-automation",
        "Execution and automation",
        "How orders are worked, and what you should and should not automate.",
        (_EXEC, _AUTOMATION),
    ),
)
