"""Stage 8 — Market by market. Every market uses the same headings."""

from __future__ import annotations

from mentor.domain.curriculum.book._kit import (
    Bar,
    Chart,
    Evidence,
    HLine,
    Lesson,
    Mark,
    Q,
    QuizQuestion,
    Series,
    Verdict,
    candle_chart,
    chapter,
    fact,
)
from mentor.domain.curriculum.charts import path


def _market(
    *,
    slug: str,
    title: str,
    summary: str,
    concepts: tuple[str, ...],
    goal: str,
    intro: str,
    how: str,
    hours: str,
    costs: str,
    leverage: str,
    moves: str,
    plan: str,
    steps: tuple[str, ...],
    example: str,
    mistakes: tuple[str, ...],
    evidence: Evidence,
    try_it: str,
    quiz: tuple[QuizQuestion, ...],
    takeaways: tuple[str, ...],
    charts: tuple[Chart, ...],
    sources: tuple[str, ...] = (),
) -> Lesson:
    """A market lesson with the same headings for every market."""
    body = (
        f"{intro.strip()}\n\n"
        f"### How it trades\n\n{how.strip()}\n\n"
        f"### Hours\n\n{hours.strip()}\n\n"
        f"### Costs\n\n{costs.strip()}\n\n"
        f"### Leverage\n\n{leverage.strip()}\n\n"
        f"### What moves it\n\n{moves.strip()}\n\n"
        f"### How your plan must change\n\n{plan.strip()}"
    )
    return Lesson(
        slug=slug,
        title=title,
        summary=summary,
        est_minutes=9,
        key_concepts=concepts,
        goal=goal,
        body_md=body,
        steps=steps,
        example_md=example.strip(),
        mistakes=mistakes,
        evidence=evidence,
        try_it=try_it,
        quiz=quiz,
        takeaways=takeaways,
        charts=charts,
        sources=sources,
    )


