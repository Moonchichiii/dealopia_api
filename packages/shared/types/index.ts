export interface Product {
  id: string
  name: string
  price: number
  sustainabilityScore?: number
  category: string
}

export interface User {
  id: string
  email: string
  firstName?: string
  lastName?: string
  preferredEcoCategories?: string[]
}

export interface Deal {
  id: string
  productId: string
  shopId: string
  title: string
  discountPercent: number
  expiresAt?: string
}
