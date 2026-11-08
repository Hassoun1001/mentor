"""Stage 9 — Psychology and journaling."""

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

_BIASES = Lesson(
    slug="mind/biases-that-cost-money",
    title="Biases that cost money",
    summary="The predictable mental errors that show up in almost every trading account.",
    est_minutes=7,
    key_concepts=("loss aversion", "disposition effect", "overconfidence", "hindsight bias"),
    goal="Recognise the most common mental errors so you can design rules against them.",
    body_md="""
Your brain was not built for trading. Five patterns come up again and again.

- **Loss aversion:** losses feel stronger than equal gains. Research by Kahneman and Tversky suggests losses hurt about twice as much as gains feel good.
- **Disposition effect:** selling winners too soon and holding losers too long, because realising a loss hurts.
- **Overconfidence:** believing you are better than you are, especially after a win streak.
- **Confirmation bias:** noticing only the information that supports your view.
- **Recency and hindsight bias:** giving too much weight to what just happened, and believing you "knew it all along".

### What works against them

You cannot think your way out of these while the trade is running. **You design your way out in advance**: rules, checklists, stop orders placed before entering, and a journal that records what you actually did.
""".strip(),
    charts=(
        Chart(
            title="Selling winners more readily than losers",
            caption="A finding from Odean's study of retail accounts: investors were about 1.5 times more likely to sell a winning position than a losing one. A value of 1.0 would mean no difference.",
            data_kind="published",
            kind="bars",
            y_format="plain",
            y_label="Likelihood of selling, relative to a losing position",
            source_note="Odean, as summarised in his own later writing.",
            bars=(
                Bar("Winning position", 1.5, "accentSoft"),
                Bar("Losing position", 1.0, "danger"),
            ),
        ),
    ),
    steps=(
        "Read the list of biases, and pick the one you recognise most in yourself.",
        "Write a rule that blocks it.",
        "Put that rule on your pre-trade checklist.",
        "Check your journal monthly for signs of it.",
    ),
    example_md="""
A trader notices they cut winners quickly. Their last 20 winners averaged 0.8R but their losers averaged 1.1R.

**Rule:** "Once I enter, I cannot exit a winner until my target or trailing stop is hit, unless my plan's time stop triggers."

Two months later, their winners average 1.6R. It worked not because they became a better predictor, but because the rule protected them from themselves.
""".strip(),
    mistakes=(
        "Thinking that knowing about a bias makes you immune.",
        "Using willpower instead of rules.",
        "Fixing a bias you do not actually have.",
    ),
    evidence=Evidence(
        Verdict.SUPPORTED,
        """
Behavioural finance has strong evidence for these patterns. Barber and Odean's work documents overtrading and its cost, and Odean found investors are more likely to sell winners than losers. Kahneman and Tversky's prospect theory underlies this work (we cite the original paper from general knowledge; it was not re-opened for this book).

Whether a given trader can fully overcome these with rules is less clear, but the rules at least make the bias visible.
""".strip(),
    ),
    try_it="Look at your last 20 closed trades. Compare your average winning hold time with your average losing hold time.",
    quiz=(
        Q(
            "What is the disposition effect?",
            (
                "Selling winners too soon, holding losers too long",
                "Buying when others sell",
                "A fee",
            ),
            0,
            "Realising a loss hurts, so people avoid it.",
        ),
        Q(
            "What is the best defence against biases during a trade?",
            ("Rules made in advance", "Trying harder", "Watching the screen more closely"),
            0,
            "Design the decision ahead of time.",
        ),
    ),
    takeaways=("Biases are predictable.", "Rules beat willpower.", "Your journal shows the truth."),
    sources=("odean-disposition", "barber-odean-2000", "kahneman-1979"),
)

