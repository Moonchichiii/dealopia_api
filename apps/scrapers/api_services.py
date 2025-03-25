import json
import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.categories.models import Category
from apps.deals.models import Deal
from apps.shops.models import Shop
from core.utils.errors import ServiceError

logger = logging.getLogger('dealopia.api_integration')


class BaseAPIService:
    """Base class for API integrations"""
    
    API_NAME = "Base API"
    API_BASE_URL = None
    API_KEY_SETTING = None
    
    @classmethod
    def get_api_key(cls):
        """Get API key from settings"""
        if not cls.API_KEY_SETTING:
            raise ServiceError(f"API key setting not defined for {cls.API_NAME}")
        
        api_key = getattr(settings, cls.API_KEY_SETTING, None)
        if not api_key:
            raise ServiceError(f"API key not found in settings for {cls.API_NAME}")
        
        return api_key
    
    @classmethod
    def make_request(cls, endpoint, method='GET', params=None, data=None, headers=None):
        """Make a request to the API"""
        if not cls.API_BASE_URL:
            raise ServiceError(f"API base URL not defined for {cls.API_NAME}")
        
        url = f"{cls.API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        
        default_headers = {
            'Authorization': f"Bearer {cls.get_api_key()}",
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if headers:
            default_headers.update(headers)
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=default_headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, params=params, json=data, headers=default_headers, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, params=params, json=data, headers=default_headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, params=params, headers=default_headers, timeout=30)
            else:
                raise ServiceError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"{cls.API_NAME} HTTP error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"{cls.API_NAME} error details: {error_detail}")
                except:
                    logger.error(f"{cls.API_NAME} response text: {e.response.text}")
            raise ServiceError(f"{cls.API_NAME} HTTP error: {str(e)}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"{cls.API_NAME} request error: {e}")
            raise ServiceError(f"{cls.API_NAME} request error: {str(e)}")
            
        except json.JSONDecodeError:
            logger.error(f"{cls.API_NAME} JSON decode error: Invalid response format")
            raise ServiceError(f"{cls.API_NAME} response format error: Invalid JSON")
            
        except Exception as e:
            logger.exception(f"{cls.API_NAME} unexpected error: {e}")
            raise ServiceError(f"{cls.API_NAME} unexpected error: {str(e)}")


class GoodOnYouAPIService(BaseAPIService):
    """Integration with the Good On You ethical fashion API"""
    
    API_NAME = "Good On You"
    API_BASE_URL = "https://api.goodonyou.eco/api/v1"
    API_KEY_SETTING = "GOOD_ON_YOU_API_KEY"
    
    @classmethod
    def search_brands(cls, query, limit=20):
        """Search for sustainable fashion brands"""
        response = cls.make_request('/brands/search', params={
            'q': query,
            'limit': limit
        })
        
        return response.get('brands', [])
    
    @classmethod
    def get_brand_details(cls, brand_id):
        """Get detailed information about a specific brand"""
        return cls.make_request(f'/brands/{brand_id}')
    
    @classmethod
    def sync_sustainable_brands(cls, limit=100):
        """Sync sustainable brands with our database"""
        response = cls.make_request('/brands', params={
            'min_rating': 4,
            'limit': limit
        })
        
        brands = response.get('brands', [])
        
        created_count = 0
        updated_count = 0
        
        sustainable_category, _ = Category.objects.get_or_create(
            name__icontains='sustainable',
            defaults={
                'name': "Sustainable Fashion",
                'description': "Ethical and sustainable fashion brands and products",
                'icon': "leaf",
                'is_active': True
            }
        )
        
        with transaction.atomic():
            for brand_data in brands:
                brand_id = brand_data.get('id')
                
                try:
                    details = cls.get_brand_details(brand_id)
                except ServiceError:
                    continue
                
                shop, created = Shop.objects.update_or_create(
                    name=details.get('name'),
                    defaults={
                        'description': details.get('description', ''),
                        'short_description': f"Sustainability rating: {details.get('rating', 'N/A')}",
                        'website': details.get('website', ''),
                        'is_verified': True
                    }
                )
                
                shop.categories.add(sustainable_category)
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                
                if 'featured_products' in details and details['featured_products']:
                    for product in details['featured_products'][:5]:
                        if not product.get('price') or not product.get('sale_price'):
                            continue
                            
                        regular_price = float(product.get('price', 0))
                        sale_price = float(product.get('sale_price', 0))
                        
                        if sale_price >= regular_price:
                            continue
                        
                        discount_percentage = int(((regular_price - sale_price) / regular_price) * 100)
                        
                        Deal.objects.update_or_create(
                            shop=shop,
                            title=product.get('name', ''),
                            defaults={
                                'description': product.get('description', ''),
                                'original_price': regular_price,
                                'discounted_price': sale_price,
                                'discount_percentage': discount_percentage,
                                'image': product.get('image_url', ''),
                                'start_date': timezone.now(),
                                'end_date': timezone.now() + timedelta(days=30),
                                'redemption_link': product.get('url', ''),
                                'is_verified': True,
                                'is_exclusive': False
                            }
                        )
        
        return {
            'success': True,
            'shops_created': created_count,
            'shops_updated': updated_count,
            'total_processed': created_count + updated_count
        }


class HotUKDealsAPIService(BaseAPIService):
    """Integration with the HotUKDeals API"""
    
    API_NAME = "HotUKDeals"
    API_BASE_URL = "https://api.hotukdeals.com/rest"
    API_KEY_SETTING = "HOTUKDEALS_API_KEY"
    
    @classmethod
    def get_hot_deals(cls, limit=20, category=None):
        """Get hot deals from the API"""
        params = {'limit': limit}
        
        if category:
            params['category'] = category
            
        response = cls.make_request('/deals/hot', params=params)
        
        return response.get('deals', [])
    
    @classmethod
    def sync_uk_deals(cls, limit=100):
        """Sync deals from HotUKDeals with our database"""
        deals_data = cls.get_hot_deals(limit=limit)
        
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for deal_data in deals_data:
                if not deal_data.get('title') or not deal_data.get('merchant'):
                    continue
                
                shop_name = deal_data.get('merchant', {}).get('name', '')
                if not shop_name:
                    continue
                
                shop, _ = Shop.objects.get_or_create(
                    name=shop_name,
                    defaults={
                        'short_description': f"Deals from {shop_name}",
                        'website': deal_data.get('merchant', {}).get('website', ''),
                        'is_verified': True
                    }
                )
                
                try:
                    original_price = float(deal_data.get('price', {}).get('original', 0))
                    current_price = float(deal_data.get('price', {}).get('current', 0))
                except (ValueError, TypeError):
                    continue
                    
                if current_price <= 0 or current_price >= original_price:
                    continue
                
                discount_percentage = int(((original_price - current_price) / original_price) * 100)
                
                deal_categories = []
                if 'category' in deal_data:
                    category_name = deal_data['category'].get('name', '')
                    if category_name:
                        category = Category.objects.filter(name__icontains=category_name).first()
                        if category:
                            deal_categories.append(category)
                
                deal, created = Deal.objects.update_or_create(
                    shop=shop,
                    title=deal_data.get('title', ''),
                    defaults={
                        'description': deal_data.get('description', ''),
                        'original_price': original_price,
                        'discounted_price': current_price,
                        'discount_percentage': discount_percentage,
                        'image': deal_data.get('image', ''),
                        'start_date': timezone.now(),
                        'end_date': timezone.now() + timedelta(days=14),
                        'redemption_link': deal_data.get('url', ''),
                        'is_verified': True,
                        'is_exclusive': deal_data.get('exclusive', False)
                    }
                )
                
                if deal_categories:
                    deal.categories.add(*deal_categories)
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
        
        return {
            'success': True,
            'deals_created': created_count,
            'deals_updated': updated_count,
            'total_processed': created_count + updated_count
        }


class APIServiceFactory:
    """Factory for creating API service instances"""
    
    @staticmethod
    def get_service(service_name):
        """Get an API service by name"""
        services = {
            'good_on_you': GoodOnYouAPIService,
            'hotukdeals': HotUKDealsAPIService,
        }
        
        service = services.get(service_name.lower())
        if not service:
            raise ServiceError(f"Unknown API service: {service_name}")
            
        return service
