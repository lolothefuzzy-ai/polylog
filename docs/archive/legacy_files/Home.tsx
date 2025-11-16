 * Polylog Visualizer - Home Page
 * Foundation milestone: Babylon.js + Polygon Slider + Drag-Drop
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { APP_TITLE } from '@/const';
import BabylonWorkspace from '@/components/BabylonWorkspace';
import PolygonSlider from '@/components/PolygonSlider';

export default function Home() {
  const [selectedPolygonSides, setSelectedPolygonSides] = useState<number | null>(3);  // Default to triangle
  const [polygonCount, setPolygonCount] = useState(0);
  const [openEdges, setOpenEdges] = useState(0);

  const handlePolygonSelect = (sides: number) => {
    setSelectedPolygonSides(sides);
  };

  const [placeTrigger, setPlaceTrigger] = useState(0);

  const handlePlaceClick = () => {
    if (!selectedPolygonSides) return;
    setPolygonCount(prev => prev + 1);
    setOpenEdges(prev => prev + selectedPolygonSides);
    setPlaceTrigger(prev => prev + 1);  // Trigger re-render in BabylonWorkspace
  };

  const handleClearAll = () => {
    setPolygonCount(0);
    setOpenEdges(0);
    window.location.reload();  // Temporary: will implement proper scene clearing
  };

  const closure = polygonCount > 0 ? Math.max(0, 100 - (openEdges / polygonCount) * 10) : 100;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-primary">{APP_TITLE}</h1>
            <p className="text-sm text-muted-foreground">
              Foundation: Babylon.js + Polygon Slider + Drag-Drop
            </p>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="text-right">
              <div className="text-xs text-muted-foreground">Polygons</div>
              <div className="text-lg font-bold">{polygonCount}</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-muted-foreground">Open Edges</div>
              <div className="text-lg font-bold text-orange-600">{openEdges}</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-muted-foreground">Closure</div>
              <div className="text-lg font-bold text-green-600">{closure.toFixed(0)}%</div>
            </div>
            <Button
              variant="outline"
              onClick={handleClearAll}
              disabled={polygonCount === 0}
            >
              Clear All
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Left Sidebar: Polygon Slider */}
        <aside className="w-80 border-r bg-card/30 p-4 overflow-y-auto">
          <PolygonSlider onPolygonSelect={handlePolygonSelect} />
          
          {selectedPolygonSides && (