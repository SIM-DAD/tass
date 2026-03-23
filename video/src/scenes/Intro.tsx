import React from 'react';
import {
  AbsoluteFill, interpolate, spring, staticFile,
  useCurrentFrame, useVideoConfig,
} from 'remotion';
import { C, FONT } from '../tokens';

export const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Icon bounces in from below
  const iconProgress = spring({ frame, fps, config: { damping: 16, stiffness: 90 } });
  const iconY   = interpolate(iconProgress, [0, 1], [40, 0]);
  const iconOp  = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: 'clamp' });

  // Wordmark slides up slightly after icon
  const wordProgress = spring({
    frame: Math.max(0, frame - 12), fps,
    config: { damping: 20, stiffness: 80 },
  });
  const wordY  = interpolate(wordProgress, [0, 1], [20, 0]);
  const wordOp = interpolate(frame, [12, 35], [0, 1], { extrapolateRight: 'clamp' });

  // Tagline fades in last
  const tagOp = interpolate(frame, [32, 58], [0, 1], { extrapolateRight: 'clamp' });

  // Accent line under wordmark grows in
  const lineW = interpolate(
    spring({ frame: Math.max(0, frame - 28), fps, config: { damping: 24 } }),
    [0, 1], [0, 48],
  );

  // Whole scene fades out at end
  const sceneOp = interpolate(frame, [78, 90], [1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{
      background: C.darkBg,
      opacity: sceneOp,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: FONT,
    }}>
      {/* Icon + wordmark row */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 28,
        marginBottom: 16,
        opacity: iconOp,
        transform: `translateY(${iconY}px)`,
      }}>
        <img src={staticFile('icon.svg')} style={{ width: 80, height: 80 }} />
        <div style={{
          opacity: wordOp,
          transform: `translateY(${wordY}px)`,
        }}>
          <span style={{
            fontSize: 80,
            fontWeight: 800,
            color: C.accent,
            letterSpacing: '-0.03em',
            lineHeight: 1,
          }}>
            TASS
          </span>
        </div>
      </div>

      {/* Accent rule */}
      <div style={{
        width: lineW,
        height: 3,
        background: C.accent,
        borderRadius: 2,
        marginBottom: 24,
      }} />

      {/* Tagline */}
      <div style={{
        fontSize: 22,
        fontWeight: 400,
        color: 'rgba(255,255,255,0.65)',
        letterSpacing: '0.01em',
        opacity: tagOp,
      }}>
        Text analysis for serious researchers.
      </div>
    </AbsoluteFill>
  );
};
