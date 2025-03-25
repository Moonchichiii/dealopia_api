import random

import pandas as pd
import requests
from django.conf import settings
from scrapy import signals
from scrapy.exceptions import NotConfigured
from sentry_sdk import capture_exception
from sklearn.neighbors import LocalOutlierFactor


def solve_captcha(image_url):
    """Solve captcha images via API service"""
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


def clean_deal_data(raw_data):
    """Clean and validate deal data with outlier detection"""
    df = pd.DataFrame(raw_data)
    
    df['discount_pct'] = ((df['original_price'] - df['discounted_price']) 
                          / df['original_price']) * 100
    
    clf = LocalOutlierFactor(n_neighbors=20)
    outliers = clf.fit_predict(df[['discount_pct', 'original_price']])
    df = df[outliers == 1]
    
    valid_coords = df['location'].apply(
        lambda x: 40.477399 < x.lat < 40.917577 and
                 -74.259090 < x.lon < -73.700272
    )
    
    return df[valid_coords].to_dict('records')


class SmartProxyMiddleware:
    """Middleware for managing rotating proxies"""
    def __init__(self, proxies):
        self.proxies = proxies
        self.failed_proxies = {}

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        proxies = [
            f"http://user:{settings['PROXY_PASS']}@gate1:3128",
            f"http://user:{settings['PROXY_PASS']}@gate2:3128"
        ]
        middleware = cls(proxies)
        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)
        return middleware

    def process_request(self, request, spider):
        if 'proxy' not in request.meta:
            request.meta['proxy'] = self.choose_proxy(request.url)

    def choose_proxy(self, url):
        domain = url.split('/')[2]
        available_proxies = [
            p for p in self.proxies
            if p not in self.failed_proxies.get(domain, [])
        ]
        if not available_proxies:
            self.failed_proxies[domain] = []
            available_proxies = self.proxies
        
        return random.choice(available_proxies)
    
    def spider_closed(self, spider):
        pass


class SentryLoggerExtension:
    """Extension for Sentry error logging"""
    def __init__(self, sentry_dsn):
        self.sentry_dsn = sentry_dsn

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool('SENTRY_LOGGING_ENABLED'):
            raise NotConfigured
        return cls(crawler.settings.get('SENTRY_DSN'))

    def spider_error(self, failure, response, spider):
        capture_exception(failure.value, extra={
            'spider': spider.name,
            'url': response.url,
            'status': response.status
        })
