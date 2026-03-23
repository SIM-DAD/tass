import React from 'react';
import {
  AbsoluteFill, interpolate, spring,
  useCurrentFrame, useVideoConfig,
} from 'remotion';
import { C, FONT, ANNOTATION } from '../tokens';

export const ExportCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Scene fades in
  const sceneOp = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: 'clamp' });

  // Header slides in from left
  const headerX = interpolate(
    spring({ frame, fps, config: { damping: 20, stiffness: 90 } }),
    [0, 1], [-30, 0],
  );
  const headerOp = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: 'clamp' });

  // Citation block slides up
  const citeProgress = spring({
    frame: Math.max(0, frame - 14), fps,
    config: { damping: 22, stiffness: 80 },
  });
  const citeY  = interpolate(citeProgress, [0, 1], [28, 0]);
  const citeOp = interpolate(frame, [14, 34], [0, 1], { extrapolateRight: 'clamp' });

  // Checkmark draws in
  const checkScale = spring({
    frame: Math.max(0, frame - 44), fps,
    config: { damping: 12, stiffness: 200 },
  });
  const checkOp = interpolate(frame, [44, 56], [0, 1], { extrapolateRight: 'clamp' });

  // "Exported to clipboard" label
  const exportedOp = interpolate(frame, [54, 68], [0, 1], { extrapolateRight: 'clamp' });

  // Scene fades out
  const sceneOut = interpolate(frame, [108, 120], [1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{
      background: C.bg,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: FONT,
      opacity: Math.min(sceneOp, sceneOut),
    }}>

      {/* Header */}
      <div style={{
        opacity: headerOp,
        transform: `translateX(${headerX}px)`,
        marginBottom: 28,
        textAlign: 'center',
      }}>
        <div style={{
          fontSize: 14,
          fontWeight: 700,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: C.muted,
          marginBottom: 8,
        }}>
          Publication-ready export
        </div>
        <div style={{
          fontSize: 13,
          color: C.muted,
        }}>
          APA inline citation · Results table · Effect size summary
        </div>
      </div>

      {/* Citation card */}
      <div style={{
        opacity: citeOp,
        transform: `translateY(${citeY}px)`,
        width: 720,
        border: `1px solid ${C.border}`,
        borderRadius: 10,
        overflow: 'hidden',
        boxShadow: '0 4px 24px rgba(0,0,0,0.07)',
      }}>
        {/* Card header */}
        <div style={{
          background: C.accent,
          padding: '10px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: '#fff', letterSpacing: '0.04em' }}>
            TASS EXPORT REPORT
          </span>
          <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)' }}>
            anxiety · positivity · anger
          </span>
        </div>

        {/* Citation body */}
        <div style={{
          background: '#FAFAFA',
          padding: '20px 24px',
          fontFamily: '"Courier New", Courier, monospace',
          fontSize: 13,
          lineHeight: 1.7,
          color: C.text,
        }}>
          <div style={{ marginBottom: 16, color: C.muted, fontSize: 12, letterSpacing: '0.05em', fontFamily: FONT, fontWeight: 700, textTransform: 'uppercase' }}>
            Results Summary
          </div>
          <div>Variable: <span style={{ fontWeight: 700 }}>Anxiety</span></div>
          <div style={{ paddingLeft: 20 }}>
            <div>Treatment (n = 423):  M = 0.42, SD = 0.18</div>
            <div>Control &nbsp; (n = 424):  M = 0.31, SD = 0.16</div>
          </div>
          <div style={{ marginTop: 10, padding: '10px 14px', background: C.accentL, borderRadius: 6, borderLeft: `3px solid ${C.accent}` }}>
            t(845) = 4.32, p &lt; .001, Cohen's d = 0.30 [95% CI: 0.21, 0.40]
          </div>
          <div style={{ marginTop: 12, fontSize: 12, color: C.muted }}>
            APA: Treatment group showed significantly higher anxiety scores
            than controls, t(845) = 4.32, p &lt; .001, d = 0.30.
          </div>
        </div>
      </div>

      {/* Checkmark + status row */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        marginTop: 24,
      }}>
        <div style={{
          opacity: checkOp,
          transform: `scale(${checkScale})`,
          width: 32,
          height: 32,
          borderRadius: '50%',
          background: C.accent,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          {/* Checkmark SVG */}
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M3 8l3.5 3.5L13 5" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div style={{
          opacity: exportedOp,
          fontSize: 14,
          fontWeight: 600,
          color: C.accent,
        }}>
          Exported to CSV, DOCX, and clipboard
        </div>
      </div>

      {/* Annotation */}
      <div style={{
        position: 'absolute',
        bottom: 20,
        left: 0, right: 0,
        textAlign: 'center',
        fontSize: 11,
        color: C.muted,
        fontStyle: 'italic',
        fontFamily: FONT,
      }}>
        {ANNOTATION}
      </div>
    </AbsoluteFill>
  );
};
