export interface Location {
    id: number;
    address: string;
    city: string;
    state: string;
    country: string;
    postal_code: string;
    point: any;
    latitude?: number;
    longitude?: number;
    created_at: string;
    updated_at: string;
}

export interface LocationDetails {
    address: string;
    city: string;
    state: string;
    country: string;
    postal_code: string;
    latitude?: number;
    longitude?: number;
}