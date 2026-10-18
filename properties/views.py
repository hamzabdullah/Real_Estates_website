from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Property, Favorite

PAGE_SIZE = 12

# Only the columns a property card needs (faster list pages)
CARD_FIELDS = (
    'id', 'title', 'image', 'listing_type', 'address', 'city',
    'price', 'bedrooms', 'bathrooms', 'area_sqft',
)


def home(request):
    properties = Property.objects.filter(
        is_active=True
    ).only(*CARD_FIELDS).order_by('-created_at')

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

    # Pagination: loads 12 cards at a time instead of every property
    paginator = Paginator(properties, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))
    page_properties = list(page_obj.object_list)

    # Keep the search/filter values when moving between pages
    params = request.GET.copy()
    params.pop('page', None)
    querystring = params.urlencode()

    favorite_ids = set()

    if request.user.is_authenticated and page_properties:
        favorite_ids = set(
            Favorite.objects.filter(
                user=request.user,
                property_id__in=[p.id for p in page_properties],
            ).values_list('property_id', flat=True)
        )

    return render(request, 'index.html', {
        'properties': page_properties,
        'page_obj': page_obj,
        'querystring': querystring,
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
        Property.objects.select_related(
            'property_video'
        ).prefetch_related('gallery_images'),
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
def favorites(request):
    saved = (
        Favorite.objects.filter(
            user=request.user,
            property__is_active=True,
        )
        .select_related('property')
        .order_by('-created_at')
    )

    properties = [item.property for item in saved]

    return render(request, 'favorites.html', {
        'properties': properties,
        'favorite_ids': {p.id for p in properties},
    })


@require_POST
def toggle_favorite(request, property_id):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    fallback_url = (
        reverse('property_detail', args=[property_id])
        if request.POST.get('source') == 'detail'
        else reverse('home')
    )

    next_url = request.POST.get('next', '')

    if not (
        next_url
        and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
    ):
        next_url = ''

    # Logged-out visitors: send them to login and bring them back to the
    # page they were on (not to the POST-only favorite URL).
    if not request.user.is_authenticated:
        login_url = redirect_to_login(next_url or fallback_url).url

        if is_ajax:
            return JsonResponse({'login_url': login_url}, status=401)

        return redirect(login_url)

    property = get_object_or_404(
        Property,
        id=property_id,
        is_active=True,
    )

    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        property=property,
    )

    if not created:
        favorite.delete()

    if is_ajax:
        return JsonResponse({
            'favorited': created,
            'count': Favorite.objects.filter(
                user=request.user,
                property__is_active=True,
            ).count(),
        })

    return redirect(next_url or fallback_url)
