
from django.contrib import admin
from .models import Property, PropertyImage, PropertyVideo


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ('image',)
    show_change_link = True


class PropertyVideoInline(admin.StackedInline):
    model = PropertyVideo
    extra = 0
    max_num = 1
    fields = ('video',)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'property_type',
        'listing_type',
        'price',
        'city',
        'is_active',
    )

    list_filter = (
        'property_type',
        'listing_type',
        'city',
        'is_active',
    )

    search_fields = ('title', 'address', 'city')
    list_editable = ('is_active',)
    inlines = [PropertyImageInline, PropertyVideoInline]


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'id')
    list_select_related = ('property',)


@admin.register(PropertyVideo)
class PropertyVideoAdmin(admin.ModelAdmin):
    list_display = ('property', 'id')
    list_select_related = ('property',)
