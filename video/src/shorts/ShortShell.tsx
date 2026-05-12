/**
 * ShortShell — vertical (9:16) canvas wrapper for TASS TikTok/Shorts content.
 *
 * TASS shorts open with a data-themed intro (accent green on dark) and
 * close with the product name + academic positioning. Visually distinct
 * from Ibis and Lector shells.
 */
import React from 'react';
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { C, FONT, V } from '../tokens';

const INTRO_FRAMES = 30;
const OUTRO_FRAMES = 45;

interface ShortShellProps {
  children: React.ReactNode;
  totalFrames: number;
  bg?: string;
}

const IntroCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({ frame, fps, config: { damping: 22, stiffness: 90 } });
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        background: '#0F0F0F',
        justifyContent: 'center',
        alignItems: 'center',
        opacity,
      }}
    >
      <div
        style={{
          fontFamily: FONT,
          fontSize: 56,
          fontWeight: 800,
          color: C.accent,
          letterSpacing: '-0.03em',
          transform: `scale(${scale})`,
        }}
      >
        TASS
      </div>
      <div
        style={{
          fontFamily: FONT,
          fontSize: 15,
          fontWeight: 600,
          color: 'rgba(255,255,255,0.45)',
          marginTop: 10,
          letterSpacing: '0.1em',
          textTransform: 'uppercase' as const,
          opacity: interpolate(frame, [10, 22], [0, 1], { extrapolateRight: 'clamp' }),
        }}
      >
        Text Analysis Support Software
      </div>
    </AbsoluteFill>
  );
};

const OutroCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: 'clamp' });
  const spring1 = spring({ frame, fps, config: { damping: 18, stiffness: 80 } });

  return (
    <AbsoluteFill
      style={{
        background: '#0F0F0F',
        justifyContent: 'center',
        alignItems: 'center',
        opacity: fadeIn,
      }}
    >
      <div
        style={{
          fontFamily: FONT,
          fontSize: 44,
          fontWeight: 800,
          color: C.accent,
          letterSpacing: '-0.03em',
          transform: `translateY(${interpolate(spring1, [0, 1], [20, 0])}px)`,
        }}
      >
        TASS
      </div>
      <div
        style={{
          fontFamily: FONT,
          fontSize: 15,
          fontWeight: 500,
          color: 'rgba(255,255,255,0.5)',
          marginTop: 12,
          opacity: interpolate(frame, [15, 28], [0, 1], { extrapolateRight: 'clamp' }),
        }}
      >
        usetass.app
      </div>
    </AbsoluteFill>
  );
};

export const ShortShell: React.FC<ShortShellProps> = ({
  children,
  totalFrames,
  bg = C.bg,
}) => {
  const contentStart = INTRO_FRAMES;
  const contentDuration = totalFrames - INTRO_FRAMES - OUTRO_FRAMES;
  const outroStart = totalFrames - OUTRO_FRAMES;

  return (
    <AbsoluteFill style={{ background: bg }}>
      <Sequence from={0} durationInFrames={INTRO_FRAMES}>
        <IntroCard />
      </Sequence>
      <Sequence from={contentStart} durationInFrames={contentDuration}>
        {children}
      </Sequence>
      <Sequence from={outroStart} durationInFrames={OUTRO_FRAMES}>
        <OutroCard />
      </Sequence>
    </AbsoluteFill>
  );
};

export { INTRO_FRAMES, OUTRO_FRAMES };
