# config/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.views.static import serve as static_serve
from django.conf import settings
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/submissions/', include('submissions.urls')),
    path('api/widgets/', include('widgets.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/auth/token/', TokenObtainPairView.as_view()),
    path('api/auth/token/refresh/', TokenRefreshView.as_view()),
    path('api/auth/', include('accounts.urls')),
    path('widget.js', static_serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'static', 'widget'),
        'path': 'widget.v1.js',
    }),
]