// Synthetic 2017 Harley-Davidson XL1200CX Roadster ride profile.
//
// This intentionally models rider-facing behaviour, not CAN IDs/scaling.
// Real CAN-derived values replace these as soon as the target bike is captured.

export type HarleyRoadsterSample = Record<string, unknown>

const TWO_PI = Math.PI * 2

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v))
}

function smoothstep(a: number, b: number, t: number): number {
  const x = clamp((t - a) / (b - a), 0, 1)
  return x * x * (3 - 2 * x)
}

function speedProfile(t: number): number {
  if (t < 10) return 0
  if (t < 24) return 45 * smoothstep(10, 24, t)
  if (t < 52) return 52 + 13 * Math.sin(((t - 24) / 28) * TWO_PI * 1.7)
  if (t < 78) return 62 + 48 * smoothstep(52, 78, t)
  if (t < 98) return 96 + 10 * Math.sin(((t - 78) / 20) * TWO_PI)
  if (t < 116) return 96 - 76 * smoothstep(98, 116, t)
  return 20 - 20 * smoothstep(116, 120, t)
}

function gearFor(speedKph: number, t: number): number | 'N' {
  if (speedKph < 1) return 'N'
  if (speedKph < 20) return 1
  if (speedKph < 40) return 2
  if (speedKph < 62) return 3
  if (speedKph < 88) return 4
  return 5
}

const OVERALL_GEAR_RATIO: Record<number, number> = {
  1: 9.315,
  2: 6.653,
  3: 4.948,
  4: 4.102,
  5: 3.517
}

// 150/70R18 rear tyre from Harley's 2017 Roadster specifications.
// This is good enough for a UI simulator; live RPM comes from CAN.
const REAR_TYRE_CIRCUMFERENCE_M = Math.PI * ((18 * 25.4 + 2 * (150 * 0.7)) / 1000)

function rpmFor(speedKph: number, gear: number | 'N', t: number): number {
  if (gear === 'N') {
    return t < 4 ? 0 : 980 + 45 * Math.sin(t * 1.8)
  }

  const metresPerMinute = (speedKph * 1000) / 60
  const wheelRpm = metresPerMinute / REAR_TYRE_CIRCUMFERENCE_M
  const drivelineRpm = wheelRpm * OVERALL_GEAR_RATIO[gear]
  const pulse = 45 * Math.sin(t * 2.2)
  return clamp(drivelineRpm + pulse, 850, 5200)
}

export function harleyRoadsterSample(tMs: number): HarleyRoadsterSample {
  const t = (tMs / 1000) % 120
  const tAbs = tMs / 1000
  const speedKph = clamp(speedProfile(t), 0, 160)
  const gear = gearFor(speedKph, t)
  const rpm = rpmFor(speedKph, gear, t)

  const engineRunning = t >= 4
  const warm = smoothstep(4, 95, t)
  const oilC = engineRunning ? 42 + 62 * warm + 3 * Math.sin(tAbs / 8) : 24
  const ambientC = 21 + 1.1 * Math.sin(tAbs / 27)
  const batteryV = engineRunning ? 14.15 + 0.12 * Math.sin(tAbs / 5) : 12.55

  const leftWindow = t >= 31 && t < 37
  const rightWindow = t >= 71 && t < 77
  const hazards = t >= 114 && t < 118
  const turn = hazards ? 'none' : leftWindow ? 'left' : rightWindow ? 'right' : 'none'
  const highBeam = t >= 54 && t < 60

  const lean =
    t >= 24 && t < 52
      ? 22 * Math.sin(((t - 24) / 28) * TWO_PI * 1.7)
      : speedKph > 10
        ? 3.5 * Math.sin(tAbs / 3.4)
        : 0

  const fuelPct = clamp(74 - t / 120, 0, 100)
  const rangeKm = Math.round(185 * (fuelPct / 100))

  return {
    speedKph,
    rpm,
    gear,
    lights: engineRunning,
    highBeam,
    hazards,
    turn,
    parkingBrake: false,
    batteryV,
    fuelPct,
    rangeKm,
    oilC,
    ambientC,
    leanDeg: lean,
    pitchDeg: speedKph > 1 ? 1.5 + 1.8 * Math.sin(tAbs / 5.5) : 0,
    gForceX: Math.tan((lean * Math.PI) / 180) * 0.48,
    gForceY: t >= 10 && t < 24 ? 0.22 : t >= 98 ? -0.3 : 0,
    gpsFix: tAbs > 2,
    gpsSatellites: tAbs > 2 ? 9 : 3,
    gps: {
      heading: (300 + 45 * Math.sin((t / 120) * TWO_PI) + t * 1.1) % 360,
      alt: 110 + 12 * Math.sin((t / 120) * TWO_PI + 0.8),
      speedMs: speedKph / 3.6
    },
    imuRecalibrating: false
  }
}

