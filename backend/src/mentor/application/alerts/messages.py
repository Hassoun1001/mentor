"""Every Telegram message the system sends, in plain words.

The owner reads these on a phone and is not a quant. A message full of
"H1 champion", "P(up)", "Brier", "drift" and commit hashes tells them
nothing — so every message here has the same three parts, readable at a
glance:

1. a headline saying what happened;
2. a line or two of why, in everyday words;
3. 👉 what, if anything, the owner should do.

All wording lives in this module so it stays consistent, and is tested in
one place. The technical detail is never lost: it stays in the logs, the
JSON report and the Loop page.
"""

from __future__ import annotations

from collections.abc import Sequence

from mentor.domain.strategy_lab.live import LiveAction

LANE_NAMES = {"h1": "24-hour forecast", "d1": "5-day forecast"}

NOTHING_TO_DO = "Nothing — this is the system looking after itself."


def lane_name(lane: str) -> str:
    return LANE_NAMES.get(lane, f"{lane} forecast")


def compose(headline: str, *body: str, action: str) -> str:
    """Headline, a short explanation, then the one line that says what to do."""
    lines = [headline, *[b for b in body if b], "", f"👉 {action}"]
    return "\n".join(lines)


def _pair(symbol: str) -> str:
    s = symbol.upper().replace("/", "")
    return f"{s[:3]}/{s[3:]}" if len(s) == 6 else s


def horizon_words(bars: int, timeframe: str) -> str:
    """How far ahead a forecast looks, as a person would say it."""
    if timeframe == "1d":
        return f"{bars} trading day{'s' if bars != 1 else ''}"
    if timeframe == "1h":
        return f"{bars} hour{'s' if bars != 1 else ''}"
    if timeframe == "5m":
        return f"{bars * 5} minutes"
    return f"{bars} bars"


def _duration(minutes: int) -> str:
    if minutes < 90:
        return f"{minutes} minutes"
    return f"{round(minutes / 60)} hours"


# ---- the trading loop --------------------------------------------------------


def feed_problem(*, failures: int, every_minutes: int) -> str:
    return compose(
        "⚠️ Price updates have stopped",
        f"Mentor couldn't get new EUR/USD prices for about "
        f"{_duration(failures * every_minutes)} ({failures} attempts in a row). "
        "Forecasts pause until prices come back.",
        action=(
            "Nothing yet — it keeps retrying on its own. If this message comes again "
            "tomorrow, ask Claude to take a look."
        ),
    )


def strong_forecast(*, symbol: str, p_up: float, horizon_bars: int, timeframe: str) -> str:
    up = p_up >= 0.5
    chance = p_up if up else 1.0 - p_up
    pair = _pair(symbol)
    return compose(
        f"{'📈' if up else '📉'} Forecast: {pair} more likely to go {'UP' if up else 'DOWN'}",
        f"The model gives about a {chance * 100:.0f}% chance that {pair} will be "
        f"{'higher' if up else 'lower'} {horizon_words(horizon_bars, timeframe)} from now.",
        "That's a leaning, not a certainty, and the model hasn't yet proven it beats "
        "trading costs.",
        action=(
            "Optional: open the Trade plan page for a full plan (entry, stop, size). "
            "This is not advice — any trade is your decision."
        ),
    )


def rough_patch(*, lane: str) -> str:
    return compose(
        "🔄 The forecaster is having a rough patch",
        f"Its recent {lane_name(lane)} predictions have been less accurate than usual, so "
        "it is retraining itself now (about an hour). It only switches to a new version if "
        "that version proves better on data it has never seen.",
        action=NOTHING_TO_DO,
    )


def new_model(*, lane: str, accuracy: float, breakeven: float) -> str:
    proof = (
        f"right {accuracy * 100:.0f}% of the time, where {breakeven * 100:.1f}% is needed "
        "to cover trading costs"
        if accuracy > 0
        else "it passed every check"
    )
    return compose(
        "🏆 A better forecaster took over",
        f"After retraining, a new version of the {lane_name(lane)} beat the old one on data "
        f"it had never seen: {proof}.",
        "It makes the forecasts from now on. If it stops performing, it is replaced "
        "automatically.",
        action=NOTHING_TO_DO,
    )