_JOURNAL = Lesson(
    slug="psychology/journaling-beats-memory",
    title="Journaling beats memory",
    summary="Memory keeps the wins and rewrites the losses. The journal does not.",
    est_minutes=6,
    key_concepts=("journal", "review", "self-report bias"),
    figures=(Figure("journal-vs-memory", "A journal keeps what memory rewrites."),),
    goal="Keep a journal that captures the truth about your trading.",
    body_md="""
Without a journal, you remember the wins and reframe the losses. "I would have been right if not for that Fed announcement." With a journal, you cannot. The row is what it is.

The key is writing the entry **before** the trade. That is the reason the pre-trade checklist exists. After 100 trades you can filter your journal for "FOMO" (fear of missing out) and watch your average R-multiple collapse. No signal can teach you that.

### What to record

Before: setup, reason, entry, stop, target, planned R, your mood, and whether it passed your checklist.

After: fill price, result in R, what went right or wrong, and whether you followed the plan.

Keep it short. A journal you do not fill in has no value.
""".strip(),
    charts=(
        Chart(
            title="Where the money leaks in one journal",
            caption="Illustrative journal totals in R over 100 trades, showing how filtering by a tag makes a costly habit obvious.",
            data_kind="illustrative",
            kind="bars",
            y_format="r",
            y_label="Total result in R",
            bars=(
                Bar("Planned setups", 22, "accentSoft"),
                Bar("Moved stop", -9, "danger"),
                Bar("FOMO entries", -12, "danger"),
                Bar("Traded the news", -5, "danger"),
            ),
        ),
    ),
    steps=(
        "Make a trade journal with entry, stop, target, reason and result.",
        "Write the entry before taking the trade.",
        "Tag each trade with what went right or wrong.",
        "Review weekly.",
    ),
    example_md="""
A trader's journal over 100 trades shows: planned setups earned **+22R**, trades tagged "moved stop" cost **−9R**, and FOMO entries cost **−12R**.

The strategy was working. The trader was not. Removing the two bad habits would have nearly doubled the result.
""".strip(),
    mistakes=(
        "Filling in the journal days later.",
        "Leaving out the worst trades.",
        "Writing long entries that you stop doing after a week.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Research on overtrading and the disposition effect shows how biased individual trading is, and a journal is a practical response. We know of no strong controlled study proving that keeping a journal raises returns. Its value here is logical: you cannot fix what you cannot measure.
""".strip(),
    ),
    try_it="Add your next 10 trades to a journal, writing the entry before each trade. Tag one thing that went well and one that didn't after each.",
    quiz=(
        Q(
            "When should you write the journal entry?",
            ("Before the trade", "Weeks later", "Only for losing trades"),
            0,
            "Before the trade, so you cannot rewrite the reason.",
        ),
        Q(
            "Why tag trades?",
            ("So you can count habits", "To make it longer", "Regulators require it"),
            0,
            "Tags make patterns countable.",
        ),
    ),
    takeaways=(
        "A journal keeps the truth.",
        "Write it before the trade.",
        "Tag habits so you can count them.",
    ),
    sources=("barber-odean-2000",),
)

_TILT = Lesson(
    slug="psychology/tilt",
    title="Tilt and how to break it",
    summary="The emotional state after a loss, and the rules that stop it.",
    est_minutes=6,
    key_concepts=("tilt", "revenge trading", "daily loss limit", "circuit breaker"),
    figures=(Figure("tilt-spiral", "A loss, a bigger trade, a bigger loss."),),
    goal="Have rules ready that stop a bad moment from becoming a bad month.",
    body_md="""
**Tilt** is what poker players call the emotional state that follows a big loss. You take more risk, on worse setups, faster than usual. Everyone tilts. Pretending you do not is part of the problem.

### Rules that work

- **Daily loss limit:** hit it and stop for the day.
- **Cooling off:** after any trade of −2R or worse, step away. Walk.
- **No revenge trades:** no new entries for an hour after a stop-out. The setup that was perfect is suddenly less perfect, and that is information.
- **Reduce size** after a run of losses until you feel steady.

The guardrail engine in this app implements the daily loss limit. The rest is up to you, and your journal will show you when you break the rules.
""".strip(),
    charts=(
        Chart(
            title="A session spiralling into tilt",
            caption="Illustrative day. After two losses the trader doubles size twice, and a normal losing day becomes a large one.",
            data_kind="illustrative",
            kind="lines",
            y_format="r",
            y_label="Day's total in R",
            x_label="Trades",
            x_labels=("1", "2", "3", "4", "5"),
            series=(
                Series("With rules", (-1, -2, -2, -2, -2), "accentSoft"),
                Series("On tilt", (-1, -2, -4, -8, -9), "danger"),
            ),
        ),
    ),
    steps=(
        "Write your daily loss limit.",
        "Write what you will physically do after a large loss.",
        "Close your platform when a limit hits.",
        "Note the time and cause in your journal.",
    ),
    example_md="""
A trader risks 1% per trade. After two losses (−2%), they feel the urge to "win it back" and double up.

Their rule says **stop at −2%**. They close the platform and go for a walk.

The next trade might have won. It does not matter. Without the rule, a bad day can turn into a bad month.
""".strip(),
    mistakes=(
        "Believing you do not tilt.",
        "Raising size to recover a loss.",
        "Treating a limit as advice.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
Direct studies of tilt in markets are limited, although research on loss aversion and overtrading supports the broad idea. Daily loss limits are standard in professional and prop-firm settings, mainly because they prevent large damage.
""".strip(),
    ),
    try_it="Write your physical plan for after a big loss: where you will go, what you will do, and for how long you will stop.",
    quiz=(
        Q(
            "What is revenge trading?",
            (
                "Trading to win back a recent loss",
                "A strategy from a textbook",
                "Selling at the market top",
            ),
            0,
            "It often increases risk just when judgement is worst.",
        ),
        Q(
            "You hit your daily loss limit. What should you do?",
            ("Stop for the day", "Trade smaller", "Add a new setup"),
            0,
            "The rule removes the choice.",
        ),
    ),
    takeaways=("Everyone tilts.", "Rules work better than willpower.", "Stop when a limit hits."),
)

