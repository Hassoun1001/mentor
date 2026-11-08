/**
 * The Methods Atlas: one card for each of 150 trading methods, searchable and
 * filterable. Popularity and evidence are always shown as two separate labels,
 * because a method can be very popular and still have weak evidence.
 */
import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

import { type AtlasMethod, type BookSource, getAtlas, getSources } from '../../api/curriculum';
import { type AtlasState, EMPTY_ATLAS } from './atlasState';
import { VERDICT } from './verdict';

const USAGE: Record<string, { label: string; tone: string; hint: string }> = {
  very_common: {
    label: 'Very common',
    tone: 'border-mentor-accent/50 text-mentor-accent',
    hint: 'You will meet this on almost every platform or course.',
  },
  common: {
    label: 'Common',
    tone: 'border-mentor-accentSoft/50 text-mentor-accentSoft',
    hint: 'Many traders know and use this, but it is not a default.',
  },
  specialist: {
    label: 'Specialist',
    tone: 'border-mentor-warn/50 text-mentor-warn',
    hint: 'Used by a smaller group with special data, skills or access.',
  },
  rare: {
    label: 'Rare',
    tone: 'border-mentor-border text-mentor-muted',
    hint: 'Few people rely on this.',
  },
};

const USERS: Record<string, string> = {
  retail: 'Retail traders',
  prop: 'Prop traders',
  funds: 'Funds',
  banks: 'Banks',
  market_makers: 'Market makers',
};

const MARKETS: Record<string, string> = {
  forex: 'Forex',
  stocks: 'Stocks',
  indices: 'Indices',
  futures: 'Futures',
  commodities: 'Commodities',
  bonds: 'Bonds',
  options: 'Options',
  crypto: 'Crypto',
};

const ACCESS: Record<string, { label: string; tone: string }> = {
  easy: { label: 'Easy for retail', tone: 'text-mentor-accentSoft' },
  paid: { label: 'Retail can get it, at a cost', tone: 'text-mentor-warn' },
  hard: { label: 'Hard for retail: mostly firms', tone: 'text-mentor-danger' },
};

/** Cards use a shorter word than lessons do for "nothing to test". */
const EVIDENCE_LABEL: Record<string, string> = {
  ...Object.fromEntries(Object.entries(VERDICT).map(([key, value]) => [key, value.label])),
  fact: 'Measure or definition',
};

const FIELD_CLASS =
  'w-full rounded-lg border border-mentor-border bg-mentor-panel px-3 py-2.5 text-base text-mentor-fg focus:border-mentor-accent focus:outline-none sm:text-sm';

function searchableText(method: AtlasMethod): string {
  return [
    method.name,
    method.what,
    method.usage_why,
    method.when_to_use,
    method.when_not,
    method.tools,
    method.evidence,
  ]
    .join(' ')
    .toLowerCase();
}

/** Short searches such as "ICT" or "RSI" must match a whole word, not "predict". */
function matches(haystack: string, word: string): boolean {
  if (word.length > 3) return haystack.includes(word);
  return new RegExp(`\\b${word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`).test(haystack);
}

function isVisible(method: AtlasMethod, state: AtlasState, words: string[]): boolean {
  if (state.usage && method.usage !== state.usage) return false;
  if (state.verdict && method.verdict !== state.verdict) return false;
  if (state.market && !method.markets.includes(state.market)) return false;
  if (state.access && method.access !== state.access) return false;
  if (state.lessonOnly && !method.lesson_slug) return false;
  if (!words.length) return true;
  const haystack = searchableText(method);
  return words.every((word) => matches(haystack, word));
}