def model_retired(*, lane: str) -> str:
    return compose(
        "📉 A forecaster was retired",
        f"The {lane_name(lane)} model stopped passing its checks several times in a row, so "
        "it was removed. A simple built-in rule makes the forecasts until a new model earns "
        "the job.",
        action="Nothing — this is the safety net working as designed.",
    )


# ---- the strategy lab ---------------------------------------------------------


def ideas_tested(results: Sequence[tuple[str, bool]]) -> str:
    """``results``: (idea title, passed) for each idea tested this run."""
    n = len(results)
    passed = [title for title, ok in results if ok]
    ideas = f"{n} new trading idea{'s were' if n != 1 else ' was'}"
    if passed:
        return compose(
            "🧪 A trading idea passed its test!",
            f"{ideas} tested on years of price history. Passed: {', '.join(passed)}.",
            "It now trades with pretend money only, to prove itself on the live market. "
            "Mentor never places real trades.",
            action="Nothing — you'll get a message if it proves itself live.",
        )
    return compose(
        "🧪 New trading ideas tested — none good enough",
        f"{ideas} tested on years of price history. None made enough money after trading "
        "costs to pass.",
        "That's normal: most trading ideas fail, and the test is strict on purpose.",
        action=NOTHING_TO_DO,
    )


def paper_status(*, title: str, action: LiveAction) -> str | None:
    """A change in an idea's pretend-money trading status, or None if nothing changed."""
    if action is LiveAction.PROMOTE:
        return compose(
            "⭐ A trading idea proved itself",
            f"'{title}' has made money on pretend trades against the live market — enough "
            "to rule out luck. It is now marked as recommended on the Strategy Lab page.",
            "Mentor never trades for you.",
            action="Optional: look at the Strategy Lab page. Any real trading is your decision.",
        )
    if action is LiveAction.DEMOTE:
        return compose(
            "📉 A trading idea slipped",
            f"'{title}' was doing well on pretend trades, but its recent results dropped "
            "below the bar, so it is no longer recommended. It keeps paper trading and can "
            "earn its place back.",
            action=NOTHING_TO_DO,
        )
    if action is LiveAction.RETIRE:
        return compose(
            "🛑 A trading idea was dropped",
            f"'{title}' kept losing on pretend trades, so it was stopped for good.",
            action=NOTHING_TO_DO,
        )
    return None


# ---- the weekly report ----------------------------------------------------------


def record_line(*, n: int, win_rate: float | None, breakeven: float) -> str | None:
    if win_rate is None or n == 0:
        return None
    return (
        f"• Right {win_rate * 100:.1f}% of the time across {n} separate forecasts "
        f"(it needs {breakeven * 100:.1f}% to beat trading costs)."
    )


def verdict_line(*, n: int, significant: bool, win_rate: float | None, breakeven: float) -> str:
    if n == 0 or win_rate is None:
        return "• No checked forecasts yet."
    if significant and win_rate > breakeven:
        return "• Proven: it reliably beats trading costs."
    if significant:
        return "• Clearly losing after trading costs."
    return "• Not proven yet: too few results to rule out luck."


def accuracy_trend(this_week: float | None, last_week: float | None) -> str | None:
    """Brier is an error score — lower is better — so say it the other way round."""
    if this_week is None:
        return None
    if last_week is None:
        return None
    diff = this_week - last_week
    if abs(diff) < 0.005:
        trend = "about the same as last week"
    elif diff < 0:
        trend = "better than last week"
    else:
        trend = "worse than last week"
    return f"• Accuracy this week: {trend}."


def in_charge_line(*, has_model: bool, since: str | None) -> str:
    if not has_model:
        return "• In charge: a simple built-in rule (no trained model has earned the job yet)."
    when = f" since {_short_date(since)}" if since else ""
    return f"• In charge: a trained model{when}."


