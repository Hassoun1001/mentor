"""Stage 4, additions: Value at Risk, Expected Shortfall and beta."""

from __future__ import annotations

from mentor.domain.curriculum.book._kit import Bar, Chart, Evidence, Lesson, Q, Series, Verdict
from mentor.domain.curriculum.charts import Tone, beta_paths, fat_tailed_returns, histogram

_RETURNS = fat_tailed_returns(2500, seed=113, scale=1.0)
_EDGES = (-9.0, -7.0, -5.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 5.0, 7.0, 9.0)
_COUNTS = histogram(_RETURNS, _EDGES)
_SORTED = sorted(_RETURNS)
_TAIL = max(int(len(_SORTED) * 0.01), 1)
_VAR99 = -_SORTED[_TAIL]
_ES99 = -sum(_SORTED[:_TAIL]) / _TAIL


def _bucket_tone(low: float) -> Tone:
    return "danger" if low < -_VAR99 else "muted"


VAR_ES = Lesson(
    slug="risk/value-at-risk-and-expected-shortfall",
    title="Value at Risk and Expected Shortfall",
    summary="Two numbers for bad days, and what each one hides.",
    est_minutes=9,
    key_concepts=("Value at Risk", "VaR", "Expected Shortfall", "tail risk", "fat tails", "Basel"),
    goal="Work out VaR and Expected Shortfall from a list of results, and explain why VaR alone can mislead.",
    body_md="""
Banks and funds want one number for how bad a normal bad day can be.

### Value at Risk

**VaR** answers: *"What loss should we exceed only rarely?"*

A **99% one-day VaR of $620** means: on about 99 days out of 100, the loss should be smaller than $620. On the other day or so, it will be larger.

**VaR does not tell you how much larger.**

### Expected Shortfall

**Expected Shortfall (ES)** answers the next question: *"When we do cross that line, what is the average loss?"*

Because it looks inside the tail, it responds to extreme losses that VaR ignores.

### Why this matters

- Researchers have shown that VaR can fail to reward diversification. Combining positions can even look riskier.
- Banking rules moved from VaR to Expected Shortfall under stress in 2016.

### What both miss

They use past data, and they assume the future looks broadly similar. Many real crises were worse than anything in the sample. Bank VaR models have had trouble predicting changes in risk.

**Treat them as measures of normal-times risk.** Stress tests and position limits are still needed.
""".strip(),
    charts=(
        Chart(
            title="Most days are small, the tail is where it hurts",
            caption=f"Calculated from a seeded simulation of 2,500 daily results (%). Most days are calm, with rare larger moves. In this sample the 99% VaR is about {_VAR99:.1f}% and Expected Shortfall about {_ES99:.1f}%. Red marks the buckets that hold the VaR line or lie beyond it.",
            data_kind="calculated",
            kind="bars",
            y_format="plain",
            y_label="Number of days",
            bars=tuple(
                Bar(f"{_EDGES[i]:g}% to {_EDGES[i + 1]:g}%", _COUNTS[i], _bucket_tone(_EDGES[i]))
                for i in range(len(_COUNTS))
            ),
        ),
    ),
    steps=(
        "List daily profit and loss for a long period.",
        "Sort the results from worst to best.",
        "For 99% VaR, find the loss that only 1% of days were worse than.",
        "Average the losses beyond that point for Expected Shortfall.",
        "Compare both with a stress case, such as your largest ever day doubled.",
    ),
    example_md="""
You have **200 daily results**. 1% of 200 is **2 days**. The losses sorted worst first are:

**−$1,500, −$900, −$620, −$580, ...**

- **99% VaR:** only 2 days were worse than the third-worst day, so VaR is about **$620**.
- **Expected Shortfall:** the average of the two worst days = (1,500 + 900) ÷ 2 = **$1,200**.

Now imagine the worst day had been **−$6,000** instead. VaR would not change at all. It would still be $620. But Expected Shortfall would jump to (6,000 + 900) ÷ 2 = **$3,450**.

That is exactly why regulators moved toward Expected Shortfall. With only two days in the tail, though, it is a very unstable estimate.
""".strip(),
    mistakes=(
        "Treating VaR as the worst that can happen.",
        "Estimating tail numbers from a small amount of data.",
        "Summing the VaRs of positions and assuming the total is correct.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
**Sound measurement, with limits.** Artzner, Delbaen, Eber and Heath set out what a good risk measure should do, and showed that VaR can fail to reward diversification.

The Basel Committee moved its market-risk rules from VaR to Expected Shortfall under stress.

Pérignon and Smith found that historical simulation was by far the most popular VaR method at banks, and that it contained very little information about future volatility.
""".strip(),
    ),
    try_it="Export your daily trading results, or a price series. Sort them and calculate the 95% VaR and Expected Shortfall.",
    quiz=(
        Q(
            "What does VaR not tell you?",
            (
                "How much larger the loss can be beyond the line",
                "A loss level exceeded only rarely",
                "A confidence level",
            ),
            0,
            "Losses beyond the line are invisible to it.",
        ),
        Q(
            "If the single worst day gets much worse, which number changes?",
            ("Only Expected Shortfall", "Only VaR", "Neither"),
            0,
            "Expected Shortfall averages the tail, so it responds to how bad the tail is.",
        ),
    ),
    takeaways=(
        "VaR is a line that is rarely crossed.",
        "Expected Shortfall shows the average beyond that line.",
        "Neither replaces stress tests.",
    ),
    sources=("artzner-1999", "frtb-2016", "perignon-2010"),
)

# ---------- beta ----------

_market, _high, _low = beta_paths(60, seed=127, betas=(1.0, 1.5, 0.6))

BETA = Lesson(
    slug="risk/beta",
    title="Beta: how much is just the market?",
    summary="Measuring how much a share or portfolio moves with the whole market.",
    est_minutes=7,
    key_concepts=("beta", "portfolio beta", "market risk", "hedge", "betting against beta"),
    goal="Calculate portfolio beta and use it to understand how much of your risk is really market risk.",
    body_md="""
**Beta** measures how much something tends to move when the whole market moves.

- **Beta of 1:** it tends to move with the market.
- **Beta of 1.5:** it tends to move about 1.5% when the market moves 1%.
- **Beta of 0.5:** it tends to move about half as much.
- **Beta near 0:** it tends not to move with the market.

### How it is calculated

Beta = how much the share and market move together ÷ how much the market moves on its own. It is normally measured using a few years of returns.

### Portfolio beta

Portfolio beta is the **weighted average** of the betas of what you hold.

### Why this matters

If you own ten shares and all have a high beta, you may think you are diversified. In fact you may just own **one large bet on the market**. Beta helps you see that.

### Limits

- Beta changes over time.
- It only measures movement with one market.
- It does not capture a share's own bad news.
""".strip(),
    charts=(
        Chart(
            title="The same market, different betas",
            caption="Calculated from a seeded simulation: each line takes the same daily market move, multiplied by its beta. Real shares also have their own moves, which are left out here.",
            data_kind="calculated",
            kind="lines",
            y_format="plain",
            y_label="Value, start = 100",
            x_label="Days",
            x_labels=tuple(str(d) for d in range(0, 61)),
            series=(
                Series("Market", _market, "muted"),
                Series("Beta 1.5", _high, "danger"),
                Series("Beta 0.6", _low, "accent"),
            ),
        ),
    ),
    steps=(
        "Write down each holding and its weight.",
        "Find each beta on a data site, or calculate it from returns.",
        "Multiply each beta by its weight.",
        "Add them up to get the portfolio beta.",
        "Ask what a 5% market fall would do to the account.",
    ),
    example_md="""
A **$100,000** portfolio:

| Share | Weight | Beta | Weight × beta |
|---|---|---|---|
| A | 50% | 1.4 | 0.70 |
| B | 30% | 0.8 | 0.24 |
| C | 20% | 0.5 | 0.10 |
| **Total** | | | **1.04** |

A market fall of **5%** would be expected to cost about 5% × 1.04 = **5.2%**, or about **$5,200**, before any news specific to the shares.

To cancel the market risk, a professional might short an index position of about 1.04 × $100,000 = **$104,000**. What remains is the risk from the shares themselves.
""".strip(),
    mistakes=(
        "Thinking many shares means many separate risks.",
        "Using a beta from a very short period.",
        "Assuming beta is stable through a crisis.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Beta is a good measure of how much a share moves with the market. But classic theory says high-beta shares should earn more, and in practice they have often earned less than predicted.

Frazzini and Pedersen found this across many markets and built a "betting against beta" strategy. Novy-Marx and Velikov later challenged how that strategy is constructed. So beta is sound as a risk measure, but the evidence on using it for extra return is disputed.
""".strip(),
    ),
    try_it="Write down your holdings or a sample portfolio. Find each beta and calculate the total. What would a 10% market fall do to it?",
    quiz=(
        Q(
            "A portfolio with a beta of 1.2 would be expected to move about how much if the market falls 5%?",
            ("-2.5%", "-6%", "-12%"),
            1,
            "1.2 × 5% = 6%.",
        ),
        Q(
            "Portfolio beta is…",
            (
                "The weighted average of the holdings' betas",
                "The highest single beta",
                "Always equal to 1",
            ),
            0,
            "Weight each beta by the size of the holding.",
        ),
    ),
    takeaways=(
        "Beta shows how much of your risk is market risk.",
        "Portfolio beta is a weighted average.",
        "Use it to measure risk, and do not treat it as a promise of return.",
    ),
    sources=("frazzini-pedersen-2014",),
)
