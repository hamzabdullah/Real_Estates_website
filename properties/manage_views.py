from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PropertyForm
from .models import Property, PropertyImage, PropertyVideo

MANAGER_ROLES = ('ADMIN', 'AGENT')


def can_manage_properties(user):
    """Only superusers and users with the Admin or Agent role."""
    return user.is_authenticated and (
        user.is_superuser or getattr(user, 'role', None) in MANAGER_ROLES
    )


def sees_all_properties(user):
    """Admins see every listing; agents only see their own."""
    return user.is_superuser or getattr(user, 'role', None) == 'ADMIN'


def manager_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        if not can_manage_properties(request.user):
            raise PermissionDenied

        return view(request, *args, **kwargs)

    return wrapper


def managed_properties(user):
    queryset = Property.objects.all()

    if not sees_all_properties(user):
        queryset = queryset.filter(agent=user)

    return queryset


@manager_required
def my_properties(request):
    properties = (
        managed_properties(request.user)
        .annotate(saved_count=Count('favorited_by'))
        .order_by('-created_at')
    )

    return render(request, 'manage/my_properties.html', {
        'properties': properties,
        'show_agent': sees_all_properties(request.user),
    })


def _save_media(form, prop):
    """Saves video and extra photos after the property itself is saved."""
    video = form.cleaned_data.get('video')

    if form.cleaned_data.get('remove_video'):
        PropertyVideo.objects.filter(property=prop).delete()

    if video:
        PropertyVideo.objects.update_or_create(
            property=prop,
            defaults={'video': video},
        )

    for photo in form.cleaned_data.get('gallery') or []:
        PropertyImage.objects.create(property=prop, image=photo)


@manager_required
def add_property(request):
    form = PropertyForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            prop = form.save(commit=False)
            prop.agent = request.user
            prop.save()
            _save_media(form, prop)

        messages.success(request, f'"{prop.title}" was added successfully.')
        return redirect('my_properties')

    return render(request, 'manage/property_form.html', {
        'form': form,
        'is_edit': False,
    })


@manager_required
def edit_property(request, property_id):
    prop = get_object_or_404(
        managed_properties(request.user).prefetch_related('gallery_images'),
        pk=property_id,
    )

    form = PropertyForm(
        request.POST or None,
        request.FILES or None,
        instance=prop,
    )

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            prop = form.save()

            # Photos the user ticked "remove" on
            remove_ids = [
                value for value in request.POST.getlist('remove_images')
                if value.isdigit()
            ]

            if remove_ids:
                PropertyImage.objects.filter(
                    property=prop,
                    pk__in=remove_ids,
                ).delete()

            _save_media(form, prop)

        messages.success(request, f'"{prop.title}" was updated.')
        return redirect('my_properties')

    return render(request, 'manage/property_form.html', {
        'form': form,
        'is_edit': True,
        'property': prop,
        'gallery_images': prop.gallery_images.all(),
    })


@manager_required
@require_POST
def delete_property(request, property_id):
    prop = get_object_or_404(
        managed_properties(request.user),
        pk=property_id,
    )

    title = prop.title
    prop.delete()

    messages.success(request, f'"{title}" was deleted.')
    return redirect('my_properties')


@manager_required
@require_POST
def toggle_property_active(request, property_id):
    prop = get_object_or_404(
        managed_properties(request.user),
        pk=property_id,
    )

    prop.is_active = not prop.is_active
    prop.save(update_fields=['is_active'])

    state = 'visible on the website' if prop.is_active else 'hidden from the website'
    messages.success(request, f'"{prop.title}" is now {state}.')
    return redirect('my_properties')
