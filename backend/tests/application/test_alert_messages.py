"""Every Telegram message must be readable by someone who isn't a quant.

Each one says what happened, why, and — on its last line — what the owner
should do. None may leak internal vocabulary: model names, "champion",
"P(up)", "Brier", "drift", lane codes.
"""

from __future__ import annotations

import pytest

from mentor.application.alerts import messages as msg
from mentor.domain.strategy_lab.live import LiveAction

_JARGON = ("champion", "P(up)", "Brier", "drift", "H1", "D1", "bars", "auto_eurusd", "regime")


def _all_messages() -> list[str]:
    paper = [
        m
        for a in (LiveAction.PROMOTE, LiveAction.DEMOTE, LiveAction.RETIRE)
        if (m := msg.paper_status(title="Buy the dip in a trend", action=a)) is not None
    ]
    return [
        msg.feed_problem(failures=3, every_minutes=60),
        msg.strong_forecast(symbol="EURUSD", p_up=0.68, horizon_bars=24, timeframe="1h"),
        msg.strong_forecast(symbol="EURUSD", p_up=0.31, horizon_bars=5, timeframe="1d"),
        msg.rough_patch(lane="h1"),
        msg.new_model(lane="h1", accuracy=0.583, breakeven=0.5178),
        msg.new_model(lane="d1", accuracy=0.0, breakeven=0.507),
        msg.model_retired(lane="h1"),
        msg.ideas_tested([("Channel breakout", False), ("Momentum", False)]),
        msg.ideas_tested([("Buy the dip in a trend", True)]),
        *paper,
    ]


@pytest.mark.parametrize("text", _all_messages())
def test_every_message_ends_by_saying_what_to_do(text: str) -> None:
    *_, last = text.splitlines()
    assert last.startswith("👉 ")
    assert len(last) > 4


@pytest.mark.parametrize("text", _all_messages())
def test_no_message_leaks_internal_vocabulary(text: str) -> None:
    for word in _JARGON:
        assert word not in text, f"{word!r} in: {text}"


def test_a_downward_forecast_says_down_and_gives_the_chance_of_down() -> None:
    text = msg.strong_forecast(symbol="EURUSD", p_up=0.31, horizon_bars=5, timeframe="1d")
    assert text.startswith("📉 Forecast: EUR/USD more likely to go DOWN")
    assert "69% chance" in text  # 1 - 0.31, not the up-probability
    assert "5 trading days from now" in text


def test_an_upward_forecast_reads_naturally() -> None:
    text = msg.strong_forecast(symbol="EURUSD", p_up=0.68, horizon_bars=24, timeframe="1h")
    assert text.startswith("📈 Forecast: EUR/USD more likely to go UP")
    assert "68% chance that EUR/USD will be higher 24 hours from now" in text
    assert "not advice" in text


def test_a_new_model_explains_its_proof_in_percentages() -> None:
    text = msg.new_model(lane="h1", accuracy=0.583, breakeven=0.5178)
    assert "24-hour forecast" in text
    assert "right 58% of the time, where 51.8% is needed" in text


def test_a_new_model_without_a_recorded_accuracy_does_not_invent_one() -> None:
    text = msg.new_model(lane="d1", accuracy=0.0, breakeven=0.507)
    assert "0%" not in text
    assert "passed every check" in text


def test_ideas_that_fail_are_reported_as_normal() -> None:
    text = msg.ideas_tested([("Channel breakout", False), ("Momentum", False)])
    assert "2 new trading ideas were tested" in text
    assert "most trading ideas fail" in text


def test_an_idea_that_passes_names_itself_and_says_it_is_pretend_money() -> None:
    text = msg.ideas_tested([("Buy the dip in a trend", True)])
    assert "Passed: Buy the dip in a trend." in text
    assert "pretend money" in text
    assert "never places real trades" in text


def test_no_paper_message_when_nothing_changed() -> None:
    assert msg.paper_status(title="x", action=LiveAction.NONE) is None


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("digest.feed", "Prices aren't updating."),
        ("digest.resolution", "Some forecasts haven't been checked against what happened yet."),
        ("h1.champion_failing", "The 24-hour forecast's model failed its latest check"),
        ("d1.retrain_stalled", "The 5-day forecast has stopped retraining."),
        ("deploy.refused_protected", "An automatic update was blocked by the safety rules."),
        ("log.warning.gdelt.rate_limited", "A background warning keeps repeating."),
        ("job.news_tone", "A background job failed recently: news tone."),
        ("strategy.trend_pullback_d1.paper_stalled", "Pretend trading for one of the trading"),
    ],
)
def test_issue_codes_become_sentences(code: str, expected: str) -> None:
    assert msg.plain_issue(code, "raw technical detail").startswith(expected)


def test_an_unknown_issue_falls_back_to_its_detail() -> None:
    assert msg.plain_issue("something.new", "The raw detail.") == "The raw detail."


@pytest.mark.parametrize(
    ("this_week", "last_week", "expected"),
    [
        (0.217, 0.241, "better than last week"),  # lower error = better
        (0.260, 0.240, "worse than last week"),
        (0.2401, 0.2399, "about the same as last week"),
    ],
)
def test_accuracy_trend_reads_error_scores_the_right_way_round(
    this_week: float, last_week: float, expected: str
) -> None:
    line = msg.accuracy_trend(this_week, last_week)
    assert line is not None and expected in line


def test_no_trend_without_last_week() -> None:
    assert msg.accuracy_trend(0.22, None) is None


def test_long_outages_are_described_in_hours() -> None:
    assert "about 3 hours" in msg.feed_problem(failures=3, every_minutes=60)
    assert "about 30 minutes" in msg.feed_problem(failures=3, every_minutes=10)
