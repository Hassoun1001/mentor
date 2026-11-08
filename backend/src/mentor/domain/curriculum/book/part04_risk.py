"""Stage 4 — Risk and position sizing."""

from __future__ import annotations

import math

from mentor.domain.curriculum.book import more_risk
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
    candle_chart,
    chapter,
    fact,
)
from mentor.domain.curriculum.charts import equity_paths, path


def _losing_run_probability(run: int, trades: int, loss_rate: float) -> float:
    """Exact chance of at least one run of ``run`` losses in ``trades`` independent trades."""
    # streak[k] = probability of being alive with a current losing streak of k.
    streak = [0.0] * run
    streak[0] = 1.0
    hit = 0.0
    for _ in range(trades):
        next_streak = [0.0] * run
        for k, chance in enumerate(streak):
            next_streak[0] += chance * (1 - loss_rate)
            if k + 1 == run:
                hit += chance * loss_rate
            else:
                next_streak[k + 1] += chance * loss_rate
        streak = next_streak
    return hit


def _ruin_probability(
    win_rate: float, win_r: float, risk_pct: float, trades: int, floor: float
) -> float:
    """Exact chance that compounding at fixed risk falls to ``floor`` at any point.

    Equity depends only on the count of wins and losses, so one sweep over the
    (wins, losses) grid gives the exact answer without simulation.
    """
    f = risk_pct / 100
    alive: dict[tuple[int, int], float] = {(0, 0): 1.0}
    for _ in range(trades):
        next_alive: dict[tuple[int, int], float] = {}
        for (wins, losses), chance in alive.items():
            for won, p in ((True, win_rate), (False, 1 - win_rate)):
                state = (wins + 1, losses) if won else (wins, losses + 1)
                if (1 + f * win_r) ** state[0] * (1 - f) ** state[1] <= floor:
                    continue
                next_alive[state] = next_alive.get(state, 0.0) + chance * p
        alive = next_alive
    survive = sum(alive.values())
    return 1 - survive


_WHY_RISK = Lesson(
    slug="risk-first/why-risk-beats-prediction",
    title="Why risk management beats prediction",
    summary="Most traders fail on position size, not on direction.",
    est_minutes=7,
    key_concepts=("position sizing", "expectancy", "drawdown", "ruin"),
    figures=(
        Figure(
            "risk-vs-predict",
            "Small risk with a lower win rate can beat big risk with a higher win rate.",
        ),
    ),
    goal="Understand why how much you risk matters more than being right.",
    body_md="""
The popular myth says good traders predict the market. The more accurate picture is that they manage their losses.

Compare two traders over a long run:

- **Trader A** is right **55%** of the time and risks **10%** of the account on each trade.
- **Trader B** is right **45%** of the time and risks **1%** on each trade.

Trader A is the better predictor. Trader A is also far more likely to blow up, because 10% risk per trade means a normal losing run destroys the account.

The reason is the **asymmetry of losses**. Losing 50% requires gaining 100% just to get back to the start. Losing 80% requires 400%. Big losses are the ones that really matter.

### The app's view

The risk engine was built before any forecast. The position-size calculator sizes every trade from your stop, not your hope. Guardrails block a trade if it breaks your per-day or portfolio limit.

If a feature gets in the way of disciplined sizing, the feature is wrong and the discipline is right.

Prediction is hard. A small, consistent risk per trade lets you survive being wrong.
""".strip(),
    charts=(
        Chart(
            title="Gain needed to recover from a loss",
            caption="Calculated. If you lose x% you need x / (100 − x) to get back to where you started. The gap grows faster and faster.",
            data_kind="calculated",
            kind="bars",
            y_format="pct",
            y_label="Gain needed to recover",
            x_label="Size of loss",
            bars=(
                Bar("Lose 10%", round(10 / 90 * 100, 1), "accentSoft"),
                Bar("Lose 20%", 25.0, "accent"),
                Bar("Lose 30%", round(30 / 70 * 100, 1), "accent"),
                Bar("Lose 50%", 100.0, "warn"),
                Bar("Lose 75%", 300.0, "danger"),
                Bar("Lose 90%", 900.0, "danger"),
            ),
        ),
    ),
    steps=(
        "Decide on a fixed percentage of your account to risk per trade. Many traders use 0.5–2%.",
        "Before every trade, work out the money amount you are risking.",
        "If the stop would cost more than that amount, reduce the size or skip the trade.",
        "Write down your risk for each trade in your journal.",
        "Never raise your risk because you feel confident.",
    ),
    example_md="""
Both traders start with $10,000.

**Trader A** risks 10% and loses three in a row: $10,000 → $9,000 → $8,100 → **$7,290**. Down 27%.

**Trader B** risks 1% and loses three in a row: $10,000 → $9,900 → $9,801 → **$9,703**. Down 3%.

Trader A now needs a gain of about 37% to get back to even. Trader B needs about 3%.
""".strip(),
    mistakes=(
        "Spending all your effort on entries and none on sizing.",
        "Increasing risk to 'make back' a loss.",
        "Thinking a higher win rate protects you. A long losing run can still wipe out an account that uses big risk.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
The arithmetic of recovery is certain. Regulators found that most retail leveraged accounts lose money, and limiting leverage was one of their main responses.

There is no controlled study proving a specific figure like '1%' is best. The right percentage depends on your strategy's real results, and on how much pain you can stand. What is certain is that risking a large share per trade makes ruin far more likely, whatever your win rate.
""".strip(),
    ),
    try_it="Write your maximum risk per trade as a percentage and as a money amount for your demo account. Put it where you can see it.",
    quiz=(
        Q(
            "Who is more likely to survive long-term?",
            (
                "55% win rate, risking 10% per trade",
                "45% win rate, risking 1% per trade",
                "They are equivalent, only win rate matters",
            ),
            1,
            "Sizing beats accuracy. With 10% risk a normal losing run ruins the account.",
        ),
        Q(
            "If you lose 50% of your account, what gain do you need to get back to even?",
            ("50%", "100%", "150%"),
            1,
            "Half of what you have left must double. Big losses need disproportionately big recoveries.",
        ),
    ),
    takeaways=(
        "How much you risk matters more than being right.",
        "Big losses need disproportionately big recoveries.",
        "Pick a fixed small risk and stick to it.",
    ),
    sources=("esma-cfd-2018",),
)

_RUN_TABLE = {k: round(_losing_run_probability(k, 100, 0.5) * 100, 1) for k in (4, 5, 6, 7, 8, 10)}

_ONE_PERCENT = Lesson(
    slug="risk-first/the-one-percent-rule",
    title="The 1% rule and where it comes from",
    summary="It is not magic. It is about how long you can survive a losing streak.",
    est_minutes=7,
    key_concepts=("risk per trade", "drawdown", "losing streak", "risk of ruin"),
    figures=(
        Figure("drawdown-recovery", "The deeper the loss, the bigger the gain needed to recover."),
    ),
    goal="Know what the 1% rule really protects you from, and choose your own number.",
    body_md="""
Risking 1% per trade is not a sacred number. It is a **survival** number.

Losing streaks are completely normal. Even a good strategy will have them. Look at the chart: in 100 trades that win 50% of the time, the chance of at least one streak of **7 losses in a row** is about **32%**, and a streak of 5 is very likely.

So plan for that streak:

- At **1%** risk, seven losses costs about **6.8%**. Uncomfortable, and recoverable.
- At **5%** risk, seven losses costs about **30%**, and needs about 43% to recover.
- At **10%** risk, seven losses costs about **52%**, and you are probably done psychologically and practically.

### Choosing your number

- **1–2%** is the textbook range for discretionary traders.
- **0.25–1%** is common among professionals and in prop firm evaluations.
- Below 0.5% can be sensible while you are still learning.
- If you risk less than you could afford, you lose nothing but some speed.

Fixed percentage risk also **automatically shrinks** your size when you are losing and grows it when you are winning.
""".strip(),
    charts=(
        Chart(
            title="Chance of at least one losing streak in 100 trades",
            caption="Exact calculation, assuming each trade is independent and wins 50% of the time. This is why the rule exists.",
            data_kind="calculated",
            kind="bars",
            y_format="pct",
            y_label="Chance of at least one streak",
            x_label="Length of losing streak",
            bars=tuple(
                Bar(f"{k} losses in a row", v, "danger" if v > 25 else "warn")
                for k, v in _RUN_TABLE.items()
            ),
        ),
    ),
    steps=(
        "Pick the longest losing streak you think is realistic for your strategy, then add a few more.",
        "Multiply that streak by your planned risk, and treat the total as your likely deep drawdown.",
        "Ask yourself honestly whether you could keep trading after that drawdown.",
        "If not, reduce your risk until you could.",
        "Review your number every few months using your actual results.",
    ),
    example_md="""
Your strategy wins about 45% of the time. Over 100 trades the chance of a losing streak of 8 or more is high enough to expect it to happen eventually.

- At **0.5%** per trade, a streak of 8 costs about **3.9%**.
- At **1%** per trade, a streak of 8 costs about **7.7%**.
- At **2%** per trade, a streak of 8 costs about **14.9%**.
- At **5%** per trade, a streak of 8 costs about **33.7%**.

If you know you would panic at 20%, the 5% version is not a choice you can really make, however good the strategy looks.
""".strip(),
    mistakes=(
        "Treating 1% as fixed truth rather than a sensible starting point.",
        "Adding many open trades at 1% each, so that your real risk is 5%.",
        "Risking 1% but leaving no stop, so a single trade can cost far more.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
The arithmetic of streaks is exact. The **specific number 1%** is a rule of thumb that practitioners use, and no controlled study proves it best. The right figure depends on your win rate, your payoffs and your tolerance for drawdowns.

The sensible claim is smaller: small fixed percentage risk makes ruin far less likely. Kelly-based analysis (later in this stage) shows that betting too big reduces long-run growth, even when you have a real edge.
""".strip(),
    ),
    try_it="Assume a streak of 10 losing trades. Compute the account drop at 0.5%, 1% and 2% risk per trade. Which drop could you actually live with?",
    quiz=(
        Q(
            "In 100 trades at 50% win rate, how likely is at least one streak of 7 losses in a row?",
            ("About 1%", "About 32%", "About 90%"),
            1,
            "It is about 32%, so you must expect streaks like this to happen.",
        ),
        Q(
            "What is the main purpose of the 1% rule?",
            (
                "It maximises profit",
                "It lets you survive normal losing streaks",
                "It raises your win rate",
            ),
            1,
            "It does not make you right more often. It keeps you in the game when you are wrong.",
        ),
    ),
    takeaways=(
        "Losing streaks are normal, even for good strategies.",
        "Pick a risk per trade based on the drawdown you can survive.",
        "1% is a sensible starting point, not a law.",
    ),
)

