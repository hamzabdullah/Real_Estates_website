
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator

class Property(models.Model):

    PROPERTY_TYPES = [
        ('HOUSE', 'House'),
        ('APARTMENT', 'Apartment'),
        ('CONDO', 'Condo'),
        ('LAND', 'Land'),
    ]

    LISTING_TYPES = [
        ('SALE', 'For Sale'),
        ('RENT', 'For Rent'),
    ]

    title = models.CharField(max_length=200)
    property_type = models.CharField(
        max_length=20,
        choices=PROPERTY_TYPES
    )
    listing_type = models.CharField(
        max_length=10,
        choices=LISTING_TYPES
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100, default='Toronto')
    bedrooms = models.PositiveIntegerField(default=0)
    bathrooms = models.PositiveIntegerField(default=0)
    area_sqft = models.PositiveIntegerField(default=0)
    description = models.TextField()
    image = models.ImageField(
        upload_to='properties/',
        blank=True,
        null=True
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='properties'
    )
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



class PropertyImage(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='gallery_images'
    )
    image = models.ImageField(upload_to='properties/gallery/')

    def __str__(self):
        return f"{self.property.title} - Image {self.pk}"



class PropertyVideo(models.Model):
    property = models.OneToOneField(
        Property,
        on_delete=models.CASCADE,
        related_name='property_video'
    )
    video = models.FileField(
        upload_to='properties/videos/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', 'webm', 'mov']
            )
        ]
    )

    def __str__(self):
        return f"{self.property.title} - Video"


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_properties',
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='favorited_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'property'],
                name='unique_user_favorite_property',
            ),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} - {self.property.title}'
