import React from "react";
import { useCurrentFrame } from "remotion";
import { theme } from "../../theme";

export const HoltWintersSurface: React.FC = () => {
  const frame = useCurrentFrame();

  const rotationY = frame * 0.012;
  const elevation = 25 + Math.sin(frame * 0.015) * 8;

  return (
    <group rotation={[elevation * 0.017, rotationY, 0]}>
      <mesh>
        <torusKnotGeometry args={[1.5, 0.5, 128, 32]} />
        <meshStandardMaterial
          color={theme.colors.holtWinters}
          roughness={0.3}
          metalness={0.4}
        />
      </mesh>
    </group>
  );
};
