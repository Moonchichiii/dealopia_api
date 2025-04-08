import logging
import re

import scrapy
from dateutil import parser
from django.contrib.gis.geos import Point
from django.utils import timezone

from apps.categories.models import Category
from apps.deals.models import Deal
from apps.locations.models import Location
from apps.shops.models import Shop

logger = logging.getLogger("dealopia.scrapers")


class SustainableDealSpider(scrapy.Spider):
    name = "sustainable_deal_spider"
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "USER_AGENT": "Dealopia Sustainable Shopping Bot (+https://dealopia.com/about/bot)",
        "FEEDS": {"deals.json": {"format": "json", "overwrite": True}},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eco_keywords = [
            "sustainable",
            "eco",
            "green",
            "organic",
            "fair trade",
            "recycled",
            "upcycled",
            "second hand",
            "refurbished",
            "local",
            "carbon neutral",
            "eco-friendly",
            "biodegradable",
        ]
        self.unsustainable_keywords = [
            "fast fashion",
            "single-use",
            "disposable",
            "non-recyclable",
        ]

    def start_requests(self):
        shops = Shop.objects.filter(is_verified=True, scrape_url__isnull=False).only(
            "id", "scrape_url", "deal_selector", "location"
        )
        if not shops.exists():
            logger.warning("No shops configured for scraping")
            return
        for shop in shops:
            if not shop.scrape_url:
                continue
            logger.info(f"Scraping {shop.name} from {shop.scrape_url}")
            yield scrapy.Request(
                url=shop.scrape_url,
                callback=self.parse_deals,
                errback=self.handle_error,
                meta={
                    "shop_id": shop.id,
                    "shop_name": shop.name,
                    "deal_selector": shop.deal_selector,
                },
            )

    def parse_deals(self, response):
        shop_id = response.meta["shop_id"]
        shop_name = response.meta["shop_name"]
        selector = (
            response.meta.get("deal_selector")
            or ".product, .deal, .offer, [data-product]"
        )
        deals_found = 0
        sustainable_deals = 0
        for item in response.css(selector):
            deals_found += 1
            title = self.extract_text(item, "h2, h3, .title, .product-title")
            description = self.extract_text(
                item, ".description, .short-desc, .product-desc"
            )
            if not title:
                continue
            if not self.check_sustainability(title, description):
                continue
            sustainable_deals += 1
            original_price = self.extract_price(
                item, ".original-price, .regular-price, .old-price, del, s, .was-price"
            )
            discounted_price = self.extract_price(
                item,
                ".sale-price, .discounted-price, .current-price, .special-price, .price:not(del):not(s)",
            )
            if (
                not original_price
                or not discounted_price
                or discounted_price >= original_price
            ):
                continue
            discount_percentage = int(
                ((original_price - discounted_price) / original_price) * 100
            )
            image_url = self.extract_attribute(item, "img", "src, data-src")
            if image_url and not image_url.startswith(("http://", "https://")):
                image_url = response.urljoin(image_url)
            product_url = self.extract_attribute(item, "a", "href")
            if product_url and not product_url.startswith(("http://", "https://")):
                product_url = response.urljoin(product_url)
            expiration_str = self.extract_attribute(
                item,
                "time, .expiry, .expires-on, [data-expiry]",
                "datetime, data-date, content",
            )
            expiration = timezone.now() + timezone.timedelta(days=30)
            if expiration_str:
                try:
                    parsed_date = parser.parse(expiration_str)
                    if parsed_date > timezone.now():
                        expiration = parsed_date
                except Exception:
                    pass
            try:
                shop = Shop.objects.get(id=shop_id)
                location = None
                if shop.location and shop.location.coordinates:
                    location = Point(
                        shop.location.coordinates.x, shop.location.coordinates.y
                    )
                sustainability_score = self.calculate_sustainability_score(
                    title, description
                )
                yield {
                    "shop_id": shop_id,
                    "shop_name": shop_name,
                    "title": title,
                    "description": description,
                    "original_price": original_price,
                    "discounted_price": discounted_price,
                    "discount_percentage": discount_percentage,
                    "image_url": image_url,
                    "product_url": product_url,
                    "expiration": expiration,
                    "location": location,
                    "sustainability_score": sustainability_score,
                    "source": "web_scrape",
                }
            except Exception as e:
                logger.error(f"Error processing deal from {shop_name}: {e}")
        logger.info(
            f"{shop_name}: Found {deals_found} deals, {sustainable_deals} sustainable"
        )

    def extract_text(self, selector, css_path):
        for path in css_path.split(","):
            text = selector.css(f"{path.strip()}::text").get()
            if text:
                return text.strip()
        return None

    def extract_attribute(self, selector, element, attributes):
        for attr in attributes.split(","):
            value = selector.css(f"{element.strip()}::attr({attr.strip()})").get()
            if value:
                return value.strip()
        return None

    def extract_price(self, selector, css_path):
        raw = self.extract_text(selector, css_path)
        if not raw:
            return None
        price_str = re.sub(r"[^\d.,]", "", raw)
        if "," in price_str and "." in price_str:
            if price_str.rindex(",") > price_str.rindex("."):
                price_str = price_str.replace(".", "").replace(",", ".")
            else:
                price_str = price_str.replace(",", "")
        elif "," in price_str:
            price_str = price_str.replace(",", ".")
        try:
            return float(price_str)
        except ValueError:
            return None

    def check_sustainability(self, title, description):
        if not title:
            return False
        text = f"{title} {description or ''}".lower()
        for kw in self.unsustainable_keywords:
            if kw in text:
                return False
        return any(kw in text for kw in self.eco_keywords)

    def calculate_sustainability_score(self, title, description):
        if not title:
            return 5.0
        text = f"{title} {description or ''}".lower()
        score = 5.0
        score += min(sum(kw in text for kw in self.eco_keywords) * 0.5, 3.0)
        score -= sum(kw in text for kw in self.unsustainable_keywords) * 1.0
        return max(min(score, 10.0), 0.0)

    def handle_error(self, failure):
        shop_id = failure.request.meta.get("shop_id")
        shop_name = failure.request.meta.get("shop_name", "Unknown")
        logger.error(f"Error scraping {shop_name} (ID: {shop_id}): {failure}")
        try:
            if shop_id:
                shop = Shop.objects.get(id=shop_id)
                shop.last_scrape_error = str(failure)
                shop.last_scrape_attempt = timezone.now()
                shop.save(update_fields=["last_scrape_error", "last_scrape_attempt"])
        except Exception as e:
            logger.error(f"Error updating shop status: {e}")
