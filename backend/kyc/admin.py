from django.contrib import admin

from kyc.models import KYCSubmission, NotificationEvent

admin.site.register(KYCSubmission)
admin.site.register(NotificationEvent)
