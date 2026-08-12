import React from "react";
import { useCurrentFrame } from "remotion";
import { theme } from "../../theme";

export const EnsembleSurfaces: React.FC = () => {
  const frame = useCurrentFrame();

  const rotationY = frame * 0.01;
  const elevation = 25 + Math.sin(frame * 0.018) * 10;

  return (
    <group rotation={[elevation * 0.017, rotationY, 0]}>
      <mesh position={[0, 0, -1.5]}>
        <octahedronGeometry args={[1.2, 0]} />
        <meshStandardMaterial
          color={theme.colors.linear}
          roughness={0.5}
          metalness={0.2}
          transparent
          opacity={0.8}
        />
      </mesh>
      
      <mesh position={[-1.5, 0, 0.5]}>
        <dodecahedronGeometry args={[1.2, 0]} />
        <meshStandardMaterial
          color={theme.colors.holtWinters}
          roughness={0.4}
          metalness={0.3}
          transparent
          opacity={0.7}
        />
      </mesh>
      
      <mesh position={[1.5, 0, 0.5]}>
        <icosahedronGeometry args={[1.2, 0]} />
        <meshStandardMaterial
          color={theme.colors.sarima}
          roughness={0.3}
          metalness={0.4}
          transparent
          opacity={0.6}
        />
      </mesh>
      
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[1.8, 32, 32]} />
        <meshStandardMaterial
          color={theme.colors.ensemble}
          roughness={0.3}
          metalness={0.5}
          emissive={theme.colors.ensemble}
          emissiveIntensity={0.2}
        />
      </mesh>
    </group>
  );
};
