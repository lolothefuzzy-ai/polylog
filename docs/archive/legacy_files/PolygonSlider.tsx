/**
 * Polygon Range Slider (3-20 sides)
 * 
 * References fixed Unicode library for polygon instantiation
 */

import { useState } from 'react';
import { Slider } from '@/components/ui/slider';
import { getSeriesFromSides, generateSingleSymbol } from '@/lib/polygonSymbolsV2';

interface PolygonSliderProps {
  onPolygonSelect: (sides: number) => void;
}

export default function PolygonSlider({ onPolygonSelect }: PolygonSliderProps) {
  const [sides, setSides] = useState(3);

  const handleSliderChange = (value: number[]) => {
    const newSides = value[0];
    setSides(newSides);
    onPolygonSelect(newSides);
  };

  const matches = getSeriesFromSides(sides);
  const symbol = matches.length > 0 ? generateSingleSymbol(matches[0].series, matches[0].subscript) : `?${sides}`;
  const polygonName = getPolygonName(sides);

  return (
    <div className="w-full space-y-4 p-4 bg-card rounded-lg border">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Polygon Selector</h3>
          <p className="text-sm text-muted-foreground">Select polygon sides (3-20)</p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-primary">{symbol}</div>
          <div className="text-sm text-muted-foreground">{sides} sides</div>
        </div>
      </div>

      <Slider
        value={[sides]}
        onValueChange={handleSliderChange}
        min={3}
        max={20}
        step={1}
        className="w-full"
      />

      <div className="text-center">
        <div className="text-lg font-medium">{polygonName}</div>
        <div className="text-xs text-muted-foreground mt-1">
          Unicode: {symbol} • Unit edge length: 1.00
        </div>
      </div>
    </div>
  );
}

function getPolygonName(sides: number): string {
  const names: Record<number, string> = {
    3: 'Triangle',
    4: 'Square',
    5: 'Pentagon',
    6: 'Hexagon',
    7: 'Heptagon',
    8: 'Octagon',
    9: 'Nonagon',
    10: 'Decagon',
    11: 'Hendecagon',
    12: 'Dodecagon',
    13: 'Tridecagon',
    14: 'Tetradecagon',
    15: 'Pentadecagon',
    16: 'Hexadecagon',
    17: 'Heptadecagon',
    18: 'Octadecagon',
    19: 'Enneadecagon',
    20: 'Icosagon'
  };
  return names[sides] || `${sides}-gon`;
}
