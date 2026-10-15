import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {AltamiraVideo} from './video';

const Root = () => (
  <>
    <Composition id="Altamira2026" component={AltamiraVideo} durationInFrames={1800} fps={30} width={1920} height={1080} defaultProps={{testMode: false}} />
    <Composition id="AltamiraTeste" component={AltamiraVideo} durationInFrames={180} fps={30} width={1920} height={1080} defaultProps={{testMode: true}} />
  </>
);

registerRoot(Root);
