import React from "react";
import { Composition, Sequence, AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { theme } from "./theme";
import { IntroScene } from "./components/scenes/IntroScene";
import { BilingualTitle } from "./components/BilingualTitle";
import { SubtitleBar } from "./components/SubtitleBar";
import { ThreeCanvas } from "./components/3d/ThreeCanvas";
import { LinearSurface } from "./components/3d/LinearSurface";
import { HoltWintersSurface } from "./components/3d/HoltWintersSurface";
import { SARIMASurface } from "./components/3d/SARIMASurface";
import { EnsembleSurfaces } from "./components/3d/EnsembleSurfaces";
import { interFont, notoSansSC } from "./fonts";

const LinearScene: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.background }}>
      <BilingualTitle
        cn="线性回归模型"
        en="Linear Regression Model"
      />
      
      <ThreeCanvas>
        <LinearSurface />
      </ThreeCanvas>
      
      <SubtitleBar
        cn="预测值 = 截距 + 斜率 × 特征"
        en="Prediction = Intercept + Slope × Feature"
      />
    </AbsoluteFill>
  );
};

const HoltWintersScene: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.background }}>
      <BilingualTitle
        cn="Holt-Winters 指数平滑"
        en="Holt-Winters Exponential Smoothing"
      />
      
      <ThreeCanvas>
        <HoltWintersSurface />
      </ThreeCanvas>
      
      <SubtitleBar
        cn="水平 + 趋势 + 季节性"
        en="Level + Trend + Seasonality"
      />
    </AbsoluteFill>
  );
};

const SARIMAScene: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.background }}>
      <BilingualTitle
        cn="SARIMA 季节模型"
        en="SARIMA Seasonal Model"
      />
      
      <ThreeCanvas>
        <SARIMASurface />
      </ThreeCanvas>
      
      <SubtitleBar
        cn="季节性自回归综合移动平均"
        en="Seasonal AutoRegressive Integrated Moving Average"
      />
    </AbsoluteFill>
  );
};

const EnsembleScene: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.background }}>
      <BilingualTitle
        cn="模型加权融合"
        en="Weighted Ensemble Fusion"
      />
      
      <ThreeCanvas>
        <EnsembleSurfaces />
      </ThreeCanvas>
      
      <SubtitleBar
        cn="集成学习提升预测精度"
        en="Ensemble learning improves prediction accuracy"
      />
    </AbsoluteFill>
  );
};

const HolidayScene: React.FC = () => {
  const frame = useCurrentFrame();
  const visibleCount = Math.min(12, Math.floor(frame / 15) + 1);

  const months = [
    { cn: "1月", en: "Jan", effect: 1.12 },
    { cn: "2月", en: "Feb", effect: 1.15 },
    { cn: "3月", en: "Mar", effect: 1.08 },
    { cn: "4月", en: "Apr", effect: 1.0 },
    { cn: "5月", en: "May", effect: 1.0 },
    { cn: "6月", en: "Jun", effect: 1.0 },
    { cn: "7月", en: "Jul", effect: 1.10 },
    { cn: "8月", en: "Aug", effect: 1.10 },
    { cn: "9月", en: "Sep", effect: 1.0 },
    { cn: "10月", en: "Oct", effect: 1.08 },
    { cn: "11月", en: "Nov", effect: 1.0 },
    { cn: "12月", en: "Dec", effect: 1.0 },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.background }}>
      <BilingualTitle
        cn="节假日效应修正"
        en="Holiday Effect Correction"
      />
      
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: "80%",
          height: "40%",
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-around",
          padding: "0 20px",
        }}
      >
        {months.slice(0, visibleCount).map((month, i) => {
          const height = (month.effect - 0.95) * 400;
          return (
            <div
              key={i}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
              }}
            >
              <div
                style={{
                  width: 40,
                  height: height,
                  backgroundColor: theme.colors.holiday,
                  borderRadius: "4px 4px 0 0",
                  opacity: 0.9,
                }}
              />
              <p
                style={{
                  fontFamily: notoSansSC,
                  fontSize: 12,
                  color: theme.colors.muted,
                  marginTop: 8,
                  marginBottom: 0,
                }}
              >
                {month.cn}/{month.en}
              </p>
            </div>
          );
        })}
      </div>
      
      <div
        style={{
          position: "absolute",
          top: "30%",
          left: "10%",
          right: "10%",
          height: 2,
          backgroundColor: theme.colors.accent,
          opacity: 0.5,
        }}
      />
      
      <SubtitleBar
        cn="调整春运等特殊时期的预测值"
        en="Adjust predictions for special periods like Spring Festival"
      />
    </AbsoluteFill>
  );
};