_FOREX = _market(
    slug="every-market/forex",
    title="Forex",
    summary="The world's largest market: pairs, sessions and rate differentials.",
    concepts=("forex", "pair", "rate differential", "swap"),
    goal="Know how forex works, what moves it, and how plans must fit it.",
    intro="**Forex** (foreign exchange) is the market for currencies. In April 2025 it traded **$9.6 trillion a day**, according to the Bank for International Settlements, but only about 31% of that was spot trading.",
    how="Spot forex is mostly over-the-counter, meaning dealers quote prices directly. Retail traders usually access it through a broker, often via CFDs.",
    hours="24 hours from Sunday evening to Friday evening (UTC), led by the Tokyo, London and New York sessions. The London–New York overlap is usually the busiest.",
    costs="Spread, commission and overnight swap. Major pairs like EUR/USD are usually the cheapest.",
    leverage="High in many places. The EU caps retail leverage at 30:1 on majors. The US at 50:1. Check your own rules.",
    moves="Interest rate differentials, inflation and central bank expectations. Risk appetite. Trade and capital flows.",
    plan="Plan around sessions and macro events. Watch for correlation, since many pairs share a dollar leg. Include swap in longer holds.",
    steps=(
        "Pick one or two major pairs.",
        "Note the active session for those pairs.",
        "Find the central-bank calendar for both currencies.",
        "Include swap in your cost estimates.",
    ),
    example="""
EUR/USD: a 0.10 lot position with a 40-pip stop risks **$40**. Hold it through three weeknights and you pay about **$1–$4** in swap, depending on your broker. Small, but it adds up on a longer plan.

Note that a large fraction of forex daily volume is institutional hedging and funding, and not speculative trading.
""",
    mistakes=(
        "Trading too many pairs at once.",
        "Ignoring that most pairs are correlated through the dollar.",
        "Trading exotics with wide spreads.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
Forecasting exchange rates is famously hard. Rossi's survey found that results depend heavily on method and period, and that the random walk is the toughest benchmark. Carry has been the most robust effect, along with some long-horizon momentum.

Retail CFD accounts lost money in 74–89% of cases in EU regulator studies, a group that includes many forex traders.
""",
    ),
    try_it="Note the spread on EUR/USD and on an exotic pair like USD/ZAR at the same moment. Compare the cost as a share of a typical day's move.",
    quiz=(
        Q(
            "What share of FX turnover was spot in April 2025?",
            ("About 10%", "About 31%", "About 80%"),
            1,
            "The rest was swaps, forwards and options.",
        ),
        Q(
            "What usually matters most for a major pair?",
            ("Rate differentials and macro expectations", "Stock splits", "Earnings per share"),
            0,
            "Rates and expectations drive currencies.",
        ),
    ),
    takeaways=(
        "Forex is huge and mostly institutional.",
        "Sessions and macro events matter.",
        "Correlation through the dollar is common.",
    ),
    charts=(
        Chart(
            title="FX turnover by product, April 2025",
            caption="Share of daily turnover. The headline $9.6 trillion is much larger than the spot market most retail traders use.",
            data_kind="published",
            kind="bars",
            y_format="pct",
            y_label="Share of turnover",
            source_note="Bank for International Settlements, Triennial Survey 2025.",
            bars=(
                Bar("FX swaps", 42, "accent"),
                Bar("Spot", 31, "accentSoft"),
                Bar("Forwards", 19, "accent"),
                Bar("Options", 7, "warn"),
            ),
        ),
    ),
    sources=("bis-fx-2025", "rossi-2013", "esma-cfd-2018"),
)

_STOCKS = _market(
    slug="every-market/stocks-and-etfs",
    title="Stocks and ETFs",
    summary="Shares of companies and baskets, and how trading them differs.",
    concepts=("stock", "ETF", "earnings", "gap"),
    goal="Know how stocks and ETFs trade, what moves them, and how to plan for gaps.",
    intro="A **stock** is a share of a company. An **ETF** (exchange-traded fund) is a fund that trades like a share and usually holds a basket of assets.",
    how="Most shares trade on regulated exchanges with public prices and volume. Prices can gap between sessions.",
    hours="US shares trade officially 09:30–16:00 New York time, with extended sessions either side. Exchanges have been moving towards longer hours, so check your broker.",
    costs="Commission (often zero at retail brokers), spread, and any financing on margin. Spreads are usually tight on big names and wider on small ones.",
    leverage="US margin accounts usually allow about 2:1 overnight. The US $25,000 pattern-day-trader minimum was approved for removal in 2026 (FINRA Rule 4210, effective 4 June 2026), though implementation depends on your broker.",
    moves="Company earnings and guidance, interest rates, sector news and the overall market mood.",
    plan="Plan for gaps, especially around earnings. Stocks often move together with the market, so measure risk in terms of the market as well as the single stock.",
    steps=(
        "Check the next earnings date before any trade.",
        "Check average daily volume.",
        "Set your stop with gap risk in mind.",
        "Size smaller around earnings, or avoid them.",
    ),
    example="""
You buy 100 shares of a company at $60 with a stop at $56 (risk $400). The company reports earnings overnight. The shares open at $50.

Your stop does not protect you. Your loss is **$1,000**, not $400. Many traders avoid holding through earnings for this reason, or use options to define their risk.
""",
    mistakes=(
        "Forgetting about earnings dates.",
        "Assuming a stop works across an overnight gap.",
        "Trading illiquid shares with large spreads.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Momentum is well documented in stocks: Jegadeesh and Titman found past 3- to 12-month winners kept beating losers over the next 3 to 12 months. McLean and Pontiff found that published return predictors shrink after publication.

Frequent trading hurts ordinary investors: US households that traded the most earned 11.4% a year when the market earned 17.9% (Barber and Odean).
""",
    ),
    try_it="For a stock you follow, find the next earnings date and the size of its last four earnings-day moves.",
    quiz=(
        Q(
            "Why do overnight gaps matter?",
            (
                "A stop cannot protect you when the market opens beyond it",
                "They reduce commission",
                "They only affect futures",
            ),
            0,
            "A gap can jump past your stop.",
        ),
        Q(
            "Which is a real research finding about stocks?",
            (
                "Past 3–12 month winners tended to keep outperforming",
                "Stocks never gap",
                "Earnings don't move prices",
            ),
            0,
            "That is the momentum effect.",
        ),
    ),
    takeaways=(
        "Stocks can gap past your stop.",
        "Know earnings dates.",
        "Momentum is documented, but frequent trading hurts many investors.",
    ),
    charts=(
        candle_chart(
            path([(0, 58), (12, 60), (13, 51), (30, 50)], seed=203, noise=0.2),
            title="An earnings gap",
            caption="Illustrative prices. Your stop at 56 does not fill until price is already at 51.",
            hlines=(HLine(56, "Stop at 56", "danger"),),
            marks=(Mark(13, 51, "Overnight gap", "danger"),),
        ),
    ),
    sources=("jegadeesh-1993", "mclean-pontiff-2016", "barber-odean-2000", "finra-pdt-2026"),
)

