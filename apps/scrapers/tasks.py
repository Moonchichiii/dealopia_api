from celery import shared_task
from deals.models import Deal
from playwright.sync_api import sync_playwright


@shared_task(bind=True, max_retries=3)
def scrape_modern_shop(self, url):
    """
    Scrape deal information from a modern shop website.
    
    Creates Deal objects from scraped data including title, price, image URL,
    and geographic coordinates.
    
    Args:
        url (str): The website URL to scrape
        
    Returns:
        int: Number of deals scraped
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        try:
            page.goto(url, timeout=60000)
            page.wait_for_selector('.dynamic-deals', timeout=30000)
            
            deals = page.evaluate('''() => {
                return Array.from(document.querySelectorAll('.dynamic-deals .item'))
                    .map(item => ({
                        title: item.querySelector('h3').innerText,
                        price: item.dataset.price,
                        image: item.querySelector('img').src,
                        coordinates: item.closest('[data-coords]').dataset.coords
                    }))
            }''')
            
            # Use bulk_create for better performance
            Deal.objects.bulk_create([
                Deal(
                    title=deal['title'],
                    current_price=deal['price'],
                    image_url=deal['image'],
                    location=f"POINT({deal['coordinates']})"
                ) for deal in deals
            ])
            
            return len(deals)
        
        except Exception as e:
            # Proper retry with bound task
            self.retry(exc=e, countdown=60)
        finally:
            browser.close()