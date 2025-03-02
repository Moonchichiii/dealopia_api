import requests
from django.conf import settings

def solve_captcha(image_url):
    response = requests.post(
        "https://api.captcha.ai/solve",
        json={
            "clientKey": settings.CAPTCHA_API_KEY,
            "task": {
                "type": "ImageToTextTask",
                "body": image_url,
                "phrase": False,
                "case": False,
                "numeric": 0,
                "math": 0
            }
        }
    )
    return response.json()['solution']['text']