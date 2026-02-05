import { DealCard } from '../entities/deal/ui/DealCard'
import type { Deal } from '@dealopia/shared/types'

const demoDeal: Deal = {
  id: 'demo-deal-1',
  productId: 'product-1',
  shopId: 'shop-1',
  title: 'Eco-Friendly Running Shoes',
  discountPercent: 25,
  sustainability_score: 87
}

export default function App() {
  return (
    <main style={{ maxWidth: 640, margin: '2rem auto', fontFamily: 'Inter, sans-serif' }}>
      <h1>Dealopia Eco-Pulse</h1>
      <DealCard deal={demoDeal} />
    </main>
  )
}
