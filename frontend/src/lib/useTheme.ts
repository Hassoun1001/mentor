import { useEffect, useState } from 'react';

export type Theme = 'dark' | 'light';

// v2: the Aurora redesign is light-first, so reset everyone to the new
// default once (old 'mentor-theme' values are ignored).
const KEY = 'mentor-theme-v2';

function readStored(): Theme {
  if (typeof localStorage === 'undefined') return 'light';
  return localStorage.getItem(KEY) === 'dark' ? 'dark' : 'light';
}

/**
 * App theme. Persists to localStorage and toggles the `dark` class on
 * <html> (Tailwind's darkMode: 'class'), which swaps the CSS-variable
 * palette defined in index.css. Defaults to light — the Aurora look.
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
