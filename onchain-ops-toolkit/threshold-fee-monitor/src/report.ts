export type MonthWindow = {
  label: string
  start: Date
  end: Date
}

export function parseIsoDate(value: string): Date {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new Error(`Invalid date: ${value}. Use YYYY-MM-DD.`)
  const date = new Date(`${value}T00:00:00.000Z`)
  if (Number.isNaN(date.valueOf()) || date.toISOString().slice(0, 10) !== value) {
    throw new Error(`Invalid date: ${value}. Use YYYY-MM-DD.`)
  }
  return date
}

export function monthWindows(fromIso: string, toIso: string): MonthWindow[] {
  const from = parseIsoDate(fromIso)
  const to = parseIsoDate(toIso)
  if (from >= to) throw new Error('The start date must be earlier than the end date.')

  const windows: MonthWindow[] = []
  let cursor = from
  while (cursor < to) {
    const nextMonth = new Date(Date.UTC(cursor.getUTCFullYear(), cursor.getUTCMonth() + 1, 1))
    const end = nextMonth < to ? nextMonth : to
    windows.push({
      label: `${cursor.getUTCFullYear()}-${String(cursor.getUTCMonth() + 1).padStart(2, '0')}`,
      start: cursor,
      end
    })
    cursor = end
  }
  return windows
}

export function summariseYears(monthly: Record<string, bigint>): Record<string, bigint> {
  const yearly: Record<string, bigint> = {}
  for (const [month, value] of Object.entries(monthly)) {
    const year = month.slice(0, 4)
    yearly[year] = (yearly[year] ?? 0n) + value
  }
  return yearly
}
