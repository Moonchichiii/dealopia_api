import logging
from django.db import transaction
from django.utils import timezone
from playwright.sync_api import sync_playwright

from apps.deals.models import Deal
from apps.shops.models import Shop

logger = logging.getLogger('dealopia.scrapers')


class ScraperService:
    """Service for scraper-related business logic, providing methods
    for web scraping and data processing."""
    
    @staticmethod
    def scrape_shop_deals(shop_id, scrape_all=False):
        """Scrape deals for a specific shop."""
        try:
            shop = Shop.objects.get(id=shop_id)
            
            if not shop.website:
                return {'success': False, 'error': 'Shop has no website defined'}
            
            domain = shop.website.split('//')[1].split('/')[0] if '//' in shop.website else shop.website
            
            if any(x in domain for x in ['dynamic', 'react', 'vue', 'angular']):
                return ScraperService._scrape_dynamic_shop(shop, scrape_all)
            else:
                return ScraperService._scrape_static_shop(shop, scrape_all)
                
        except Shop.DoesNotExist:
            return {'success': False, 'error': f'Shop with ID {shop_id} not found'}
        except Exception as e:
            logger.exception(f"Error scraping shop {shop_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _scrape_dynamic_shop(shop, scrape_all=False):
        """Scrape a dynamic JavaScript-heavy shop using Playwright."""
        deals_created = 0
        deals_updated = 0
        browser = None
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                page.goto(shop.website, timeout=60000)
                
                deal_selector = '.product-card, .deal-item, .discount-item'
                page.wait_for_selector(deal_selector, timeout=30000)
                
                deals = page.evaluate(f'''() => {{
                    return Array.from(document.querySelectorAll('{deal_selector}')).map(item => {{
                        const title = item.querySelector('h2, h3, .title')?.innerText || '';
                        
                        const originalPriceEl = item.querySelector('.original-price, .regular-price, .was-price, s, del');
                        const originalPrice = originalPriceEl ? 
                            parseFloat(originalPriceEl.innerText.replace(/[^0-9.]/g, '')) : 0;
                        
                        const discountedPriceEl = item.querySelector('.discounted-price, .sale-price, .now-price, .price:not(s):not(del)');
                        const discountedPrice = discountedPriceEl ? 
                            parseFloat(discountedPriceEl.innerText.replace(/[^0-9.]/g, '')) : 0;
                        
                        const discountEl = item.querySelector('.discount, .save, .percent-off');
                        const discountText = discountEl ? discountEl.innerText : '';
                        const discountMatch = discountText.match(/([0-9]+)%/);
                        const discountPercentage = discountMatch ? parseInt(discountMatch[1]) : 
                            (originalPrice && discountedPrice ? Math.round((originalPrice - discountedPrice) / originalPrice * 100) : 0);
                        
                        const imageEl = item.querySelector('img');
                        const imageUrl = imageEl ? (imageEl.src || imageEl.dataset.src) : '';
                        
                        const linkEl = item.closest('a') || item.querySelector('a');
                        const productUrl = linkEl ? linkEl.href : '';
                        
                        const descriptionEl = item.querySelector('.description, .details, .summary');
                        const description = descriptionEl ? descriptionEl.innerText : '';
                        
                        return {{
                            title,
                            originalPrice,
                            discountedPrice,
                            discountPercentage,
                            imageUrl,
                            productUrl,
                            description
                        }};
                    }});
                }}''')
                
                browser.close()
                browser = None
                
                # Prefetch shop categories to avoid multiple queries
                shop_categories = list(shop.categories.all())
                
                with transaction.atomic():
                    for deal_data in deals:
                        if not deal_data['title'] or deal_data['discountedPrice'] >= deal_data['originalPrice']:
                            continue
                        
                        end_date = timezone.now() + timezone.timedelta(days=30)
                        
                        image_url = deal_data['imageUrl']
                        if image_url and not image_url.startswith(('http://', 'https://')):
                            image_url = f"{shop.website.rstrip('/')}/{image_url.lstrip('/')}"
                            
                        product_url = deal_data['productUrl']
                        if product_url and not product_url.startswith(('http://', 'https://')):
                            product_url = f"{shop.website.rstrip('/')}/{product_url.lstrip('/')}"
                        
                        existing_deal = Deal.objects.filter(
                            shop=shop,
                            title=deal_data['title']
                        ).first()
                        
                        if existing_deal:
                            existing_deal.original_price = deal_data['originalPrice']
                            existing_deal.discounted_price = deal_data['discountedPrice']
                            existing_deal.discount_percentage = deal_data['discountPercentage']
                            existing_deal.redemption_link = product_url
                            existing_deal.end_date = end_date
                            existing_deal.is_verified = True
                            
                            if image_url:
                                existing_deal.image = image_url
                                
                            existing_deal.save()
                            deals_updated += 1
                        else:
                            new_deal = Deal.objects.create(
                                shop=shop,
                                title=deal_data['title'],
                                description=deal_data['description'],
                                original_price=deal_data['originalPrice'],
                                discounted_price=deal_data['discountedPrice'],
                                discount_percentage=deal_data['discountPercentage'],
                                image=image_url,
                                start_date=timezone.now(),
                                end_date=end_date,
                                redemption_link=product_url,
                                is_verified=True
                            )
                            
                            if shop_categories:
                                new_deal.categories.add(*shop_categories)
                            
                            deals_created += 1
            
            return {
                'success': True, 
                'deals_created': deals_created,
                'deals_updated': deals_updated,
                'total_processed': deals_created + deals_updated
            }
                
        except Exception as e:
            if browser:
                browser.close()
            logger.exception(f"Error in dynamic scraping for shop {shop.id}: {str(e)}")
            return {'success': False, 'error': str(e)}
