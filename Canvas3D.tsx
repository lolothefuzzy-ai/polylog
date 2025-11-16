import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

interface Canvas3DProps {
  children?: React.ReactNode;
}

export default function Canvas3D({ children }: Canvas3DProps) {
  return (
    <div className="w-full h-full">
      <Canvas
        camera={{
          position: [5, 5, 5],
          fov: 50,
        }}
        gl={{
          antialias: true,
        }}
      >
        {/* Lighting */}
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <directionalLight position={[-10, -10, -5]} intensity={0.3} />
        
        {/* Grid */}
        <gridHelper args={[20, 20, '#6366f1', '#8b5cf6']} />
        
        {/* Content */}
        {children}
        
        {/* Controls */}
        <OrbitControls
          enableDamping
          dampingFactor={0.05}
          minDistance={2}
          maxDistance={50}
        />
      </Canvas>
    </div>
  );
}
