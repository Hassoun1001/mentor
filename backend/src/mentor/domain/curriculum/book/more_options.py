"""Stage 8, options in depth: volatility, straddles, spreads, hedging and skew."""

from __future__ import annotations

import math

from mentor.domain.curriculum.book._kit import Bar, Chart, Evidence, Lesson, Q, Series, Verdict
from mentor.domain.curriculum.charts import (
    Num,
    call_delta,
    call_price,
    option_gamma,
    put_price,
)

_SPOTS = tuple(range(80, 121, 2))
_LABELS = tuple(str(s) for s in _SPOTS)
_MONTH = 30 / 365


def _line(values: list[float]) -> tuple[Num, ...]:
    return tuple(round(v, 3) for v in values)


# ---------- implied vs historical ----------

_DAYS = (1, 5, 10, 20, 30, 45, 60, 90)

IV_VS_HV = Lesson(
    slug="options/implied-vs-historical-volatility",
    title="Implied and historical volatility",
    summary="What moved, what option prices expect, and the premium between them.",
    est_minutes=9,
    key_concepts=("implied volatility", "historical volatility", "expected move", "put/call ratio", "options flow"),
    goal="Calculate historical volatility, turn implied volatility into an expected move, and understand the volatility premium.",
    body_md="""
**Volatility** means how much a price moves around. Option traders talk about two kinds.

### Historical volatility

This is what **did** happen. It is the standard deviation of past daily returns, shown as a yearly number:

**Yearly volatility ≈ daily volatility × √252**

We use 252 because a year has about 252 trading days.

### Implied volatility

This is what option prices **suggest** will happen. It is worked backwards from the option's price using a pricing formula. Higher implied volatility means more expensive options.

### Turning it into an expected move

**Expected move ≈ price × implied volatility × √(days ÷ 365)**

This gives about a one-standard-deviation range. The price is expected to stay inside it about two-thirds of the time, if the model's assumptions are right.

### The volatility premium

On stock indexes, implied volatility has usually been **higher** than the volatility that followed. Option buyers have paid extra for protection. Sellers have collected that extra, but have also taken very large losses in crashes.

### Two crowd measures

- **Put/call ratio:** puts traded divided by calls traded. It is a rough fear gauge. Much of the volume is hedging.
- **Options flow:** reports of large unusual trades. A public feed usually cannot tell you whether a trade opens a position, closes one or hedges another.
""".strip(),
    charts=(
        Chart(
            title="Expected move grows with the square root of time",
            caption="Calculated: a $100 share with 20% implied volatility. Four times as many days gives only about twice the expected move.",
            data_kind="calculated",
            kind="lines",
            y_format="usd",
            y_label="One-standard-deviation move",
            x_label="Days to expiry",
            x_labels=tuple(str(d) for d in _DAYS),
            series=(
                Series(
                    "Expected move",
                    tuple(round(100 * 0.20 * math.sqrt(d / 365), 2) for d in _DAYS),
                    "accent",
                ),
            ),
        ),
    ),
    steps=(
        "Calculate the daily percentage changes of a price.",
        "Find their standard deviation and multiply by √252.",
        "Read the implied volatility from an option chain.",
        "Convert it into an expected move for your expiry.",
        "Compare it with what has been happening lately.",
    ),
    example_md="""
**Historical:** a share's daily moves have a standard deviation of **1%**.

Yearly volatility ≈ 1% × √252 ≈ 1% × 15.9 = **about 15.9%**.

**Implied:** the option chain shows **20%** for options with 30 days left, on a share priced at **$100**.

Expected move ≈ 100 × 0.20 × √(30 ÷ 365) ≈ 100 × 0.20 × 0.287 = **about $5.73**.

So the market is roughly pricing a range of **$94.27 to $105.73** in 30 days, about two-thirds of the time. The implied number is above the recent 15.9%, so these options look relatively expensive compared with recent movement. That does not mean they are wrongly priced. An event may be coming.
""".strip(),
    mistakes=(
        "Buying options because you expect a move, without checking the size already priced in.",
        "Selling options because implied volatility is high, without a plan for a crash.",
        "Assuming the put/call ratio shows direction, when much of it is hedging.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
**Tested:** Carr and Wu found stock-index options price in more variance than usually follows, in both good and bad markets. Bakshi and Kapadia found S&P 500 option buyers who hedged away direction lost on average.

**The limit:** returns from selling volatility come with occasional huge losses.

**On put/call data:** Pan and Poteshman found stock returns could be predicted from new buyer-initiated option trades, but this used non-public data. The widely quoted public ratio is a different number.
""".strip(),
    ),
    try_it="Find the implied volatility of a 30-day at-the-money option on one share. Work out the expected move. Check after 30 days whether the price stayed inside the range.",
    quiz=(
        Q(
            "What is implied volatility?",
            (
                "How much the price moved last month",
                "The movement suggested by the option's price",
                "A broker's fee",
            ),
            1,
            "It is worked backward from the option's price.",
        ),
        Q(
            "On stock indexes, implied volatility has usually been…",
            (
                "Above what later happens",
                "Below what later happens",
                "Exactly the same as what later happens",
            ),
            0,
            "This gap is the volatility premium. Sellers collect it and take the crash risk.",
        ),
    ),
    takeaways=(
        "Historical volatility looks back. Implied volatility looks forward.",
        "Expected move grows with the square root of time.",
        "Sellers collect a premium, but the tail risk is real.",
    ),
    sources=("carr-wu-2009", "bakshi-kapadia-2003", "pan-poteshman-2006"),
)

# ---------- straddles and strangles ----------

_S_CALL = call_price(100, 100, 0.4, _MONTH)
_S_PUT = put_price(100, 100, 0.4, _MONTH)
_ST_CALL = call_price(100, 105, 0.4, _MONTH)
_ST_PUT = put_price(100, 95, 0.4, _MONTH)

STRADDLE = Lesson(
    slug="options/straddles-and-strangles",
    title="Straddles and strangles",
    summary="Positions that care about the size of a move, not its direction.",
    est_minutes=9,
    key_concepts=("straddle", "strangle", "breakeven", "implied move", "earnings", "theta"),
    goal="Work out the cost and breakeven of a straddle and a strangle, and see the true question each one asks.",
    body_md="""
A **long straddle** means buying a call and a put with the **same strike** and the same date. You gain if the price moves far enough in either direction.

A **long strangle** is similar, but the call and the put have **different strikes**, both outside the current price. It costs less and needs a bigger move.

### The real question

Many beginners say: "Earnings are coming, a big move is likely, so a straddle must be good."

That misses the point. **The option price already includes the move the market expects.** A straddle only makes money if the actual move is **bigger than what you paid for**.

### Sellers take the other side

Selling a straddle or strangle brings in money up front. It gains if the market stays calm. **But the possible loss is very large**, especially on a naked short strangle.

### Time and volatility

- As time passes, a long straddle loses value every day if price does not move.
- If implied volatility falls after an event, it can lose value even when price moved. This is often called a **volatility crush**.
""".strip(),
    charts=(
        Chart(
            title="What each position pays at expiry",
            caption="Calculated with standard option pricing: share at $100, 30 days, 40% volatility. Straddle: buy 100 call and 100 put. Strangle: buy 105 call and 95 put. Costs are subtracted. No commissions.",
            data_kind="calculated",
            kind="lines",
            y_format="usd",
            y_label="Profit or loss per share",
            x_label="Share price at expiry",
            x_labels=_LABELS,
            series=(
                Series(
                    "Long straddle",
                    _line([abs(s - 100) - _S_CALL - _S_PUT for s in _SPOTS]),
                    "accent",
                ),
                Series(
                    "Long strangle",
                    _line(
                        [max(s - 105, 0) + max(95 - s, 0) - _ST_CALL - _ST_PUT for s in _SPOTS]
                    ),
                    "warn",
                ),
            ),
        ),
    ),
    steps=(
        "Add the prices of the call and the put.",
        "Add that total to the strike for the upper breakeven.",
        "Subtract it for the lower breakeven.",
        "Compare those breakevens with similar past moves.",
        "Plan what happens if volatility falls after the event.",
    ),
    example_md="""
A share is at **$100**. With 30 days left and 40% implied volatility, standard pricing gives:

- 100-strike call: **$4.57**
- 100-strike put: **$4.57**

**Straddle cost: $9.14 per share.** Breakevens: **$90.86 and $109.14**. In this example the share has to move **more than 9.1%** by expiry before the position gains anything.

**Strangle:**

- 105-strike call: **$2.60**
- 95-strike put: **$2.40**

**Strangle cost: $5.00 per share.** Breakevens: **$90 and $110**, which is a move of more than **10%**.

The strangle is cheaper, but it needs a larger move.
""".strip(),
    mistakes=(
        "Assuming that 'a big move is coming' means a straddle is a good idea.",
        "Holding through an event and being surprised by a volatility crush.",
        "Selling strangles with no plan for a move much larger than usual.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
**Buying has lost on average.** Coval and Shumway found that market-neutral at-the-money S&P 500 straddles lost about **3% per week** on average.

**Selling is not free money.** Carr and Wu and Bakshi and Kapadia show a premium for selling volatility, but with sudden heavy losses. Retail option traders overall tend to lose money, according to Bryzgalova, Pavlova and Sikorskaya.
""".strip(),
    ),
    try_it="Before the next earnings report of any share, write down the straddle cost as a percentage of the price. After the report, compare it with the actual move.",
    quiz=(
        Q(
            "When does a long straddle make money at expiry?",
            (
                "Whenever the price moves at all",
                "When the move is bigger than the total cost of both options",
                "Only if the price rises",
            ),
            1,
            "The move must exceed what you paid.",
        ),
        Q(
            "How does a strangle differ from a straddle?",
            (
                "The call and put have different strikes, so it costs less and needs a bigger move",
                "It only uses calls",
                "It has no time decay",
            ),
            0,
            "Further-out strikes make it cheaper, but the required move is larger.",
        ),
    ),
    takeaways=(
        "Long straddles pay only if the move beats the price paid.",
        "Option prices already include the expected move.",
        "Selling these positions carries very large tail risk.",
    ),
    sources=("coval-shumway-2001", "carr-wu-2009", "bakshi-kapadia-2003", "bryzgalova-2023"),
)

