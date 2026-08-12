import React from "react";
import { useCurrentFrame } from "remotion";
import { theme } from "../../theme";

export const LinearSurface: React.FC = () => {
  const frame = useCurrentFrame();

  const rotationY = frame * 0.015;
  const elevation = 25 + Math.sin(frame * 0.02) * 10;

  return (
    <group rotation={[elevation * 0.017, rotationY, 0]}>
      <mesh>
        <planeGeometry args={[6, 6, 32, 32]} />
        <meshStandardMaterial
          color={theme.colors.linear}
          roughness={0.4}
          metalness={0.3}
          side={2}
        />
      </mesh>
    </group>
  );
};
