import re
import logging
import scrapy
from dateutil import parser
from django.contrib.gis.geos import Point
from django.utils import timezone

from apps.shops.models import Shop
from apps.deals.models import Deal
from apps.categories.models import Category
from apps.locations.models import Location

logger = logging.getLogger("dealopia.scrapers")


class SustainableDealSpider(scrapy.Spider):
    """
    Spider for scraping sustainable deals from configured shops.
    Uses eco_keywords to filter sustainable items and avoids those with
    unsustainable_keywords.
    """

    name = "sustainable_deal_spider"

    # Custom settings for this spider
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 3,  # More respectful crawling
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "USER_AGENT": "Dealopia Sustainable Shopping Bot (+https://dealopia.com/about/bot)",
        "FEEDS": {"deals.json": {"format": "json", "overwrite": True}},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Keywords to identify sustainable products
        self.eco_keywords = [
            "sustainable", "eco", "green", "organic", "fair trade",
            "recycled", "upcycled", "second hand", "refurbished", "local",
            "carbon neutral", "eco-friendly", "biodegradable",
        ]

        # Keywords to identify potentially unsustainable products
        self.unsustainable_keywords = [
            "fast fashion", "single-use", "disposable", "non-recyclable",
        ]

    def start_requests(self):
        """
        Grab scraping URLs from verified shops in the database.
        Only shops with 'scrape_url' and 'is_verified=True' are considered.
        """
        shops = Shop.objects.filter(is_verified=True, scrape_url__isnull=False).only(
            "id", "scrape_url", "deal_selector", "location"
        )

        if not shops.exists():
            logger.warning("No shops configured for scraping")
            return

        for shop in shops:
            if not shop.scrape_url:
                continue

            logger.info(f"Starting to scrape {shop.name} from {shop.scrape_url}")

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
        """
        Parse deals from the specified selector, apply sustainability filtering,
        and yield results.
        """
        shop_id = response.meta["shop_id"]
        shop_name = response.meta["shop_name"]

        # Fallback selector if shop.deal_selector is not defined
        deal_selector = (
            response.meta.get("deal_selector")
            or ".product, .deal, .offer, [data-product]"
        )

        deals_found = 0
        sustainable_deals = 0

        # Find all potential deal elements
        for item in response.css(deal_selector):
            deals_found += 1

            # Extract core text fields
            title = self.extract_text(item, "h2, h3, .title, .product-title")
            description = self.extract_text(
                item, ".description, .short-desc, .product-desc"
            )

            # Skip if no title
            if not title:
                continue

            # Check for sustainability indicators
            is_sustainable = self.check_sustainability(title, description)
            if not is_sustainable:
                continue
            sustainable_deals += 1

            # Extract pricing
            original_price = self.extract_price(
                item, ".original-price, .regular-price, .old-price, del, s, "
                ".was-price"
            )
            discounted_price = self.extract_price(
                item,
                ".sale-price, .discounted-price, .current-price, .special-price, "
                ".price:not(del):not(s)",
            )

            # Skip if price data is invalid or no discount
            if (not original_price or not discounted_price or 
                    discounted_price >= original_price):
                continue

            discount_percentage = int(
                ((original_price - discounted_price) / original_price) * 100
            )

            # Attempt to find an image URL
            image_url = self.extract_attribute(item, "img", "src, data-src")
            if not image_url and item.css("img"):
                # Attempt from style attribute (background-image, etc.)
                style = item.css("img::attr(style)").get()
                if style and "url(" in style:
                    match = re.search(r'url\([\'"]?([^\'"]+)[\'"]?\)', style)
                    if match:
                        image_url = match.group(1)

            # Attempt to find product URL
            product_url = self.extract_attribute(item, "a", "href")

            # Ensure absolute URLs
            if image_url and not image_url.startswith(("http://", "https://")):
                image_url = response.urljoin(image_url)
            if product_url and not product_url.startswith(("http://", "https://")):
                product_url = response.urljoin(product_url)

            # Extract expiration date if available
            expiration_str = self.extract_attribute(
                item,
                "time, .expiry, .expires-on, [data-expiry]",
                "datetime, data-date, content",
            )
            # Default to 30 days
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

                # If the shop has a location
                location = None
                if shop.location and shop.location.coordinates:
                    location = Point(
                        shop.location.coordinates.x,
                        shop.location.coordinates.y
                    )

                # Score for sustainability
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
                logger.error(f"Error processing deal from {shop_name}: {str(e)}")

        logger.info(
            f"Scraped {shop_name}: Found {deals_found} deals, "
            f"{sustainable_deals} considered sustainable"
        )

    def extract_text(self, selector, css_path):
        """
        Extract text from a set of CSS selectors,
        returning the first match that yields a non-empty string.
        """
        for path in css_path.split(","):
            text = selector.css(f"{path.strip()}::text").get()
            if text:
                return text.strip()
        return None

    def extract_attribute(self, selector, element, attributes):
        """
        Extract an attribute from the first element that exists,
        trying multiple attribute names in `attributes`.
        """
        for attribute in attributes.split(","):
            attr = selector.css(
                f"{element.strip()}::attr({attribute.strip()})"
            ).get()
            if attr:
                return attr.strip()
        return None

    def extract_price(self, selector, css_path):
        """
        Extract price by removing currency symbols and parsing as float.
        Handles either '.' or ',' decimal separators.
        """
        raw_price = self.extract_text(selector, css_path)
        if not raw_price:
            return None

        # Remove currency symbols and keep only digits/decimals
        price_str = re.sub(r"[^\d.,]", "", raw_price)

        # Handle possible decimal formats
        if "," in price_str and "." in price_str:
            # If both '.' and ',' appear, assume the last occurrence is the decimal
            if price_str.rindex(",") > price_str.rindex("."):
                price_str = price_str.replace(".", "")
                price_str = price_str.replace(",", ".")
            else:
                price_str = price_str.replace(",", "")
        elif "," in price_str:
            # Assume comma is decimal separator
            price_str = price_str.replace(",", ".")

        try:
            return float(price_str)
        except ValueError:
            return None

    def check_sustainability(self, title, description):
        """
        Determine if an item is "sustainable" by searching for eco_keywords
        and making sure none of the unsustainable_keywords appear.
        """
        if not title:
            return False
        text = f"{title} {description or ''}".lower()

        # Quick check for unsustainable indicators => auto-fail
        for keyword in self.unsustainable_keywords:
            if keyword in text:
                return False

        # If at least one eco_keyword is present => pass
        return any(keyword in text for keyword in self.eco_keywords)

    def calculate_sustainability_score(self, title, description):
        """
        Calculate sustainability score based on keywords.
        Score starts at 5, adds 0.5 per eco keyword, subtracts 1 per unsustainable.
        Clamped between 0 and 10.
        """
        if not title:
            return 5.0  # default medium

        text = f"{title} {description or ''}".lower()
        score = 5.0

        eco_count = sum(kw in text for kw in self.eco_keywords)
        score += min(eco_count * 0.5, 3.0)

        bad_count = sum(kw in text for kw in self.unsustainable_keywords)
        score -= bad_count * 1.0

        return max(min(score, 10.0), 0.0)

    def handle_error(self, failure):
        """
        Handle scraping errors gracefully, logging them
        and possibly updating the Shop model with error info.
        """
        shop_id = failure.request.meta.get("shop_id")
        shop_name = failure.request.meta.get("shop_name", "Unknown")

        logger.error(f"Error scraping {shop_name} (ID: {shop_id}): {repr(failure)}")

        try:
            if shop_id:
                shop = Shop.objects.get(id=shop_id)
                shop.last_scrape_error = str(failure)
                shop.last_scrape_attempt = timezone.now()
                shop.save(update_fields=["last_scrape_error", "last_scrape_attempt"])
        except Exception as e:
            logger.error(f"Error updating shop scrape status: {str(e)}")
