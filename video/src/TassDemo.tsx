import React from 'react';
import { AbsoluteFill, Sequence } from 'remotion';
import { SEQ } from './tokens';
import { Intro }        from './scenes/Intro';
import { ImportScene }  from './scenes/ImportScene';
import { AnalysisScene } from './scenes/AnalysisScene';
import { ExportCard }   from './scenes/ExportCard';
import { EndCard }      from './scenes/EndCard';

export const TassDemo: React.FC = () => (
  <AbsoluteFill>
    <Sequence from={SEQ.intro.from}    durationInFrames={SEQ.intro.duration}>
      <Intro />
    </Sequence>
    <Sequence from={SEQ.import.from}   durationInFrames={SEQ.import.duration}>
      <ImportScene />
    </Sequence>
    <Sequence from={SEQ.analysis.from} durationInFrames={SEQ.analysis.duration}>
      <AnalysisScene />
    </Sequence>
    <Sequence from={SEQ.export.from}   durationInFrames={SEQ.export.duration}>
      <ExportCard />
    </Sequence>
    <Sequence from={SEQ.endCard.from}  durationInFrames={SEQ.endCard.duration}>
      <EndCard />
    </Sequence>
  </AbsoluteFill>
);