_SIZE = Lesson(
    slug="risk-first/size-from-your-stop",
    title="Sizing from your stop, not your target",
    summary="The position-size formula, and why the target is not in it.",
    est_minutes=7,
    key_concepts=("position size", "stop", "pip value", "ceiling"),
    figures=(
        Figure("size-formula", "Risk amount ÷ (stop distance × value per pip) = position size."),
    ),
    goal="Be able to work out exactly how big your position should be, from your stop.",
    body_md="""
Position size comes from your stop.

**Risk amount = account × risk percentage.**
**Stop distance = entry price − stop price (ignoring the sign).**
**Lots = risk amount ÷ (stop distance in pips × value per pip per lot).**

Notice what is *not* in the formula: your target. The target changes your reward-to-risk ratio. It does not change your size. A 30-pip stop and $100 of risk means you size for 30 pips, however far away your target is.

### Round down

The app's calculator rounds **down** to your broker's minimum lot. That is deliberate: your risk budget is a ceiling, not a target. A larger lot would put you over budget, and that is the one thing the system will never do.

If the rounded size is `0`, your stop is too far for the budget you have set. Choose a tighter stop that still makes sense, raise your budget carefully, or skip the trade.

### The step most people skip

Check the stop before the size. If the stop is placed where the market normally wanders, your size calculation is correct, but your trade is bad.
""".strip(),
    charts=(
        Chart(
            title="Same $100 risk, different stop distances",
            caption="Calculated for EUR/USD with $10 per pip per standard lot: position size = $100 / (stop pips × $10). A wider stop means a smaller position.",
            data_kind="calculated",
            kind="bars",
            y_format="plain",
            y_label="Lots",
            x_label="Stop distance",
            bars=(
                Bar("10 pip stop", 1.0, "accent"),
                Bar("20 pip stop", 0.5, "accent"),
                Bar("40 pip stop", 0.25, "accent"),
                Bar("80 pip stop", 0.12, "accent"),
                Bar("120 pip stop", 0.08, "accent"),
            ),
        ),
    ),
    steps=(
        "Decide your risk percentage and find your risk amount in money.",
        "Find the price that proves your idea wrong. That is your stop.",
        "Measure the distance from entry to stop in pips.",
        "Divide risk amount by (pips × value per pip per lot).",
        "Round down to a size your broker allows, and check the result.",
    ),
    example_md="""
Account **$8,000**, risk **1%**, so risk amount **$80**.

Trade EUR/USD: entry 1.0850, stop 1.0815, distance **35 pips**. Pip value per standard lot is **$10**.

Lots = $80 / (35 × $10) = 0.2285, rounded down to **0.22 lots**.

Check: 0.22 lots × $10 = $2.20 per pip. 35 pips × $2.20 = **$77**, within the $80 limit.

If your pair is priced in another currency, such as USD/JPY, the pip value changes with the price and is converted to your account currency. The calculator does this for you.
""".strip(),
    mistakes=(
        "Choosing the size first and the stop afterwards to fit.",
        "Placing a very tight stop only to make the position larger.",
        "Forgetting that pip value differs across instruments.",
    ),
    evidence=fact(
        "This is arithmetic. A correct size does not make a trade good. It only makes sure that being wrong costs what you agreed in advance."
    ),
    try_it="Use the app's calculator for three different stop distances on the same account. Then do one by hand and compare.",
    quiz=(
        Q(
            "Which of these does NOT affect your position size?",
            ("Your risk amount", "Your stop distance", "Your profit target"),
            2,
            "Target affects reward-to-risk, not size.",
        ),
        Q(
            "Account $5,000, risk 1%, stop 25 pips, EUR/USD. What is the size?",
            ("0.1 lots", "0.2 lots", "0.5 lots"),
            1,
            "$50 / (25 × $10) = 0.2 lots.",
        ),
    ),
    takeaways=(
        "Size comes from your stop and your risk amount.",
        "The target is not in the sizing formula.",
        "Round down, because the risk limit is a ceiling.",
    ),
)

