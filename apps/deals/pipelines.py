from django.db import IntegrityError

class DjangoWriterPipeline:
    def process_item(self, item, spider):
        try:
            Deal.objects.update_or_create(
                shop_id=item['shop'],
                title=item['title'],
                defaults={
                    'original_price': item['original_price'],
                    'current_price': item['discounted_price'],
                    'expiration_date': item['expiration'],
                    'location': f"POINT({item['location']['lng']} {item['location']['lat']})"
                }
            )
        except IntegrityError as e:
            spider.logger.error(f"Database error: {e}")
        return item