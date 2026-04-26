from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from kyc.models import KYCSubmission

User = get_user_model()


class KYCStateMachineAPITests(APITestCase):
    def setUp(self):
        self.reviewer = User.objects.create_user(
            username="reviewer_test",
            email="reviewer_test@example.com",
            password="password123",
            role="reviewer",
        )
        token = Token.objects.create(user=self.reviewer)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        merchant = User.objects.create_user(
            username="merchant_test",
            email="merchant_test@example.com",
            password="password123",
            role="merchant",
        )
        self.submission = KYCSubmission.objects.create(
            merchant=merchant,
            state=KYCSubmission.State.SUBMITTED,
            personal_name="Merchant Test",
            personal_email="merchant_test@example.com",
            personal_phone="+919999111111",
            business_name="Merchant Test Co",
            business_type=KYCSubmission.BusinessType.FREELANCER,
            expected_monthly_volume_usd=1000,
        )

    def test_illegal_transition_submitted_to_approved_returns_400(self):
        url = reverse("reviewer-action", kwargs={"submission_id": self.submission.id})
        response = self.client.post(url, {"action": "approve"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["details"]["message"], "Cannot move submitted to approved.")

    def test_approve_already_approved_submission_returns_helpful_400(self):
        self.submission.state = KYCSubmission.State.APPROVED
        self.submission.save(update_fields=["state"])

        url = reverse("reviewer-action", kwargs={"submission_id": self.submission.id})
        response = self.client.post(url, {"action": "approve"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"]["details"]["message"],
            "Submission is already approved.",
        )

    def test_reject_without_reason_returns_400(self):
        self.submission.state = KYCSubmission.State.UNDER_REVIEW
        self.submission.save(update_fields=["state"])

        url = reverse("reviewer-action", kwargs={"submission_id": self.submission.id})
        response = self.client.post(url, {"action": "reject", "reason": ""}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"]["details"]["message"],
            "Reason is required for this action.",
        )

    def test_merchant_upload_rejects_invalid_file_type(self):
        merchant_token = Token.objects.create(user=self.submission.merchant)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {merchant_token.key}")

        url = reverse("merchant-submission")
        invalid_file = SimpleUploadedFile(
            "malicious.exe", b"not-a-valid-doc", content_type="application/octet-stream"
        )
        response = self.client.patch(url, {"pan_document": invalid_file}, format="multipart")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"]["details"]["pan_document"][0],
            "Only PDF, JPG, and PNG files are allowed.",
        )

    def test_queue_item_at_risk_flag_after_24_hours(self):
        self.submission.state = KYCSubmission.State.SUBMITTED
        self.submission.submitted_at = timezone.now() - timedelta(hours=30)
        self.submission.save(update_fields=["state", "submitted_at"])

        url = reverse("reviewer-queue")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) > 0)
        self.assertTrue(response.data[0]["at_risk"])