_GUARDRAILS = Lesson(
    slug="risk-first/account-guardrails",
    title="Account guardrails",
    summary="Three limits that protect you from yourself.",
    est_minutes=6,
    key_concepts=("max risk per trade", "max open risk", "daily loss limit", "tilt"),
    figures=(
        Figure(
            "guardrails", "Three layered limits. The daily loss cap is the one that stops tilt."
        ),
    ),
    goal="Set three limits in advance that stop one bad day from becoming a disaster.",
    body_md="""
Three limits sit on top of your per-trade sizing.

- **Max risk per trade:** the hard cap on one position.
- **Max open risk:** the cap on all open trades together. Two trades at 2% each is 4% at risk.
- **Daily loss limit:** when your realised loss today hits this number, the day is over. No more trades.

The daily loss limit matters most. After two losses, the brain wants to "get it back". This is what traders call **tilt**: emotional trading after a loss. That instinct is how accounts die. The limit removes the choice.

Many professionals also use a **weekly** and a **monthly** limit, as prop firms do.

### Set them before you need them

Limits are only useful if you set them when calm. Write them in your plan and treat breaking one as a process failure, even if the trade made money.

The app's guardrail report names the rule, shows current against limit, and warns you when you get close.
""".strip(),
    charts=(
        Chart(
            title="How a daily limit changes a bad day",
            caption="Illustrative example: a trader keeps trading after losses without a limit. With a 2% daily loss limit the day stops early.",
            data_kind="illustrative",
            kind="lines",
            y_format="pct",
            y_label="Day's result",
            x_label="Trade number",
            x_labels=("0", "1", "2", "3", "4", "5", "6"),
            series=(
                Series(
                    "With a 2% daily limit", (0.0, -1.0, -2.0, -2.0, -2.0, -2.0, -2.0), "accentSoft"
                ),
                Series(
                    "No limit, chasing losses", (0.0, -1.0, -2.0, -4.0, -6.0, -9.0, -13.0), "danger"
                ),
            ),
        ),
    ),
    steps=(
        "Write your max risk per trade.",
        "Write your max open risk across all positions.",
        "Write your daily loss limit, usually 2 to 3 times your risk per trade.",
        "Set a weekly limit too.",
        "When a limit is hit, close the platform. Do not negotiate with it.",
    ),
    example_md="""
Account **$10,000**. Limits: 1% per trade, 3% open risk, 2% daily loss.

You lose **$100** on your first trade and **$110** on your second. Daily loss is **$210, or 2.1%**. You have hit your limit.

You feel you have spotted a great setup. **You stop anyway.**

If the setup worked, you missed one trade. If you are the kind of person who overrides limits, the setup does not matter. Over a career, one override can cost more than many missed trades.
""".strip(),
    mistakes=(
        "Treating a limit as a suggestion the moment it is reached.",
        "Counting only the risk on each trade and forgetting all your open positions together.",
        "Setting a daily limit too tight to survive normal noise.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Limits like these are standard in professional risk management and prop firm rules. There is little direct research showing a particular daily limit is best. The main support comes from behavioural research, such as Odean's work on investors holding losers, showing that people make worse decisions after losses.

Whether stops add value depends on how a market behaves, and that research is not reviewed in depth here. The job of these limits is mostly to stop emotional trading, which is a behavioural claim rather than a statistical one.
""".strip(),
    ),
    try_it="Write your three limits for your demo account, and the rule for what you do when you hit one.",
    quiz=(
        Q(
            "You have 2% risk on three open trades. What is your open risk?",
            ("2%", "4%", "6%"),
            2,
            "Open risk adds across positions. Correlated trades can make it worse.",
        ),
        Q(
            "Why is the daily loss limit so important?",
            (
                "It maximises profit",
                "It stops emotional trading after losses",
                "Brokers require it",
            ),
            1,
            "It removes the choice at the moment you are most likely to make a bad one.",
        ),
    ),
    takeaways=(
        "Set limits per trade, for all open trades, and per day.",
        "The daily loss limit stops tilt.",
        "Treat a broken limit as a failure of process.",
    ),
    sources=("odean-disposition",),
)

_managed = path(
    [(0, 1.1000), (6, 1.1025), (10, 1.1012), (18, 1.1055), (24, 1.1040), (30, 1.1090)],
    seed=28,
    noise=0.2,
)

_MANAGE = Lesson(
    slug="risk-first/managing-the-open-trade",
    title="Managing the trade after you are in",
    summary="Break-even, trailing, partial exits, the time stop, and the one rule you never break.",
    est_minutes=10,
    key_concepts=("break-even", "trailing stop", "partial close", "time stop", "R multiple"),
    figures=(
        Figure("trade-management", "Move to break-even, trail, bank part, and exit on time."),
    ),
    goal="Decide how you will manage an open trade before you are in it.",
    body_md="""
Almost every trading course stops at entry, as if the trade then plays itself. It does not. An hour after you enter, you are watching a number move and making decisions in the worst mental state. So decide everything now, before any money is at risk.

Everything below uses **R**, meaning the amount you risked on this trade. With entry 1.1000 and stop 1.0950, 1R is 50 pips.

**Rule 1 — Break-even at 1R.** Once price has moved 1R in your favour, move your stop to your entry price. The trade can no longer lose. The cost: some winners will stop you out at zero and then run to target without you.

Why not sooner? Moving to break-even after 10 pips puts your stop inside normal noise, so random moves will take you out of nearly every trade.

**Rule 2 — Then trail by one sigma.** After break-even, move your stop up behind price as it rises. Never down. How far behind? "Trail by 20 pips" ignores today's market. The app trails by **one sigma of the expected move**, the typical distance this market is travelling now. A quiet market gets a tighter trail and a wild one gets a wider trail.

**Rule 3 — Bank half at 1R (optional).** Close half the position and let the rest run. It puts real money in the account and makes the rest easier to hold. The cost: you make less on the trades that run straight to target.

**Rule 4 — The time stop.** If neither stop nor target is hit within the forecast's horizon, close the trade at market. The forecast had an expiry date. Holding past it is no longer your system's trade. It is hope.

**Rule 5 — never move your stop away from price.** Not rarely. Never. Widening a stop often works, which is what makes it so dangerous. You get rewarded and the habit grows. Then one day price does not come back, and a single trade costs months. This is the most common way a funded account dies.
""".strip(),
    charts=(
        candle_chart(
            _managed,
            title="Stops only move in your favour",
            caption="Illustrative prices. Entry at 1.1000 with a stop at 1.0950 (1R = 50 pips). At +1R the stop moves to entry and then trails behind price.",
            hlines=(
                HLine(1.0950, "Initial stop (-1R)", "danger"),
                HLine(1.1000, "Break-even after +1R", "warn"),
                HLine(1.1040, "Trailed stop", "accent"),
            ),
            marks=(Mark(30, 1.1090, "Exit", "accentSoft"),),
        ),
    ),
    steps=(
        "Before entering, write your rules for break-even, trailing, partial exits and time.",
        "Measure everything in R, not in pips or money.",
        "At +1R, move the stop to entry, and close half if that is your rule.",
        "Trail the stop by your volatility rule, and only ever in your favour.",
        "If the trade has run past its horizon, close it, even if it is flat or slightly negative.",
    ),
    example_md="""
Long EUR/USD at 1.1000, stop 1.0950 (**1R = 50 pips**), target 1.1150 (**3R**), 0.10 lots ($1 per pip).

- Price reaches **1.1050 (+1R)**. You move the stop to 1.1000 and close half (0.05 lots), banking **$25**.
- Price rises to **1.1090**. Your trailing stop moves to 1.1040.
- Price falls to 1.1040 and you exit the other half at +40 pips, **+$20**.

Total: **+$45**, about +0.9R on the original $50 risk.

If you had held the entire position to 1.1150, you would have made $150 (+3R) on that one trade. But you would also have been at risk of giving back all of it.

Now imagine the trade had gone to 1.1020 and then back to the stop. Without Rule 5 you might have widened it. With Rule 5 you take the 1R loss and move on.
""".strip(),
    mistakes=(
        "Moving to break-even almost immediately, inside normal noise.",
        "Moving your stop further away because you hope price will come back.",
        "Holding a trade for weeks because closing it would make the loss real.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
These are management rules rather than tested edges. Partial exits and break-even stops mainly change the *shape* of your results, such as how often you win and how large the wins are. They need testing on your own strategy before you assume they help.

The behavioural argument for Rule 5 is strong: Odean's research found investors tend to hold losers and sell winners, and a stop moved further away is exactly that bias. Separately, research on stop-loss rules suggests they do not always add value in every market (we did not review this in depth here), so a stop's main job is to protect you, not to create profit.
""".strip(),
    ),
    try_it="Write your five rules in your own words for your demo account, and print them next to your screen. Check them against your last three trades.",
    quiz=(
        Q(
            "You are long, 40 pips in profit on a trade that risked 50 pips. Price stalls. What does the plan say?",
            (
                "Close now, a profit is a profit",
                "Widen the stop so it has room to work",
                "Nothing yet: 40 is not 1R and the rules trigger at 50",
            ),
            2,
            "The point of deciding in advance is that a nervous feeling is not one of the triggers. Your rules fire at 1R.",
        ),
        Q(
            "Which move is never allowed?",
            (
                "Moving the stop to break-even at +1R",
                "Trailing the stop up",
                "Moving the stop further from price",
            ),
            2,
            "A stop moved away from price is how one trade can undo months of work.",
        ),
    ),
    takeaways=(
        "Decide trade management before you enter.",
        "Move stops only in your favour.",
        "A trade that outlives its horizon is hope, not a plan.",
    ),
    sources=("odean-disposition",),
)

