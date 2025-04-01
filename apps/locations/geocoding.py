import requests
from django.conf import settings

def external_geocode_api(address):
    """
    Talk to an external geocoding provider, return (lat, lng) or None if fail.
    This is just an example with Nominatim (OpenStreetMap).
    """

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
    }
    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        lat = float(data[0]["lat"])
        lng = float(data[0]["lon"])
        return (lat, lng)
    except Exception:
        return None
