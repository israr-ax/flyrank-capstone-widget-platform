from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WidgetViewSet, WidgetConfigView

router = DefaultRouter()
router.register('', WidgetViewSet, basename='widget')

urlpatterns = [
    path('<uuid:widget_id>/config/', WidgetConfigView.as_view(), name='widget-config'),
    path('', include(router.urls)),
]