_SIZING_ANY = Lesson(
    slug="risk/sizing-in-any-market",
    title="Sizing in any market",
    summary="The same formula works for shares, futures, crypto and more.",
    est_minutes=7,
    key_concepts=("position size", "tick value", "contract", "share size"),
    goal="Apply the same position-sizing idea to any instrument, in any market.",
    body_md="""
The sizing formula is the same everywhere:

**Position size = risk amount ÷ (stop distance × value of one unit of price).**

What changes is the "value of one unit of price".

### Shares

If you buy 1 share, a $1 move is worth $1. So **shares = risk amount ÷ stop distance in dollars**.

### Futures

The value of a price move is set by the exchange. The E-mini S&P 500 is **$50 for each index point** and moves in steps of 0.25, so each step is **$12.50**. The Micro E-mini is **$5 per point**, with each step worth $1.25.

**Contracts = risk amount ÷ (points to stop × dollars per point).** If the answer is below 1, you cannot take this trade with this contract. Use a smaller contract, or skip it.

### Crypto

With a quantity in coins: **coins = risk amount ÷ stop distance in dollars per coin**. Crypto moves a lot, so stops have to be wider and sizes smaller.

### Options

Buying an option has a defined maximum loss: the price you paid. **Contracts = risk amount ÷ (premium × contract multiplier)**. Selling options is different: the risk can be much larger than the premium received.

### Check your broker's numbers

Contract sizes and tick values can differ between brokers, especially for CFDs. Always look them up.
""".strip(),
    charts=(
        Chart(
            title="$500 risk, sized in each market",
            caption="Calculated examples with made-up prices: shares with a $5 stop, E-mini with a 10-point stop, Micro E-mini with a 10-point stop, bitcoin with a $2,000 stop.",
            data_kind="calculated",
            kind="bars",
            y_format="plain",
            y_label="Position size",
            bars=(
                Bar("Shares", 100, "accent"),
                Bar("E-mini contracts", 1, "accentSoft"),
                Bar("Micro E-mini", 10, "accentSoft"),
                Bar("Bitcoin (coins)", 0.25, "warn"),
            ),
        ),
    ),
    steps=(
        "Find your risk amount.",
        "Find your stop distance in the units of the market.",
        "Find how much one unit of price is worth per contract, share or coin.",
        "Divide. Round down.",
        "If the size is below the smallest unit you can trade, the trade is too big for this account.",
    ),
    example_md="""
Account **$25,000**, risk **1%**, so **$250**.

**Share of Company X**, entry $80, stop $76: $4 per share. Shares = $250 / $4 = **62 shares**.

**E-mini S&P 500**, stop 10 points: 10 × $50 = $500 per contract. $250 / $500 = 0.5 contracts, which is **too large**. Options: use the **Micro** ($50 per contract at a 10-point stop, so 5 contracts), or skip.

**Bitcoin**, entry $60,000, stop $58,000: $250 / $2,000 = **0.125 BTC**.

The trade idea is the same each time. The size has to change to keep the risk the same.
""".strip(),
    mistakes=(
        "Taking one standard contract because it is the 'normal' size.",
        "Forgetting that different brokers use different contract sizes for CFDs.",
        "Sizing an option you are selling as if its risk were only the premium.",
    ),
    evidence=fact(
        "Arithmetic. Contract sizes come from each exchange's specifications; those quoted here for the E-mini and Micro E-mini match CME Group's published details. Always check current specifications."
    ),
    try_it="Pick three instruments you might trade. Calculate the size for a $200 risk on each, using a sensible stop.",
    quiz=(
        Q(
            "You risk $200 on a stock with a $4 stop. How many shares?",
            ("20", "50", "100"),
            1,
            "$200 / $4 = 50 shares.",
        ),
        Q(
            "A futures position gives a size of 0.3 contracts. What should you do?",
            ("Round up to 1", "Use a smaller contract, or skip the trade", "Add leverage"),
            1,
            "Rounding up means risking more than planned. Use a smaller product or skip it.",
        ),
    ),
    takeaways=(
        "One formula fits every market.",
        "Only the value of a price move changes.",
        "If it will not fit your risk budget, use a smaller product or skip it.",
    ),
    sources=("cme-micro",),
)

