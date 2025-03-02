from celery import shared_task
from playwright.sync_api import sync_playwright
from deals.models import Deal

@shared_task
def scrape_modern_shop(url):
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
            
            for deal in deals:
                Deal.objects.create(
                    title=deal['title'],
                    current_price=deal['price'],
                    image_url=deal['image'],
                    location=f"POINT({deal['coordinates']})"
                )
            
            browser.close()
            return len(deals)
        
        except Exception as e:
            browser.close()
            raise self.retry(exc=e, countdown=60)