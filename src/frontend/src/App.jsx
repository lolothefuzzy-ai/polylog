import React, { useState } from 'react';
import { BabylonScene } from './components/BabylonScene.jsx';
import { PolyhedraLibrary } from './components/PolyhedraLibrary.jsx';
import { PolygonSlider } from './components/PolygonSlider.jsx';
import { AttachmentValidator } from './components/AttachmentValidator.jsx';
import { PolyformGenerator } from './components/PolyformGenerator.jsx';
import { Tier0Display } from './components/Tier0Display.jsx';
import './App.css';

function App() {
  const [selectedPolyhedra, setSelectedPolyhedra] = useState([]);
  const [selectedAttachment, setSelectedAttachment] = useState(null);
  const [generatedPolyforms, setGeneratedPolyforms] = useState([]);
  const [warmupComplete, setWarmupComplete] = useState(false);
  const [babylonScene, setBabylonScene] = useState(null);
  
  // Warmup: Only enable advanced features after 3+ polygons
  const canShowAdvancedFeatures = selectedPolyhedra.length >= 3;

  const handleSelectPolyhedron = (poly) => {
    setSelectedPolyhedra([...selectedPolyhedra, poly]);
  };

  const handleSelectAttachment = (option) => {
    setSelectedAttachment(option);
    // Apply attachment to workspace
    console.log('Selected attachment:', option);
  };

  const handlePolyformGenerated = (polyform) => {
    setGeneratedPolyforms(prev => [...prev, polyform]);
    // Add generated polyform to selected list for visualization
    setSelectedPolyhedra(prev => [...prev, {
      symbol: polyform.symbol || polyform.unicode,
      name: `Generated: ${polyform.composition}`,
      classification: 'generated',
      geometry: polyform.geometry,
      ...polyform.metadata
    }]);
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
                  {selectedPolyhedra.length < 3 ? (
                    <PolygonSlider onSelect={handleSelectPolyhedron} />
                  ) : (
                    <PolyhedraLibrary onSelect={handleSelectPolyhedron} />
                  )}
                </div>

        <div className="app-main">
          <BabylonScene 
            selectedPolyhedra={selectedPolyhedra}
            selectedAttachment={selectedAttachment}
            onPolygonAttached={(attachment) => {
              console.log('Polygons attached:', attachment);
              // Could trigger generation or update UI here
            }}
            onSceneReady={(scene) => {
              setBabylonScene(scene);
            }}
          />
        </div>

                <div className="app-sidebar-right">
                  {canShowAdvancedFeatures ? (
                    <>
                      <Tier0Display scene={babylonScene} />
                      <AttachmentValidator
                        polygonA={polygonA}
                        polygonB={polygonB}
                        onSelect={handleSelectAttachment}
                      />
                      <PolyformGenerator
                        selectedPolyhedra={selectedPolyhedra}
                        onPolyformGenerated={handlePolyformGenerated}
                      />
                    </>
                  ) : (
                    <div className="warmup-message">
                      <h3>Building Polyform Net</h3>
                      <p>Add {3 - selectedPolyhedra.length} more polygon{3 - selectedPolyhedra.length !== 1 ? 's' : ''} to enable:</p>
                      <ul>
                        <li>Fold angle calculation</li>
                        <li>3D net closure detection</li>
                        <li>Polyform generation</li>
                        <li>Tier 0 symbol display</li>
                      </ul>
                      <div className="polygon-count">
                        Current: {selectedPolyhedra.length} / 3+
                      </div>
                    </div>
                  )}
                </div>
      </div>
    </div>
  );
}

export default App;