# ---------- spreads ----------

_C100 = call_price(100, 100, 0.4, _MONTH)
_C110 = call_price(100, 110, 0.4, _MONTH)
_FAR = call_price(100, 100, 0.4, 60 / 365)
_NEAR = call_price(100, 100, 0.4, _MONTH)

SPREADS = Lesson(
    slug="options/vertical-and-calendar-spreads",
    title="Vertical and calendar spreads",
    summary="Combining options to set limits on cost, gain and loss.",
    est_minutes=9,
    key_concepts=("vertical spread", "bull call spread", "calendar spread", "max loss", "time decay"),
    goal="Work out the maximum gain, loss and breakeven of a vertical spread, and understand what a calendar spread depends on.",
    body_md="""
A **spread** combines two or more options so that one helps pay for another.

### Vertical spreads

You buy one option and sell another, with the **same expiry** and a **different strike**.

A **bull call spread** buys a lower-strike call and sells a higher-strike call. Selling the second call lowers your cost, but it also caps your gain.

For a bull call spread that costs a net amount:

- **Maximum loss** = the net cost.
- **Maximum gain** = strike gap − net cost.
- **Breakeven** = lower strike + net cost.

The loss is known before you start. That is the main appeal.

### Calendar spreads

You **sell a near-term option and buy a later one** at the same strike.

The near option loses value faster. If the price stays near the strike, the position can gain as the short option decays.

**A calendar depends on implied volatility as well as price.** If later-dated volatility falls, it can lose money even when the price stays still.

### Watch the costs

Two legs mean two spreads to cross. On options with wide bid and ask prices, those costs can take much of the possible gain.
""".strip(),
    charts=(
        Chart(
            title="A bull call spread at expiry",
            caption="Calculated with standard option pricing: share at $100, 30 days, 40% volatility. Buy the 100 call and sell the 110 call. No commissions.",
            data_kind="calculated",
            kind="lines",
            y_format="usd",
            y_label="Profit or loss per share",
            x_label="Share price at expiry",
            x_labels=_LABELS,
            series=(
                Series(
                    "Bull call spread",
                    _line(
                        [max(s - 100, 0) - max(s - 110, 0) - (_C100 - _C110) for s in _SPOTS]
                    ),
                    "accent",
                ),
                Series(
                    "Buying the 100 call only",
                    _line([max(s - 100, 0) - _C100 for s in _SPOTS]),
                    "muted",
                    "dashed",
                ),
            ),
        ),
        Chart(
            title="A calendar spread when the near option expires",
            caption="Calculated: sell the 30-day 100 call, buy the 60-day 100 call, 40% volatility. The later option is valued with 30 days left. It assumes volatility does not change, and it often does.",
            data_kind="calculated",
            kind="lines",
            place="example",
            y_format="usd",
            y_label="Profit or loss per share",
            x_label="Share price at near expiry",
            x_labels=_LABELS,
            series=(
                Series(
                    "Calendar spread",
                    _line(
                        [
                            call_price(s, 100, 0.4, _MONTH) - max(s - 100, 0) - (_FAR - _NEAR)
                            for s in _SPOTS
                        ]
                    ),
                    "accent",
                ),
            ),
        ),
    ),
    steps=(
        "Write down each leg and its price.",
        "Add them to get your net cost or credit.",
        "Work out the maximum gain, maximum loss and breakeven.",
        "Check the bid and ask spread on each leg.",
        "Decide before you enter what you will do if price moves against you.",
    ),
    example_md="""
A share is at **$100**. With 30 days left and 40% implied volatility:

- Buy the 100 call at **$4.57**.
- Sell the 110 call at **$1.37**.

Net cost: **$3.20** per share.

- **Maximum loss:** $3.20
- **Maximum gain:** (110 − 100) − 3.20 = **$6.80**
- **Breakeven:** 100 + 3.20 = **$103.20**

**Calendar:** sell the 30-day 100 call at $4.57 and buy the 60-day 100 call at $6.46. Net cost: **$1.89**. If the share is at exactly $100 when the near option expires, the later call would be worth about $4.57. The result in this example would be about **$2.68** before costs, assuming volatility has not changed.
""".strip(),
    mistakes=(
        "Forgetting that wide bid-ask spreads apply on each leg.",
        "Thinking that limited loss means a good trade.",
        "Ignoring early assignment risk on the short leg in some options.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
A spread limits risk by design, so that part is arithmetic. **It does not create an edge.**

Bryzgalova, Pavlova and Sikorskaya and de Silva, Smith and So find retail option traders lose on average, often because of high trading costs and overpaying around events. We found few independent tests specific to retail calendar spreads.
""".strip(),
    ),
    try_it="Pick any share. Calculate the maximum gain, loss and breakeven of a bull call spread 10% wide. Check how much the bid-ask spreads would cost.",
    quiz=(
        Q(
            "What is the maximum loss on a bull call spread bought for a net cost?",
            ("The net cost", "Unlimited", "The width of the strikes"),
            0,
            "A debit spread cannot lose more than you paid, before other costs.",
        ),
        Q(
            "A calendar spread depends on…",
            (
                "Time decay and implied volatility as well as price",
                "Only the share price",
                "Only dividends",
            ),
            0,
            "Changes in later-dated implied volatility can matter as much as the price.",
        ),
    ),
    takeaways=(
        "Spreads set limits on cost and gain.",
        "A limit on loss is not an edge.",
        "Costs matter because every leg has a spread.",
    ),
    sources=("bryzgalova-2023", "desilva-losing-optional"),
)

# ---------- delta hedging and gamma ----------

_DG_SPOTS = tuple(range(80, 121, 2))

DELTA_GAMMA = Lesson(
    slug="options/delta-hedging-and-gamma",
    title="Delta hedging, gamma and dealer flows",
    summary="Why option desks trade shares all day, and what 'gamma exposure' really estimates.",
    est_minutes=10,
    key_concepts=("delta", "gamma", "hedging", "gamma exposure", "volatility arbitrage", "dealers"),
    goal="Explain delta and gamma, work out a hedge, and understand what hedging can do to prices.",
    body_md="""
### Delta

**Delta** is how much an option's price changes when the share moves by $1. A call with a delta of 0.50 gains about $0.50 if the share rises by $1.

### Delta hedging

A desk that holds a call can sell shares to cancel the delta. Then it no longer cares about small moves. It has become a position mostly about **volatility**.

### Gamma

**Gamma** is how much the delta changes when the share moves. It is highest for options near the strike and close to expiry.

Gamma forces hedges to change:

- **Long gamma** (the desk owns options): when the price rises it sells more, and when the price falls it buys more. It trades **against** the move.
- **Short gamma** (the desk sold options): when the price rises it must buy, and when the price falls it must sell. It trades **with** the move.

Long gamma is paid for through time decay. Short gamma earns time decay but can be hurt badly by a large move.

### Gamma exposure

**Gamma exposure** estimates how much dealers may need to hedge. Short gamma may speed up moves, and long gamma may calm them.

**Public numbers are estimates.** They must guess who holds which options, and that guess can be wrong.
""".strip(),
    charts=(
        Chart(
            title="Delta changes as the price changes",
            caption="Calculated with standard option pricing: 100-strike call, 30% volatility. Delta changes fastest near the strike, and even faster close to expiry.",
            data_kind="calculated",
            kind="lines",
            y_format="plain",
            y_label="Call delta",
            x_label="Share price",
            x_labels=tuple(str(s) for s in _DG_SPOTS),
            series=(
                Series(
                    "30 days left",
                    _line([call_delta(s, 100, 0.3, _MONTH) for s in _DG_SPOTS]),
                    "accent",
                ),
                Series(
                    "5 days left",
                    _line([call_delta(s, 100, 0.3, 5 / 365) for s in _DG_SPOTS]),
                    "warn",
                ),
            ),
        ),
        Chart(
            title="Gamma peaks near the strike and near expiry",
            caption="Calculated with standard option pricing: 100-strike call, 30% volatility.",
            data_kind="calculated",
            kind="lines",
            place="example",
            y_format="plain",
            y_label="Gamma per $1 move",
            x_label="Share price",
            x_labels=tuple(str(s) for s in _DG_SPOTS),
            series=(
                Series(
                    "30 days left",
                    _line([option_gamma(s, 100, 0.3, _MONTH) for s in _DG_SPOTS]),
                    "accent",
                ),
                Series(
                    "5 days left",
                    _line([option_gamma(s, 100, 0.3, 5 / 365) for s in _DG_SPOTS]),
                    "warn",
                ),
            ),
        ),
    ),
    steps=(
        "Find the delta of the option and multiply by the number of shares it covers.",
        "Trade the opposite number of shares to hedge it.",
        "Work out the new delta after the price moves.",
        "Adjust the hedge and record the cost.",
        "Compare the total hedging result with the time decay you paid or earned.",
    ),
    example_md="""
A desk owns **100 call options**, each covering 100 shares. The share is at $100 and the 30-day option has a delta of about **0.517**.

Total delta: 100 × 100 × 0.517 = **5,170 shares**. The desk sells 5,170 shares to hedge.

The share rises to **$101**. Delta becomes about **0.563**, and total delta is **5,630 shares**. The desk sells **460 more shares** at the higher price.

If the share falls back to $100, delta returns to 0.517 and the desk buys those 460 shares back at a lower price. That gain is 460 × $1 = **$460** in this example.

Long gamma sells high and buys low when hedging. The cost of this is the option's time decay, and the desk gains overall only if the share moves enough.
""".strip(),
    mistakes=(
        "Trusting a public gamma number as if it were exact.",
        "Thinking a delta-neutral position has no risk.",
        "Forgetting trading costs when the hedge has to change often.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
**Hedging itself is basic option mathematics.**

**On buying volatility:** Bakshi and Kapadia found delta-hedged S&P 500 option buying lost money on average, which points to a volatility risk premium.

**On flows moving prices:** Baltussen, Da, Lammers and Martens found that market intraday momentum across more than 60 futures is linked to hedging short gamma. That is real evidence of an effect, but public gamma estimates are rough.
""".strip(),
    ),
    try_it="Pick an option. Using an online calculator, note its delta at today's price and at a price $1 higher. Work out how many shares a desk would need to trade to re-hedge 10 contracts.",
    quiz=(
        Q(
            "What does gamma measure?",
            (
                "How much the delta changes when the price moves",
                "How fast time passes",
                "The size of the spread",
            ),
            0,
            "Gamma is the rate of change of delta.",
        ),
        Q(
            "A dealer who is short gamma must usually…",
            (
                "Trade against the move",
                "Trade with the move: buy as price rises and sell as it falls",
                "Do nothing",
            ),
            1,
            "That is why short-gamma hedging can add to a move.",
        ),
    ),
    takeaways=(
        "Delta hedging removes direction, not all risk.",
        "Long gamma buys low and sells high, but pays time decay.",
        "Gamma exposure figures are estimates.",
    ),
    sources=("bakshi-kapadia-2003", "baltussen-2021", "carr-wu-2009"),
)

