export const ECO_CATEGORIES = [
  'zero-waste',
  'organic',
  'recycled',
  'fair-trade',
  'local-artisan'
] as const

export const ENVIRONMENTAL_IMPACT_METRICS = {
  low: { co2Kg: 1, waterLiters: 50 },
  medium: { co2Kg: 5, waterLiters: 200 },
  high: { co2Kg: 12, waterLiters: 500 }
} as const
