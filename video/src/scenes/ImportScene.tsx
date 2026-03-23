import React from 'react';
import {
  AbsoluteFill, interpolate, spring,
  useCurrentFrame, useVideoConfig,
} from 'remotion';
import { C, FONT, ANNOTATION } from '../tokens';

const ROWS = [
  { id: '001', text: 'The policy was clearly outlined by officials…',   group: 'Treatment' },
  { id: '002', text: 'No comment was made by the administration…',       group: 'Control'   },
  { id: '003', text: 'A sweeping reform passed with bipartisan support…', group: 'Treatment' },
  { id: '004', text: 'The announcement drew immediate criticism…',        group: 'Control'   },
  { id: '005', text: 'Critics argue the measure falls short…',            group: 'Treatment' },
  { id: '006', text: 'In response to public pressure, officials said…',   group: 'Control'   },
  { id: '007', text: 'The committee voted 8–4 in favor of the bill…',     group: 'Treatment' },
  { id: '008', text: 'Local officials expressed concerns over funding…',  group: 'Control'   },
];

const ROW_DELAY = 18; // frames between each row appearing
const ROW_START = 22; // frame at which first row begins

export const ImportScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Window fades in
  const windowOp = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: 'clamp' });
  const windowY  = interpolate(
    spring({ frame, fps, config: { damping: 20, stiffness: 90 } }),
    [0, 1], [24, 0],
  );

  // Status bar (last 30 frames of scene)
  const lastRowEnd = ROW_START + ROWS.length * ROW_DELAY + 10;
  const statusOp = interpolate(frame, [lastRowEnd, lastRowEnd + 15], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const statusText = frame >= lastRowEnd ? '847 entries loaded · 2 groups detected' : 'Importing…';

  // Scene fade-in and fade-out
  const sceneOp = interpolate(frame, [228, 240], [1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  const ROW_H = 36;
  const colWidths = { id: 52, text: 460, group: 110 };

  const headerStyle: React.CSSProperties = {
    fontSize: 11,
    fontWeight: 700,
    color: C.muted,
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
  };

  return (
    <AbsoluteFill style={{
      background: C.bg,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: FONT,
      opacity: sceneOp,
    }}>

      {/* Mock application window */}
      <div style={{
        width: 860,
        borderRadius: 10,
        border: `1px solid ${C.border}`,
        boxShadow: '0 8px 40px rgba(0,0,0,0.12)',
        overflow: 'hidden',
        opacity: windowOp,
        transform: `translateY(${windowY}px)`,
      }}>

        {/* Title bar — Windows 11 style */}
        <div style={{
          background: '#F3F3F3',
          borderBottom: `1px solid ${C.border}`,
          height: 32,
          display: 'flex',
          alignItems: 'center',
          paddingLeft: 12,
          userSelect: 'none',
        }}>
          {/* App icon */}
          <div style={{
            width: 16, height: 16, borderRadius: 3,
            background: C.accent,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginRight: 8, flexShrink: 0,
          }}>
            <span style={{ color: 'white', fontSize: 9, fontWeight: 800 }}>T</span>
          </div>
          {/* Title */}
          <span style={{ fontSize: 12, fontWeight: 400, color: '#1A1A1A', flex: 1 }}>
            TASS — Text Analysis Support Software
          </span>
          {/* Window controls */}
          {['—', '□', '✕'].map((btn) => (
            <div key={btn} style={{
              width: 46, height: 32,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 13, color: '#444',
            }}>
              {btn}
            </div>
          ))}
        </div>

        {/* Toolbar */}
        <div style={{
          background: C.surface,
          borderBottom: `1px solid ${C.border}`,
          padding: '6px 16px',
          display: 'flex',
          gap: 4,
        }}>
          {['File', 'Import', 'Analyze', 'Export', 'Help'].map((item, i) => (
            <div key={item} style={{
              padding: '4px 12px',
              fontSize: 13,
              fontWeight: i === 1 ? 600 : 400,
              color: i === 1 ? C.accent : C.text,
              background: i === 1 ? C.accentL : 'transparent',
              borderRadius: 4,
              cursor: 'default',
            }}>
              {item}
            </div>
          ))}
          <div style={{
            marginLeft: 'auto',
            fontSize: 12,
            color: C.muted,
            padding: '4px 0',
            opacity: statusOp,
          }}>
            {statusText}
          </div>
        </div>

        {/* Table */}
        <div style={{ background: C.bg }}>
          {/* Header */}
          <div style={{
            display: 'flex',
            padding: '8px 16px',
            background: C.surface,
            borderBottom: `1px solid ${C.border}`,
            gap: 0,
          }}>
            <div style={{ ...headerStyle, width: colWidths.id }}>ID</div>
            <div style={{ ...headerStyle, flex: 1 }}>Text</div>
            <div style={{ ...headerStyle, width: colWidths.group, textAlign: 'right' }}>Group</div>
          </div>

          {/* Rows */}
          {ROWS.map((row, i) => {
            const rowFrame = Math.max(0, frame - (ROW_START + i * ROW_DELAY));
            const rowOp = interpolate(rowFrame, [0, 10], [0, 1], { extrapolateRight: 'clamp' });
            const rowX  = interpolate(
              spring({ frame: rowFrame, fps, config: { damping: 22, stiffness: 140 } }),
              [0, 1], [-16, 0],
            );

            const isEven = i % 2 === 0;
            const isControl = row.group === 'Control';

            return (
              <div key={row.id} style={{
                display: 'flex',
                alignItems: 'center',
                padding: `0 16px`,
                height: ROW_H,
                background: isEven ? C.bg : C.surface,
                borderBottom: `1px solid ${C.border}`,
                opacity: rowOp,
                transform: `translateX(${rowX}px)`,
              }}>
                <div style={{ width: colWidths.id, fontSize: 12, color: C.muted, fontWeight: 500 }}>
                  {row.id}
                </div>
                <div style={{ flex: 1, fontSize: 13, color: C.text, overflow: 'hidden', whiteSpace: 'nowrap' }}>
                  {row.text}
                </div>
                <div style={{ width: colWidths.group, textAlign: 'right' }}>
                  <span style={{
                    display: 'inline-block',
                    padding: '2px 8px',
                    borderRadius: 4,
                    fontSize: 11,
                    fontWeight: 600,
                    background: isControl ? '#EFF6FF' : C.accentL,
                    color: isControl ? '#1D4ED8' : C.accent,
                  }}>
                    {row.group}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Status bar — Windows style */}
        <div style={{
          background: C.surface,
          borderTop: `1px solid ${C.border}`,
          padding: '5px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
        }}>
          <div style={{
            width: 7, height: 7, borderRadius: '50%',
            background: frame >= lastRowEnd ? '#22C55E' : '#F59E0B',
          }} />
          <div style={{
            fontSize: 12,
            color: C.muted,
            fontWeight: 500,
          }}>
            {frame >= lastRowEnd
              ? '847 entries loaded · 2 groups detected · Ready to analyze'
              : `Loading… ${Math.min(ROWS.length, Math.floor((frame - ROW_START) / ROW_DELAY) + 1)} of 847`}
          </div>
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
