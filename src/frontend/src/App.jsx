import React, { useState } from 'react';
import { BabylonScene } from './components/BabylonScene.jsx';
import { PolyhedraLibrary } from './components/PolyhedraLibrary.jsx';
import { AttachmentValidator } from './components/AttachmentValidator.jsx';
import './App.css';

function App() {
  const [selectedPolyhedra, setSelectedPolyhedra] = useState([]);
  const [selectedAttachment, setSelectedAttachment] = useState(null);

  const handleSelectPolyhedron = (poly) => {
    setSelectedPolyhedra([...selectedPolyhedra, poly]);
  };

  const handleSelectAttachment = (option) => {
    setSelectedAttachment(option);
    // Apply attachment to workspace
    console.log('Selected attachment:', option);
  };

  const getLastTwoPolyhedra = () => {
    const len = selectedPolyhedra.length;
    if (len < 2) return { a: null, b: null };
    return {
      a: selectedPolyhedra[len - 2]?.symbol,
      b: selectedPolyhedra[len - 1]?.symbol
    };
  };

  const { a: polygonA, b: polygonB } = getLastTwoPolyhedra();

  return (
    <div className="app">
      <div className="app-header">
        <h1>Polylog6 - Polyform Visualizer</h1>
        <div className="app-subtitle">Interactive 3D Polyform Design & Generation</div>
      </div>

      <div className="app-layout">
        <div className="app-sidebar-left">
          <PolyhedraLibrary onSelect={handleSelectPolyhedron} />
        </div>

        <div className="app-main">
          <BabylonScene 
            selectedPolyhedra={selectedPolyhedra}
            selectedAttachment={selectedAttachment}
          />
        </div>

        <div className="app-sidebar-right">
          <AttachmentValidator
            polygonA={polygonA}
            polygonB={polygonB}
            onSelect={handleSelectAttachment}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