function Chip({ title, label, tone }: { title: string; label: string; tone: string }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-xs ${tone}`}>
      <span className="opacity-70">{title}:</span>
      <span className="font-medium">{label}</span>
    </span>
  );
}

function Detail({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wider text-mentor-muted">{title}</dt>
      <dd className="mt-0.5 leading-relaxed text-mentor-fg">{children}</dd>
    </div>
  );
}

function Card({
  method,
  open,
  sources,
  onToggle,
  onOpenLesson,
}: {
  method: AtlasMethod;
  open: boolean;
  sources: Map<string, BookSource>;
  onToggle: () => void;
  onOpenLesson: (slug: string) => void;
}) {
  const usage = USAGE[method.usage];
  const verdict = VERDICT[method.verdict] ?? VERDICT.fact;
  const access = ACCESS[method.access];
  const cited = method.sources.flatMap((key) => {
    const source = sources.get(key);
    return source ? [source] : [];
  });
  return (
    <li id={`method-${method.slug}`} className="rounded-xl border border-mentor-border bg-mentor-panel">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="w-full p-4 text-left"
      >
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-base font-medium leading-snug text-mentor-fg">{method.name}</h3>
          <span className="flex-shrink-0 text-xs text-mentor-muted">{open ? 'Hide' : 'Details'}</span>
        </div>
        <p className="mt-1 text-sm leading-relaxed text-mentor-fg">{method.what}</p>
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {usage && <Chip title="Usage" label={usage.label} tone={usage.tone} />}
          {verdict && (
            <Chip title="Evidence" label={EVIDENCE_LABEL[method.verdict] ?? ''} tone={verdict.tone} />
          )}
        </div>
      </button>
      {open && (
        <dl className="space-y-3 border-t border-mentor-border px-4 pb-4 pt-3 text-sm">
          <Detail title="Who mainly uses it">
            {method.users.map((user) => USERS[user] ?? user).join(', ')}
          </Detail>
          <Detail title="How widely used">
            <span className="font-medium">{usage?.label}.</span> {method.usage_why}
          </Detail>
          <Detail title="When people use it">{method.when_to_use}</Detail>
          <Detail title="When it does not suit">{method.when_not}</Detail>
          <Detail title="Markets it suits">
            {method.markets.map((market) => MARKETS[market] ?? market).join(', ')}
          </Detail>
          <Detail title="Data and tools it needs">
            {method.tools} {access && <span className={`font-medium ${access.tone}`}>{access.label}.</span>}
          </Detail>
          <Detail title="Does it actually work?">
            {verdict && (
              <span className={`mr-1.5 inline-block rounded border px-1.5 py-0.5 text-xs font-medium ${verdict.tone}`}>
                {EVIDENCE_LABEL[method.verdict]}
              </span>
            )}
            {method.evidence}
          </Detail>
          {method.lesson_slug ? (
            <button
              type="button"
              onClick={() => onOpenLesson(method.lesson_slug as string)}
              className="text-sm font-medium text-mentor-accent hover:underline"
            >
              Read the full lesson: {method.lesson_title} →
            </button>
          ) : (
            <p className="text-xs text-mentor-muted">No full lesson yet. This card is the whole entry.</p>
          )}
          {cited.length > 0 && (
            <div className="text-xs leading-relaxed text-mentor-muted">
              Sources:{' '}
              {cited.map((source, i) => (
                <span key={source.key}>
                  {i > 0 && '; '}
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="underline hover:text-mentor-fg"
                  >
                    {source.authors} ({source.year})
                  </a>
                  {!source.checked && ' (not re-checked)'}
                </span>
              ))}
            </div>
          )}
        </dl>
      )}
    </li>
  );
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: [string, string][];
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs text-mentor-muted">{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)} className={FIELD_CLASS}>
        <option value="">All</option>
        {options.map(([key, text]) => (
          <option key={key} value={key}>
            {text}
          </option>
        ))}
      </select>
    </label>
  );
}

const entries = (map: Record<string, { label: string }>): [string, string][] =>
  Object.entries(map).map(([key, value]) => [key, value.label]);

export function MethodsAtlas({
  state,
  onChange,
  onOpenLesson,
  onHome,
}: {
  state: AtlasState;
  onChange: (state: AtlasState) => void;
  onOpenLesson: (slug: string) => void;
  onHome: () => void;
}) {
  const atlas = useQuery({ queryKey: ['curriculum', 'atlas'], queryFn: getAtlas, staleTime: Infinity });
  const sources = useQuery({ queryKey: ['curriculum', 'sources'], queryFn: getSources, staleTime: Infinity });
  const sourceMap = useMemo(
    () => new Map((sources.data ?? []).map((source) => [source.key, source])),
    [sources.data]
  );
  const update = (patch: Partial<AtlasState>) => onChange({ ...state, ...patch });

  const words = state.text.toLowerCase().split(/\s+/).filter(Boolean);
  const groups = (atlas.data?.groups ?? [])
    .filter((group) => !state.group || group.letter === state.group)
    .map((group) => ({
      ...group,
      methods: group.methods.filter((method) => isVisible(method, state, words)),
    }))
    .filter((group) => group.methods.length > 0);
  const total = (atlas.data?.groups ?? []).reduce((sum, group) => sum + group.methods.length, 0);
  const shown = groups.reduce((sum, group) => sum + group.methods.length, 0);
  const visibleSlugs = groups.flatMap((group) => group.methods.map((method) => method.slug));
  const allOpen = visibleSlugs.length > 0 && visibleSlugs.every((slug) => state.open.includes(slug));

  const toggle = (slug: string) =>
    update({
      open: state.open.includes(slug)
        ? state.open.filter((item) => item !== slug)
        : [...state.open, slug],
    });

  return (
    <section className="mx-auto max-w-3xl space-y-4">
      <header>
        <button type="button" onClick={onHome} className="text-sm text-mentor-muted hover:text-mentor-fg">
          ← All lessons
        </button>
        <h1 className="mt-2 text-2xl font-medium tracking-tight text-mentor-fg">Methods Atlas</h1>
        <p className="mt-1 text-sm leading-relaxed text-mentor-muted">
          150 trading methods. For each one: what it is, who uses it, when it suits, what it needs,
          and whether it has been shown to work. This is education, and nothing here tells you what
          to trade.
        </p>
      </header>

      {atlas.data && (
        <div className="rounded-xl border border-mentor-warn/40 bg-mentor-warn/5 px-4 py-3 text-sm leading-relaxed text-mentor-fg">
          <strong className="font-semibold">About the labels.</strong> {atlas.data.usage_note}
        </div>
      )}

      <div className="space-y-3">
        <label className="block">
          <span className="sr-only">Search the methods</span>
          <input
            type="search"
            value={state.text}
            onChange={(e) => update({ text: e.target.value })}
            placeholder="Search: RSI, order flow, options, recession…"
            className={`${FIELD_CLASS} placeholder:text-mentor-muted`}
          />
        </label>

        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter by group">
          <GroupChip active={!state.group} label="All" onClick={() => update({ group: '' })} />
          {(atlas.data?.groups ?? []).map((group) => (
            <GroupChip
              key={group.letter}
              active={state.group === group.letter}
              label={`${group.letter} ${group.title}`}
              onClick={() => update({ group: group.letter })}
            />
          ))}
        </div>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Select label="Usage" value={state.usage} options={entries(USAGE)} onChange={(usage) => update({ usage })} />
          <Select
            label="Evidence"
            value={state.verdict}
            options={Object.entries(EVIDENCE_LABEL)}
            onChange={(verdict) => update({ verdict })}
          />
          <Select
            label="Market"
            value={state.market}
            options={Object.entries(MARKETS)}
            onChange={(market) => update({ market })}
          />
          <Select label="Retail access" value={state.access} options={entries(ACCESS)} onChange={(access) => update({ access })} />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 text-sm">
          <label className="inline-flex items-center gap-2 text-mentor-fg">
            <input
              type="checkbox"
              checked={state.lessonOnly}
              onChange={(e) => update({ lessonOnly: e.target.checked })}
            />
            Only methods with a full lesson
          </label>
          <div className="flex items-center gap-3 text-mentor-muted">
            <span aria-live="polite">
              Showing {shown} of {total}
            </span>
            <button
              type="button"
              className="underline hover:text-mentor-fg"
              onClick={() => update({ open: allOpen ? [] : visibleSlugs })}
            >
              {allOpen ? 'Hide all' : 'Open all'}
            </button>
            <button
              type="button"
              className="underline hover:text-mentor-fg"
              onClick={() => onChange(EMPTY_ATLAS)}
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {atlas.isLoading && <p className="text-sm text-mentor-muted">Loading…</p>}
      {atlas.data && shown === 0 && (
        <p className="rounded-xl border border-mentor-border bg-mentor-panel p-4 text-sm text-mentor-muted">
          No method matches these filters.
        </p>
      )}

      {groups.map((group) => (
        <div key={group.letter}>
          <h2 className="text-lg font-medium text-mentor-fg">
            {group.letter}. {group.title}
          </h2>
          <p className="mb-2 text-sm text-mentor-muted">{group.summary}</p>
          <ul className="space-y-2">
            {group.methods.map((method) => (
              <Card
                key={method.slug}
                method={method}
                open={state.open.includes(method.slug)}
                sources={sourceMap}
                onToggle={() => toggle(method.slug)}
                onOpenLesson={onOpenLesson}
              />
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

function GroupChip({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`rounded-full border px-2.5 py-1 text-xs ${
        active
          ? 'border-mentor-accent bg-mentor-accent/10 text-mentor-accent'
          : 'border-mentor-border text-mentor-muted hover:text-mentor-fg'
      }`}
    >
      {label}
    </button>
  );
}
