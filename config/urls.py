
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from properties.views import home, property_detail, toggle_favorite

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),

    path('', home, name='home'),

    path(
        'property/<int:property_id>/favorite/',
        toggle_favorite,
        name='toggle_favorite',
    ),

    path(
        'property/<int:property_id>/',
        property_detail,
        name='property_detail',
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