_REVIEW = Lesson(
    slug="psychology/weekend-review",
    title="The cost of skipped reviews",
    summary="Thirty minutes a week is where most of the learning happens.",
    est_minutes=5,
    key_concepts=("weekly review", "mistake tags", "pattern", "improvement"),
    figures=(Figure("review-tags", "Tags show patterns before P&L does."),),
    goal="Run a short weekly review that actually finds your patterns.",
    body_md="""
A weekly review takes thirty minutes. Open the journal, sort by R, and read the worst five trades. Tag what went wrong. Read the best five. Tag what went right.

Patterns appear in tags before they appear in profit and loss. "Moved stop" showing up six times this month is a story. "FOMO entry" appearing every Monday after the open is a story. Without tags, those stories never get told.

This app can show you those patterns automatically. If you do it by hand, it still takes only thirty minutes a week.
""".strip(),
    charts=(
        Chart(
            title="Mistakes counted over a month",
            caption="Illustrative tag counts. The largest bar is the habit worth fixing first, even if each case seemed small.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Count this month",
            bars=(
                Bar("Moved stop", 6, "danger"),
                Bar("FOMO entry", 5, "warn"),
                Bar("Over-sized", 2, "warn"),
                Bar("Broke hours rule", 1, "muted"),
            ),
        ),
    ),
    steps=(
        "Sort the week's trades by result in R.",
        "Read the worst five. Tag each.",
        "Read the best five. Tag each.",
        "Write down one thing to do differently next week.",
    ),
    example_md="""
This week: eight trades. Two tagged "traded outside hours", both losers, total −2.4R.

Next week's rule: "No trades after 21:00 Dubai time."

One simple change, based on the data. Do not change more than one thing at a time, or you will not know what helped.
""".strip(),
    mistakes=(
        "Skipping the review when the week went well.",
        "Changing five things at once.",
        "Reviewing only losing trades.",
    ),
    evidence=fact(
        "A habit, not a claim. We know of no good study isolating weekly reviews. Their value is that they create the data you need to decide what to change."
    ),
    try_it="Put a fixed 30-minute review in your calendar for this weekend. Write the single change you will make.",
    quiz=(
        Q(
            "In a review, what should you look at first?",
            ("The worst and best trades", "Your bank balance", "News headlines"),
            0,
            "Both ends of the results teach most.",
        ),
        Q(
            "How many things should you change after a review?",
            ("One", "As many as possible", "None, ever"),
            0,
            "One change at a time lets you see what worked.",
        ),
    ),
    takeaways=(
        "A weekly review is short.",
        "Tags show patterns early.",
        "Change one thing at a time.",
    ),
)

