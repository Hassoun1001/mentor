/** How each evidence verdict is labelled, in lessons and in the Methods Atlas. */
export const VERDICT: Record<string, { label: string; tone: string; hint: string }> = {
  fact: {
    label: 'Definition',
    tone: 'border-mentor-border text-mentor-muted',
    hint: 'This explains a word or a sum. There is nothing to test.',
  },
  supported: {
    label: 'Supported',
    tone: 'border-mentor-accentSoft/50 text-mentor-accentSoft',
    hint: 'Repeated testing finds this, within the limits described.',
  },
  mixed: {
    label: 'Mixed evidence',
    tone: 'border-mentor-warn/50 text-mentor-warn',
    hint: 'Some tests pass and some fail. Results depend on the setup.',
  },
  weak: {
    label: 'Weak evidence',
    tone: 'border-mentor-danger/50 text-mentor-danger',
    hint: 'Tests mostly fail, or it only works before costs.',
  },
  untested: {
    label: 'Little testing',
    tone: 'border-mentor-danger/50 text-mentor-danger',
    hint: 'Popular, but rarely tested properly.',
  },
};
