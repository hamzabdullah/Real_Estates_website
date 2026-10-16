from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Property, Favorite


def home(request):
    properties = Property.objects.filter(
        is_active=True
    ).order_by('-created_at')

    q = request.GET.get('q', '').strip()
    city = request.GET.get('city', '').strip()
    listing_type = request.GET.get('listing_type', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    bedrooms = request.GET.get('bedrooms', '').strip()

    # Main search: property title, city, or address
    if q:
        properties = properties.filter(
            Q(title__icontains=q)
            | Q(city__icontains=q)
            | Q(address__icontains=q)
        )

    # City filter
    if city:
        properties = properties.filter(city__icontains=city)

    # Sale or rent filter
    if listing_type in ('SALE', 'RENT'):
        properties = properties.filter(listing_type=listing_type)

    # Minimum price
    try:
        if min_price:
            properties = properties.filter(
                price__gte=Decimal(min_price)
            )
    except (InvalidOperation, ValueError):
        min_price = ''

    # Maximum price
    try:
        if max_price:
            properties = properties.filter(
                price__lte=Decimal(max_price)
            )
    except (InvalidOperation, ValueError):
        max_price = ''

    # Any non-negative whole number of bedrooms
    if bedrooms.isdigit():
        properties = properties.filter(
            bedrooms=int(bedrooms)
        )
    elif bedrooms:
        bedrooms = ''

    favorite_ids = set()

    if request.user.is_authenticated:
        favorite_ids = set(
            Favorite.objects.filter(
                user=request.user,
                property__is_active=True,
            ).values_list('property_id', flat=True)
        )

    return render(request, 'index.html', {
        'properties': properties,
        'q': q,
        'city': city,
        'listing_type': listing_type,
        'min_price': min_price,
        'max_price': max_price,
        'bedrooms': bedrooms,
        'favorite_ids': favorite_ids,
    })


def property_detail(request, property_id):
    property = get_object_or_404(
        Property,
        id=property_id,
        is_active=True,
    )

    is_favorite = (
        request.user.is_authenticated
        and Favorite.objects.filter(
            user=request.user,
            property=property,
        ).exists()
    )

    return render(request, 'property_detail.html', {
        'property': property,
        'is_favorite': is_favorite,
    })


@login_required
@require_POST
def toggle_favorite(request, property_id):
    property = get_object_or_404(
        Property,
        id=property_id,
        is_active=True,
    )

    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        property=property,
    )

    if created:
        messages.success(request, 'Property added to favorites.')
    else:
        favorite.delete()
        messages.success(request, 'Property removed from favorites.')

    fallback_url = (
        reverse('property_detail', args=[property.id])
        if request.POST.get('source') == 'detail'
        else reverse('home')
    )

    next_url = request.POST.get('next', '')

    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)

    return redirect(fallback_url)