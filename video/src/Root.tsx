import React from 'react';
import { Composition } from 'remotion';
import { TassDemo } from './TassDemo';
import { FPS, TOTAL_FRAMES, W, H } from './tokens';

export const Root: React.FC = () => (
  <Composition
    id="TassDemo"
    component={TassDemo}
    durationInFrames={TOTAL_FRAMES}
    fps={FPS}
    width={W}
    height={H}
  />
);
