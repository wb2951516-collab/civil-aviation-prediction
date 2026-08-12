import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { interFont, notoSansSC } from "../fonts";
import { theme } from "../theme";

export const SubtitleBar: React.FC<{
  cn: string;
  en: string;
  delay?: number;
}> = ({ cn, en, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const adjustedFrame = Math.max(0, frame - delay * fps);
  
  const opacity = interpolate(adjustedFrame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });
  
  const yOffset = interpolate(adjustedFrame, [0, 20], [30, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: 60,
        left: "5%",
        right: "5%",
        backgroundColor: "rgba(26, 31, 46, 0.95)",
        padding: "20px 30px",
        borderRadius: 8,
        border: `1px solid ${theme.colors.muted}`,
        opacity,
        transform: `translateY(${yOffset}px)`,
      }}
    >
      <p
        style={{
          fontFamily: notoSansSC,
          fontSize: 20,
          fontWeight: "700",
          color: theme.colors.text,
          margin: "0 0 8px 0",
          textAlign: "center",
        }}
      >
        {cn}
      </p>
      <p
        style={{
          fontFamily: interFont,
          fontSize: 16,
          fontWeight: "400",
          color: theme.colors.muted,
          margin: 0,
          textAlign: "center",
        }}
      >
        {en}
      </p>
    </div>
  );
};
