"""Reading list behind the book.

``checked`` is True when the source was opened or searched for during the
November 2026 research pass and its key claim confirmed there. False means the
reference is cited from general knowledge and was not re-opened: treat it as a
pointer, not a verified quotation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class Source:
    key: str
    authors: str
    year: str
    title: str
    url: str
    note: str
    topic: str
    checked: bool = True


SOURCES: Final[tuple[Source, ...]] = (
    # ---- who wins, who loses ----
    Source(
        "esma-cfd-2018",
        "European Securities and Markets Authority",
        "2018",
        "ESMA agrees to prohibit binary options and restrict CFDs to protect retail investors",
        "https://www.esma.europa.eu/node/84933",
        "National regulators found 74–89% of retail CFD accounts lose money; average losses "
        "per client €1,600 to €29,000. Sets leverage caps from 30:1 down to 2:1.",
        "Retail outcomes",
    ),
    Source(
        "barber-day-2014",
        "Barber, Lee, Liu, Odean",
        "2014",
        "The cross-section of speculator skill: evidence from day trading",
        "https://econpapers.repec.org/RePEc:eee:finmar:v:18:y:2014:i:c:p:1-24",
        "Taiwan day traders 1992–2006: under 1% predictably earn positive returns after fees.",
        "Retail outcomes",
    ),
    Source(
        "chague-2020",
        "Chague, De-Losso, Giovannetti",
        "2020",
        "Day trading for a living?",
        "https://www.scribd.com/document/428540384/SSRN-id3423101",
        "Brazilian futures day traders who persisted: about 3% profited after fees. The page "
        "seen is a copy of the working paper, so check the journal version before quoting it.",
        "Retail outcomes",
    ),
    Source(
        "barber-odean-2000",
        "Barber, Odean",
        "2000",
        "Trading is hazardous to your wealth",
        "https://econpapers.repec.org/RePEc:bla:jfinan:v:55:y:2000:i:2:p:773-806",
        "66,465 US households 1991–96: those trading most earned 11.4% a year, the market 17.9%.",
        "Retail outcomes",
    ),
    Source(
        "bryzgalova-2023",
        "Bryzgalova, Pavlova, Sikorskaya",
        "2023",
        "Retail trading in options and the rise of the big three wholesalers",
        "https://econpapers.repec.org/RePEc:cpr:ceprdp:17688",
        "Retail option buyers favour cheap weekly options with wide spreads and lose on average.",
        "Retail outcomes",
    ),
    Source(
        "desilva-losing-optional",
        "de Silva, Smith, So",
        "2022",
        "Losing is optional: retail option trading and earnings announcement volatility",
        "https://www.econbiz.de/Record/losing-is-optional-retail-option-trading-and-earnings-"
        "announcement-volatility-silva-tim/10013403980",
        "Retail buyers overpay around earnings, pay large spreads, and react slowly.",
        "Retail outcomes",
    ),
    # ---- market structure and regulation ----
    Source(
        "bis-fx-2025",
        "Bank for International Settlements",
        "2025",
        "OTC foreign exchange turnover in April 2025 (Triennial Survey)",
        "https://www.bis.org/statistics/rpfx25_fx.htm",
        "$9.6 trillion a day; swaps 42%, spot 31%, forwards 19%, options 7%; USD on 89.2% of "
        "trades, EUR 28.9%, JPY 16.8%, GBP 10.2%.",
        "Markets",
    ),
    Source(
        "finra-pdt-2026",
        "SEC / FINRA",
        "2026",
        "Federal Register notice approving amendments to FINRA Rule 4210",
        "https://www.govinfo.gov/content/pkg/FR-2026-04-17/html/2026-07485.htm",
        "Removes the $25,000 pattern-day-trader minimum; FINRA Notice 26-10 gives 4 June 2026 "
        "as effective. Brokers may roll this out over time, so check yours.",
        "Regulation",
    ),
    Source(
        "cme-micro",
        "CME Group",
        "n.d.",
        "Micro E-mini futures products overview",
        "https://cmegroup.com/cn-t/education/courses/micro-e-mini-futures/"
        "micro-e-mini-futures-products-overview.html",
        "E-mini S&P 500 has a $50 multiplier and $12.50 tick; the Micro has a $5 multiplier.",
        "Markets",
    ),
    Source(
        "cftc-cot",
        "CFTC",
        "n.d.",
        "Commitments of Traders report descriptions and release schedule",
        "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm",
        "Weekly positions data, generally released Friday for the previous Tuesday. Reports "
        "suggest a twice-weekly schedule may follow; check the schedule page.",
        "Markets",
    ),
    Source(
        "cftc-forex-alert",
        "CFTC and NASAA",
        "n.d.",
        "Investor alert: foreign exchange currency fraud",
        "https://www.cftc.gov/LearnAndProtect/AdvisoriesAndArticles/cftcnasaaforexalert.html",
        "Regulators warn off-exchange retail forex is at best very risky and can be fraud; "
        "check a firm's registration first.",
        "Regulation",
    ),
    Source(
        "finra-duration",
        "FINRA",
        "n.d.",
        "Duration: what an interest rate hike could do to your bond portfolio",
        "https://www.finra.org/investors/alerts/duration-what-interest-rate-hike-could-do-your-"
        "bond-portfolio",
        "Higher duration means more rate sensitivity: a 10-year-duration fund falls about 10% "
        "if rates rise 1%.",
        "Markets",
    ),
    Source(
        "sec-rate-risk",
        "SEC",
        "n.d.",
        "Interest rate risk: when interest rates go up, prices of fixed-rate bonds fall",
        "https://www.sec.gov/files/ib_interestraterisk.pdf",
        "Investor bulletin on why bond prices move opposite to yields.",
        "Markets",
    ),
    Source(
        "finra-leveraged-etf",
        "FINRA and SEC",
        "2009",
        "FINRA, SEC warn retail investors about leveraged or inverse ETFs",
        "https://finra.org/media-center/news-releases/2009/finra-sec-warn-retail-investors-"
        "about-investing-leveraged-or-inverse",
        "Most reset daily, so multi-day results can differ sharply from the stated multiple.",
        "Markets",
    ),
    Source(
        "finra-options-2208",
        "FINRA",
        "2022",
        "Regulatory Notice 22-08: complex products and options",
        "https://www.sifma.org/wp-content/uploads/2022/05/FINRA-Regulatory-Notice-22-08-"
        "Complex-Products-and-Options-5.9.2022.pdf",
        "Firms reminded that options can be risky for retail investors who do not understand them.",
        "Regulation",
    ),
    Source(
        "sec-bitcoin-etf",
        "National Law Review summary of the SEC order",
        "2024",
        "SEC approves 11 bitcoin spot ETFs",
        "https://natlawreview.com/article/sec-approves-11-bitcoin-spot-etfs",
        "SEC approved 11 spot bitcoin products on 10 January 2024.",
        "Markets",
    ),
    Source(
        "uae-finfluencer",
        "Pinsent Masons, Hadef & Partners, Clyde & Co",
        "2025–26",
        "UAE licensing regime for finfluencers (SCA Chairman Resolution No. 10 of 2025)",
        "https://www.pinsentmasons.com/out-law/news/uae-new-licensing-regime-finfluencers",
        "Licensing for people giving financial recommendations on social media. Law-firm "
        "summaries, not the text of the resolution; the regulator is reported renamed CMA.",
        "Regulation",
    ),
    Source(
        "prop-mff",
        "Finance Magnates",
        "2025",
        "My Forex Funds wins dismissal of CFTC case",
        "https://www.financemagnates.com/forex/myforexfunds-hints-at-comeback-after-winning-"
        "legal-battle-against-cftc/",
        "CFTC sued in 2023; the case was dismissed in 2025 and left the wider questions open.",
        "Prop firms",
    ),
    Source(
        "prop-stats",
        "Track360 (industry source, unaudited)",
        "2026",
        "Prop trading industry statistics",
        "https://track360.io/blog/prop-trading-industry-statistics-2026",
        "Roughly 12–14% of challenges pass and about 7% of buyers are ever paid. Treat as a "
        "rough, industry-reported estimate.",
        "Prop firms",
    ),
    # ---- does technical analysis work ----
    Source(
        "fama-1970",
        "Fama",
        "1970",
        "Efficient capital markets: a review of theory and empirical work",
        "https://www.econbiz.de/Record/efficient-capital-markets-a-review-of-theory-and-"
        "empirical-work-fama-eugene/10005302862",
        "The classic statement that prices reflect available information.",
        "Market efficiency",
    ),
    Source(
        "grossman-stiglitz-1980",
        "Grossman, Stiglitz",
        "1980",
        "On the impossibility of informationally efficient markets",
        "https://cir.nii.ac.jp/crid/1130000794301884928?lang=en",
        "If prices held all information nobody would pay to gather it, so markets can only be "
        "nearly efficient.",
        "Market efficiency",
    ),
    Source(
        "brock-1992",
        "Brock, Lakonishok, LeBaron",
        "1992",
        "Simple technical trading rules and the stochastic properties of stock returns",
        "https://econpapers.repec.org/RePEc:bla:jfinan:v:47:y:1992:i:5:p:1731-64",
        "Moving-average and range-break rules on the Dow 1897–1986 looked informative. Later "
        "work disputes how much survives costs and data snooping.",
        "Technical analysis",
    ),
    Source(
        "stw-1999",
        "Sullivan, Timmermann, White",
        "1999",
        "Data-snooping, technical trading rule performance, and the bootstrap",
        "https://bashtage.github.io/kevinsheppard.com/files/teaching/mfe/advanced-econometrics/"
        "Sullivan_Timmermann_White.pdf",
        "Tests a large universe of rules on 100 years of Dow data, correcting for having "
        "searched through so many.",
        "Technical analysis",
    ),
    Source(
        "park-irwin-2007",
        "Park, Irwin",
        "2007",
        "What do we know about the profitability of technical analysis?",
        "https://econpapers.repec.org/RePEc:bla:jecsur:v:21:y:2007:i:4:p:786-826",
        "Positive results are common but most studies have problems such as data snooping and "
        "choosing rules after the fact.",
        "Technical analysis",
    ),
    Source(
        "lmw-2000",
        "Lo, Mamaysky, Wang",
        "2000",
        "Foundations of technical analysis",
        "https://econpapers.repec.org/RePEc:bla:jfinan:v:55:y:2000:i:4:p:1705-1765",
        "Computer-detected chart patterns carried some extra information; that is not the "
        "same as a profit after costs.",
        "Technical analysis",
    ),
    Source(
        "marshall-candles-2006",
        "Marshall, Young, Rose",
        "2006",
        "Candlestick technical trading strategies: can they create value for investors?",
        "https://ideas.repec.org/a/eee/pacfin/v26y2014icp65-78.html",
        "The study behind later tests. Page linked is a follow-up on Taiwan, which found "
        "results depend heavily on the exit rule.",
        "Technical analysis",
    ),
    Source(
        "thai-candles-2017",
        "SAGE Open study",
        "2017",
        "Profitability of candlestick charting patterns in the Stock Exchange of Thailand",
        "https://journals.sagepub.com/doi/10.1177/2158244017736799",
        "Mean returns of most reversal patterns were not statistically different from zero.",
        "Technical analysis",
    ),
    Source(
        "batchelor-2006",
        "Batchelor, Ramyar",
        "2006",
        "Magic numbers in the Dow",
        "https://openaccess.city.ac.uk/id/eprint/16276/",
        "Tested Fibonacci and round-fraction clustering in Dow trends: a few significant "
        "ratios, no more than chance would produce.",
        "Technical analysis",
    ),
    Source(
        "menkhoff-taylor-2007",
        "Menkhoff, Taylor",
        "2007",
        "The obstinate passion of foreign exchange professionals: technical analysis",
        "https://econpapers.repec.org/RePEc:aea:jeclit:v:45:y:2007:i:4:p:936-972",
        "Survey of why FX professionals keep using technical analysis.",
        "Technical analysis",
    ),
    Source(
        "neely-2009",
        "Neely, Weller, Ulrich",
        "2009",
        "The adaptive markets hypothesis: evidence from the foreign exchange market",
        "https://ideas.repec.org/a/cup/jfinqa/v44y2009i02p467-488_09.html",
        "Profits to particular FX rules fade over time as more traders learn them.",
        "Technical analysis",
    ),
    # ---- what has held up ----
    Source(
        "jegadeesh-1993",
        "Jegadeesh, Titman",
        "1993",
        "Returns to buying winners and selling losers",
        "https://en.wikipedia.org/wiki/Momentum_investing",
        "Past 3–12 month stock winners kept beating losers over the next 3–12 months. Link is "
        "an overview page; the paper is Journal of Finance 48(1).",
        "Momentum and trend",
    ),
    Source(
        "moskowitz-2012",
        "Moskowitz, Ooi, Pedersen",
        "2012",
        "Time series momentum",
        "https://papers.ssrn.com/abstract=2089463",
        "Significant momentum in all 58 liquid futures tested across equity, currency, "
        "commodity and bond markets.",
        "Momentum and trend",
    ),
    Source(
        "hurst-2017",
        "Hurst, Ooi, Pedersen",
        "2017",
        "A century of evidence on trend-following investing",
        "https://fairmodel.econ.yale.edu/ec439/hurst.pdf",
        "Positive trend returns over more than 100 years and good results in 8 of the 10 "
        "worst 60/40 drawdowns. Written by a fund manager that runs such strategies.",
        "Momentum and trend",
    ),
    Source(
        "daniel-2016",
        "Daniel, Moskowitz",
        "2016",
        "Momentum crashes",
        "https://econpapers.repec.org/RePEc:nbr:nberwo:20439",
        "Momentum can crash in rebounds after market falls when volatility is high.",
        "Momentum and trend",
    ),
    Source(
        "brunnermeier-2008",
        "Brunnermeier, Nagel, Pedersen",
        "2008",
        "Carry trades and currency crashes",
        "https://www.nber.org/papers/w14473",
        "Carry returns are negatively skewed: slow gains and sudden crashes when funding dries up.",
        "Carry",
    ),
    Source(
        "koijen-2018",
        "Koijen, Moskowitz, Pedersen, Vrugt",
        "2018",
        "Carry",
        "https://econpapers.repec.org/RePEc:eee:jfinec:v:127:y:2018:i:2:p:197-225",
        "Carry predicts returns across asset classes and is not explained by value or momentum.",
        "Carry",
    ),
    Source(
        "lustig-2011",
        "Lustig, Roussanov, Verdelhan",
        "2011",
        "Common risk factors in currency markets",
        "https://repository.upenn.edu/fnce_papers/335",
        "Carry returns reflect exposure to a common global risk factor.",
        "Carry",
    ),
    Source(
        "gatev-2006",
        "Gatev, Goetzmann, Rouwenhorst",
        "2006",
        "Pairs trading: performance of a relative-value arbitrage rule",
        "https://econpapers.repec.org/RePEc:oup:rfinst:v:19:y:2006:i:3:p:797-827",
        "Daily US data 1962–2002: about 11% annual excess return for top pairs. Later studies "
        "find profits have fallen.",
        "Other strategies",
    ),
    Source(
        "bouman-2002",
        "Bouman, Jacobsen",
        "2002",
        "The Halloween indicator: sell in May and go away",
        "https://www.tias.edu/docs/default-source/Kennisartikelen/ssrn-id76248.pdf?sfvrsn=2",
        "November–April stock returns beat May–October in 36 of 37 countries, 1970–1998. Later "
        "work disputes how strong this is.",
        "Other strategies",
    ),
    Source(
        "lucca-2015",
        "Lucca, Moench",
        "2015",
        "The pre-FOMC announcement drift",
        "https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr512.pdf",
        "US stocks gained unusually in the day before Fed meetings; a later update found it "
        "mostly at meetings with a press conference.",
        "Other strategies",
    ),
    Source(
        "cboe-callan",
        "Callan Associates for Cboe",
        "n.d.",
        "An analysis of index option writing",
        "https://cdn.cboe.com/resources/education/research_publications/Callan_CBOE.pdf",
        "Commissioned by the exchange. Buy-write indexes showed better risk-adjusted results "
        "than stocks over 18 years, with their own crash exposure.",
        "Options",
    ),
    Source(
        "evans-lyons-2002",
        "Evans, Lyons",
        "2002",
        "Order flow and exchange rate dynamics",
        "https://www.nber.org/papers/w7317",
        "Signed dealer order flow explains much of daily exchange rate moves, unlike macro models.",
        "Order flow",
    ),
    # ---- forecasting and testing ----
    Source(
        "rossi-2013",
        "Rossi",
        "2013",
        "Exchange rate predictability",
        "https://econpapers.repec.org/RePEc:aea:jeclit:v:51:y:2013:i:4:p:1063-1119",
        "Forecasting ability depends on predictor, horizon and sample; the random walk "
        "without drift is the toughest benchmark.",
        "Forecasting",
    ),
    Source(
        "gu-kelly-xiu-2020",
        "Gu, Kelly, Xiu",
        "2020",
        "Empirical asset pricing via machine learning",
        "https://nber.org/papers/w25398",
        "Trees and neural networks led among methods predicting stock returns; momentum, "
        "liquidity and volatility were the main predictors.",
        "Forecasting",
    ),
    Source(
        "hamilton-regimes",
        "Hamilton",
        "1989",
        "Regime-switching models (overview by the author)",
        "https://econweb.ucsd.edu/~jhamilton/palgrav1.pdf",
        "Models where hidden states switch the behaviour of a time series.",
        "Forecasting",
    ),
    Source(
        "bailey-2014",
        "Bailey, Borwein, López de Prado, Zhu",
        "2014",
        "The probability of backtest overfitting",
        "https://papers.ssrn.com/abstract=2326253",
        "Great-looking backtests are easy to reach after trying only a modest number of "
        "variations.",
        "Testing",
    ),
    Source(
        "harvey-2016",
        "Harvey, Liu, Zhu",
        "2016",
        "...and the cross-section of expected returns",
        "https://econpapers.repec.org/RePEc:nbr:nberwo:20592",
        "With hundreds of tested factors, a new finding needs a t-statistic above about 3, not 2.",
        "Testing",
    ),
    Source(
        "mclean-pontiff-2016",
        "McLean, Pontiff",
        "2016",
        "Does academic research destroy stock return predictability?",
        "https://law-journals-books.vlex.com/vid/does-academic-research-destroy-855658380",
        "97 published predictors shrink out of sample and shrink more after publication. The "
        "26%/58% decline figures were seen only in secondary tables.",
        "Testing",
    ),
    Source(
        "almgren-chriss",
        "Almgren, Chriss",
        "2000",
        "Optimal execution of portfolio transactions",
        "https://arxiv.org/html/2410.04867v2",
        "Trading a large order fast costs impact, slowly costs price risk. Linked page is a "
        "recent paper summarising the model.",
        "Execution",
    ),
    Source(
        "kelly-1956",
        "Kelly (overview page)",
        "1956",
        "Kelly criterion",
        "https://www.wikipedia.org/wiki/Kelly_criterion",
        "Maximises long-run growth when the odds are known; markets do not give known odds.",
        "Risk",
    ),
    Source(
        "odean-disposition",
        "Odean",
        "1998",
        "Are investors reluctant to realize their losses?",
        "https://faculty.haas.berkeley.edu/odean/Papers%20current%20versions/"
        "Individual_Investor_Performance_Final.pdf",
        "Linked review: investors sell winners more readily than losers.",
        "Psychology",
    ),
    Source(
        "kahneman-1979",
        "Kahneman, Tversky",
        "1979",
        "Prospect theory: an analysis of decision under risk",
        "https://doi.org/10.2307/1914185",
        "Losses are felt more strongly than equal gains. Not re-opened in this research pass.",
        "Psychology",
        checked=False,
    ),
    Source(
        "mandelbrot-1963",
        "Mandelbrot; Engle (ARCH)",
        "1963 / 1982",
        "Volatility clustering",
        "https://en.wikipedia.org/wiki/Volatility_clustering",
        "Large price changes tend to be followed by large changes, of either sign.",
        "Forecasting",
    ),
    # ---- added with the Methods Atlas, November 2026 ----
    Source(
        "brown-dow-1998",
        "Brown, Goetzmann, Kumar",
        "1998",
        "The Dow Theory: William Peter Hamilton's track record reconsidered",
        "https://archive.nyu.edu/handle/2451/26858",
        "Re-tests the Wall Street Journal editor's calls of 1902–1929 with risk adjustment and "
        "finds useful timing, reversing an early 1934 study. Later on, trading frictions "
        "remove most of the benefit.",
        "Technical analysis",
    ),
    Source(
        "taylor-allen-1992",
        "Taylor, Allen (Bank of England)",
        "1989 / 1992",
        "Chart analysis and the foreign exchange market",
        "https://www.bankofengland.co.uk/-/media/boe/files/quarterly-bulletin/1989/"
        "chart-analysis-and-the-foreign-exchange-market",
        "Survey of London currency dealers: most put some weight on charts for short horizons, "
        "and less for long ones. It is old and covers one market.",
        "Who uses what",
    ),
    Source(
        "hoffmann-shefrin-2014",
        "Hoffmann, Shefrin",
        "2014",
        "Technical analysis and individual investors",
        "https://econpapers.repec.org/RePEc:eee:jeborg:v:107:y:2014:i:pb:p:487-511",
        "Clients of one Dutch online broker: about a third reported using technical analysis, "
        "and those who did tended to do worse, above all heavy options traders. One sample only.",
        "Who uses what",
    ),
    Source(
        "pinto-valuation-2019",
        "Pinto, Robinson, Stowe",
        "2019",
        "Equity valuation: a survey of professional practice",
        "https://econpapers.repec.org/RePEc:wly:revfec:v:37:y:2019:i:2:p:219-233",
        "Survey of investment professionals: market multiples and present-value models dominate. "
        "It shows what people use, not which method is accurate.",
        "Who uses what",
    ),
    Source(
        "barclayhedge-2018",
        "BarclayHedge",
        "2018",
        "Majority of hedge fund pros use AI/machine learning in investment strategies",
        "https://barclayhedge.com/research/press_releases/PR_July_18_2018-survey.html",
        "A short industry poll with only 55 replies, so treat it as a rough signal of direction.",
        "Who uses what",
    ),
    Source(
        "fang-2014",
        "Fang, Jacobsen, Qin",
        "2014",
        "Predictability of the simple technical trading rules: an out-of-sample test",
        "https://law-journals-books.vlex.com/vid/predictability-simple-technical-trading-rules-855670296",
        "Tests well-known technical rules on fresh data from 1987 to 2011 and finds no evidence "
        "that they predict stock markets over that period.",
        "Technical analysis",
    ),
    Source(
        "szakmary-2010",
        "Szakmary, Shen, Sharma",
        "2010",
        "Trend-following trading strategies in commodity futures: a re-examination",
        "https://econpapers.repec.org/RePEc:eee:jbfina:v:34:y:2010:i:2:p:409-426",
        "Moving-average and channel rules on 28 commodity markets over 48 years, positive after "
        "costs in most markets. A later study of US stocks found such profits vanished after 2007.",
        "Momentum and trend",
    ),
    Source(
        "wilder-1978",
        "Wilder",
        "1978",
        "New concepts in technical trading systems (ADX overview page)",
        "https://en.wikipedia.org/wiki/Average_directional_movement_index",
        "The book that introduced RSI, ATR, ADX and Parabolic SAR. Cited from general knowledge.",
        "Technical analysis",
        checked=False,
    ),
    Source(
        "osler-2003",
        "Osler",
        "2003",
        "Currency orders and exchange rate dynamics",
        "https://econpapers.repec.org/RePEc:bla:jfinan:v:58:y:2003:i:5:p:1791-1819",
        "Bank order data: take-profit orders cluster at round numbers and stop-loss orders "
        "cluster just beyond them, which can explain some chart behaviour.",
        "Order flow",
    ),
    Source(
        "cont-ofi-2014",
        "Cont, Kukanov, Stoikov",
        "2014",
        "The price impact of order book events",
        "https://arxiv.org/abs/1011.6402",
        "In 50 US stocks, order flow imbalance at the best prices is the main driver of very "
        "short-term price changes, and the effect is stronger when the book is thin.",
        "Order flow",
    ),
    Source(
        "steidlmayer",
        "Steidlmayer; Steidlmayer and Koy (overview page)",
        "1986",
        "Market Profile",
        "https://en.wikipedia.org/wiki/Market_profile",
        "Overview of the chart built at the Chicago Board of Trade in the 1980s: letters per "
        "half hour, point of control and a 70% value area. No reliable success rates exist.",
        "Order flow",
    ),
    Source(
        "aquilina-2022",
        "Aquilina, Budish, O'Neill",
        "2022",
        "Quantifying the high-frequency trading arms race",
        "https://www.fca.org.uk/publications/occasional-papers/"
        "occasional-paper-no-50-quantifying-high-frequency-trading-arms-race-new-methodology",
        "UK share data: speed races are about a fifth of volume, and a handful of firms take "
        "most of the wins.",
        "Order flow",
    ),
    Source(
        "carr-wu-2009",
        "Carr, Wu",
        "2009",
        "Variance risk premiums",
        "https://typeset.io/pdf/variance-risk-premiums-2r5d548tv2.pdf",
        "Stock index options price in more variance than usually follows, in good and bad markets.",
        "Options",
    ),
    Source(
        "bakshi-kapadia-2003",
        "Bakshi, Kapadia",
        "2003",
        "Delta-hedged gains and the negative market volatility risk premium",
        "https://ideas.repec.org/a/oup/rfinst/v16y2003i2p527-566.html",
        "S&P 500 option buyers who hedged away direction lost on average, and lost more when "
        "volatility was high.",
        "Options",
    ),
    Source(
        "coval-shumway-2001",
        "Coval, Shumway",
        "2001",
        "Expected option returns",
        "https://econpapers.repec.org/RePEc:bla:jfinan:v:56:y:2001:i:3:p:983-1009",
        "Zero-beta at-the-money S&P 500 straddles lost about 3% per week on average.",
        "Options",
    ),
    Source(
        "baltussen-2021",
        "Baltussen, Da, Lammers, Martens",
        "2021",
        "Hedging demand and market intraday momentum",
        "https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403",
        "Over 60 futures, 1974–2020: hedging short gamma trades with the move, and links to "
        "intraday momentum in the last half hour.",
        "Options",
    ),
    Source(
        "driessen-2009",
        "Driessen, Maenhout, Vilkov",
        "2009",
        "The price of correlation risk: evidence from equity options",
        "https://econpapers.repec.org/RePEc:bla:jfinan:v:64:y:2009:i:3:p:1377-1406",
        "Index options look expensive because they insure against rising correlation, but the "
        "premium could not be exploited with realistic trading frictions.",
        "Options",
    ),
    Source(
        "pan-poteshman-2006",
        "Pan, Poteshman",
        "2006",
        "The information in option volume for future stock prices",
        "https://econpapers.repec.org/RePEc:oup:rfinst:v:19:y:2006:i:3:p:871-908",
        "Put-call ratios from non-public data on new buyer-initiated trades predicted stock "
        "returns over the next days. The public ratio is a different number.",
        "Options",
    ),
    Source(
        "rubinstein-1994",
        "Rubinstein",
        "1994",
        "Implied binomial trees",
        "https://doi.org/10.1111/j.1540-6261.1994.tb00079.x",
        "Classic paper on the volatility smile in index options after the 1987 crash. Cited "
        "from general knowledge and from summaries, not re-opened.",
        "Options",
        checked=False,
    ),
    Source(
        "piotroski-2000",
        "Piotroski",
        "2000",
        "Value investing: the use of historical financial statement information",
        "https://econpapers.repec.org/RePEc:bla:joares:v:38:y:2000:i::p:1-41",
        "A nine-point accounting score separated stronger from weaker cheap US shares, 1976–1996, "
        "mainly in small, thinly followed firms.",
        "Fundamentals",
    ),
    Source(
        "bernard-thomas-1989",
        "Bernard, Thomas",
        "1989",
        "Post-earnings-announcement drift: delayed price response or risk premium?",
        "https://econpapers.repec.org/RePEc:bla:joares:v:27:y:1989:i::p:1-36",
        "Shares with good earnings surprises kept beating those with bad ones in most quarters "
        "from 1974 to 1985. The effect has weakened since.",
        "Fundamentals",
    ),
    Source(
        "estrella-mishkin-1996",
        "Estrella, Mishkin",
        "1996",
        "The yield curve as a predictor of US recessions",
        "https://www.newyorkfed.org/research/current_issues/ci2-7.pdf",
        "The 10-year minus 3-month spread beat other indicators for predicting recessions two "
        "to six quarters ahead.",
        "Macro",
    ),
    Source(
        "driesprong-2008",
        "Driesprong, Jacobsen, Maat",
        "2008",
        "Striking oil: another puzzle?",
        "https://econpapers.repec.org/RePEc:eee:jfinec:v:89:y:2008:i:2:p:307-327",
        "Oil price changes predicted stock returns in many countries, which the authors read as "
        "investors under-reacting. Results are in-sample.",
        "Macro",
    ),
    Source(
        "miranda-rey-2020",
        "Miranda-Agrippino, Rey",
        "2017 / 2021",
        "US monetary policy and the global financial cycle (review)",
        "https://repec.cepr.org/repec/cpr/ceprdp/DP16580.pdf",
        "US policy helps drive a global cycle in asset prices, credit and risk appetite.",
        "Macro",
    ),
    Source(
        "caldara-2022",
        "Caldara, Iacoviello",
        "2022",
        "Measuring geopolitical risk",
        "https://www.aeaweb.org/doi/10.1257/aer.20191823",
        "A news-based index: higher geopolitical risk comes with weaker investment and jobs and "
        "falling shares. The share-price effect was short-lived in earlier drafts.",
        "Macro",
    ),
    Source(
        "dxy-ice",
        "Overview of the ICE US Dollar Index",
        "n.d.",
        "U.S. Dollar Index",
        "https://en.wikipedia.org/wiki/U.S._Dollar_Index",
        "Weights: euro 57.6%, yen 13.6%, pound 11.9%, Canadian dollar 9.1%, krona 4.2%, "
        "franc 3.6%. Changed only once, when the euro began.",
        "Macro",
    ),
    Source(
        "tetlock-2007",
        "Tetlock",
        "2007",
        "Giving content to investor sentiment: the role of media in the stock market",
        "https://econpapers.repec.org/RePEc:bla:jfinan:v:62:y:2007:i:3:p:1139-1168",
        "Pessimistic Wall Street Journal text predicted falling prices that later reversed.",
        "Sentiment",
    ),
    Source(
        "baker-wurgler-2006",
        "Baker, Wurgler",
        "2006",
        "Investor sentiment and the cross-section of stock returns",
        "https://econpapers.repec.org/RePEc:bla:jfinan:v:61:y:2006:i:4:p:1645-1680",
        "When sentiment is high, small, young and hard-to-value shares later earn relatively "
        "low returns.",
        "Sentiment",
    ),
    Source(
        "cnn-fear-greed",
        "NerdWallet explainer of the CNN index",
        "n.d.",
        "What is the Fear and Greed Index?",
        "https://www.nerdwallet.com/article/investing/what-is-the-fear-and-greed-index",
        "Seven equally weighted market measures on a 0 to 100 scale. A secondary description.",
        "Sentiment",
    ),
    Source(
        "rapach-short-2016",
        "Rapach, Ringgenberg, Zhou",
        "2016",
        "Short interest and aggregate stock returns",
        "https://econpapers.repec.org/RePEc:eee:jfinec:v:121:y:2016:i:1:p:46-65",
        "Total US short interest was a strong predictor of later market returns, in and out of "
        "sample, which suggests short sellers are often well informed.",
        "Sentiment",
    ),
    Source(
        "frazzini-lamont-2008",
        "Frazzini, Lamont",
        "2008",
        "Dumb money: mutual fund flows and the cross-section of stock returns",
        "https://econpapers.repec.org/RePEc:eee:jfinec:v:88:y:2008:i:2:p:299-322",
        "Retail money moving into funds tends to precede lower returns for the favoured shares.",
        "Sentiment",
    ),
    Source(
        "cohen-insiders-2012",
        "Cohen, Malloy, Pomorski",
        "2012",
        "Decoding inside information",
        "https://econpapers.repec.org/RePEc:bla:jfinan:v:67:y:2012:i:3:p:1009-1043",
        "Unusual insider trades carried all the predictive power, about 0.8% a month in the "
        "working paper, and routine trades carried none.",
        "Sentiment",
    ),
    Source(
        "frtb-2016",
        "Basel Committee on Banking Supervision",
        "2016",
        "Minimum capital requirements for market risk",
        "https://www.bis.org/bcbs/publ/d352.htm",
        "Moves bank market-risk rules from value-at-risk to expected shortfall under stress. "
        "Later superseded by a January 2019 version.",
        "Risk",
    ),
    Source(
        "artzner-1999",
        "Artzner, Delbaen, Eber, Heath",
        "1999",
        "Coherent measures of risk",
        "https://econpapers.repec.org/RePEc:bla:mathfi:v:9:y:1999:i:3:p:203-228",
        "Sets out what a good risk measure should do, and shows that quantile measures such as "
        "value-at-risk can fail to reward diversification.",
        "Risk",
    ),
    Source(
        "perignon-2010",
        "Pérignon, Smith",
        "2010",
        "The level and quality of value-at-risk disclosure by commercial banks",
        "https://econpapers.repec.org/RePEc:eee:jbfina:v:34:y:2010:i:2:p:362-377",
        "Historical simulation is by far the most popular bank method, and it contained very "
        "little information about future volatility.",
        "Risk",
    ),
    Source(
        "demiguel-2009",
        "DeMiguel, Garlappi, Uppal",
        "2009",
        "Optimal versus naive diversification",
        "https://econpapers.repec.org/RePEc:oup:rfinst:v:22:y:2009:i:5:p:1915-1953",
        "Across 14 models and seven datasets, none reliably beat simply holding equal weights.",
        "Risk",
    ),
    Source(
        "frazzini-pedersen-2014",
        "Frazzini, Pedersen",
        "2014",
        "Betting against beta",
        "https://econpapers.repec.org/RePEc:eee:jfinec:v:111:y:2014:i:1:p:1-25",
        "High-beta assets earned less than theory predicts across many markets. A later paper "
        "(Novy-Marx and Velikov, 2022) disputes how the strategy is built.",
        "Risk",
    ),
    Source(
        "kaminski-lo-2014",
        "Kaminski, Lo",
        "2014",
        "When do stop-loss rules stop losses?",
        "https://ideas.repec.org/a/eee/finmar/v18y2014icp234-254.html",
        "In a random market stops only lower return. With momentum they can add return and cut "
        "volatility.",
        "Risk",
    ),
    Source(
        "perold-1988",
        "Perold",
        "1988",
        "The implementation shortfall: paper versus reality",
        "https://www.proquest.com/docview/195579087",
        "The paper that named this cost. Only the catalogue record was seen.",
        "Execution",
        checked=False,
    ),
    Source(
        "hansen-lunde-2005",
        "Hansen, Lunde",
        "2005",
        "A forecast comparison of volatility models: does anything beat a GARCH(1,1)?",
        "https://econpapers.repec.org/RePEc:jae:japmet:v:20:y:2005:i:7:p:873-889",
        "330 models: none clearly beat GARCH(1,1) on currency data, but on IBM shares models "
        "that treat falls differently did better.",
        "Forecasting",
    ),
)

SOURCE_KEYS: Final[frozenset[str]] = frozenset(source.key for source in SOURCES)
