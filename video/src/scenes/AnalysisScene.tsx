import React from 'react';
import {
  AbsoluteFill, interpolate, spring,
  useCurrentFrame, useVideoConfig,
} from 'remotion';
import { C, FONT, ANNOTATION } from '../tokens';

interface BarGroupProps {
  label: string;
  valA: number;
  valB: number;
  frame: number;
  fps: number;
  delay: number;
  maxH: number;
}

const BarGroup: React.FC<BarGroupProps> = ({ label, valA, valB, frame, fps, delay, maxH }) => {
  const f = Math.max(0, frame - delay);

  const scaleA = spring({ frame: f, fps, config: { damping: 18, stiffness: 70 } });
  const scaleB = spring({ frame: Math.max(0, f - 6), fps, config: { damping: 18, stiffness: 70 } });

  const hA = valA * maxH * scaleA;
  const hB = valB * maxH * scaleB;

  const barW = 52;
  const gap  = 8;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
      {/* Value labels */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-end',
        gap: gap,
        height: maxH,
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end', height: '100%' }}>
          <div style={{
            fontSize: 13,
            fontWeight: 700,
            color: C.accent,
            marginBottom: 4,
            opacity: scaleA > 0.8 ? 1 : 0,
          }}>
            {valA.toFixed(2)}
          </div>
          <div style={{
            width: barW,
            height: hA,
            background: C.accent,
            borderRadius: '4px 4px 0 0',
          }} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end', height: '100%' }}>
          <div style={{
            fontSize: 13,
            fontWeight: 700,
            color: '#2D6A8F',
            marginBottom: 4,
            opacity: scaleB > 0.8 ? 1 : 0,
          }}>
            {valB.toFixed(2)}
          </div>
          <div style={{
            width: barW,
            height: hB,
            background: '#2D6A8F',
            borderRadius: '4px 4px 0 0',
          }} />
        </div>
      </div>
      {/* X-axis line */}
      <div style={{ width: barW * 2 + gap, height: 2, background: C.border }} />
      {/* Metric label */}
      <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{label}</div>
    </div>
  );
};

export const AnalysisScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Scene fade in
  const sceneOp = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });

  // Header fades in
  const headerOp = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  // Progress bar: frames 18 → 100
  const progressVal = interpolate(frame, [18, 100], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const progressPct = Math.round(progressVal * 100);

  // Progress bar fades out after completion
  const progressOp = interpolate(frame, [106, 120], [1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Chart section fades in
  const chartOp = interpolate(frame, [112, 132], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Legend fades in with charts
  const legendOp = interpolate(frame, [126, 143], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Stats card rises in
  const statsOp = interpolate(frame, [170, 188], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const statsY = interpolate(
    spring({ frame: Math.max(0, frame - 170), fps, config: { damping: 20 } }),
    [0, 1], [20, 0],
  );

  const maxH = 200;
  const CHART_DELAY = 132;

  // Scene fade-out
  const sceneOut = interpolate(frame, [228, 240], [1, 0], {
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

      {/* Section header */}
      <div style={{
        fontSize: 14,
        fontWeight: 600,
        color: C.muted,
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        marginBottom: 28,
        opacity: headerOp,
      }}>
        Analyzing: Sentiment · Anxiety · Positivity
      </div>

      {/* Progress bar block */}
      {progressOp > 0 && (
        <div style={{ opacity: progressOp, width: 560 }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: 13,
            color: C.muted,
            marginBottom: 10,
          }}>
            <span>Processing 847 texts across 12 dictionaries…</span>
            <span style={{ fontWeight: 700, color: progressVal >= 1 ? C.accent : C.text }}>
              {progressPct === 100 ? 'Complete' : `${progressPct}%`}
            </span>
          </div>
          <div style={{
            width: '100%',
            height: 10,
            background: C.border,
            borderRadius: 6,
            overflow: 'hidden',
          }}>
            <div style={{
              width: `${progressPct}%`,
              height: '100%',
              background: C.accent,
              borderRadius: 6,
              transition: 'width 0.1s linear',
            }} />
          </div>
        </div>
      )}

      {/* Bar chart section */}
      {chartOp > 0 && (
        <div style={{ opacity: chartOp }}>
          <div style={{ display: 'flex', gap: 64, alignItems: 'flex-end', justifyContent: 'center' }}>
            <BarGroup label="Anxiety"    valA={0.42} valB={0.31} frame={frame} fps={fps} delay={CHART_DELAY}      maxH={maxH} />
            <BarGroup label="Positivity" valA={0.67} valB={0.54} frame={frame} fps={fps} delay={CHART_DELAY + 8}  maxH={maxH} />
            <BarGroup label="Anger"      valA={0.28} valB={0.22} frame={frame} fps={fps} delay={CHART_DELAY + 16} maxH={maxH} />
          </div>

          {/* Legend */}
          <div style={{
            display: 'flex',
            gap: 28,
            justifyContent: 'center',
            marginTop: 20,
            opacity: legendOp,
          }}>
            {[
              { color: C.accent,  label: 'Treatment (n = 423)' },
              { color: '#2D6A8F', label: 'Control (n = 424)' },
            ].map(({ color, label }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 14, height: 14, borderRadius: 3, background: color }} />
                <span style={{ fontSize: 13, color: C.muted }}>{label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stats card */}
      {statsOp > 0 && (
        <div style={{
          marginTop: 28,
          opacity: statsOp,
          transform: `translateY(${statsY}px)`,
          padding: '16px 32px',
          background: C.accentL,
          border: `1px solid ${C.accent}`,
          borderRadius: 8,
          display: 'flex',
          gap: 40,
          alignItems: 'center',
        }}>
          {[
            { label: 't-statistic', value: 't(845) = 4.32' },
            { label: 'p-value',     value: 'p < .001' },
            { label: "Cohen's d",   value: 'd = 0.30' },
          ].map(({ label, value }) => (
            <div key={label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 22, fontWeight: 800, color: C.accent, letterSpacing: '-0.02em' }}>
                {value}
              </div>
              <div style={{ fontSize: 11, fontWeight: 600, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.08em', marginTop: 4 }}>
                {label}
              </div>
            </div>
          ))}
        </div>
      )}

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