_INDICES = _market(
    slug="every-market/indices",
    title="Indices",
    summary="Trading the whole market through one number.",
    concepts=("index", "S&P 500", "index futures"),
    goal="Know how indices work and how to trade them through futures, ETFs or CFDs.",
    intro="An **index** is a number representing a basket of shares, such as the S&P 500 or the Nasdaq 100. You cannot buy the index directly; you trade a future, an ETF or a CFD that follows it.",
    how="ETFs trade on exchanges. Index futures, such as the E-mini S&P 500, trade nearly around the clock on CME. CFDs trade with your broker.",
    hours="US stock index futures trade about 23 hours a day on weekdays. The cash market hours are the most active.",
    costs="Futures have tick costs and fees. ETFs have tight spreads and small annual fees. CFDs include financing.",
    leverage="Futures have a built-in leverage. Check initial and maintenance margins. The EU allows 20:1 on major indices via CFDs.",
    moves="The overall economy, interest rates, large-company earnings and investor risk appetite.",
    plan="Trade the most liquid product available. Note that indices have a long-term upward bias from earnings and dividends, so short positions fight a tailwind.",
    steps=(
        "Choose how you will trade it: future, ETF or CFD.",
        "Find the point value and costs.",
        "Plan around earnings seasons and central bank days.",
        "Size using the point value.",
    ),
    example="""
E-mini S&P 500 is $50 per point. A 15-point stop is **$750** per contract. A $25,000 account at 1% risks $250, so one E-mini is too large.

The Micro E-mini at $5 per point: 15 points is $75 per contract. You can trade 3 contracts for $225.
""",
    mistakes=(
        "Taking E-mini size on a small account.",
        "Shorting without noticing the long-run upward drift.",
        "Treating an index CFD as if it were the exchange product.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Long-term equity index returns have been positive over long periods, reflecting company profits and dividends. Market timing is much harder: Barber and Odean show that frequent trading tends to hurt ordinary investors.

The 'sell in May' seasonal effect is documented across many countries, and it is debated. Treat any index-timing rule with care.
""",
    ),
    try_it="Find the point value of two index products your broker offers. Compute the money risk for a 20-point stop on each.",
    quiz=(
        Q(
            "How much is one point on the E-mini S&P 500?",
            ("$5", "$12.50", "$50"),
            2,
            "It is $50 per point; the Micro is $5.",
        ),
        Q(
            "Why are shorts at a disadvantage in indices over the long run?",
            (
                "Indices tend to rise over long periods",
                "Shorting is illegal",
                "Dividends don't exist",
            ),
            0,
            "Long-run returns have been positive, which works against persistent shorts.",
        ),
    ),
    takeaways=(
        "You trade an index through a product.",
        "Point value determines your risk.",
        "Long-run upward drift works against shorts.",
    ),
    charts=(
        Chart(
            title="How much one point is worth",
            caption="Money per one point move in the index, from CME specifications.",
            data_kind="published",
            kind="bars",
            y_format="usd",
            y_label="Dollars per point",
            source_note="CME Group product overview.",
            bars=(
                Bar("E-mini S&P 500", 50, "accent"),
                Bar("Micro E-mini S&P 500", 5, "accentSoft"),
            ),
        ),
    ),
    sources=("cme-micro", "barber-odean-2000", "bouman-2002"),
)

_FUTURES = _market(
    slug="every-market/futures",
    title="Futures",
    summary="Standardised contracts with built-in leverage.",
    concepts=("futures", "margin", "tick", "expiry", "contango", "backwardation"),
    goal="Understand how futures work, including margin and expiry.",
    intro="A **future** is a standard contract, traded on an exchange, to buy or sell something at a set price on a future date.",
    how="Every future has a fixed size, tick value, expiry date and exchange. A clearing house stands behind each trade. Most traders close or roll positions before expiry.",
    hours="Many major futures trade about 23 hours a day from Sunday evening to Friday afternoon, US Central Time. There are short maintenance breaks.",
    costs="Commission and exchange fees, plus the spread. Margin is a deposit, not a cost.",
    leverage="Built-in and often high. You post a margin deposit that is a small part of the contract value. Losses can exceed your margin.",
    moves="Depends on the underlying: economic data, supply and demand, or interest rates.",
    plan="Know contract size, tick value and margin before you trade. Roll positions before expiry. Be careful of low liquidity in far-dated contracts.",
    steps=(
        "Read the contract specification.",
        "Note tick value, margin and expiry date.",
        "Size using tick value and stop distance.",
        "Plan to roll or close before expiry.",
    ),
    example="""
Micro E-mini at $5 per point, tick 0.25 = **$1.25**. You trade one contract with a 20-point stop.

- Risk: 20 × $5 = **$100**.
- Margin might be about $1,500 (it changes). That money is a deposit, not your risk. Your risk is $100 if the stop fills as expected.

If the market gaps through your stop, you can lose more than $100. Over a long holiday weekend this risk is larger.
""",
    mistakes=(
        "Confusing margin with maximum risk.",
        "Letting a contract roll into physical delivery by accident.",
        "Trading a far-dated contract with poor liquidity.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Time-series momentum has been found in equity, currency, commodity and bond futures (Moskowitz, Ooi and Pedersen; Hurst et al.). Those results use a diversified portfolio and low costs.

Remember the clearing house removes counterparty risk, not market risk.
""",
    ),
    try_it="Open the contract specification page for one future. Write its tick value, trading hours and expiry dates.",
    quiz=(
        Q(
            "Is margin the most you can lose on a future?",
            ("Yes", "No, losses can exceed margin", "Only on Fridays"),
            1,
            "Margin is a deposit. Moves can exceed it.",
        ),
        Q(
            "What must you do before a contract expires, if you want to keep the position?",
            ("Nothing", "Roll to the next contract", "Add more margin"),
            1,
            "Rolling moves the position to the next expiry.",
        ),
    ),
    takeaways=(
        "Futures have fixed size and tick value.",
        "Margin is not your maximum risk.",
        "Plan for expiry.",
    ),
    charts=(
        Chart(
            title="What one tick costs on two contracts",
            caption="Calculated from the E-mini and Micro E-mini tick values on CME: $12.50 and $1.25.",
            data_kind="published",
            kind="bars",
            y_format="usd",
            y_label="Dollars per tick",
            source_note="CME Group product overview.",
            bars=(Bar("E-mini tick", 12.5, "accent"), Bar("Micro tick", 1.25, "accentSoft")),
        ),
    ),
    sources=("cme-micro", "moskowitz-2012", "hurst-2017"),
)

