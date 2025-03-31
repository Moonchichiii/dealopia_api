import logging

import scrapy
from django.contrib.gis.geos import Point
from django.utils import timezone

from apps.categories.models import Category
from apps.deals.models import Deal, Shop

logger = logging.getLogger("dealopia.scrapers")


class SustainableDealSpider(scrapy.Spider):
    """Spider for scraping sustainable deals from configured shops."""

    name = "sustainable_deal_spider"
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

        # Keywords to identify potentially unsustainable products
        self.unsustainable_keywords = [
            "fast fashion",
            "single-use",
            "disposable",
            "non-recyclable",
        ]

    def start_requests(self):
        """Get scraping URLs from verified sustainable shops."""
        # Only scrape from verified shops with scraping URLs
        shops = Shop.objects.filter(is_verified=True, scrape_url__isnull=False).only(
            "id", "scrape_url", "deal_selector", "location"
        )

        if not shops:
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
        """Parse deals from shop pages with sustainability filtering."""
        shop_id = response.meta["shop_id"]
        shop_name = response.meta["shop_name"]

        # Get custom selector if specified, otherwise use defaults
        deal_selector = (
            response.meta.get("deal_selector")
            or ".product, .deal, .offer, [data-product]"
        )

        deals_found = 0
        sustainable_deals = 0

        # Find all potential deal elements
        for item in response.css(deal_selector):
            deals_found += 1

            # Extract deal data with fallbacks for different site structures
            title = self.extract_text(item, "h2, h3, .title, .product-title")
            description = self.extract_text(
                item, ".description, .short-desc, .product-desc"
            )

            # Skip if no title
            if not title:
                continue

            # Check if product has sustainable indicators
            is_sustainable = self.check_sustainability(title, description)

            if not is_sustainable:
                continue

            sustainable_deals += 1

            # Extract price information with thorough fallbacks
            original_price = self.extract_price(
                item, ".original-price, .regular-price, .old-price, del, s, .was-price"
            )

            discounted_price = self.extract_price(
                item,
                ".sale-price, .discounted-price, .current-price, .special-price, .price:not(del):not(s)",
            )

            # Skip if no valid price data
            if (
                not original_price
                or not discounted_price
                or discounted_price >= original_price
            ):
                continue

            # Calculate discount
            discount_percentage = int(
                ((original_price - discounted_price) / original_price) * 100
            )

            # Get image URL
            image_url = self.extract_attribute(item, "img", "src, data-src")
            if not image_url and item.css("img"):
                # Try to extract from style attribute for background images
                style = item.css("img::attr(style)").get()
                if style and "url(" in style:
                    import re

                    match = re.search(r'url\([\'"]?([^\'"]+)[\'"]?\)', style)
                    if match:
                        image_url = match.group(1)

            # Get product URL
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

            # Default to 30 days from now
            expiration = timezone.now() + timezone.timedelta(days=30)

            # Try to parse expiration date
            if expiration_str:
                try:
                    from dateutil import parser

                    parsed_date = parser.parse(expiration_str)
                    if parsed_date > timezone.now():
                        expiration = parsed_date
                except:
                    pass

            try:
                shop = Shop.objects.get(id=shop_id)

                # Location data
                if shop.location and shop.location.point:
                    location = Point(shop.location.point.x, shop.location.point.y)
                else:
                    location = None

                # Sustainability score
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
            f"Scraped {shop_name}: Found {deals_found} deals, {sustainable_deals} sustainable"
        )

    def extract_text(self, selector, css_path):
        """Extract text with fallbacks for multiple potential selectors."""
        for path in css_path.split(","):
            text = selector.css(f"{path.strip()}::text").get()
            if text:
                return text.strip()
        return None

    def extract_attribute(self, selector, element, attributes):
        """Extract attribute with fallbacks for multiple attributes."""
        for attribute in attributes.split(","):
            attr = selector.css(f"{element.strip()}::attr({attribute.strip()})").get()
            if attr:
                return attr.strip()
        return None

    def extract_price(self, selector, css_path):
        """Extract and parse price with proper number handling."""
        raw_price = self.extract_text(selector, css_path)
        if not raw_price:
            return None

        # Remove currency symbols and non-numeric characters except decimal separator
        import re

        price_str = re.sub(r"[^\d.,]", "", raw_price)

        # Handle different decimal separators
        if "," in price_str and "." in price_str:
            # If both present, the last one is the decimal separator
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
        except:
            return None

    def check_sustainability(self, title, description):
        """Check if a product is sustainable based on its title and description."""
        if not title:
            return False

        text = f"{title} {description or ''}".lower()

        # Quick check for unsustainable indicators
        for keyword in self.unsustainable_keywords:
            if keyword in text:
                return False

        # Check for sustainable indicators
        return any(keyword in text for keyword in self.eco_keywords)

    def calculate_sustainability_score(self, title, description):
        """Calculate basic sustainability score based on keyword presence."""
        if not title:
            return 5.0  # Default medium score

        text = f"{title} {description or ''}".lower()

        # Start with medium score
        score = 5.0

        # Count sustainable keywords
        eco_count = sum(keyword in text for keyword in self.eco_keywords)

        # Adjust score based on keywords (max +3.0)
        score += min(eco_count * 0.5, 3.0)

        # Penalize for unsustainable keywords
        unsustainable_count = sum(
            keyword in text for keyword in self.unsustainable_keywords
        )
        score -= unsustainable_count * 1.0

        # Ensure score is within bounds
        return max(min(score, 10.0), 0.0)

    def handle_error(self, failure):
        """Handle request errors gracefully."""
        shop_id = failure.request.meta.get("shop_id")
        shop_name = failure.request.meta.get("shop_name", "Unknown")

        logger.error(f"Error scraping {shop_name} (ID: {shop_id}): {repr(failure)}")

        # Log the error and update shop scraping status if needed
        try:
            if shop_id:
                shop = Shop.objects.get(id=shop_id)
                # Potentially update shop metadata to track scraping failures
                shop.last_scrape_error = str(failure)
                shop.last_scrape_attempt = timezone.now()
                shop.save(update_fields=["last_scrape_error", "last_scrape_attempt"])
        except Exception as e:
            logger.error(f"Error updating shop scrape status: {str(e)}")
