import os
from io import BytesIO

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import FileExtensionValidator
from PIL import Image, ImageOps

from .models import Property

MAX_IMAGE_UPLOAD_MB = 15      # raw upload size limit per photo
MAX_VIDEO_UPLOAD_MB = 100
MAX_GALLERY_PER_UPLOAD = 12
MAX_IMAGE_SIDE = 1600         # photos are shrunk to this size (px)


def optimize_image(upload, max_side=MAX_IMAGE_SIDE, quality=82):
    """
    Shrinks and compresses an uploaded photo so pages load fast on
    slow internet. Returns a new JPEG file.
    """
    if upload.size > MAX_IMAGE_UPLOAD_MB * 1024 * 1024:
        raise ValidationError(
            f'Each photo must be smaller than {MAX_IMAGE_UPLOAD_MB} MB.'
        )

    try:
        image = Image.open(upload)
        image = ImageOps.exif_transpose(image)
    except Exception:
        raise ValidationError('This file is not a valid image.')

    if image.mode in ('RGBA', 'LA', 'P'):
        image = image.convert('RGBA')
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    else:
        image = image.convert('RGB')

    image.thumbnail((max_side, max_side), Image.LANCZOS)

    buffer = BytesIO()
    image.save(buffer, 'JPEG', quality=quality, optimize=True, progressive=True)

    base_name = os.path.splitext(os.path.basename(upload.name))[0][:60] or 'photo'
    return ContentFile(buffer.getvalue(), name=f'{base_name}.jpg')


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    """An image field that accepts many files at once."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean

        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data if item]

        return [single_clean(data, initial)] if data else []


class PropertyForm(forms.ModelForm):
    image = forms.ImageField(
        required=False,
        label='Main photo',
        widget=forms.FileInput(attrs={'accept': 'image/*'}),
        help_text='This is the photo shown on the home page.',
    )

    gallery = MultipleImageField(
        required=False,
        label='More photos',
        widget=MultipleFileInput(attrs={'accept': 'image/*'}),
        help_text=f'You can select up to {MAX_GALLERY_PER_UPLOAD} photos at once.',
    )

    video = forms.FileField(
        required=False,
        label='Video (optional)',
        widget=forms.FileInput(attrs={'accept': 'video/mp4,video/webm,video/quicktime'}),
        validators=[FileExtensionValidator(['mp4', 'webm', 'mov'])],
        help_text='MP4, WebM or MOV, up to 100 MB.',
    )

    remove_video = forms.BooleanField(required=False, label='Remove current video')

    class Meta:
        model = Property
        fields = [
            'title', 'property_type', 'listing_type', 'price',
            'address', 'city', 'bedrooms', 'bathrooms', 'area_sqft',
            'description', 'is_active',
        ]
        labels = {
            'title': 'Property title',
            'property_type': 'Property type',
            'listing_type': 'For sale or rent',
            'price': 'Price (CA$)',
            'area_sqft': 'Area (sqft)',
            'is_active': 'Show this property on the website',
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Modern 3 bedroom house'}),
            'price': forms.NumberInput(attrs={'min': 0, 'step': '1', 'placeholder': 'e.g. 850000'}),
            'address': forms.TextInput(attrs={'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'placeholder': 'Toronto'}),
            'bedrooms': forms.NumberInput(attrs={'min': 0}),
            'bathrooms': forms.NumberInput(attrs={'min': 0}),
            'area_sqft': forms.NumberInput(attrs={'min': 0}),
            'description': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Describe the property: rooms, location, features...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # A new listing needs a main photo; when editing it is optional.
        if not self.instance.pk:
            self.fields['image'].required = True

    def clean_price(self):
        price = self.cleaned_data['price']

        if price <= 0:
            raise ValidationError('Price must be greater than zero.')

        return price

    def clean_title(self):
        return self.cleaned_data['title'].strip()

    def clean_image(self):
        image = self.cleaned_data.get('image')

        # Only process a newly uploaded file (not the existing one).
        if isinstance(image, UploadedFile):
            return optimize_image(image)

        return image

    def clean_gallery(self):
        files = self.cleaned_data.get('gallery') or []

        if len(files) > MAX_GALLERY_PER_UPLOAD:
            raise ValidationError(
                f'Please upload at most {MAX_GALLERY_PER_UPLOAD} photos at a time.'
            )

        return [optimize_image(item) for item in files]

    def clean_video(self):
        video = self.cleaned_data.get('video')

        if isinstance(video, UploadedFile):
            if video.size > MAX_VIDEO_UPLOAD_MB * 1024 * 1024:
                raise ValidationError(
                    f'The video must be smaller than {MAX_VIDEO_UPLOAD_MB} MB.'
                )

        return video
