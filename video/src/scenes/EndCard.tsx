import React from 'react';
import {
  AbsoluteFill, interpolate, spring, staticFile,
  useCurrentFrame, useVideoConfig,
} from 'remotion';
import { C, FONT } from '../tokens';

export const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Scene fades in from export card
  const sceneOp = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: 'clamp' });

  // Logo + wordmark spring in
  const logoScale = spring({ frame, fps, config: { damping: 18, stiffness: 80 } });
  const logoOp    = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: 'clamp' });

  // Tagline fades in
  const tagOp = interpolate(frame, [14, 32], [0, 1], { extrapolateRight: 'clamp' });

  // Rule grows across
  const ruleW = interpolate(
    spring({ frame: Math.max(0, frame - 26), fps, config: { damping: 24 } }),
    [0, 1], [0, 64],
  );

  // URL pill slides up
  const urlProgress = spring({
    frame: Math.max(0, frame - 34), fps,
    config: { damping: 20, stiffness: 100 },
  });
  const urlY  = interpolate(urlProgress, [0, 1], [16, 0]);
  const urlOp = interpolate(frame, [34, 50], [0, 1], { extrapolateRight: 'clamp' });

  // Subtext
  const subOp = interpolate(frame, [44, 58], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{
      background: C.bg,
      opacity: sceneOp,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: FONT,
    }}>

      {/* Logo + wordmark */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 24,
        marginBottom: 18,
        opacity: logoOp,
        transform: `scale(${logoScale})`,
      }}>
        <img src={staticFile('icon.svg')} style={{ width: 64, height: 64 }} />
        <span style={{
          fontSize: 64,
          fontWeight: 800,
          color: C.accent,
          letterSpacing: '-0.03em',
          lineHeight: 1,
        }}>
          TASS
        </span>
      </div>

      {/* Tagline */}
      <div style={{
        fontSize: 20,
        fontWeight: 400,
        color: C.muted,
        letterSpacing: '0.01em',
        marginBottom: 28,
        opacity: tagOp,
      }}>
        Text analysis for serious researchers.
      </div>

      {/* Accent rule */}
      <div style={{
        width: ruleW,
        height: 3,
        background: C.accent,
        borderRadius: 2,
        marginBottom: 28,
      }} />

      {/* URL pill */}
      <div style={{
        opacity: urlOp,
        transform: `translateY(${urlY}px)`,
        marginBottom: 14,
      }}>
        <div style={{
          background: C.accent,
          color: C.white,
          padding: '12px 36px',
          borderRadius: 99,
          fontSize: 18,
          fontWeight: 700,
          letterSpacing: '0.01em',
        }}>
          usetass.app
        </div>
      </div>

      {/* Sub-CTA */}
      <div style={{
        opacity: subOp,
        fontSize: 14,
        color: C.muted,
        letterSpacing: '0.02em',
      }}>
        Join the waitlist — free early access for researchers
      </div>
    </AbsoluteFill>
  );
};
