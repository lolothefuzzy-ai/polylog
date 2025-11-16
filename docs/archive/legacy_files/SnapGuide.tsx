import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { useThree, useFrame } from '@react-three/fiber';
import { SnapGuide as SnapGuideType } from '@/lib/attachmentResolver';

interface SnapGuideProps {
  snapGuide: SnapGuideType | null;
}

export default function SnapGuide({ snapGuide }: SnapGuideProps) {
  const { scene } = useThree();
  const guideRef = useRef<THREE.Group | null>(null);
  const pulseRef = useRef(0);
  
  useEffect(() => {
    if (!snapGuide) {
      // Remove guide if it exists
      if (guideRef.current) {
        scene.remove(guideRef.current);
        guideRef.current = null;
      }
      return;
    }
    
    // Create snap guide visualization
    const group = new THREE.Group();
    
    // Create line between edge midpoints
    const lineGeometry = new THREE.BufferGeometry().setFromPoints([
      snapGuide.sourceEdge.midpoint,
      snapGuide.targetEdge.midpoint,
    ]);
    
    const lineMaterial = new THREE.LineDashedMaterial({
      color: snapGuide.isValid ? 0x00ff00 : 0xffff00,
      linewidth: 2,
      dashSize: 0.1,
      gapSize: 0.05,
      transparent: true,
      opacity: 0.8,
    });
    
    const line = new THREE.Line(lineGeometry, lineMaterial);
    line.computeLineDistances();
    group.add(line);
    
    // Create highlight for target edge
    const targetEdgeGeometry = new THREE.BufferGeometry().setFromPoints([
      snapGuide.targetEdge.start,
      snapGuide.targetEdge.end,
    ]);
    
    const targetEdgeMaterial = new THREE.LineBasicMaterial({
      color: snapGuide.isValid ? 0x00ff00 : 0xffff00,
      linewidth: 4,
      transparent: true,
      opacity: 0.9,
    });
    
    const targetEdgeLine = new THREE.Line(targetEdgeGeometry, targetEdgeMaterial);
    group.add(targetEdgeLine);
    
    // Create snap point indicator
    const snapPointGeometry = new THREE.SphereGeometry(0.1, 16, 16);
    const snapPointMaterial = new THREE.MeshBasicMaterial({
      color: snapGuide.isValid ? 0x00ff00 : 0xffff00,
      transparent: true,
      opacity: 0.7,
    });
    
    const snapPoint = new THREE.Mesh(snapPointGeometry, snapPointMaterial);
    snapPoint.position.copy(snapGuide.snapPosition);
    group.add(snapPoint);
    
    // Add to scene
    scene.add(group);
    guideRef.current = group;
    
    return () => {
      if (guideRef.current) {
        scene.remove(guideRef.current);
        guideRef.current = null;
      }
    };
  }, [snapGuide, scene]);
  
  // Animate pulse effect
  useFrame((state) => {
    if (!guideRef.current || !snapGuide) return;
    
    pulseRef.current += 0.05;
    const pulse = Math.sin(pulseRef.current) * 0.3 + 0.7;
    
    guideRef.current.children.forEach((child) => {
      if (child instanceof THREE.Mesh || child instanceof THREE.Line) {
        const material = child.material as THREE.Material & { opacity?: number };
        if (material.opacity !== undefined) {
          material.opacity = pulse;
        }
      }
    });
  });
  
  return null;
}
