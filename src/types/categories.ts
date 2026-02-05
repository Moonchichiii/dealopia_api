export interface Category {
    id: number;
    name: string;
    description?: string;
    image?: string;
    icon?: string;
    parent?: number | null;
    order?: number;
    is_active: boolean;
    is_eco_friendly?: boolean;
    sustainability_impact?: string;
    created_at: string;
    updated_at: string;
    subcategories?: Category[];
}

export interface CategoryParams {
    parent?: number;
    is_active?: boolean;
    limit?: number;
    page?: number;
    ordering?: string;
}