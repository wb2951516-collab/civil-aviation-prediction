import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { interFont, notoSansSC } from "../fonts";
import { theme } from "../theme";

export const BilingualTitle: React.FC<{
  cn: string;
  en: string;
  delay?: number;
}> = ({ cn, en, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const adjustedFrame = Math.max(0, frame - delay * fps);
  
  const opacity = interpolate(adjustedFrame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });
  
  const yOffset = interpolate(adjustedFrame, [0, 30], [50, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 80,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        opacity,
        transform: `translateY(${yOffset}px)`,
      }}
    >
      <h1
        style={{
          fontFamily: notoSansSC,
          fontSize: 56,
          fontWeight: "700",
          color: theme.colors.text,
          margin: 0,
          textAlign: "center",
        }}
      >
        {cn}
      </h1>
      <h2
        style={{
          fontFamily: interFont,
          fontSize: 28,
          fontWeight: "400",
          color: theme.colors.muted,
          margin: "8px 0 0 0",
          textAlign: "center",
        }}
      >
        {en}
      </h2>
    </div>
  );
};
