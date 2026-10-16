
from django.contrib import admin
from .models import ContactSettings, ContactMessage


@admin.register(ContactSettings)
class ContactSettingsAdmin(admin.ModelAdmin):
    list_display = ("email", "whatsapp_number")

    def has_add_permission(self, request):
        # Only one contact settings record is needed.
        return not ContactSettings.objects.exists()


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "subject",
        "property_title",
        "is_read",
        "created_at",
    )

    list_filter = ("is_read", "created_at")
    search_fields = (
        "name",
        "email",
        "subject",
        "message",
        "property_title",
    )
    readonly_fields = ("created_at", "property_url")
    list_editable = ("is_read",)
    fieldsets = (
        ("Contact Details", {
            "fields": ("name", "email", "subject", "message"),
        }),
        ("Property Details", {
            "fields": ("property_title", "property_url"),
        }),
        ("Status", {
            "fields": ("is_read", "created_at"),
        }),
    )