_COMMOD = _market(
    slug="every-market/commodities-and-gold",
    title="Commodities and gold",
    summary="Real things with real supply and demand.",
    concepts=("commodity", "gold", "oil", "contango", "backwardation", "seasonality"),
    goal="Understand what drives commodities and how they differ from financial markets.",
    intro="**Commodities** are physical goods: energy, metals and crops. They trade mostly through futures.",
    how="Futures on exchanges like CME and ICE are the main venue. Gold is also traded as spot and through ETFs.",
    hours="Most major commodity futures trade about 23 hours on weekdays, depending on the product.",
    costs="Futures fees and spreads, and sometimes **contango**, which is when later contracts cost more, making it expensive to hold long.",
    leverage="Built into futures. EU retail CFD limits for gold are 20:1.",
    moves="Supply, demand, weather, storage, geopolitics. Gold responds especially to real interest rates and the dollar.",
    plan="Expect seasonal patterns and event-driven moves. Understand the contract, because the holding cost can matter a lot. Be careful with leverage in volatile products.",
    steps=(
        "Learn the supply and demand story for your commodity.",
        "Check whether the futures curve makes holding expensive.",
        "Plan around scheduled reports, such as inventories.",
        "Size for high volatility.",
    ),
    example="""
An oil trader goes long the front-month contract. Each month the position has to be rolled to the next, more expensive contract. If contango is 2% a month, that is a big annual drag on returns even if the spot oil price is flat.

Many retail oil ETFs have suffered this way over long periods.
""",
    mistakes=(
        "Ignoring the shape of the futures curve.",
        "Trading through an inventory report without a plan.",
        "Assuming seasonal patterns will repeat.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Commodities show evidence of momentum and carry (Moskowitz et al.; Koijen et al.). Seasonal patterns exist where real seasons exist, like harvests, but traders know about them.

Gold's reputation as an inflation hedge is widely repeated, but the relationship has been inconsistent over time; we have not reviewed this in depth.
""",
    ),
    try_it="Look at the price of the first and second contract for a commodity future. Is it in contango or backwardation?",
    quiz=(
        Q(
            "What is contango?",
            ("Later contracts cost more than nearer ones", "A type of candle", "An exchange"),
            0,
            "Rolling long positions in contango costs money.",
        ),
        Q(
            "What often moves gold?",
            ("Real interest rates and the dollar", "Airline earnings", "Stock splits"),
            0,
            "Gold is sensitive to real rates and the dollar.",
        ),
    ),
    takeaways=(
        "Commodities have real supply and demand.",
        "The futures curve can cost you money.",
        "Volatility can be high, so size carefully.",
    ),
    charts=(
        Chart(
            title="An example of contango",
            caption="Illustrative futures curve. Each later contract is priced higher, so holding long involves paying up each time you roll.",
            data_kind="illustrative",
            kind="lines",
            y_format="usd",
            y_label="Contract price",
            x_label="Contract month",
            x_labels=("Jan", "Feb", "Mar", "Apr", "May", "Jun"),
            series=(Series("Futures curve", (75, 76, 77.1, 78, 78.8, 79.5), "warn"),),
        ),
    ),
    sources=("moskowitz-2012", "koijen-2018"),
)

_BONDS = _market(
    slug="every-market/bonds-and-rates",
    title="Bonds and rates",
    summary="Prices fall when yields rise. Duration tells you how much.",
    concepts=("bond", "yield", "duration", "yield curve", "credit"),
    goal="Understand how bond prices and yields move, and what duration means.",
    intro="A **bond** is a loan to a government or company. It pays interest and returns the loan at the end. The **yield** is the return it pays, as a percentage of its price.",
    how="Government bonds trade through dealers. Most retail traders use bond ETFs or Treasury futures.",
    hours="Major bond futures trade nearly around the clock on weekdays. The cash market has its own schedule.",
    costs="Spreads and fund fees. Bond ETFs are simple to trade.",
    leverage="Bond futures have very high built-in leverage, because bond prices move slowly.",
    moves="Interest rates, inflation expectations and central bank policy. Credit risk for corporate bonds.",
    plan="Think in **duration**, not in dollars. Remember that a small change in yield can mean a large change in price for a long-duration bond.",
    steps=(
        "Find the duration of the bond or ETF.",
        "Estimate the price move for a 1% rise in rates.",
        "Check what central banks are expected to do.",
        "Decide your risk based on that estimate.",
    ),
    example="""
A bond fund has a **duration of 8**. If rates rise by 1%, the fund falls by about **8%**. On a $10,000 position that is $800.

A shorter-duration fund (duration 2) would fall by about $200 for the same rate move. Duration is a quick way to compare interest-rate risk.
""",
    mistakes=(
        "Thinking bonds are always safe.",
        "Ignoring duration.",
        "Forgetting inflation eats fixed payments.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
The inverse relationship between bond prices and yields is a mechanical fact, as FINRA and the SEC explain. FINRA gives the example that a fund with a 10-year duration falls about 10% for a 1% rate rise.

Forecasting rates is hard. Momentum research includes bond futures, with the usual caveats.
""",
    ),
    try_it="Find the duration of a bond ETF. Compute how much it would fall if rates rose by 1%.",
    quiz=(
        Q(
            "When interest rates rise, fixed-rate bond prices…",
            ("Fall", "Rise", "Do not change"),
            0,
            "Existing bonds become less attractive.",
        ),
        Q(
            "A fund has duration 6. Rates rise 1%. The fund falls about…",
            ("1%", "6%", "60%"),
            1,
            "Duration is a rule of thumb: duration × rate change.",
        ),
    ),
    takeaways=(
        "Bond prices move opposite to yields.",
        "Duration tells you how much.",
        "Rates and inflation are the main drivers.",
    ),
    charts=(
        Chart(
            title="Price fall for a 1% rate rise, by duration",
            caption="Calculated rule of thumb: price change ≈ −duration × rate change. It ignores second-order effects.",
            data_kind="calculated",
            kind="bars",
            y_format="pct",
            y_label="Approximate price change",
            bars=(
                Bar("Duration 2", -2, "accentSoft"),
                Bar("Duration 5", -5, "accent"),
                Bar("Duration 8", -8, "warn"),
                Bar("Duration 15", -15, "danger"),
            ),
        ),
    ),
    sources=("finra-duration", "sec-rate-risk", "moskowitz-2012"),
)

