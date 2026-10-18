
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


from properties.views import (
    home,
    property_detail,
    toggle_favorite,
    favorites,
)
from properties.manage_views import (
    my_properties,
    add_property,
    edit_property,
    delete_property,
    toggle_property_active,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('contact/', include('contactus.urls')),
    path('', home, name='home'),

    path('favorites/', favorites, name='favorites'),

    # Property management for Admin / Agent users
    path('manage/', my_properties, name='my_properties'),
    path('manage/add/', add_property, name='add_property'),
    path('manage/<int:property_id>/edit/', edit_property, name='edit_property'),
    path('manage/<int:property_id>/delete/', delete_property, name='delete_property'),
    path(
        'manage/<int:property_id>/toggle/',
        toggle_property_active,
        name='toggle_property_active',
    ),

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