_MATH = Lesson(
    slug="expectancy/the-math-of-survival",
    title="The maths of survival: expectancy",
    summary="The average result per trade, and why it matters more than win rate.",
    est_minutes=7,
    key_concepts=("expectancy", "win rate", "R:R", "edge"),
    figures=(
        Figure(
            "expectancy-formula",
            "Expectancy = (win rate × average win) − (loss rate × average loss).",
        ),
    ),
    goal="Calculate expectancy, and use it to judge any strategy.",
    body_md="""
**Expectancy** is your average result per trade, over many trades.

**Expectancy = (win rate × average win) − (loss rate × average loss).**

Positive means the strategy makes money over time. Negative means it bleeds. Near zero means it pays only the costs.

### The 40% / 2R example

Win 40% of the time, average win 2R, average loss 1R:

0.40 × 2R − 0.60 × 1R = **+0.2R per trade**.

Over 100 trades, that is **+20R** on average. At 1% risk per trade on a $10,000 account (R = $100), that is about **+$2,000**, before costs, and with a lot of variation around that average.

### Why this changes how you think

- You do not need to win often. You need a positive average.
- A "high win rate" strategy can still lose money overall.
- A low win rate strategy can be good, but you have to survive the losing streaks.

Expectancy is what you try to estimate from a backtest and confirm in live trading. It is an **estimate**: the true number is unknown and can change.
""".strip(),
    charts=(
        Chart(
            title="Win rate and reward-to-risk: what makes a positive expectancy",
            caption="Calculated. Expectancy per trade at different win rates, with average win of 2R and loss of 1R, before costs.",
            data_kind="calculated",
            kind="bars",
            y_format="r",
            y_label="Expectancy per trade",
            x_label="Win rate",
            bars=tuple(
                Bar(
                    f"{w}%",
                    round(w / 100 * 2 - (1 - w / 100) * 1, 2),
                    "accentSoft" if w > 34 else "danger",
                )
                for w in (25, 30, 35, 40, 45, 50)
            ),
        ),
    ),
    steps=(
        "Write down your win rate and average win and loss in R.",
        "Compute expectancy using the formula.",
        "Subtract costs in R.",
        "Multiply by your expected trades per year to see the rough total.",
        "Treat the result as an estimate, and test it again on new data.",
    ),
    example_md="""
Your backtest shows: 48% win rate, average win 1.4R, average loss 1R, cost per trade 0.08R.

Expectancy = 0.48 × 1.4 − 0.52 × 1 − 0.08 = 0.672 − 0.52 − 0.08 = **+0.072R per trade**.

Over 200 trades a year at 1% risk, that is about +14.4R, or **+14%**, before compounding and after these costs.

If costs rise to 0.15R, expectancy becomes +0.002R, which is effectively zero. Small changes matter a lot when the edge is small.
""".strip(),
    mistakes=(
        "Choosing strategies by win rate.",
        "Forgetting to subtract costs.",
        "Treating a backtest expectancy as a guaranteed future result.",
    ),
    evidence=fact(
        "The formula is arithmetic. Estimating the true expectancy of a strategy is much harder, and Stage 10 is about doing that honestly."
    ),
    try_it="Take your journal or 20 demo trades. Compute win rate, average win, average loss and expectancy.",
    quiz=(
        Q(
            "Win 40% of the time, average win 2R, average loss 1R. What is the expectancy per trade?",
            ("Negative, it loses money", "+0.2R per trade", "Exactly break-even"),
            1,
            "(0.40 × 2R) − (0.60 × 1R) = +0.2R per trade.",
        ),
        Q(
            "A strategy wins 70% of the time with average win 0.5R and average loss 1.5R. Expectancy?",
            ("-0.10R", "+0.35R", "+0.50R"),
            0,
            "(0.7 × 0.5) − (0.3 × 1.5) = 0.35 − 0.45 = -0.10R. A high win rate does not guarantee profit.",
        ),
    ),
    takeaways=(
        "Expectancy is the average result per trade.",
        "A low win rate can be fine, and a high one can lose.",
        "Subtract costs before believing the number.",
    ),
)

_R = Lesson(
    slug="expectancy/r-multiples",
    title="R-multiples: measuring every trade the same way",
    summary="A language for comparing trades of any size.",
    est_minutes=5,
    key_concepts=("R-multiple", "normalisation", "journal"),
    figures=(Figure("r-ruler", "A ruler measured in units of risk."),),
    goal="Express every trade in R, so you can compare any trade with any other.",
    body_md="""
An **R-multiple** is a trade's result divided by the amount you risked.

- A full stop-out is **−1R**.
- A trade that gained twice what it risked is **+2R**.
- A break-even trade is **0R**.

R makes different trades comparable.

- Strategy A makes 5% with 0.5% risk per trade: that is **+10R**.
- Strategy B makes 5% with 2% risk per trade: that is **+2.5R**.

Same money. But per unit of risk, A had an edge four times larger.

So when you look at 100 trades, "average +0.3R" tells you something real. "Average +12 pips" tells you almost nothing, because 12 pips means different things at different stop sizes and different volatility.

The app's journal stores realised R for every closed trade. Expectancy, profit factor and your largest wins and losses all come from that one column.
""".strip(),
    charts=(
        Chart(
            title="A set of 10 trades in R",
            caption="Illustrative sample of trades. The total is +3.5R. The same list works whether each trade was $10 or $10,000.",
            data_kind="illustrative",
            kind="bars",
            y_format="r",
            y_label="Result of each trade",
            bars=tuple(
                Bar(f"Trade {i}", r, "accentSoft" if r > 0 else "danger")
                for i, r in enumerate(
                    (-1.0, 2.0, -1.0, 0.5, -1.0, 3.0, -1.0, 1.5, 1.5, -1.0), start=1
                )
            ),
        ),
    ),
    steps=(
        "Record your planned risk in money before you enter.",
        "When the trade closes, divide the result by that planned risk.",
        "Write the R in your journal.",
        "Add up your R by week and by setup.",
        "Compare your setups in R.",
    ),
    example_md="""
You risked **$120**. You lost **$96** when you closed early. Your result is **−0.8R**.

Later you risked **$80** and made **$200**. Your result is **+2.5R**.

If you compared these in dollars you would see −$96 and +$200. In R you see exactly how each decision worked out against the plan.

If you once lost −3R because you moved your stop, that shows up clearly. R is one of the honest measures of whether you followed your rules.
""".strip(),
    mistakes=(
        "Calculating R from the money you made instead of from the risk you planned.",
        "Counting a trade you moved your stop on as −1R.",
        "Comparing R results that use very different risk per trade without noticing.",
    ),
    evidence=fact(
        "A measurement tool rather than a strategy, popularised by Van Tharp's teaching. It tells you nothing about whether your edge is real; it only shows it more clearly."
    ),
    try_it="Convert your last 10 trades to R. Mark any trade worse than −1R. Why did it happen?",
    quiz=(
        Q(
            "You risked $50 and made $125. What is the R-multiple?",
            ("1.5R", "2R", "2.5R"),
            2,
            "$125 / $50 = 2.5R.",
        ),
        Q(
            "Why is R better than pips for comparing trades?",
            ("It is more exciting", "It adjusts for how much you risked", "Regulators require it"),
            1,
            "R puts every trade on the same scale.",
        ),
    ),
    takeaways=(
        "R measures results against planned risk.",
        "Compare setups in R, not pips or money.",
        "A loss bigger than −1R means a rule was broken or a gap hit you.",
    ),
)

