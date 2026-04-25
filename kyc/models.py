from django.conf import settings
from django.db import models


class KYCSubmission(models.Model):
    class State(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        MORE_INFO_REQUESTED = "more_info_requested", "More Info Requested"

    class BusinessType(models.TextChoices):
        FREELANCER = "freelancer", "Freelancer"
        AGENCY = "agency", "Agency"
        ECOMMERCE = "ecommerce", "Ecommerce"
        SAAS = "saas", "SaaS"
        OTHER = "other", "Other"

    merchant = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="kyc_submission"
    )
    personal_name = models.CharField(max_length=255, blank=True)
    personal_email = models.EmailField(blank=True)
    personal_phone = models.CharField(max_length=20, blank=True)
    business_name = models.CharField(max_length=255, blank=True)
    business_type = models.CharField(
        max_length=30, choices=BusinessType.choices, blank=True
    )
    expected_monthly_volume_usd = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    pan_document = models.FileField(upload_to="kyc_documents/", null=True, blank=True)
    aadhaar_document = models.FileField(upload_to="kyc_documents/", null=True, blank=True)
    bank_statement_document = models.FileField(
        upload_to="kyc_documents/", null=True, blank=True
    )
    state = models.CharField(max_length=30, choices=State.choices, default=State.DRAFT)
    reviewer_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_submissions",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    REQUIRED_SUBMISSION_FIELDS = (
        "personal_name",
        "personal_email",
        "personal_phone",
        "business_name",
        "business_type",
        "expected_monthly_volume_usd",
        "pan_document",
        "aadhaar_document",
        "bank_statement_document",
    )

    def __str__(self):
        return f"KYC<{self.id}> {self.merchant.username} {self.state}"

    def missing_required_fields(self):
        missing = []
        for field_name in self.REQUIRED_SUBMISSION_FIELDS:
            value = getattr(self, field_name, None)
            if value in (None, "", []):
                missing.append(field_name)
        return missing


class NotificationEvent(models.Model):
    merchant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification<{self.id}> {self.event_type}"
