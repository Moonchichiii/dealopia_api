import random
from scrapy import signals

class SmartProxyMiddleware:
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
        return random.choice([
            p for p in self.proxies 
            if p not in self.failed_proxies.get(domain, [])
        ])