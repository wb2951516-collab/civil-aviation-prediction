import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { BilingualTitle } from "../BilingualTitle";
import { SubtitleBar } from "../SubtitleBar";
import { interFont, notoSansSC } from "../../fonts";
import { theme } from "../../theme";

export const IntroScene: React.FC = () => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });

  const scale = interpolate(frame, [0, 30], [0.8, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.background }}>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          opacity,
          transform: `scale(${scale})`,
        }}
      >
        <h1
          style={{
            fontFamily: notoSansSC,
            fontSize: 72,
            fontWeight: "700",
            color: theme.colors.text,
            margin: 0,
            textAlign: "center",
          }}
        >
          民航旅客运输量预测模型
        </h1>
        <h2
          style={{
            fontFamily: interFont,
            fontSize: 36,
            fontWeight: "400",
            color: theme.colors.muted,
            margin: "16px 0 0 0",
            textAlign: "center",
          }}
        >
          Civil Aviation Passenger Traffic Prediction Model
        </h2>
        <h3
          style={{
            fontFamily: notoSansSC,
            fontSize: 28,
            fontWeight: "400",
            color: theme.colors.accent,
            margin: "32px 0 0 0",
            textAlign: "center",
          }}
        >
          3D 科学演示视频
        </h3>
        <h4
          style={{
            fontFamily: interFont,
            fontSize: 22,
            fontWeight: "400",
            color: theme.colors.muted,
            margin: "8px 0 0 0",
            textAlign: "center",
          }}
        >
          3D Scientific Demonstration
        </h4>
      </div>
    </AbsoluteFill>
  );
};
