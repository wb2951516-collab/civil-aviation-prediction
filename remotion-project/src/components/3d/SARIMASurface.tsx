import React from "react";
import { useCurrentFrame } from "remotion";
import { theme } from "../../theme";

export const SARIMASurface: React.FC = () => {
  const frame = useCurrentFrame();

  const rotationY = frame * 0.018;
  const elevation = 25 + Math.sin(frame * 0.025) * 12;

  return (
    <group rotation={[elevation * 0.017, rotationY, 0]}>
      <mesh>
        <icosahedronGeometry args={[2, 1]} />
        <meshStandardMaterial
          color={theme.colors.sarima}
          roughness={0.2}
          metalness={0.6}
          flatShading
        />
      </mesh>
    </group>
  );
};
