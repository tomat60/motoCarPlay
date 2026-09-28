import { harleyRoadsterSample } from '../harleyRoadster'

describe('harleyRoadsterSample', () => {
  test('starts stationary in neutral', () => {
    const s = harleyRoadsterSample(0)
    expect(s.speedKph).toBe(0)
    expect(s.rpm).toBe(0)
    expect(s.gear).toBe('N')
    expect(s.lights).toBe(false)
  })

  test('idles after the simulated engine start', () => {
    const s = harleyRoadsterSample(6000)
    expect(s.speedKph).toBe(0)
    expect(s.gear).toBe('N')
    expect(s.rpm).toEqual(expect.any(Number))
    expect(s.rpm as number).toBeGreaterThan(850)
    expect(s.lights).toBe(true)
    expect(s.batteryV as number).toBeGreaterThan(13.5)
  })

  test('uses only Roadster forward gears 1 through 5', () => {
    for (let t = 10_000; t < 116_000; t += 1_000) {
      const gear = harleyRoadsterSample(t).gear
      if (gear !== 'N') {
        expect(typeof gear).toBe('number')
        expect(gear as number).toBeGreaterThanOrEqual(1)
        expect(gear as number).toBeLessThanOrEqual(5)
      }
    }
  })
  test('exercises rider-facing telltales', () => {
    expect(harleyRoadsterSample(33_000).turn).toBe('left')
    expect(harleyRoadsterSample(56_000).highBeam).toBe(true)
    expect(harleyRoadsterSample(73_000).turn).toBe('right')
    expect(harleyRoadsterSample(115_000).hazards).toBe(true)
  })

  test('keeps synthetic ride values finite and plausible', () => {
    for (let t = 0; t < 120_000; t += 500) {
      const s = harleyRoadsterSample(t)
      expect(Number.isFinite(s.speedKph)).toBe(true)
      expect(Number.isFinite(s.rpm)).toBe(true)
      expect(s.speedKph as number).toBeGreaterThanOrEqual(0)
      expect(s.speedKph as number).toBeLessThanOrEqual(160)
      expect(s.rpm as number).toBeGreaterThanOrEqual(0)
      expect(s.rpm as number).toBeLessThanOrEqual(5200)
      expect(s.fuelPct as number).toBeGreaterThanOrEqual(0)
      expect(s.fuelPct as number).toBeLessThanOrEqual(100)
    }
  })
})