_LOW_WIN = Lesson(
    slug="expectancy/why-low-win-rate-can-be-profitable",
    title="Why a 40%-win system can pay",
    summary="Win rate alone tells you nothing. The hard part is living through the losses.",
    est_minutes=6,
    key_concepts=("win rate", "R:R", "expectancy", "psychology"),
    figures=(
        Figure(
            "winrate-myth",
            "A low win rate with big winners can beat a high win rate with small ones.",
        ),
    ),
    goal="See why a low win rate can be profitable, and what it really costs you.",
    body_md="""
A 40% win rate with 3R wins and 1R losses gives:

0.40 × 3 − 0.60 × 1 = **+0.6R per trade**.

That is a very strong result on paper. Almost nobody can trade it. Why? Because losing 60% of the time, with stretches of five or more losses in a row, feels terrible.

### Reward and win rate are linked

You cannot just pick a far target and keep the same win rate. A target further away is less likely to be reached. That is why "always use 3:1" is not a free lunch. The realistic question is what your system really does at a particular target and stop, tested on data.

### Why the journal matters

Without a written record, six losses in a row feel like proof that the strategy is broken. With a journal, six losses in a row look like an expected slice of the distribution.

If expectancy is positive and the rules have not changed, keep trading. If you cannot, the system's expectancy does not matter, because you will not survive long enough to get it.
""".strip(),
    charts=(
        Chart(
            title="Same 40% win rate: 3R winners, simulated",
            caption="Simulated: 12 possible paths of 100 trades, 40% win rate, winners 3R and losers 1R, risking 1% per trade. Even a strong edge has long painful stretches.",
            data_kind="calculated",
            kind="lines",
            y_format="plain",
            y_label="Account (start = 100)",
            x_label="Trades",
            series=equity_paths(
                n_paths=12, n_trades=100, win_rate=0.4, win_r=3.0, risk_pct=1.0, seed=19
            ),
        ),
    ),
    steps=(
        "Calculate the expectancy you actually got from your trades.",
        "Find your longest losing streak so far.",
        "Assume the future will be worse than the past.",
        "Decide what would really tell you that your system has stopped working.",
        "Write that rule down.",
    ),
    example_md="""
Compare two systems:

| System | Win rate | Avg win | Avg loss | Expectancy |
|---|---|---|---|---|
| A | 75% | 0.5R | 1.5R | −0.00R |
| B | 40% | 3R | 1R | +0.6R |

System A: 0.75 × 0.5 − 0.25 × 1.5 = 0.375 − 0.375 = **0.00R**. It looks great, wins three-quarters of the time, and it earns nothing before costs.

System B wins less than half the time, and it is the better system on paper. But it asks you to sit through many losses.
""".strip(),
    mistakes=(
        "Believing that a higher reward-to-risk ratio always helps.",
        "Giving up on a system during a normal losing run, without checking the numbers.",
        "Keeping a system with a high win rate that has a poor expectancy.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
The arithmetic is certain. Real trend-following systems often have win rates below 50% (see the research cited in Stage 7), so low-win systems are real.

But any specific figure such as 40% and 3R is only an example. Your real numbers need to come from testing with costs and on unseen data, and win rate and reward are linked.
""".strip(),
    ),
    try_it="Compute how much you would lose if you lost 10 in a row at your risk. Decide if you could keep following the plan after that.",
    quiz=(
        Q(
            "A 40% win rate with 3R wins and 1R losses has what expectancy?",
            ("+0.2R", "+0.6R", "+1.2R"),
            1,
            "0.40 × 3 − 0.60 × 1 = 1.2 − 0.6 = +0.6R.",
        ),
        Q(
            "If you move a target further away, what usually happens?",
            ("The win rate falls", "Nothing changes", "The win rate rises"),
            0,
            "A far target is less likely to be reached. Reward and win rate are linked.",
        ),
    ),
    takeaways=(
        "Win rate alone tells you nothing.",
        "Reward and win rate are linked.",
        "A low win rate is only worth having if you can live through the losses.",
    ),
)

_RUIN_LEVELS = (0.5, 1.0, 2.0, 5.0, 10.0)
_RUIN_VALUES = tuple(
    round(_ruin_probability(0.45, 1.5, r, 200, 0.5) * 100, 2) for r in _RUIN_LEVELS
)

_RUIN = Lesson(
    slug="risk/risk-of-ruin",
    title="Risk of ruin",
    summary="The chance of losing so much you cannot keep going.",
    est_minutes=8,
    key_concepts=("risk of ruin", "fixed fractional", "drawdown"),
    goal="Understand how much your risk per trade changes the chance of ruin.",
    body_md="""
**Risk of ruin** means the chance that your account falls so far that you cannot continue. You can define ruin however you like: a 50% loss, a loss that breaches a prop firm limit, or the point where you would quit.

Even with a real edge, you can be ruined by chance. The chart shows the **exact** answer for one example. A strategy wins 45% of the time and pays 1.5R, so it has a positive expectancy of +0.125R per trade. Risk 5% or 10% per trade, and the chance of a **50% drawdown within 200 trades** is high, even though the strategy works.

### What drives it

- **Risk per trade.** The biggest lever.
- **Win rate and payoff.** A weaker edge makes ruin more likely.
- **How many trades.** More trades mean more chances for a bad streak.
- **Your definition of ruin.** If you would quit at a 20% loss, ruin arrives much sooner.
- **Correlation.** Trades that lose together behave like one big trade.

### Two more cautions

These calculations assume each trade is **independent**. Real losses can cluster, because volatility clusters and because you may trade worse after losses. So treat these numbers as optimistic.

They also assume you actually know your win rate and payoff. You do not. Your estimates will be uncertain, and that uncertainty is another reason to use smaller risk.
""".strip(),
    charts=(
        Chart(
            title="Chance of a 50% drawdown within 200 trades",
            caption="Exact calculation. Assumes 45% win rate, 1.5R winners, 1R losers, independent trades, compounding at the risk shown. Positive expectancy of +0.125R per trade.",
            data_kind="calculated",
            kind="bars",
            y_format="pct",
            y_label="Chance of 50% drawdown",
            x_label="Risk per trade",
            bars=tuple(
                Bar(f"{r}%", v, "danger" if v > 5 else "accentSoft")
                for r, v in zip(_RUIN_LEVELS, _RUIN_VALUES, strict=True)
            ),
        ),
    ),
    steps=(
        "Define ruin for yourself, in percent of your account.",
        "Use your realistic win rate and payoff, then make them a little worse.",
        "Compute or simulate the chance of ruin at several risk levels.",
        "Choose a risk level where the chance is small, even with worse assumptions.",
        "Re-check whenever your strategy changes.",
    ),
    example_md=f"""
Using the same assumptions as the chart:

- At **1%** risk, the chance of a 50% drawdown in 200 trades is effectively zero.
- At **2%** risk, it is about **{_RUIN_VALUES[2]}%**.
- At **5%** risk, it is about **{_RUIN_VALUES[3]}%**.
- At **10%** risk, it is about **{_RUIN_VALUES[4]}%**.

So the same edge goes from barely any chance of disaster to very likely disaster, just by changing size. Nothing about the strategy changed.
""".strip(),
    mistakes=(
        "Assuming a positive expectancy cannot be ruined.",
        "Using a perfect backtest's numbers to compute your risk of ruin.",
        "Ignoring correlation between open positions.",
    ),
    evidence=fact(
        "The figures here are exact maths under the stated assumptions. Real life is worse than the assumptions: losses can cluster, and you do not know your true edge. Use these numbers as an optimistic limit."
    ),
    try_it="Pick your own win rate and reward. Use the app's Risk of Ruin panel, or simulate with a spreadsheet, and find the risk level you would be comfortable with.",
    quiz=(
        Q(
            "What is the biggest lever on risk of ruin?",
            ("Which broker you use", "Risk per trade", "The colour of your charts"),
            1,
            "Position size changes ruin probability far more than anything else you control.",
        ),
        Q(
            "A strategy has positive expectancy. Can it still be ruined?",
            (
                "No, a positive edge cannot lose",
                "Yes, especially at large risk per trade",
                "Only in crypto",
            ),
            1,
            "Even a good edge can be ruined by bad luck at large position sizes.",
        ),
    ),
    takeaways=(
        "A positive edge does not stop ruin.",
        "Risk per trade is the biggest lever you have.",
        "Real markets are usually worse than the maths assumes.",
    ),
)

_DRAWDOWN = Lesson(
    slug="risk/drawdown-limits",
    title="Drawdown limits",
    summary="How deep is too deep, and what to do when you get there.",
    est_minutes=7,
    key_concepts=("drawdown", "max drawdown", "recovery", "circuit breaker"),
    goal="Set the drawdown levels at which you reduce risk or stop trading.",
    body_md="""
A **drawdown** is how far your account has fallen from its highest point, or **peak**. The **maximum drawdown** is the worst of these over a period.

Drawdowns are normal. The question is how deep and how long you can accept.

### A simple plan

Think of it as a set of traffic lights.

- **Normal:** trade as planned.
- **Yellow, for example 10% down from the peak:** halve your risk per trade. Check whether your rules are being followed.
- **Red, for example 20% down from the peak:** stop trading live. Review everything. Go back to demo until you have new evidence.

Prop firms apply a version of this. They commonly use both a **daily loss limit** and a **maximum total drawdown**, and breaking either ends the account. Stage 12 covers this in depth.

### How to use drawdowns to learn

Compare your current drawdown with what your testing said was normal. If your testing said a typical maximum is 12% and you are down 25%, either your strategy has changed, the market has changed, or your test was over-optimistic. All three matter.
""".strip(),
    charts=(
        Chart(
            title="An account curve and its drawdown",
            caption="Illustrative. Top line: account value. The shaded lower chart shows how far below its previous high the account is, which is the drawdown.",
            data_kind="illustrative",
            kind="lines",
            y_format="plain",
            y_label="Account value",
            x_label="Trades",
            lower_title="Drawdown (%)",
            series=(
                Series(
                    "Account",
                    (100, 104, 108, 106, 112, 110, 105, 99, 96, 100, 106, 112, 118, 115, 122),
                    "accent",
                ),
                Series(
                    "Drawdown",
                    (0, 0, 0, -1.9, 0, -1.8, -6.3, -11.6, -14.3, -10.7, -5.4, 0, 0, -2.5, 0),
                    "danger",
                    "area",
                    "lower",
                ),
            ),
        ),
    ),
    steps=(
        "Calculate your account's highest value so far.",
        "Measure today's value against it. That is your drawdown.",
        "Set a yellow and a red level in your plan.",
        "When you hit yellow, cut your risk in half.",
        "When you hit red, stop and review. Return only with new evidence.",
    ),
    example_md="""
Your account peak is **$12,000**. It is now **$10,800**.

Drawdown = ($12,000 − $10,800) / $12,000 = **10%**.

Your yellow line is 10%, so you halve risk from 1% to 0.5% per trade.

A few weeks later, the account is at $9,600. Drawdown is **20%**, your red line. You stop live trading and spend two weeks reviewing your journal. You find that your last 20 losing trades broke your rule about trading the news. That is a concrete, fixable finding, and it came from stopping.
""".strip(),
    mistakes=(
        "Measuring drawdown from where you started rather than from the peak.",
        "Having no pre-agreed line, and deciding only when already in pain.",
        "Raising size during a drawdown to get back faster.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Drawdowns are real and measurable. The specific yellow and red levels above are sensible rules of thumb, not research findings. Prop firms use limits that vary widely across firms.

Be careful with short records. A strategy's real maximum drawdown is usually worse than the one seen in a backtest. Monte Carlo testing (Stage 10) helps estimate how bad it could get.
""".strip(),
    ),
    try_it="Pick your yellow and red drawdown levels. Write down exactly what you will do at each one.",
    quiz=(
        Q(
            "Peak $20,000, now $17,000. What is the drawdown?",
            ("10%", "15%", "20%"),
            1,
            "($20,000 − $17,000) / $20,000 = 15%.",
        ),
        Q(
            "You hit your red drawdown level. What should happen?",
            (
                "Increase risk to recover",
                "Stop trading live and review",
                "Switch to a new strategy immediately",
            ),
            1,
            "Stop and review. A sudden new strategy is usually just more of the same problem.",
        ),
    ),
    takeaways=(
        "Measure drawdown from the peak.",
        "Decide your limits before you need them.",
        "Cut risk first, then stop if it continues.",
    ),
)

