"""Plain-English glossary for the book."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class GlossaryTerm:
    term: str
    definition: str


def _terms(*pairs: tuple[str, str]) -> tuple[GlossaryTerm, ...]:
    return tuple(
        GlossaryTerm(term, text) for term, text in sorted(pairs, key=lambda p: p[0].lower())
    )


GLOSSARY: Final[tuple[GlossaryTerm, ...]] = _terms(
    ("Ask", "The price at which you can buy right now."),
    (
        "ATR",
        "Average True Range: the average size of recent candles. A way to measure how much a market is moving.",
    ),
    ("Backtest", "Testing a set of rules on past prices to see what would have happened."),
    ("Bearish", "Expecting the price to fall."),
    ("Bid", "The price at which you can sell right now."),
    ("Breakout", "Price moving outside a level or range it was stuck inside."),
    ("Broker", "The company that gives you access to a market and takes your orders."),
    ("Bullish", "Expecting the price to rise."),
    ("Candlestick", "A bar on a chart showing the open, high, low and close of one period."),
    (
        "Carry",
        "Money earned or paid just for holding a position over time, such as an interest difference.",
    ),
    (
        "CFD",
        "Contract for difference: a contract with a broker that pays you the price change, without owning the asset.",
    ),
    ("Commission", "A fee your broker charges per trade."),
    ("Correlation", "How closely two markets move together, from -1 (opposite) to +1 (same)."),
    ("Drawdown", "How far an account has fallen from its highest point, usually shown in percent."),
    ("Edge", "A real, repeatable advantage that still pays after all costs."),
    ("EMA", "Exponential moving average: an average that gives more weight to recent prices."),
    (
        "ETF",
        "Exchange-traded fund: a fund that trades like a share and usually tracks a basket of assets.",
    ),
    ("Expectancy", "The average amount you make or lose per trade over many trades."),
    ("Fibonacci levels", "Lines drawn at ratios such as 38.2%, 50% and 61.8% of a price move."),
    (
        "Futures",
        "An exchange-traded contract to buy or sell something at a set price on a future date.",
    ),
    ("Gap", "A jump in price between one candle's close and the next candle's open."),
    ("Hedge", "A position taken to reduce the risk of another position."),
    ("Implied volatility", "How much movement the prices of options suggest the market expects."),
    ("Instrument", "Anything you can trade: a pair, a share, a future, a coin."),
    ("Leverage", "Using borrowed money so a small deposit controls a much larger position."),
    ("Limit order", "An order to buy or sell only at your price or better."),
    ("Liquidity", "How easily you can trade without moving the price."),
    ("Long", "A position that makes money if the price rises."),
    (
        "Lot",
        "A standard trade size. In forex, one standard lot is 100,000 units of the base currency.",
    ),
    ("MACD", "A momentum indicator built from the difference between two moving averages."),
    ("Margin", "The deposit your broker holds while you have a leveraged position open."),
    (
        "Margin call",
        "A warning, or forced closing of positions, when your account no longer covers the margin needed.",
    ),
    ("Market maker", "A firm that quotes both buy and sell prices and earns the gap between them."),
    ("Market order", "An order to trade right now at the best available price."),
    ("Mean reversion", "The idea that a price that moved far from its average tends to come back."),
    (
        "Momentum",
        "The tendency of something that has been rising to keep rising, or falling to keep falling.",
    ),
    ("Moving average", "The average price over a set number of recent candles, drawn as a line."),
    (
        "Option",
        "A contract giving the right, not the duty, to buy or sell at a set price by a set date.",
    ),
    ("Order book", "The live list of buy and sell orders waiting at each price."),
    ("Overfitting", "Tuning rules so closely to past data that they stop working on new data."),
    ("Pip", "A small unit of price in forex. For most pairs it is 0.0001."),
    ("Position size", "How much you buy or sell in a trade."),
    (
        "Prop firm",
        "A company that lets traders use its capital if they pass a test, usually for a fee.",
    ),
    ("Pullback", "A short move against the main trend."),
    ("R", "The amount you risk on a trade. A trade that makes twice your risk made 2R."),
    ("Random walk", "A price path where each move is as if decided by a coin flip."),
    ("Range", "A period when price moves sideways between a high and a low."),
    ("Regime", "The current character of a market, such as trending and calm or choppy and wild."),
    ("Resistance", "A price area where rising prices have often stalled before."),
    ("Retail trader", "A person trading their own money, not working for a financial firm."),
    ("Risk of ruin", "The chance of losing so much that you cannot keep trading."),
    ("RSI", "Relative Strength Index: a 0–100 measure comparing recent gains with recent losses."),
    ("Scalping", "Very short-term trading aiming for many small gains."),
    ("Sharpe ratio", "Return divided by how much the return swings. Higher means smoother."),
    ("Short", "A position that makes money if the price falls."),
    ("Slippage", "The difference between the price you expected and the price you actually got."),
    ("Spread", "The gap between the bid and the ask. It is a cost of trading."),
    ("Stop-loss", "An order that closes your trade at a set price to limit the loss."),
    ("Support", "A price area where falling prices have often stopped before."),
    ("Swap", "An overnight fee or payment for holding a leveraged position."),
    ("Take-profit", "An order that closes your trade at a set price to bank a gain."),
    ("Tick", "The smallest price step a market can move."),
    ("Timeframe", "How much time one candle represents, such as 1 hour or 1 day."),
    ("Trend", "The general direction of price over a period."),
    ("TWAP", "Time-weighted average price: splitting an order evenly over time."),
    ("Volatility", "How much a price moves around."),
    ("Volume", "How much was traded in a period."),
    (
        "VWAP",
        "Volume-weighted average price: the average price paid, weighting busier moments more.",
    ),
    ("Walk-forward test", "Repeatedly tuning on one period and testing on the next unseen period."),
    ("Yield", "The return a bond pays, shown as a yearly percentage of its price."),
)
