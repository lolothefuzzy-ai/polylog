import { Card } from '@/components/ui/card';
import { getAllPolygonTypes } from '@/lib/polygonGeometry';
import { getAllUniquePolygons, getSeriesFromSides, generateSingleSymbol, getPolygonName } from '@/lib/polygonSymbolsV2';
import { useState } from 'react';

interface PolygonPaletteProps {
  onSelectPolygon: (sides: number) => void;
  selectedSides: number | null;
}

export default function PolygonPalette({ onSelectPolygon, selectedSides }: PolygonPaletteProps) {
  const polygonTypes = getAllPolygonTypes();

  return (
    <div className="h-full overflow-y-auto bg-card border-r border-border">
      <div className="p-4 border-b border-border sticky top-0 bg-card z-10">
        <h2 className="text-lg font-semibold text-foreground">Polygon Library</h2>
        <p className="text-sm text-muted-foreground mt-1">
          18 primitive polygons (3-20 sides)
        </p>
      </div>
      
      <div className="p-4 space-y-2">
        {polygonTypes.map((sides) => (
          <PolygonCard
            key={sides}
            sides={sides}
            isSelected={selectedSides === sides}
            onClick={() => onSelectPolygon(sides)}
          />
        ))}
      </div>
    </div>
  );
}

interface PolygonCardProps {
  sides: number;
  isSelected: boolean;
  onClick: () => void;
}

function PolygonCard({ sides, isSelected, onClick }: PolygonCardProps) {
  const name = getPolygonName(sides);
  
  return (
    <Card
      className={`p-3 cursor-pointer transition-all hover:shadow-md ${
        isSelected
          ? 'bg-primary text-primary-foreground ring-2 ring-primary'
          : 'bg-card text-card-foreground hover:bg-accent hover:text-accent-foreground'
      }`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg">{getSeriesFromSides(sides).length > 0 ? generateSingleSymbol(getSeriesFromSides(sides)[0].series, getSeriesFromSides(sides)[0].subscript) : '?'}</span>
            <span className="font-medium">{name}</span>
          </div>
          <div className={`text-xs ${isSelected ? 'text-primary-foreground/80' : 'text-muted-foreground'}`}>
            {sides} sides
          </div>
        </div>
        <div className="w-12 h-12 flex items-center justify-center">
          <PolygonPreview sides={sides} />
        </div>
      </div>
    </Card>
  );
}

function PolygonPreview({ sides }: { sides: number }) {
  // Generate SVG polygon points
  const radius = 20;
  const centerX = 24;
  const centerY = 24;
  const startAngle = -Math.PI / 2;
  
  const points = Array.from({ length: sides }, (_, i) => {
    const angle = startAngle + (i * 2 * Math.PI) / sides;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);
    return `${x},${y}`;
  }).join(' ');
  
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" className="opacity-80">
      <polygon
        points={points}
        fill="currentColor"
        stroke="currentColor"
        strokeWidth="1.5"
        opacity="0.6"
      />
    </svg>
  );
}
