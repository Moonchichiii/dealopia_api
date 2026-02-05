import logging
import math
from typing import Dict, List, Optional

import requests
from django.conf import settings

logger = logging.getLogger("dealopia.search")

# Sustainability keywords for scoring
SUSTAINABILITY_KEYWORDS = [
    "eco-friendly",
    "sustainable",
    "organic",
    "fair trade",
    "recycled",
    "biodegradable",
    "carbon neutral",
    "zero waste",
    "ethical",
    "green",
    "upcycled",
    "plant-based",
    "vegan",
    "renewable",
    "local",
]


class GooglePlacesService:
    """Service for fetching sustainable shops from Google Places API."""

    BASE_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    @classmethod
    def search(
        cls,
        query: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: float = 10,
        min_sustainability: float = 0,
    ) -> List[Dict]:
        """Search for sustainable shops via Google Places API."""
        # Skip if no location provided
        if not latitude or not longitude:
            return []

        # Get API key from settings
        api_key = getattr(settings, "GOOGLE_PLACES_API_KEY", None)
        if not api_key:
            logger.warning("Google Places API key not configured")
            return []

        # Prepare search parameters
        params = {
            "location": f"{latitude},{longitude}",
            "radius": min(50000, int(radius_km * 1000)),  # Max 50km
            "key": api_key,
            "type": "store",
        }

        # Enhance query with sustainability terms if needed
        if query:
            # Add sustainability term if not already present
            if not any(kw in query.lower() for kw in SUSTAINABILITY_KEYWORDS):
                params["keyword"] = f"{query} sustainable"
            else:
                params["keyword"] = query
        else:
            # Default search for sustainable stores
            params["keyword"] = "eco sustainable shop"

        try:
            # Make API request
            response = requests.get(cls.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Process results
            results = []
            for place in data.get("results", []):
                # Calculate sustainability score
                sustainability_score = cls._calculate_sustainability_score(place)

                # Skip if below minimum score
                if sustainability_score < min_sustainability:
                    continue

                # Calculate distance
                location = place.get("geometry", {}).get("location", {})
                lat, lng = location.get("lat"), location.get("lng")
                distance = cls._compute_distance(latitude, longitude, lat, lng)

                # Create result dictionary
                results.append(
                    {
                        "id": place.get("place_id"),
                        "name": place.get("name", ""),
                        "description": place.get("vicinity", ""),
                        "sustainability_score": sustainability_score,
                        "distance": distance,
                        "source": "google_places",
                        "logo": place.get("icon"),
                        "url": f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id')}",
                    }
                )

            # Sort by sustainability score and distance
            results.sort(
                key=lambda x: (x["sustainability_score"], -x.get("distance", 1000)),
                reverse=True,
            )

            return results

        except Exception as e:
            logger.error(f"Google Places API error: {e}")
            return []

    @classmethod
    def _calculate_sustainability_score(cls, place: Dict) -> float:
        """Calculate a sustainability score based on keywords."""
        text = f"{place.get('name', '').lower()} {place.get('vicinity', '').lower()}"

        # Count sustainability keywords
        keyword_count = sum(1 for kw in SUSTAINABILITY_KEYWORDS if kw in text)

        # Base score plus keyword matches
        score = 5.0 + (keyword_count * 1.5)

        # European focus
        european_locations = [
            "germany",
            "france",
            "uk",
            "united kingdom",
            "spain",
            "italy",
            "netherlands",
            "belgium",
            "switzerland",
        ]
        if any(country in text for country in european_locations):
            score += 1.0

        # Cap at 10
        return min(10.0, score)

    @staticmethod
    def _compute_distance(
        lat1: float, lng1: float, lat2: float, lng2: float
    ) -> Optional[float]:
        """Calculate distance between coordinates using Haversine formula."""
        if None in (lat1, lng1, lat2, lng2):
            return None

        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return round(distance, 2)
