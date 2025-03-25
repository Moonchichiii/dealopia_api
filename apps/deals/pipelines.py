from django.contrib.gis.geos import Point
from django.db import IntegrityError

from apps.deals.models import Deal


class DjangoWriterPipeline:
    """Pipeline for saving scraped deals to the database using Django ORM."""
    
    def process_item(self, item, spider):
        """
        Process each scraped item and save it to the database.
        
        Args:
            item: Scraped data dictionary
            spider: Spider instance that generated the item
            
        Returns:
            The processed item
        """
        try:
            # Create location Point object from coordinates
            location = Point(
                float(item['location']['lng']), 
                float(item['location']['lat'])
            )
            
            Deal.objects.update_or_create(
                shop_id=item['shop'],
                title=item['title'],
                defaults={
                    'original_price': item['original_price'],
                    'current_price': item['discounted_price'],
                    'expiration_date': item['expiration'],
                    'location': location,
                }
            )
        except IntegrityError as e:
            spider.logger.error(f"Database error: {e}")
        
        return item