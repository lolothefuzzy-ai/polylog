import React, { useEffect, useRef } from 'react';
import * as BABYLON from '@babylonjs/core';
import { BabylonScene } from './components/BabylonScene';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Polylog6 Research Simulator</h1>
      </header>
      <main className="App-main">
        <BabylonScene />
      </main>
    </div>
  );
}

export default App;
