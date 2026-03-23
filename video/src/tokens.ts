import { loadFont } from '@remotion/google-fonts/PlusJakartaSans';

const { fontFamily } = loadFont();
export const FONT = fontFamily;

export const C = {
  bg:       '#FFFFFF',
  surface:  '#F7F7F8',
  text:     '#0F0F0F',
  accent:   '#2E7D5E',
  accentH:  '#256B50',
  accentL:  '#E8F5F1',
  muted:    '#6B7280',
  border:   '#E4E4E7',
  white:    '#FFFFFF',
  darkBg:   '#111111',
  red:      '#DC2626',
} as const;

export const FPS  = 30;
export const W    = 1280;
export const H    = 720;
export const TOTAL_FRAMES = 780; // 26 s

// Absolute sequence timing
export const SEQ = {
  intro:    { from: 0,   duration: 90  }, // 0 – 3 s
  import:   { from: 90,  duration: 240 }, // 3 – 11 s
  analysis: { from: 330, duration: 240 }, // 11 – 19 s
  export:   { from: 570, duration: 120 }, // 19 – 23 s
  endCard:  { from: 690, duration: 90  }, // 23 – 26 s
} as const;

export const ANNOTATION = 'Interface elements may not accurately represent the final product design.';
