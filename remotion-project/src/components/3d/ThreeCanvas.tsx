import React from "react";
import { ThreeCanvas as RemotionThreeCanvas } from "@remotion/three";
import { useVideoConfig } from "remotion";
import { theme } from "../../theme";

export const ThreeCanvas: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const { width, height } = useVideoConfig();

  return (
    <RemotionThreeCanvas width={width} height={height}>
      <color attach="background" args={[theme.colors.background]} />
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} intensity={1} />
      <directionalLight position={[-5, -5, -5]} intensity={0.5} />
      {children}
    </RemotionThreeCanvas>
  );
};
