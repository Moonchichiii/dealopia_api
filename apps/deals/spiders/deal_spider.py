import scrapy
from django.utils import timezone

from deals.models import Shop, Deal


class DealSpider(scrapy.Spider):
    name = "deal_spider"
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2.5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1
    }

    def start_requests(self):
        shops = Shop.objects.filter(is_verified=True).only('id', 'deal_page_url', 'location')
        for shop in shops:
            yield scrapy.Request(
                url=shop.deal_page_url,
                meta={'shop_id': shop.id},
                callback=self.parse_deals
            )

    def parse_deals(self, response):
        shop_id = response.meta['shop_id']
        shop = Shop.objects.get(id=shop_id)
        
        for item in response.css('div.deal-item'):
            yield {
                'shop': shop_id,
                'title': item.css('h2::text').get(),
                'original_price': item.attrib['data-original-price'],
                'discounted_price': item.css('.price::text').get(),
                'expiration': item.xpath('.//time/@datetime').get(),
                'location': {
                    'lat': shop.location.y,
                    'lng': shop.location.x
                }
            }