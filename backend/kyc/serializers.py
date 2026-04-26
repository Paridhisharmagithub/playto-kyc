from datetime import timedelta

from django.db.models import Avg, DurationField, ExpressionWrapper, F
from django.utils import timezone
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

from kyc.models import KYCSubmission
from kyc.state_machine import validate_transition


ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024


def validate_document(file_obj):
    extension = ""
    if "." in file_obj.name:
        extension = file_obj.name[file_obj.name.rfind(".") :].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise serializers.ValidationError("Only PDF, JPG, and PNG files are allowed.")
    if file_obj.size > MAX_UPLOAD_SIZE:
        raise serializers.ValidationError("File size must be 5 MB or less.")
    content_type = getattr(file_obj, "content_type", None)
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise serializers.ValidationError("Invalid file type. Allowed: PDF, JPG, PNG.")

    initial_position = file_obj.tell()
    file_obj.seek(0)
    header = file_obj.read(16)
    file_obj.seek(0)

    if extension == ".pdf":
        if not header.startswith(b"%PDF-"):
            raise serializers.ValidationError("Invalid PDF file contents.")
    else:
        try:
            image = Image.open(file_obj)
            if image.format not in {"JPEG", "PNG"}:
                raise serializers.ValidationError("Invalid image format. Use JPG or PNG.")
            image.verify()
        except (UnidentifiedImageError, OSError, ValueError):
            raise serializers.ValidationError("Uploaded image is corrupted or invalid.")
        finally:
            file_obj.seek(0)

    file_obj.seek(initial_position)
    return file_obj


class KYCSubmissionSerializer(serializers.ModelSerializer):
    pan_document = serializers.FileField(required=False, allow_null=True, validators=[validate_document])
    aadhaar_document = serializers.FileField(required=False, allow_null=True, validators=[validate_document])
    bank_statement_document = serializers.FileField(required=False, allow_null=True, validators=[validate_document])

    class Meta:
        model = KYCSubmission
        fields = (
            "id",
            "personal_name",
            "personal_email",
            "personal_phone",
            "business_name",
            "business_type",
            "expected_monthly_volume_usd",
            "pan_document",
            "aadhaar_document",
            "bank_statement_document",
            "state",
            "reviewer_reason",
            "created_at",
            "updated_at",
            "submitted_at",
        )
        read_only_fields = ("state", "reviewer_reason", "created_at", "updated_at", "submitted_at")


class ReviewerActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=("start_review", "approve", "reject", "request_more_info")
    )
    reason = serializers.CharField(required=False, allow_blank=True)


class ReviewerQueueItemSerializer(serializers.ModelSerializer):
    at_risk = serializers.SerializerMethodField()

    class Meta:
        model = KYCSubmission
        fields = ("id", "business_name", "personal_name", "state", "submitted_at", "at_risk")

    def get_at_risk(self, obj):
        if not obj.submitted_at:
            return False
        return timezone.now() - obj.submitted_at > timedelta(hours=24)


class ReviewerMetricsSerializer(serializers.Serializer):
    submissions_in_queue = serializers.IntegerField()
    avg_time_in_queue_seconds = serializers.FloatField()
    approval_rate_last_7_days = serializers.FloatField()


def build_reviewer_metrics():
    queue_states = [KYCSubmission.State.SUBMITTED, KYCSubmission.State.UNDER_REVIEW]
    queue_qs = KYCSubmission.objects.filter(state__in=queue_states, submitted_at__isnull=False)

    avg_duration_expr = ExpressionWrapper(
        timezone.now() - F("submitted_at"), output_field=DurationField()
    )
    avg_duration = queue_qs.annotate(duration=avg_duration_expr).aggregate(avg=Avg("duration"))["avg"]

    last_week_qs = KYCSubmission.objects.filter(reviewed_at__gte=timezone.now() - timedelta(days=7))
    reviewed_total = last_week_qs.filter(
        state__in=[KYCSubmission.State.APPROVED, KYCSubmission.State.REJECTED]
    ).count()
    approved_total = last_week_qs.filter(state=KYCSubmission.State.APPROVED).count()

    approval_rate = (approved_total / reviewed_total * 100) if reviewed_total else 0.0
    avg_seconds = avg_duration.total_seconds() if avg_duration else 0.0

    return {
        "submissions_in_queue": queue_qs.count(),
        "avg_time_in_queue_seconds": avg_seconds,
        "approval_rate_last_7_days": round(approval_rate, 2),
    }