_CORRELATION = Lesson(
    slug="risk/correlation-and-portfolio-heat",
    title="Correlation and portfolio risk",
    summary="Three trades can be one big trade in disguise.",
    est_minutes=7,
    key_concepts=("correlation", "portfolio heat", "diversification"),
    goal="Measure your real total risk when you hold several positions.",
    body_md="""
**Correlation** measures how closely two markets move together. It runs from **+1** (they move together), through **0** (no relationship), to **−1** (they move opposite).

If you are long EUR/USD, long GBP/USD and short USD/CHF, you do not have three independent trades. You have roughly **one big bet against the US dollar**. If the dollar rises, all three can lose at the same time.

**Portfolio heat** means your total open risk added together. If each of three correlated trades risks 1%, your real exposure may be close to 3% on one idea.

### Correlation changes

Correlations are not fixed. In a crisis, many assets tend to fall together. So the diversification you thought you had can disappear when you need it most.

### What to do

- Before adding a position, ask: "what does this have in common with what I already hold?"
- Treat strongly correlated trades as one trade and share the risk between them.
- Cap total open risk.
- Be careful with positions that share a common driver: the dollar, risk appetite, oil.

### True diversification is rare

Diversification is the one free lunch finance is known for, because it reduces risk without reducing expected return, if the assets are really different. Many traders think they have it when they have not.
""".strip(),
    charts=(
        Chart(
            title="Risk of three trades, by correlation",
            caption="Calculated: the volatility of three equal 1% trades when each pair has the same correlation. Portfolio risk = 1% × √(3 + 6ρ). At ρ = 1, three trades are one 3% trade.",
            data_kind="calculated",
            kind="bars",
            y_format="pct",
            y_label="Total portfolio risk",
            x_label="Correlation between trades",
            bars=tuple(
                Bar(f"ρ = {c}", round((3 + 6 * c) ** 0.5, 2), "accentSoft" if c < 0.5 else "danger")
                for c in (0.0, 0.25, 0.5, 0.75, 1.0)
            ),
        ),
    ),
    steps=(
        "List your open positions and their risk.",
        "Mark what each one depends on (a currency, a sector, oil, risk appetite).",
        "Group the ones that share a driver.",
        "Reduce the group so its total risk fits your limit.",
        "Before adding any new trade, re-do this list.",
    ),
    example_md="""
Say you have three trades, each risking 1% of your account:

- Long EUR/USD
- Long GBP/USD
- Long AUD/USD

These often move together because all are priced against the dollar. If the correlation is about 0.7, the combined risk is:

1% × √(3 + 6 × 0.7) = 1% × √7.2 = **2.68%**.

So three "1%" trades behave like one trade of about **2.7%**. If you had a limit of 2% on all correlated trades, you would need to cut each down, or drop one of them.
""".strip(),
    mistakes=(
        "Counting three correlated trades as diversified.",
        "Assuming correlations you measured in quiet times will hold in a crisis.",
        "Ignoring the fact that all your trades share the same news event.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
The maths is standard portfolio theory. It is also well known that correlations between assets rise in crises, reducing the benefit of diversification when it is most needed. Mentioned here from general knowledge and not checked individually for this book.

On currencies: Lustig, Roussanov and Verdelhan showed that exchange rates share a common global risk factor, so several currency positions can be one bet.
""".strip(),
    ),
    try_it="List your last three open positions together. Decide whether they were independent, or one bet with three tickets.",
    quiz=(
        Q(
            "Long EUR/USD and long GBP/USD together are often…",
            ("Fully independent", "Largely one bet against the dollar", "Risk-free"),
            1,
            "Both are priced in dollars, so they often move together.",
        ),
        Q(
            "What tends to happen to correlations in a crisis?",
            ("They usually rise", "They go to zero", "They always fall"),
            0,
            "When everyone sells, many assets fall together. Diversification can shrink when you need it.",
        ),
    ),
    takeaways=(
        "Correlated trades are one trade with several tickets.",
        "Add up your total open risk.",
        "Correlation can rise in a crisis.",
    ),
    sources=("lustig-2011",),
)

_KELLY = Lesson(
    slug="risk/kelly-and-why-not-full-kelly",
    title="The Kelly formula, and why not to use it in full",
    summary="The maths of the ideal bet size, and why real traders bet less.",
    est_minutes=7,
    key_concepts=("Kelly criterion", "fractional Kelly", "overbetting"),
    goal="Know what the Kelly formula tells you, and why almost nobody uses it fully.",
    body_md="""
The **Kelly criterion**, from J. L. Kelly in 1956, works out the bet size that would grow your money fastest over the long run, **if you know your true odds**.

For a bet with win probability *p*, loss probability *q* = 1 − *p*, and payoff *b* (the amount you win per 1 unit you risk):

**Kelly fraction = p − q / b.**

So with a 55% win rate and 1:1 payoff, Kelly = 0.55 − 0.45 = **10%** of your account per bet.

### Why not bet the full Kelly?

1. **You do not know your true odds.** Your backtest is only an estimate. If you overestimate your edge, full Kelly becomes severe overbetting.
2. **The ride is brutal.** Full Kelly suffers very deep drawdowns, even when the odds are exactly right.
3. **Overbetting is worse than underbetting.** Betting twice the Kelly fraction gives roughly zero long-term growth. Betting more than that loses money, even with a real edge.

So many practitioners use a **fraction** of Kelly, such as a quarter or half. It gives up some growth to reduce the drawdowns a lot.

### A more useful way to use it

Treat Kelly as an **upper limit**. If your risk per trade is above the Kelly level implied by your numbers, you are definitely risking too much.
""".strip(),
    charts=(
        Chart(
            title="Long-run growth against bet size",
            caption="Calculated: expected log growth per bet for a 55% win rate at 1:1 payoff. Growth peaks at the Kelly fraction of 10%, and turns negative when you bet beyond about twice Kelly.",
            data_kind="calculated",
            kind="lines",
            y_format="pct",
            y_label="Long-run growth per bet",
            x_label="Fraction of account bet (%)",
            x_labels=tuple(str(x) for x in range(0, 31, 2)),
            series=(
                Series(
                    "Growth per bet",
                    tuple(
                        round(
                            (0.55 * math.log(1 + x / 100) + 0.45 * math.log(1 - x / 100)) * 100, 3
                        )
                        for x in range(0, 31, 2)
                    ),
                    "accent",
                ),
            ),
        ),
    ),
    steps=(
        "Estimate your win rate and payoff from a large sample.",
        "Compute the Kelly fraction.",
        "Be sceptical: reduce your estimate of the edge.",
        "Use a fraction of the result, often a quarter or less.",
        "Check that it is not bigger than your normal risk rule.",
    ),
    example_md="""
Your backtest: win rate **52%**, average win **1.5R**, average loss 1R.

Kelly fraction = 0.52 − 0.48 / 1.5 = 0.52 − 0.32 = **20%**.

That looks huge. In practice, your 52% is uncertain. Suppose your true win rate is 47%: Kelly = 0.47 − 0.53 / 1.5 = **11.7%**. Suppose your true win rate is 42%: Kelly is **3.3%**. Now you can see why betting 20% would be wild overbetting.

A sensible trader might cap risk at 1% anyway, and use Kelly only as a check that nothing is wildly oversized.
""".strip(),
    mistakes=(
        "Using the Kelly number directly from a backtest.",
        "Thinking more risk always means more growth.",
        "Using Kelly for a strategy whose edge is not known to exist.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
The maths is well established. Kelly's result assumes known odds, which do not exist in markets. Practitioners widely use fractional Kelly for that reason.

The hard part is not the formula. It is that your inputs are guesses.
""".strip(),
    ),
    try_it="Use your own win rate and payoff to compute Kelly. Then assume your win rate is 5 percentage points lower. How much does the number change?",
    quiz=(
        Q(
            "What does the Kelly formula assume?",
            ("That you know your true odds", "That markets are efficient", "That you never lose"),
            0,
            "That is the key problem: in markets you do not know your true odds.",
        ),
        Q(
            "Why do traders use only a fraction of Kelly?",
            (
                "Because the edge is uncertain and full Kelly has severe drawdowns",
                "Because regulators require it",
                "Because it is less profitable in all cases",
            ),
            0,
            "Overestimating the edge and betting full Kelly is very dangerous.",
        ),
    ),
    takeaways=(
        "Kelly maximises growth only if you know your odds.",
        "Overbetting can turn a real edge into a loss.",
        "Use a fraction, or use Kelly only as an upper limit.",
    ),
    sources=("kelly-1956",),
)

CHAPTERS = (
    chapter(
        "risk",
        "staying-alive",
        "Staying alive",
        "The risk rules that protect your account, before any strategy comes into it.",
        (_WHY_RISK, _ONE_PERCENT, _SIZE, _GUARDRAILS, _MANAGE, _SIZING_ANY),
    ),
    chapter(
        "risk",
        "maths-of-survival",
        "The maths of survival",
        "Expectancy, R, risk of ruin, drawdown, correlation, Kelly, VaR and beta.",
        (_MATH, _R, _LOW_WIN, _RUIN, _DRAWDOWN, _CORRELATION, _KELLY, more_risk.VAR_ES, more_risk.BETA),
    ),
)
