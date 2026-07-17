import { useId } from 'react';

/**
 * The Mentor mark: a learning-loop arrow wrapping a rising candlestick
 * trend — the system in one picture (predict → grade → learn, around the
 * market). Gradient goes brand-indigo → profit-emerald.
 *
 * The gradient id must be unique per instance: the shell renders the mark
 * in both the (sometimes display:none) desktop sidebar and the mobile
 * header, and browsers won't paint a gradient whose definition lives in a
 * hidden subtree.
 */
export function Logo({ size = 32 }: { size?: number }) {
  const gid = useId();
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      aria-hidden="true"
      role="img"
    >
      <defs>
        <linearGradient id={gid} x1="6" y1="42" x2="42" y2="6" gradientUnits="userSpaceOnUse">
          {/* var() is CSS-only — presentation attributes can't resolve it, so
              the stops must be styled, not attributed. */}
          <stop offset="0" style={{ stopColor: 'rgb(var(--mentor-accent))' }} />
          <stop offset="1" style={{ stopColor: 'rgb(var(--mentor-accentSoft))' }} />
        </linearGradient>
      </defs>

      {/* learning-loop arc with arrowhead */}
      <path
        d="M42 24a18 18 0 1 1-6.2-13.6"
        stroke={`url(#${gid})`}
        strokeWidth="3.6"
        strokeLinecap="round"
      />
      <path d="M36.5 3.5l1 8.2 8-2.4z" style={{ fill: 'rgb(var(--mentor-accentSoft))' }} />

      {/* rising candles inside the loop */}
      <g stroke={`url(#${gid})`} strokeWidth="3.4" strokeLinecap="round">
        <line x1="16" y1="33" x2="16" y2="25" />
        <line x1="24" y1="30" x2="24" y2="20" />
        <line x1="32" y1="26" x2="32" y2="15" />
      </g>
    </svg>
  );
}

/** Data-URI of the mark with fixed colours, for the favicon. */
export const LOGO_FAVICON_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" fill="none"><defs><linearGradient id="g" x1="6" y1="42" x2="42" y2="6" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="%234f46e5"/><stop offset="1" stop-color="%23059669"/></linearGradient></defs><path d="M42 24a18 18 0 1 1-6.2-13.6" stroke="url(%23g)" stroke-width="3.6" stroke-linecap="round"/><path d="M36.5 3.5l1 8.2 8-2.4z" fill="%23059669"/><g stroke="url(%23g)" stroke-width="3.4" stroke-linecap="round"><line x1="16" y1="33" x2="16" y2="25"/><line x1="24" y1="30" x2="24" y2="20"/><line x1="32" y1="26" x2="32" y2="15"/></g></svg>`;
