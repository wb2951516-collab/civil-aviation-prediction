# CAPM Remotion 3D Video Project

## 📋 Overview

This is a professional Remotion project for creating a 3D scientific demonstration video for the **Civil Aviation Passenger Traffic Prediction Model**.

## 🎯 Features

- ✅ **Professional 3D visuals using Three.js and React Three Fiber
- ✅ **Bilingual (Chinese-English) display
- ✅ **Professional typography with Google Fonts (Inter + Noto Sans SC)
- ✅ **Smooth camera transitions and animations
- ✅ **Professional subtitle bar
- ✅ **Multiple 3D mathematical surfaces
- ✅ **Seamless scene transitions

## 📁 Project Structure

```
remotion-project/
├── package.json
├── remotion.config.ts
├── tsconfig.json
├── src/
│   ├── fonts.ts
│   ├── theme.ts
│   ├── index.tsx
│   ├── Root.tsx
│   ├── components/
│   │   ├── BilingualTitle.tsx
│   │   ├── SubtitleBar.tsx
│   │   └── scenes/
│   │   │   ├── IntroScene.tsx
│   │   │   ├── LinearScene.tsx
│   │   │   ├── HoltWintersScene.tsx
│   │   │   ├── SARIMAScene.tsx
│   │   │   ├── EnsembleScene.tsx
│   │   │   ├── HolidayScene.tsx
│   │   │   └── SummaryScene.tsx
│   │   └── 3d/
│   │       ├── ThreeCanvas.tsx
│   │       ├── LinearSurface.tsx
│   │       ├── HoltWintersSurface.tsx
│   │       ├── SARIMASurface.tsx
│   │       └── EnsembleSurfaces.tsx
│   └── scenes/
│   │   └── HolidayChart.tsx
│   │   └── SummaryList.tsx
```

## 🚀 Getting Started

### Installation

```bash
cd remotion-project
npm install
```

### Development

```bash
npm run dev
```

This will open the Remotion Studio at http://localhost:3000

### Rendering

```bash
npm run build
```

### Upgrading Remotion

```bash
npm run upgrade
```

## 🎨 Design Principles

### Color Scheme

```typescript
background: "#0B0F1A"
text: "#EAECEF"
muted: "#9AA4B2"
accent: "#40A9FF"
linear: "#5CDBD3"
holtWinters: "#B37FEB"
sarima: "#FF85C0"
ensemble: "#73D13D"
holiday: "#FFA940"
```

### Scene Duration
- Introduction: 5 seconds (150 frames)
- Linear Regression: 8 seconds (240 frames)
- Holt-Winters: 8 seconds (240 frames)
- SARIMA: 8 seconds (240 frames)
- Ensemble: 8 seconds (240 frames)
- Holiday Effect: 6 seconds (180 frames)
- Summary: 6 seconds (180 frames)

## 📊 Total Duration: **49 seconds
