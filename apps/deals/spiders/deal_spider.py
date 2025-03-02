import scrapy
from deals.models import Shop, Deal
from django.utils import timezone

class DealSpider(scrapy.Spider):
    name = "deal_spider"
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2.5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1
    }

    def start_requests(self):
        for shop in Shop.objects.filter(is_verified=True):
            yield scrapy.Request(
                url=shop.deal_page_url,
                meta={'shop_id': shop.id},
                callback=self.parse_deals
            )

    def parse_deals(self, response):
        shop = Shop.objects.get(id=response.meta['shop_id'])
        
        for item in response.css('div.deal-item'):
            yield {
                'shop': shop.id,
                'title': item.css('h2::text').get(),
                'original_price': item.attrib['data-original-price'],
                'discounted_price': item.css('.price::text').get(),
                'expiration': item.xpath('.//time/@datetime').get(),
                'location': {
                    'lat': shop.location.y,
                    'lng': shop.location.x
                }
            }