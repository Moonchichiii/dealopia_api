from scrapy.exceptions import NotConfigured
from sentry_sdk import capture_exception


class SentryLoggerExtension:
    """Extension to capture exceptions in Scrapy spiders and report to Sentry."""

    def __init__(self, sentry_dsn):
        self.sentry_dsn = sentry_dsn

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool('SENTRY_LOGGING_ENABLED'):
            raise NotConfigured
        return cls(crawler.settings.get('SENTRY_DSN'))

    def spider_error(self, failure, response, spider):
        capture_exception(
            failure.value, 
            extra={
                'spider': spider.name,
                'url': response.url,
                'status': response.status
            }
        )