import { useEffect, useState } from 'react';

export type Theme = 'dark' | 'light';

const KEY = 'mentor-theme';

function readStored(): Theme {
  if (typeof localStorage === 'undefined') return 'dark';
  return localStorage.getItem(KEY) === 'light' ? 'light' : 'dark';
}

/**
 * App theme. Persists to localStorage and toggles the `dark` class on
 * <html> (Tailwind's darkMode: 'class'), which swaps the CSS-variable
 * palette defined in index.css. Defaults to dark — the trading-terminal look.
 */
export function useTheme() {
  const [theme, setTheme] = useState<Theme>(readStored);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    try {
      localStorage.setItem(KEY, theme);
    } catch {
      /* ignore private-mode storage errors */
    }
  }, [theme]);

  return {
    theme,
    toggle: () => setTheme((t) => (t === 'dark' ? 'light' : 'dark')),
  };
}
