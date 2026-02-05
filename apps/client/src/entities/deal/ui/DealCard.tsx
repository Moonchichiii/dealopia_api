import type { Deal } from '@dealopia/shared/types'

type DealCardProps = {
  deal: Deal
}

function scoreLabel(score: number) {
  if (score >= 80) return 'Excellent'
  if (score >= 60) return 'Good'
  if (score >= 40) return 'Fair'
  return 'Needs improvement'
}

export function DealCard({ deal }: DealCardProps) {
  const score = deal.sustainability_score ?? 0

  return (
    <article style={{ border: '1px solid #d1d5db', borderRadius: 12, padding: 16 }}>
      <h3 style={{ margin: '0 0 8px' }}>{deal.title}</h3>
      <p style={{ margin: '0 0 8px' }}>Discount: {deal.discountPercent}%</p>
      <p style={{ margin: 0 }}>
        Sustainability Score: <strong>{score}</strong> ({scoreLabel(score)})
      </p>
    </article>
  )
}
