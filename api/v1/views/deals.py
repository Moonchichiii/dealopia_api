from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from backend.apps.deals.models import Deal
from backend.api.v1.serializers.deals import DealSerializer

class DealViewSet(viewsets.ModelViewSet):
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['shop', 'categories', 'is_featured', 'is_exclusive']
    search_fields = ['title', 'description', 'shop__name']
    ordering_fields = ['created_at', 'discount_percentage', 'end_date']
    ordering = ['-created_at']
    
    @action(detail=False)
    def featured(self, request):
        featured_deals = Deal.objects.filter(is_featured=True)
        serializer = self.get_serializer(featured_deals, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def ending_soon(self, request):
        from django.utils import timezone
        import datetime
        
        end_date = timezone.now() + datetime.timedelta(days=3)
        ending_deals = Deal.objects.filter(end_date__lte=end_date).order_by('end_date')
        serializer = self.get_serializer(ending_deals, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def track_view(self, request, pk=None):
        deal = self.get_object()
        deal.views_count += 1
        deal.save()
        return Response({'status': 'view tracked'})
    
    @action(detail=True, methods=['post'])
    def track_click(self, request, pk=None):
        deal = self.get_object()
        deal.clicks_count += 1
        deal.save()
        return Response({'status': 'click tracked'})
