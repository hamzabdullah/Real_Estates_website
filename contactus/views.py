
import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import ContactMessageForm
from .models import ContactMessage, ContactSettings
from properties.models import Property

logger = logging.getLogger(__name__)


def contact_view(request):
    contact_settings = ContactSettings.objects.first()

    property_id = (
        request.POST.get("property_id")
        if request.method == "POST"
        else request.GET.get("property_id")
    )

    selected_property = None

    if property_id:
        selected_property = Property.objects.filter(
            pk=property_id,
            is_active=True,
        ).first()

    property_url = ""
    if selected_property:
        property_url = request.build_absolute_uri(
            reverse(
                "property_detail",
                args=[selected_property.pk],
            )
        )

    if request.method == "POST":
        form = ContactMessageForm(request.POST)

        if form.is_valid():
            contact_message = form.save(commit=False)

            if selected_property:
                contact_message.property_title = (
                    selected_property.title
                )
                contact_message.property_url = property_url

            contact_message.save()

            recipient = getattr(
                settings,
                "CONTACT_RECIPIENT_EMAIL",
                "",
            )

            try:
                if not recipient:
                    raise ValueError(
                        "CONTACT_RECIPIENT_EMAIL is not configured."
                    )

                body = (
                    f"Name: {contact_message.name}\n"
                    f"Email: {contact_message.email}\n"
                    f"Subject: {contact_message.subject}\n"
                )

                if selected_property:
                    body += (
                        "\nPROPERTY DETAILS\n"
                        f"Property: {selected_property.title}\n"
                        f"Listing link: {property_url}\n"
                    )

                body += (
                    "\nMessage:\n"
                    f"{contact_message.message}\n"
                )

                email = EmailMessage(
                    subject=(
                        "Toronto Estates: "
                        f"{contact_message.subject}"
                    ),
                    body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient],
                    reply_to=[contact_message.email],
                   
                )

                email.send(fail_silently=False)

            except Exception:
                logger.exception(
                    "Contact notification email failed."
                )
                messages.warning(
                    request,
                    "Your message was saved, but its email "
                    "notification could not be sent.",
                )
            else:
                messages.success(
                    request,
                    "Your message was sent successfully!",
                )

            return redirect(reverse("contactus:contact"))

    else:
        initial = {}

        if selected_property:
            initial["subject"] = (
                f"Property inquiry: {selected_property.title}"
            )
            initial["message"] = (
                f"I am interested in {selected_property.title}.\n"
                f"Listing: {property_url}\n\n"
                "My question:\n"
            )

        form = ContactMessageForm(initial=initial)

    whatsapp_url = None

    if contact_settings and contact_settings.whatsapp_number:
        whatsapp_url = (
            "https://wa.me/"
            + contact_settings.whatsapp_number
        )

    return render(
        request,
        "contactus/contact.html",
        {
            "form": form,
            "contact_settings": contact_settings,
            "whatsapp_url": whatsapp_url,
            "selected_property": selected_property,
            "property_id": (
                selected_property.pk if selected_property else ""
            ),
        },
    )