_OPTIONS = _market(
    slug="every-market/options",
    title="Options",
    summary="Rights, premiums and the risks most buyers do not understand.",
    concepts=("option", "call", "put", "strike", "implied volatility", "theta"),
    goal="Understand what an option is and why it behaves differently from shares.",
    intro="An **option** is a contract that gives the buyer the right, not the duty, to buy (a **call**) or sell (a **put**) something at a set price (the **strike**), by a set date (the **expiry**). The buyer pays a **premium**.",
    how="Listed options trade on exchanges and clear through a central body. Spreads can be wide on less popular strikes.",
    hours="Equity options generally follow US market hours. Index options have some extended sessions.",
    costs="Spreads can be large, especially on cheap short-dated options. **Bryzgalova, Pavlova and Sikorskaya** report average spreads of about 12.6% on the cheap weekly options retail traders favour.",
    leverage="Options have strong built-in leverage. Selling options can carry large or even unlimited risk.",
    moves="The underlying price, **implied volatility**, and time. Options lose value as they get closer to expiry, which is called **theta decay**.",
    plan="Know your maximum loss before you trade. Use defined-risk structures to start. Do not buy lottery tickets every week.",
    steps=(
        "Read your regulator's options risk disclosure.",
        "Know the difference between buying and selling.",
        "Check implied volatility, not just the price.",
        "Check the bid–ask spread.",
        "Start with defined-risk trades, in small size.",
    ),
    example="""
You buy a call for **$2** on a stock trading at $100. The strike is $105, and it expires in two weeks.

You lose the $2 if the stock stays below $105. To break even you need the stock above **$107** by expiry. The stock could go up and you could still lose money.

If implied volatility falls after earnings, the option can lose value even if the stock rises a little. This is often called a **volatility crush**.
""",
    mistakes=(
        "Treating options like cheap shares.",
        "Buying short-dated options repeatedly.",
        "Selling naked options without understanding the risk.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
Studies consistently show retail options buyers lose money on average. Bryzgalova et al. and de Silva et al. find retail traders tend to overpay, especially around events, and suffer from large spreads.

FINRA has reminded firms that options can be risky for retail investors who do not understand them.
""",
    ),
    try_it="Look up one option's bid and ask. Compute the spread as a percentage of the mid price.",
    quiz=(
        Q(
            "What does a call buyer have?",
            ("The right to buy at the strike", "The duty to sell", "A loan"),
            0,
            "A call gives the right, not the duty, to buy.",
        ),
        Q(
            "What does theta decay mean?",
            (
                "Options lose time value as expiry gets closer",
                "Options earn interest",
                "Stocks fall",
            ),
            0,
            "All else equal, time works against option buyers.",
        ),
    ),
    takeaways=(
        "An option's value depends on price, volatility and time.",
        "Retail buyers tend to lose on average.",
        "Know your maximum loss before trading.",
    ),
    charts=(
        Chart(
            title="Payoff of a long call at expiry",
            caption="Calculated: strike $105, premium $2. You lose the premium below the strike, and break even at $107.",
            data_kind="calculated",
            kind="lines",
            y_format="usd",
            y_label="Profit per share",
            x_label="Stock price at expiry",
            x_labels=tuple(str(p) for p in range(95, 121, 2)),
            series=(
                Series(
                    "Long call", tuple(max(p - 105, 0) - 2.0 for p in range(95, 121, 2)), "accent"
                ),
            ),
        ),
    ),
    sources=("bryzgalova-2023", "desilva-losing-optional", "finra-options-2208"),
)

_CRYPTO = _market(
    slug="every-market/crypto",
    title="Crypto",
    summary="24/7, volatile and full of fragmented venues.",
    concepts=("crypto", "bitcoin", "perpetual futures", "funding", "custody"),
    goal="Know how crypto trading differs and what risks are unique to it.",
    intro="**Crypto** assets such as bitcoin trade on many exchanges all day, every day. In January 2024, US regulators approved spot bitcoin ETFs, which brought in more traditional access.",
    how="Trading happens on many separate exchanges. Prices can differ between them. Many traders use **perpetual futures**, which have no expiry and use funding payments to stay near the spot price.",
    hours="24 hours a day, 7 days a week. Weekends and overnight hours can be thin.",
    costs="Trading fees, spreads, **funding** on perpetuals, often paid every 8 hours on many exchanges, plus withdrawal fees.",
    leverage="Often extremely high on crypto exchanges, which is one reason regulators are wary. EU retail CFD leverage on crypto is capped at 2:1.",
    moves="Sentiment, regulation, liquidity and flows through large exchanges. Macro factors can matter too.",
    plan="Use small sizes and wide stops. Assume extreme moves. Understand who holds your money. Weekend gaps do not exist, but weekend volatility does.",
    steps=(
        "Choose venues with care and understand custody.",
        "Size far smaller than you would for forex.",
        "Check funding rates if you use perpetuals.",
        "Plan for 24/7 risk: use stops and alerts.",
    ),
    example="""
Bitcoin at **$60,000**. A daily ATR of $3,000 means a 2× ATR stop is **$6,000**, or 10% of the price.

$500 risk / $6,000 = **0.083 BTC**, a position worth about $5,000. The same risk in EUR/USD with a 60-pip stop would be 0.83 lots, about $90,000 of notional. The higher volatility forces a much smaller position.

Crypto exchanges have failed before. Do not assume your funds are safe because they are on a popular exchange.
""",
    mistakes=(
        "Using high leverage.",
        "Leaving all funds on one exchange.",
        "Forgetting that crypto is open while you sleep.",
    ),
    evidence=Evidence(
        Verdict.WEAK,
        """
Crypto is young, and academic results vary across periods and venues. Volatility is high, and exchange failures are a real risk that traditional-market studies do not capture. Be suspicious of any strategy tested only over a bull market.
""",
    ),
    try_it="Compute a 2× ATR stop on bitcoin, and find the position size for a $200 risk. Compare it with a major forex pair.",
    quiz=(
        Q(
            "Crypto markets trade…",
            ("Only on weekdays", "24 hours a day, every day", "Only during US hours"),
            1,
            "They trade continuously, which brings thin hours too.",
        ),
        Q(
            "What keeps a perpetual future's price near spot?",
            ("Funding payments", "Dividends", "Earnings"),
            0,
            "Funding payments are exchanged periodically.",
        ),
    ),
    takeaways=(
        "Crypto trades all the time.",
        "Volatility and venue risk are high.",
        "Use small sizes and wide stops.",
    ),
    charts=(
        Chart(
            title="Position size for the same $500 risk",
            caption="Calculated: notional value when each market's normal-sized stop must risk the same $500. Stops assumed at 2× a typical daily ATR.",
            data_kind="calculated",
            kind="bars",
            y_format="usd",
            y_label="Notional position",
            bars=(
                Bar("EUR/USD", 90000, "accent"),
                Bar("S&P 500 future", 50000, "accentSoft"),
                Bar("Bitcoin", 5000, "danger"),
            ),
        ),
    ),
    sources=("sec-bitcoin-etf", "esma-cfd-2018"),
)

_ADAPT = Lesson(
    slug="every-market/adapting-a-plan",
    title="Adapting a plan to a new market",
    summary="A checklist for moving any strategy from one market to another.",
    est_minutes=7,
    key_concepts=("adaptation", "checklist", "volatility scaling"),
    goal="Be able to move a plan to a new market without breaking it.",
    body_md="""
A plan that works on EUR/USD does not automatically work on gold. Before moving, check each of these.

- **Hours:** when is the market active?
- **Costs:** spread, commission, financing.
- **Volatility:** set stops relative to ATR, not fixed numbers.
- **Liquidity:** does the instrument trade enough for your size?
- **Gaps:** does it close overnight or over the weekend?
- **Drivers:** what moves it? What is on the calendar?
- **Correlation:** does it add risk to what you already hold?
- **Contract size:** what is one tick worth?

### Volatility scaling

If your plan's stop is 2× ATR in forex, make it 2× ATR in the new market, not the same number of points. If your target is 2R, keep it 2R. Rules written in units of volatility and R move more easily between markets.

### Re-test

A plan has not been tested on a new market until you have tested it there. Before risking real money, test, then demo, then go small.
""".strip(),
    charts=(
        Chart(
            title="Why fixed pip stops do not travel",
            caption="Illustrative typical daily ATR as a share of price. A stop that is sensible on one market can be noise on another.",
            data_kind="illustrative",
            kind="bars",
            y_format="pct",
            y_label="Typical daily ATR as % of price",
            bars=(
                Bar("EUR/USD", 0.5, "accentSoft"),
                Bar("S&P 500", 1.1, "accent"),
                Bar("Gold", 1.2, "accent"),
                Bar("Bitcoin", 4.0, "danger"),
            ),
        ),
    ),
    steps=(
        "Write your plan in units of ATR and R.",
        "Fill in the new market's checklist.",
        "Re-test with this market's costs.",
        "Demo trade it.",
        "Go live with the smallest possible size.",
    ),
    example_md="""
Your plan on EUR/USD: 2× ATR stop (about 100 pips), 2R target, trades at 16:00–20:00 Dubai time.

For gold futures, you change it: 2× ATR on gold is about $60, your size is set by tick value, you trade the main session, and you check gold inventories and Fed days on your calendar. The plan keeps the same logic, but the numbers change.
""".strip(),
    mistakes=(
        "Copying a plan's pip numbers directly.",
        "Assuming costs are similar.",
        "Skipping the demo stage.",
    ),
    evidence=fact(
        "A checklist rather than a claim. Whether a strategy works on a new market can only be found by testing it there. That is what the next two stages are for."
    ),
    try_it="Pick a plan you know and fill out the checklist for a second market you don't trade.",
    quiz=(
        Q(
            "Why write plans in ATR and R?",
            (
                "So they travel between markets",
                "Because it looks professional",
                "It is required by regulators",
            ),
            0,
            "They adjust to each market's volatility and risk.",
        ),
        Q(
            "Before going live on a new market, you should…",
            ("Test and demo it there first", "Use your biggest position", "Skip costs"),
            0,
            "A plan is not tested on a market until you test it there.",
        ),
    ),
    takeaways=(
        "Plans do not automatically transfer.",
        "Write rules in ATR and R.",
        "Re-test on the new market.",
    ),
)

CHAPTERS = (
    chapter(
        "every-market",
        "markets",
        "Every market",
        "How each market trades, what moves it, and how your plan must change.",
        (_FOREX, _STOCKS, _INDICES, _FUTURES, _COMMOD, _BONDS, _OPTIONS, _CRYPTO, _ADAPT),
    ),
)
