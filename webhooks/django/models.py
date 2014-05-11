# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from jsonfield.fields import JSONField
from model_utils.models import TimeStampedModel

CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_FORM = "application/x-www-form-urlencoded"


def event_choices():
    WEBHOOK_EVENTS = getattr(settings, "WEBHOOK_EVENTS", None)
    if WEBHOOK_EVENTS is None:
        msg = "Please add some webhook events."
        raise ImproperlyConfigured(msg)
    try:
        choices = [(x['name'], x['name']) for x in settings.WEBHOOK_EVENTS]
    except KeyError as e:
        msg = "Your settings.WEBHOOK_EVENTS is improperly configured"
        raise ImproperlyConfigured(e)
    except Exception as e:
        raise ImproperlyConfigured(e)

    return choices


@python_2_unicode_compatible
class Webhook(TimeStampedModel):
    """ I would prefer the name 'target', but I worry it's confusing. """

    CONTENT_TYPE_JSON = CONTENT_TYPE_JSON
    CONTENT_TYPE_FORM = CONTENT_TYPE_FORM
    CONTENT_TYPE_CHOICES = (
        (CONTENT_TYPE_JSON, CONTENT_TYPE_JSON),
        (CONTENT_TYPE_FORM, CONTENT_TYPE_FORM)
    )

    WEBHOOK_EVENTS = event_choices()

    # TODO - add Webhook event choices as indivial attributes to this model, instantiated or not

    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='webhooks')
    event = models.CharField(max_length=255, choices=event_choices())

    url = models.URLField(max_length=255)

    header_content_type = models.CharField("Header content-type",
                max_length=255, choices=CONTENT_TYPE_CHOICES)

    last_attempt = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "{}:{}".format(
            self.user.username,
            self.url[:30]
        )

    class Meta:
        ordering = ["-modified"]
        get_latest_by = "modified"


# Possibly replace with redis or something else better for writes
@python_2_unicode_compatible
class Delivery(TimeStampedModel):

    webhook = models.ForeignKey("webhooks.Webhook")

    payload = JSONField()

    success = models.BooleanField(default=False)
    attempt = models.IntegerField("How many times has this been attempted to be delivered")

    # response info
    response_message = models.TextField("Whatever is sent back", blank=True)
    response_status = models.IntegerField("HTTP status code", blank=True, null=True)
    response_content_type = models.CharField(max_length=255, blank=True, null=True)

    # TODO - add rest of recorded header infos

    def __str__(self):
        return "{}:{}".format(
            self.pk,
            self.webhook
        )

    class Meta:
        ordering = ["-created"]
        get_latest_by = "created"