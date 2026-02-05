from django.contrib.gis.geos import Point
from django.db import IntegrityError

from apps.deals.models import Deal


class DjangoWriterPipeline:
    def process_item(self, item, spider):
        try:
            location = Point(
                float(item["location"]["lng"]), float(item["location"]["lat"])
            )

            Deal.objects.update_or_create(
                shop_id=item["shop"],
                title=item["title"],
                defaults={
                    "original_price": item["original_price"],
                    "discounted_price": item["discounted_price"],
                    "end_date": item["expiration"],
                },
            )
        except IntegrityError as e:
            spider.logger.error(f"Database error: {e}")

        return item
