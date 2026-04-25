from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from kyc.models import KYCSubmission

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds default users and KYC submissions for demo"

    def handle(self, *args, **options):
        reviewer, _ = User.objects.get_or_create(
            username="reviewer1",
            defaults={"email": "reviewer1@example.com", "role": "reviewer"},
        )
        reviewer.set_password("password123")
        reviewer.save()

        merchant_draft, _ = User.objects.get_or_create(
            username="merchant_draft",
            defaults={"email": "merchant_draft@example.com", "role": "merchant"},
        )
        merchant_draft.set_password("password123")
        merchant_draft.save()

        merchant_review, _ = User.objects.get_or_create(
            username="merchant_review",
            defaults={"email": "merchant_review@example.com", "role": "merchant"},
        )
        merchant_review.set_password("password123")
        merchant_review.save()

        KYCSubmission.objects.update_or_create(
            merchant=merchant_draft,
            defaults={
                "state": KYCSubmission.State.DRAFT,
                "personal_name": "Draft Merchant",
                "personal_email": "merchant_draft@example.com",
                "personal_phone": "+919999000001",
                "business_name": "Draft Co",
                "business_type": KYCSubmission.BusinessType.FREELANCER,
                "expected_monthly_volume_usd": 1000,
            },
        )

        KYCSubmission.objects.update_or_create(
            merchant=merchant_review,
            defaults={
                "state": KYCSubmission.State.UNDER_REVIEW,
                "personal_name": "Review Merchant",
                "personal_email": "merchant_review@example.com",
                "personal_phone": "+919999000002",
                "business_name": "Review Co",
                "business_type": KYCSubmission.BusinessType.AGENCY,
                "expected_monthly_volume_usd": 5000,
                "submitted_at": timezone.now() - timedelta(hours=30),
                "reviewed_by": reviewer,
            },
        )

        self.stdout.write(self.style.SUCCESS("Seed data created successfully."))
