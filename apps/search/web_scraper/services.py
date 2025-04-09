import logging
from typing import Dict
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from django.utils import timezone
from playwright.sync_api import sync_playwright

logger = logging.getLogger("dealopia.search.web_scraper")

SUSTAINABILITY_KEYWORDS = [
    "eco-friendly",
    "sustainable",
    "organic",
    "fair trade",
    "recycled",
    "biodegradable",
    "carbon neutral",
    "zero waste",
    "ethical",
    "green",
    "upcycled",
    "plant-based",
    "cruelty-free",
    "vegan",
    "compostable",
    "renewable",
    "energy efficient",
    "locally sourced",
    "b corp",
]


class WebScraperService:
    """Service for ethically analyzing websites for sustainability information."""

    @staticmethod
    def analyze_shop_website(url: str) -> Dict:
        """Analyze a shop's website for sustainability indicators."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Dealopia Sustainable Shopping Bot (+https://dealopia.com/about/bot)"
                )
                page = context.new_page()

                page.goto(url, timeout=60000)
                page.wait_for_load_state("networkidle", timeout=30000)

                html = page.content()
                title = page.title()
                description = page.evaluate(
                    '() => document.querySelector("meta[name=\'description\']")?.content || ""'
                )

                soup = BeautifulSoup(html, "html.parser")
                sustainability_score = WebScraperService._analyze_sustainability(
                    soup, html, url
                )

                browser.close()

                return {
                    "name": title,
                    "description": description,
                    "sustainability": sustainability_score,
                    "analyzed_at": timezone.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error analyzing website {url}: {e}")
            return {"error": str(e), "url": url}

    @staticmethod
    def _analyze_sustainability(soup, html: str, base_url: str) -> Dict:
        """Analyze HTML content for sustainability indicators."""
        page_text = soup.get_text().lower()

        keywords_found = []
        for keyword in SUSTAINABILITY_KEYWORDS:
            if keyword in page_text:
                keywords_found.append(keyword)

        score = 5.0
        keyword_count = len(keywords_found)
        score += min(keyword_count * 0.5, 3.0)

        sustainability_links = []
        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            if any(term in href for term in ["sustain", "eco", "green", "environment"]):
                full_url = urljoin(base_url, link["href"])
                sustainability_links.append(full_url)

        if sustainability_links:
            score += min(len(sustainability_links) * 0.3, 1.0)

        img_count = 0
        for img in soup.find_all("img"):
            alt_text = img.get("alt", "").lower()
            src = img.get("src", "").lower()
            if any(
                keyword in alt_text or keyword in src
                for keyword in SUSTAINABILITY_KEYWORDS
            ):
                img_count += 1

        if img_count > 0:
            score += min(img_count * 0.2, 1.0)

        score = min(score, 10.0)

        return {
            "score": score,
            "keywords_found": keywords_found,
            "eco_links": sustainability_links[:5],
            "sustainability_images": img_count,
        }

    @staticmethod
    def analyze_deals_page(shop_id: int, url: str) -> Dict:
        """Analyze a shop's deals page for potential deals."""
        try:
            from apps.shops.models import Shop

            shop = Shop.objects.get(id=shop_id)

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.goto(url, timeout=60000)
                page.wait_for_load_state("networkidle", timeout=30000)

                deals_data = page.evaluate(
                    """() => {
                    const dealElements = document.querySelectorAll(
                        '.product-card, .deal-item, .offer, .discount, .product'
                    );
                    
                    return Array.from(dealElements).map(el => {
                        const title = el.querySelector('h2, h3, .title')?.textContent?.trim() || '';
                        
                        const originalPriceEl = el.querySelector(
                            '.original-price, .regular-price, .old-price, del, s'
                        );
                        const discountedPriceEl = el.querySelector(
                            '.sale-price, .discounted-price, .current-price'
                        );
                        
                        const description = el.querySelector('.description')?.textContent?.trim() || '';
                        const imageEl = el.querySelector('img');
                        const linkEl = el.querySelector('a');
                        
                        let originalPrice = 0;
                        let discountedPrice = 0;
                        
                        if (originalPriceEl && discountedPriceEl) {
                            const parsePriceText = (text) => {
                                const match = text.match(/[\\d.,]+/);
                                return match ? parseFloat(match[0].replace(',', '.')) : 0;
                            };
                            
                            originalPrice = parsePriceText(originalPriceEl.textContent);
                            discountedPrice = parsePriceText(discountedPriceEl.textContent);
                        }
                        
                        let discountPercentage = 0;
                        if (originalPrice > 0 && discountedPrice > 0 && discountedPrice < originalPrice) {
                            discountPercentage = Math.round(
                                ((originalPrice - discountedPrice) / originalPrice) * 100
                            );
                        }
                        
                        return {
                            title,
                            originalPrice,
                            discountedPrice,
                            discountPercentage,
                            description,
                            imageUrl: imageEl ? imageEl.src : '',
                            productUrl: linkEl ? linkEl.href : '',
                            isSustainable: SUSTAINABILITY_KEYWORDS.some(kw => 
                                (title + ' ' + description).toLowerCase().includes(kw)
                            )
                        };
                    }).filter(deal => 
                        deal.title && 
                        deal.originalPrice > 0 && 
                        deal.discountedPrice > 0 && 
                        deal.discountPercentage > 0
                    );
                }"""
                )

                browser.close()

                sustainable_deals = []
                for deal in deals_data:
                    if deal.get("isSustainable"):
                        sustainable_deals.append(deal)

                return {
                    "success": True,
                    "deals_found": len(deals_data),
                    "sustainable_deals": len(sustainable_deals),
                    "deal_data": sustainable_deals,
                }

        except Exception as e:
            logger.error(f"Error analyzing deals for shop {shop_id}: {e}")
            return {"error": str(e), "url": url}
