/**
 * A confidence interval rendered under a headline number.
 *
 * An equity curve is the most persuasive and least informative chart in
 * trading, and a win rate over forty trades feels like proof. This sits
 * beneath both and says out loud whether the number has earned belief —
 * the interval is drawn against the baseline so "contains the coin flip"
 * is visible, not just asserted.
 */
/**
 * An equity curve is the most persuasive and least informative chart in
 * trading. This sits under it and says whether it has earned any belief.
 */
export function SignificanceNote({
  verdict,
  significant,
  low,
  high,
  baseline,
  baselineLabel = 'coin flip',
}: {
  verdict: string;
  significant: boolean;
  low: number;
  high: number;
  baseline: number;
  /**
   * What the mark on the track represents. It is not always a coin flip:
   * grading a tradeable signal uses the spread-adjusted breakeven, which
   * sits above 50% and is the difference between "better than chance" and
   * "worth doing".
   */
  baselineLabel?: string;
}) {
  if (!verdict) return null;

  // Map the interval onto a track spanning 0-100%, with the baseline marked.
  const span = Math.max(0.0001, high - low);
  const tone = significant ? 'accent' : 'warn';

  return (
    <div
      className={`rounded-lg border p-3 ${
        significant
          ? 'border-mentor-accent/40 bg-mentor-accent/5'
          : 'border-mentor-warn/40 bg-mentor-warn/5'
      }`}
    >
      <div className="flex items-start gap-2">
        <span className={`mt-0.5 text-sm text-mentor-${tone}`}>
          {significant ? '✓' : '⚠'}
        </span>
        <p className="text-sm leading-relaxed text-mentor-fg">{verdict}</p>
      </div>

      <div className="relative mt-3 h-6">
        {/* full 0-100% track */}
        <div className="absolute inset-x-0 top-2.5 h-1 rounded-full bg-mentor-panelLight" />
        {/* the confidence interval */}
        <div
          className={`absolute top-2 h-2 rounded-full ${
            significant ? 'bg-mentor-accent' : 'bg-mentor-warn'
          }`}
          style={{ left: `${low * 100}%`, width: `${span * 100}%` }}
          title={`95% interval: ${(low * 100).toFixed(0)}%-${(high * 100).toFixed(0)}%`}
        />
        {/* the baseline mark — a coin flip, or the breakeven above it */}
        <div
          className="absolute top-0 h-6 w-px bg-mentor-fg/60"
          style={{ left: `${baseline * 100}%` }}
        />
        <span
          className="absolute top-0 -translate-x-1/2 text-[10px] text-mentor-muted"
          style={{ left: `${baseline * 100}%`, marginTop: '-2px' }}
        >
          &nbsp;
        </span>
      </div>
      <div className="flex justify-between text-[10px] text-mentor-muted">
        <span>0%</span>
        <span>
          {baselineLabel} (
          {(baseline * 100).toFixed(2).replace(/\.00$/, '')}%)
        </span>
        <span>100%</span>
      </div>
    </div>
  );
}