# ---------- skew and surface ----------

_STRIKES = (80, 85, 90, 95, 100, 105, 110, 115, 120)
_INDEX_IV = (32, 29, 26, 22.5, 20, 17.5, 16, 15.5, 15.5)
_FX_IV = (13.5, 11.5, 10, 9.2, 9, 9.2, 10, 11.5, 13.5)

SKEW = Lesson(
    slug="options/volatility-skew-and-surface",
    title="Volatility skew and the surface",
    summary="Why options at different strikes have different implied volatility.",
    est_minutes=8,
    key_concepts=("skew", "smile", "volatility surface", "risk reversal", "crash protection"),
    goal="Read a volatility skew, describe the surface, and see what the skew costs in dollars.",
    body_md="""
Basic option theory uses one volatility for all strikes. Real markets do not.

### Skew

**Skew** is how implied volatility changes across strikes.

- **Stock indexes:** lower-strike puts usually have **higher** implied volatility than higher-strike calls. People pay extra for crash protection.
- **Currencies:** often closer to a **smile**, with both sides a bit higher.
- **Single commodities:** often the opposite of stock indexes, because supply shocks push prices up.

This pattern became a clear feature of index options after the **1987 crash**.

### The surface

Add time to the picture. A **volatility surface** is a map of implied volatility across every strike and every expiry. Desks use it to keep all of their option prices consistent with each other.

### Risk reversal

Comparing an out-of-the-money call with an out-of-the-money put tells you which side costs more. In currencies, this difference is quoted directly as a **risk reversal**.

### What it does and does not tell you

Skew shows **what people are paying for protection**. A steep skew does not mean a crash is coming. It also does not mean the skew will flatten soon.
""".strip(),
    charts=(
        Chart(
            title="Two common shapes",
            caption="Illustrative values showing the typical shape only, not real quotes.",
            data_kind="illustrative",
            kind="lines",
            y_format="pct",
            y_label="Implied volatility",
            x_label="Strike, with the market at 100",
            x_labels=tuple(str(k) for k in _STRIKES),
            series=(
                Series("Stock index skew", tuple(float(v) for v in _INDEX_IV), "accent"),
                Series("Currency smile", tuple(float(v) for v in _FX_IV), "warn"),
            ),
        ),
        Chart(
            title="What the skew costs on a 90-strike put",
            caption="Calculated with standard option pricing: spot 100, 3 months, no interest. Same option, priced with flat 20% volatility and with 26% from the skew.",
            data_kind="calculated",
            kind="bars",
            place="example",
            y_format="usd",
            bars=(
                Bar("If volatility were flat at 20%", round(put_price(100, 90, 0.20, 0.25), 2), "muted"),
                Bar("With skew at 26%", round(put_price(100, 90, 0.26, 0.25), 2), "accent"),
            ),
        ),
    ),
    steps=(
        "Open an option chain and note implied volatility by strike.",
        "Plot it against the strike.",
        "Compare out-of-the-money puts with out-of-the-money calls.",
        "Repeat for a later expiry and compare the two curves.",
        "Translate the differences into dollar prices.",
    ),
    example_md="""
An index is at **100**, with 3 months left.

- The 90-strike put has implied volatility of **26%**.
- At-the-money options are at **20%**.
- The 110-strike call is at **16%**.

If volatility were flat at 20%, standard pricing would value the 90 put at about **$0.71**. At 26%, it is about **$1.45**, roughly **twice as much**.

The buyer pays about **$0.74 extra per share** for the protection. A risk reversal between these two strikes would read **16% − 26% = −10 volatility points**, meaning puts are much more expensive than calls.
""".strip(),
    mistakes=(
        "Treating a steep skew as a crash forecast.",
        "Assuming a skew must return to normal soon.",
        "Comparing implied volatility at different expiries as if they were the same thing.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Index skew has been a stable feature since the 1987 crash. Rubinstein's work on the smile is the classic reference, though we cite it from general knowledge.

Driessen, Maenhout and Vilkov found index options look expensive because they insure against correlation rising, yet that premium could not be exploited with realistic trading frictions. Skew explains prices far better than it offers a trade.
""".strip(),
    ),
    try_it="Open a free index option chain. Write down the implied volatility of a put 10% below the market and a call 10% above. Which is higher, and by how much?",
    quiz=(
        Q(
            "In stock indexes, which strikes usually have higher implied volatility?",
            ("Lower-strike puts", "Higher-strike calls", "They are always equal"),
            0,
            "Demand for crash protection lifts lower-strike put prices.",
        ),
        Q(
            "What does a volatility surface show?",
            (
                "Implied volatility across strikes and expiries",
                "Past prices only",
                "How many traders are long",
            ),
            0,
            "It is a full map of how options are priced.",
        ),
    ),
    takeaways=(
        "Implied volatility differs by strike and expiry.",
        "Index skew reflects demand for protection.",
        "A steep skew is not a forecast.",
    ),
    sources=("rubinstein-1994", "driessen-2009"),
)
