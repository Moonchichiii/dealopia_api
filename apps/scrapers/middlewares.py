import random
import logging
from scrapy import signals
from twisted.internet.error import DNSLookupError, TCPTimedOutError, TimeoutError
from scrapy.spidermiddlewares.httperror import HttpError

class SmartProxyMiddleware:
    """
    Middleware that manages proxy rotation with failure tracking.
    """

    def __init__(self, proxies):
        self.proxies = proxies
        self.failed_proxies = {}  # Tracks domain -> list of failed proxies
        self.proxy_success = {}   # Tracks successful requests per proxy
        self.logger = logging.getLogger(__name__)
        
    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        proxies = [
            f"http://user:{settings['PROXY_PASS']}@gate1:3128",
            f"http://user:{settings['PROXY_PASS']}@gate2:3128",
        ]
        middleware = cls(proxies)
        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)
        crawler.signals.connect(middleware.spider_error, signals.spider_error)
        return middleware

    def process_request(self, request, spider):
        if "proxy" not in request.meta:
            proxy = self.choose_proxy(request.url)
            self.logger.debug(f"Using proxy {proxy} for {request.url}")
            request.meta["proxy"] = proxy
            request.meta["original_url"] = request.url

    def process_exception(self, request, exception, spider):
        proxy = request.meta.get("proxy", None)
        if proxy and any(isinstance(exception, err) for err in 
                        (DNSLookupError, TCPTimedOutError, TimeoutError)):
            domain = request.url.split("/")[2]
            self.mark_proxy_failure(proxy, domain)
            self.logger.warning(f"Proxy {proxy} failed for {domain}: {exception}")
            # Remove the failed proxy and try with a new one
            del request.meta['proxy']
            return request

    def process_response(self, request, response, spider):
        proxy = request.meta.get("proxy", None)
        if proxy:
            if 200 <= response.status < 300:
                # Record success
                self.proxy_success[proxy] = self.proxy_success.get(proxy, 0) + 1
            elif response.status >= 400:
                domain = request.url.split("/")[2]
                self.mark_proxy_failure(proxy, domain)
                self.logger.warning(f"Proxy {proxy} received status {response.status} for {domain}")
                # Retry with a different proxy for 403, 429, 503
                if response.status in [403, 429, 503]:
                    del request.meta['proxy']
                    return request
        return response

    def choose_proxy(self, url):
        domain = url.split("/")[2]
        available_proxies = [
            p for p in self.proxies if p not in self.failed_proxies.get(domain, [])
        ]
        
        if not available_proxies:
            self.logger.warning(f"All proxies failed for {domain}, resetting failed list")
            self.failed_proxies[domain] = []
            available_proxies = self.proxies
            
        # Prefer proxies with successful history
        if available_proxies:
            available_proxies.sort(key=lambda p: self.proxy_success.get(p, 0), reverse=True)
            return available_proxies[0]
        
        return random.choice(self.proxies)

    def mark_proxy_failure(self, proxy, domain):
        if domain not in self.failed_proxies:
            self.failed_proxies[domain] = []
        if proxy not in self.failed_proxies[domain]:
            self.failed_proxies[domain].append(proxy)

    def spider_closed(self, spider):
        """
        Clean up resources when the spider closes.
        """
        self.logger.info(f"Proxy success stats: {self.proxy_success}")
        self.logger.info(f"Failed proxies by domain: {self.failed_proxies}")

    def spider_error(self, failure, response, spider):
        proxy = response.request.meta.get("proxy", None)
        if proxy:
            domain = response.url.split("/")[2]
            self.mark_proxy_failure(proxy, domain)
            self.logger.error(f"Spider error with proxy {proxy} for {domain}: {failure}")