def week_changes_line(*, retrains: int, promotions: int, demotions: int) -> str:
    if promotions:
        change = "a new model took over"
    elif demotions:
        change = "the model was retired"
    else:
        change = "no change of model"
    if retrains == 0:
        return f"• This week: no retraining, {change}."
    return f"• This week: retrained {retrains} time{'s' if retrains != 1 else ''}, {change}."


def _short_date(iso: str) -> str:
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    try:
        _year, m, d = (int(p) for p in iso[:10].split("-"))
    except ValueError:
        return iso[:10]
    return f"{d} {months[m - 1]}" if 1 <= m <= 12 else iso[:10]


# Issue codes the report emits, translated for a phone. Matched by prefix,
# with the lane (h1/d1) filled in where the code carries one.
_ISSUE_WORDS: tuple[tuple[str, str], ...] = (
    ("digest.feed", "Prices aren't updating."),
    ("digest.resolution", "Some forecasts haven't been checked against what happened yet."),
    ("digest.retrain", "The forecaster hasn't retrained on schedule."),
    ("digest.alerting", "Phone alerts aren't set up."),
    ("deploy.rollback_failed", "An update failed and the system may be down."),
    ("deploy.rolled_back", "An automatic update failed its checks and was undone."),
    ("deploy.refused", "An automatic update was blocked by the safety rules."),
    ("strategies.waiting", "Some trading ideas are still waiting to be tested."),
    (
        "strategies.definition_changed",
        "A trading idea was edited after testing (not allowed), so it's being ignored.",
    ),
    ("strategies.unavailable", "The trading-ideas lab couldn't be read."),
    ("job.", "A background job failed recently: {rest}."),
    ("log.error", "An error was logged in the background."),
    ("log.critical", "A serious error was logged in the background."),
    ("log.exception", "An error was logged in the background."),
    ("log.warning", "A background warning keeps repeating."),
)

_LANE_ISSUE_WORDS: tuple[tuple[str, str], ...] = (
    ("below_breakeven", "The {lane} is clearly losing after trading costs."),
    ("calibration_week", "The {lane} was less accurate than guessing this week."),
    ("champion_failing", "The {lane}'s model failed its latest check (it's retired after 3)."),
    ("retrain_stalled", "The {lane} has stopped retraining."),
)


def plain_issue(code: str, detail: str) -> str:
    """One report issue, in words a non-specialist can act on."""
    for prefix, words in _ISSUE_WORDS:
        if code.startswith(prefix):
            return words.format(rest=code[len(prefix) :].replace("_", " "))
    lane, _, rest = code.partition(".")
    if lane in LANE_NAMES:
        for suffix, words in _LANE_ISSUE_WORDS:
            if rest == suffix:
                return words.format(lane=lane_name(lane))
    if code.startswith("strategy.") and code.endswith(".paper_stalled"):
        return "Pretend trading for one of the trading ideas has stalled."
    if code.startswith("strategy.") and code.endswith((".demoted", ".retired")):
        return "A trading idea lost its place after poor pretend-trading results."
    return detail


def overall_line(status: str, n_issues: int) -> str:
    if status == "fail":
        return "❌ Something is broken."
    if status == "warn":
        return f"⚠️ {n_issues} thing{'s' if n_issues != 1 else ''} worth a look (below)."
    return "✅ All good — nothing needs you this week."


def weekly_action(status: str) -> str:
    if status == "fail":
        return "Please ask Claude to take a look soon."
    if status == "warn":
        return (
            "Nothing urgent — the daily maintenance agent works on these automatically. "
            "If the same thing shows up two weeks running, ask Claude."
        )
    return "Nothing."


def lab_line(counts: dict[str, object]) -> str:
    def n(key: str) -> int:
        v = counts.get(key)
        return v if isinstance(v, int) else 0

    tested, paper, recommended = n("evaluated"), n("paper"), n("recommended")
    parts = [f"{tested} idea{'s' if tested != 1 else ''} tested so far"]
    if recommended:
        parts.append(f"{recommended} proven and recommended")
    if paper:
        parts.append(f"{paper} trading with pretend money")
    if not recommended and not paper:
        parts.append("none good enough yet")
    return "🧪 Trading ideas: " + ", ".join(parts) + "."
