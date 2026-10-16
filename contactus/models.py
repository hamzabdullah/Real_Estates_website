
from django.db import models


class ContactSettings(models.Model):
    email = models.EmailField(blank=True)
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Include country code, e.g. 14165551234. Do not include + or spaces.",
    )

    def __str__(self):
        return "Contact Settings"

    class Meta:
        verbose_name = "Contact Settings"
        verbose_name_plural = "Contact Settings"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()

    property_title = models.CharField(max_length=200, blank=True)
    property_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.subject} — {self.name}"

    class Meta:
        ordering = ["-created_at"]