const SummaryScene: React.FC = () => {
  const frame = useCurrentFrame();

  const steps = [
    { cn: "数据预处理", en: "Data Preprocessing" },
    { cn: "时间序列构建", en: "Time Series Construction" },
    { cn: "三模型预测", en: "Three-Model Prediction" },
    { cn: "加权融合", en: "Weighted Fusion" },
    { cn: "节假日修正", en: "Holiday Correction" },
    { cn: "增长率校准", en: "Growth Calibration" },
    { cn: "结果输出", en: "Result Output" },
  ];

  const visibleSteps = Math.min(steps.length, Math.floor(frame / 25) + 1);

  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.background }}>
      <BilingualTitle
        cn="总结"
        en="Summary"
      />
      
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "12px",
        }}
      >
        {steps.slice(0, visibleSteps).map((step, i) => {
          const opacity = interpolate(
            frame,
            [(i) * 25, (i) * 25 + 20],
            [0, 1],
            { extrapolateRight: "clamp" }
          );
          
          return (
            <div
              key={i}
              style={{
                opacity,
                display: "flex",
                alignItems: "center",
                gap: "16px",
              }}
            >
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: "50%",
                  backgroundColor: theme.colors.accent,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontFamily: interFont,
                  fontSize: 20,
                  fontWeight: "700",
                  color: theme.colors.background,
                }}
              >
                {i + 1}
              </div>
              <div style={{ textAlign: "left" }}>
                <p
                  style={{
                    fontFamily: notoSansSC,
                    fontSize: 24,
                    fontWeight: "500",
                    color: theme.colors.text,
                    margin: 0,
                  }}
                >
                  {step.cn}
                </p>
                <p
                  style={{
                    fontFamily: interFont,
                    fontSize: 16,
                    fontWeight: "400",
                    color: theme.colors.muted,
                    margin: "4px 0 0 0",
                  }}
                >
                  {step.en}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const CAPM3DVideo: React.FC = () => {
  return (
    <Composition
      id="CAPM3DVideo"
      component={RootComponent}
      durationInFrames={
        theme.durations.intro +
        theme.durations.linear +
        theme.durations.holtWinters +
        theme.durations.sarima +
        theme.durations.ensemble +
        theme.durations.holiday +
        theme.durations.summary
      }
      fps={theme.sizes.fps}
      width={theme.sizes.width}
      height={theme.sizes.height}
    />
  );
};

const RootComponent: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.background }}>
      <Sequence from={0} durationInFrames={theme.durations.intro}>
        <IntroScene />
      </Sequence>
      
      <Sequence from={theme.durations.intro} durationInFrames={theme.durations.linear}>
        <LinearScene />
      </Sequence>
      
      <Sequence from={theme.durations.intro + theme.durations.linear} durationInFrames={theme.durations.holtWinters}>
        <HoltWintersScene />
      </Sequence>
      
      <Sequence from={theme.durations.intro + theme.durations.linear + theme.durations.holtWinters} durationInFrames={theme.durations.sarima}>
        <SARIMAScene />
      </Sequence>
      
      <Sequence from={theme.durations.intro + theme.durations.linear + theme.durations.holtWinters + theme.durations.sarima} durationInFrames={theme.durations.ensemble}>
        <EnsembleScene />
      </Sequence>
      
      <Sequence from={theme.durations.intro + theme.durations.linear + theme.durations.holtWinters + theme.durations.sarima + theme.durations.ensemble} durationInFrames={theme.durations.holiday}>
        <HolidayScene />
      </Sequence>
      
      <Sequence from={theme.durations.intro + theme.durations.linear + theme.durations.holtWinters + theme.durations.sarima + theme.durations.ensemble + theme.durations.holiday} durationInFrames={theme.durations.summary}>
        <SummaryScene />
      </Sequence>
    </AbsoluteFill>
  );
};