_PROCESS = Lesson(
    slug="psychology/process-goals",
    title="Process goals beat profit goals",
    summary="Set goals you actually control.",
    est_minutes=6,
    key_concepts=("process goals", "outcome goals", "variance", "control", "streaks"),
    figures=(Figure("process-vs-outcome", "Outcome = process + variance."),),
    goal="Set goals you can actually control, and judge weeks by them.",
    body_md="""
"Make $200 a day" is the most natural goal in trading, and one of the most destructive.

**Outcomes = process + variance.** In any one week, variance is loud: a perfectly run week can lose money, and a reckless one can win. If your goal lives in outcomes, variance will regularly punish good behaviour and reward bad behaviour. That is exactly how bad habits get trained in.

**Process goals put the target where you have control:**

- Every trade sized according to plan.
- No trades outside my setups.
- Journal entry within an hour of closing.
- Stop trading at the daily loss limit.

Score your week on those. A disciplined losing week is a **passed** week.

The mentor itself is run this way: it does not try to "be right this week". It aims for calibrated probabilities, honest grading and retraining on evidence.
""".strip(),
    charts=(
        Chart(
            title="Process score against the week's result",
            caption="Illustrative weeks. A high process score can still have a losing week, and a low process score can get lucky.",
            data_kind="illustrative",
            kind="bars",
            y_format="r",
            y_label="Week's result in R",
            bars=(
                Bar("Week 1 (process 95%)", 2.1, "accentSoft"),
                Bar("Week 2 (process 92%)", -1.4, "danger"),
                Bar("Week 3 (process 40%)", 3.2, "warn"),
                Bar("Week 4 (process 90%)", 0.6, "accentSoft"),
            ),
        ),
    ),
    steps=(
        "List four behaviours you can fully control.",
        "Score each one every week.",
        "Judge your week on the score, not the money.",
        "Look at the money only over longer periods.",
    ),
    example_md="""
Week 2 above lost 1.4R but scored 92% on process. Week 3 made 3.2R and scored 40%.

Week 3 is the dangerous one. A reckless winning week teaches you to keep being reckless. If you judge by money, you learn the wrong lesson.
""".strip(),
    mistakes=(
        "Setting a daily money target.",
        "Calling a reckless winning week a success.",
        "Setting process goals you cannot measure.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
There is broad research in psychology that focusing on controllable behaviour helps performance, but we did not review controlled studies specific to trading. This chapter treats process goals as a sensible practice, not a proven route to profit.
""".strip(),
    ),
    try_it="Write four process goals for next week, and score yourself on Sunday.",
    quiz=(
        Q(
            "Which is a process goal?",
            (
                "Make $500 this week",
                "Take only checklist-passing trades this week",
                "Have a 70% win rate this month",
            ),
            1,
            "Only behaviour is fully yours.",
        ),
        Q(
            "A disciplined losing week means…",
            ("You failed", "You passed", "You must change your strategy"),
            1,
            "Variance is not a failure of process.",
        ),
    ),
    takeaways=(
        "Outcomes include luck.",
        "Score behaviour, not money.",
        "Beware of reckless winning weeks.",
    ),
)

_LOSSES = Lesson(
    slug="psychology/learning-from-losses",
    title="Learning from losses without punishing yourself",
    summary="Separate 'the market beat a sound plan' from 'I made a mistake'.",
    est_minutes=8,
    key_concepts=("root cause", "process error", "outcome bias", "resulting", "R bled"),
    figures=(Figure("loss-root-causes", "Causes ranked by the risk they actually cost."),),
    goal="Sort every loss into one of two piles, and fix only what really needs fixing.",
    body_md="""
You just lost money. What went wrong? The honest answer, most of the time, is **nothing**.

Poker players call it **resulting**: judging a decision by its outcome. A system that wins 55% of the time loses 45 trades out of every 100. Those losses are the system working as designed, yet they feel exactly like losses from real mistakes.

So the trader "fixes" things, adding a filter here and tightening a rule there, until the profitable system stops being profitable.

### Two piles

**Pile one: the market beat a sound plan.** You followed your rules and lost anyway. This is the cost of doing business. In this app it is the tag **"Good process, bad outcome"**.

**Pile two: you did something you control.** You entered without a setup, you were too big, you moved your stop. These are habits, and they can be fixed.

Most improvement in trading comes from shrinking pile two. Most self-inflicted damage comes from treating pile one as if it were pile two.

### Why tags are a fixed list

Tags are for **counting**. Free text cannot be counted. "Bad entry", "rushed the entry" and "impatient" hide one habit in three spellings.

### Sort by damage, not frequency

Five trades tagged "bad timing" costing 0.2R each come to 1.0R. One "position too large" trade costing 3.0R is three times worse. The review panel sorts by **R bled**, so the biggest problem appears at the top.
""".strip(),
    charts=(
        Chart(
            title="Sort causes by damage, not by count",
            caption="Illustrative example from the text. 'Bad timing' happened most often, but 'position too large' cost the most.",
            data_kind="illustrative",
            kind="bars",
            y_format="r",
            y_label="Total cost in R",
            bars=(
                Bar("Position too large (1×)", -3.0, "danger"),
                Bar("Moved stop (2×)", -1.6, "danger"),
                Bar("Bad timing (5×)", -1.0, "warn"),
            ),
        ),
    ),
    steps=(
        "Tag every closed loss immediately.",
        "Choose pile one or pile two.",
        "Do not change your system based on pile one trades.",
        "Each week, fix the pile-two habit that cost the most.",
    ),
    example_md="""
You lost 1R on a trade that met all your rules and was correctly sized.

**Tag:** Good process, bad outcome. **Action:** none.

The next day you lost 3R by holding through a stop you had moved.

**Tag:** Moved stop. **Action:** review your rule, and add the check "I do not move stops further away" to your checklist.

If you had treated both as "bad trades" you would have tried to change the wrong thing.
""".strip(),
    mistakes=(
        "Never using the good-process tag.",
        "Changing a working system after a normal losing run.",
        "Tagging by writing paragraphs.",
    ),
    evidence=Evidence(
        Verdict.MIXED,
        """
The idea that outcomes depend on chance as well as skill is basic statistics. "Resulting" and outcome bias are well-known in decision research. We did not find controlled evidence specific to trading journals, so treat this as sensible practice.
""".strip(),
    ),
    try_it="Go through your last five losing trades. Put each into pile one or pile two. Be honest about which is which.",
    quiz=(
        Q(
            "You followed your plan exactly and lost. What should you change?",
            (
                "Tighten the entry rules",
                "Nothing: tag it good process",
                "Reduce size until you start winning",
            ),
            1,
            "Any edge has losing trades. Do not fix what is not broken.",
        ),
        Q(
            "Why sort causes by R bled and not by count?",
            (
                "The most frequent problem is not always the most costly",
                "It looks better",
                "Regulators require it",
            ),
            0,
            "One big mistake can outweigh many small ones.",
        ),
    ),
    takeaways=(
        "Many losses are not mistakes.",
        "Sort losses into two piles.",
        "Fix what costs the most.",
    ),
)

_TOOLS = Lesson(
    slug="toolkit/risk-and-journaling-tools",
    title="Risk and journaling tools",
    summary="The unglamorous tools that keep you in the game.",
    est_minutes=5,
    key_concepts=("position-size calculator", "journal", "spreadsheet", "expectancy"),
    figures=(Figure("risk-tools", "Calculator, journal, spreadsheet."),),
    goal="Set up simple tools that keep your sizing honest and your records complete.",
    body_md="""
- **Position-size calculator:** turns your risk percentage and stop distance into an exact lot size, so you never size by feel. This app has one, and it rounds down so your risk budget stays a ceiling.
- **Trade journal:** one row per trade with entry, stop, target, size, reason and realised R, written before the trade and reviewed after.
- **Spreadsheet:** even a simple one can compute expectancy, profit factor, average R, maximum drawdown and how often each mistake tag appears.

### The one habit

Log **every** trade, including the ones you are not proud of, especially those.
""".strip(),
    charts=(
        Chart(
            title="Numbers worth calculating",
            caption="Illustrative dashboard from a journal of 100 trades.",
            data_kind="illustrative",
            kind="bars",
            y_format="plain",
            y_label="Value",
            bars=(
                Bar("Average R", 0.18, "accentSoft"),
                Bar("Win rate", 0.46, "accent"),
                Bar("Profit factor", 1.3, "accentSoft"),
                Bar("Max drawdown (R)", 9.0, "danger"),
            ),
        ),
    ),
    steps=(
        "Use a calculator for every position.",
        "Keep one journal for everything.",
        "Compute your main statistics monthly.",
    ),
    example_md="""
From 100 journal rows you get: average R **+0.18**, win rate **46%**, profit factor **1.3**, and a max drawdown of **9R**.

If you risk 1% per trade, that drawdown was about 9% of the account. You now know what a normal bad stretch looks like for you.
""".strip(),
    mistakes=(
        "Sizing without a calculator.",
        "Leaving out embarrassing trades.",
        "Collecting statistics and not acting on them.",
    ),
    evidence=fact(
        "These are tools. They do not produce an edge, but they make it possible to see whether you have one."
    ),
    try_it="Build a simple spreadsheet from your journal to calculate average R, win rate and maximum drawdown.",
    quiz=(
        Q(
            "Why does a calculator round down?",
            ("Your risk budget is a ceiling", "To save money on spreads", "It is a bug"),
            0,
            "Rounding up would exceed your risk limit.",
        ),
        Q(
            "Which trades should go in your journal?",
            ("All of them", "Only the good ones", "Only large ones"),
            0,
            "Leaving trades out ruins the data.",
        ),
    ),
    takeaways=("Calculator, journal, spreadsheet.", "Log every trade.", "Use the numbers."),
)

_REVIEW_TEACH = Lesson(
    slug="mind/a-review-that-teaches",
    title="A review that teaches",
    summary="A monthly check of whether your edge is real and whether you are the problem.",
    est_minutes=6,
    key_concepts=("monthly review", "edge check", "rule adherence"),
    goal="Run a monthly review that separates your strategy's results from your own execution.",
    body_md="""
Once a month, go deeper than the weekly check. Answer three questions.

1. **Does the strategy still work?** Compare your results with what your tests said to expect.
2. **Am I following it?** What share of trades followed your rules?
3. **What would it have made if I had followed it perfectly?** Work out your **rule-adherence gap**: the difference between what your rules would have made and what you actually made.

A large gap means your behaviour is the problem. A small gap and bad results may mean the strategy has stopped working, or that you are in a normal bad stretch. Check how far your results are from your tested range before deciding.

Do not adjust the strategy after only a few trades. Wait for a sample big enough to tell the difference, which Stage 10 explains.
""".strip(),
    charts=(
        Chart(
            title="Rules against reality: a monthly check",
            caption="Illustrative month. The strategy made +6.0R if followed exactly. The trader actually made +1.5R. The gap is the cost of behaviour.",
            data_kind="illustrative",
            kind="bars",
            y_format="r",
            y_label="R this month",
            bars=(
                Bar("Rules followed exactly", 6.0, "accentSoft"),
                Bar("What actually happened", 1.5, "warn"),
                Bar("Rule-adherence gap", -4.5, "danger"),
            ),
        ),
    ),
    steps=(
        "Calculate what your rules would have made this month.",
        "Calculate what you actually made.",
        "Compute the gap and list the trades that caused it.",
        "Compare your strategy's results with your tested range.",
        "Decide one change for the next month.",
    ),
    example_md="""
October: your rules would have made **+6R**. You made **+1.5R**.

Your journal shows four trades you skipped because you felt nervous and two extra trades you took on a hunch. The gap of 4.5R is your biggest opportunity, and it needs no new strategy.
""".strip(),
    mistakes=(
        "Changing your strategy after a bad month.",
        "Forgetting to compare with what your testing predicted.",
        "Skipping the review in good months.",
    ),
    evidence=fact(
        "A review format, and not a measured result. Its purpose is to split your strategy's performance from your own behaviour."
    ),
    try_it="Pick last month. Work out roughly what your rules would have made, then compare with your actual result.",
    quiz=(
        Q(
            "A large rule-adherence gap means…",
            ("Your behaviour is costing you", "Your strategy has stopped working", "Nothing"),
            0,
            "The strategy would have done better than you did.",
        ),
        Q(
            "How quickly should you change a strategy?",
            ("After a sample big enough to matter", "After any loss", "Every Monday"),
            0,
            "Small samples are mostly noise.",
        ),
    ),
    takeaways=(
        "Measure your rule-adherence gap.",
        "Compare results to what you tested.",
        "Change slowly.",
    ),
)

CHAPTERS = (
    chapter(
        "mind",
        "mind-and-habits",
        "Mind and habits",
        "Your biggest risk is usually you. Journals, tilt, process goals and reviews.",
        (_BIASES, _JOURNAL, _TILT, _REVIEW, _PROCESS, _LOSSES, _TOOLS, _REVIEW_TEACH),
    ),
)
