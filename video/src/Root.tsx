import React from 'react';
import { Composition } from 'remotion';
import { TassDemo } from './TassDemo';
import { TassShort01, TASS_SHORT_01_FRAMES } from './shorts/TassShort01';
import { FPS, TOTAL_FRAMES, W, H, V } from './tokens';

export const Root: React.FC = () => (
  <>
    {/* ── Horizontal (16:9) — website embed ──────────────────────── */}
    <Composition
      id="TassDemo"
      component={TassDemo}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={W}
      height={H}
    />

    {/* ── Vertical (9:16) — TikTok / YouTube Shorts ──────────────── */}
    <Composition
      id="TassShort01"
      component={TassShort01}
      durationInFrames={TASS_SHORT_01_FRAMES}
      fps={FPS}
      width={V.w}
      height={V.h}
    />
  </>
);
