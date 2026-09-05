import { describe, expect, it } from 'vitest'
import { monthWindows, parseIsoDate, summariseYears } from '../src/report.js'

describe('fee report date handling', () => {
  it('keeps partial months inside the requested range', () => {
    const windows = monthWindows('2025-01-15', '2025-03-05')
    expect(windows.map(({ label, start, end }) => [label, start.toISOString(), end.toISOString()])).toEqual([
      ['2025-01', '2025-01-15T00:00:00.000Z', '2025-02-01T00:00:00.000Z'],
      ['2025-02', '2025-02-01T00:00:00.000Z', '2025-03-01T00:00:00.000Z'],
      ['2025-03', '2025-03-01T00:00:00.000Z', '2025-03-05T00:00:00.000Z']
    ])
  })

  it('rejects invalid calendar dates', () => {
    expect(() => parseIsoDate('2025-02-30')).toThrow('Invalid date')
  })

  it('sums monthly values into years', () => {
    expect(summariseYears({ '2024-12': 3n, '2025-01': 4n, '2025-02': 5n })).toEqual({
      '2024': 3n,
      '2025': 9n
    })
  })
})
