from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from kyc.models import KYCSubmission
from kyc.permissions import IsMerchant, IsReviewer
from kyc.serializers import (
    KYCSubmissionSerializer,
    ReviewerActionSerializer,
    ReviewerMetricsSerializer,
    ReviewerQueueItemSerializer,
    build_reviewer_metrics,
)
from kyc.services import transition_submission


class MerchantSubmissionView(APIView):
    permission_classes = [IsMerchant]

    def get_submission(self, user):
        submission, _ = KYCSubmission.objects.get_or_create(merchant=user)
        return submission

    def get(self, request):
        submission = self.get_submission(request.user)
        return Response(KYCSubmissionSerializer(submission).data)

    def patch(self, request):
        submission = self.get_submission(request.user)
        serializer = KYCSubmissionSerializer(submission, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MerchantSubmitView(APIView):
    permission_classes = [IsMerchant]

    def post(self, request):
        submission, _ = KYCSubmission.objects.get_or_create(merchant=request.user)
        missing_fields = submission.missing_required_fields()
        if missing_fields:
            raise ValidationError(
                {
                    "code": "INCOMPLETE_SUBMISSION",
                    "message": "Fill all required fields before submitting.",
                    "missing_fields": missing_fields,
                }
            )
        submission = transition_submission(
            submission=submission,
            target_state=KYCSubmission.State.SUBMITTED,
            actor=request.user,
        )
        return Response(KYCSubmissionSerializer(submission).data)


class ReviewerQueueView(APIView):
    permission_classes = [IsReviewer]

    def get(self, request):
        queue = KYCSubmission.objects.filter(
            state__in=[KYCSubmission.State.SUBMITTED, KYCSubmission.State.UNDER_REVIEW]
        ).order_by("submitted_at", "created_at")
        return Response(ReviewerQueueItemSerializer(queue, many=True).data)


class ReviewerSubmissionDetailView(APIView):
    permission_classes = [IsReviewer]

    def get(self, request, submission_id):
        submission = get_object_or_404(KYCSubmission, id=submission_id)
        return Response(KYCSubmissionSerializer(submission).data)


class ReviewerActionView(APIView):
    permission_classes = [IsReviewer]
    ACTION_TO_STATE = {
        "start_review": KYCSubmission.State.UNDER_REVIEW,
        "approve": KYCSubmission.State.APPROVED,
        "reject": KYCSubmission.State.REJECTED,
        "request_more_info": KYCSubmission.State.MORE_INFO_REQUESTED,
    }

    def post(self, request, submission_id):
        submission = get_object_or_404(KYCSubmission, id=submission_id)
        serializer = ReviewerActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        target_state = self.ACTION_TO_STATE[action]
        reason = (serializer.validated_data.get("reason") or "").strip()
        if action in {"reject", "request_more_info"} and not reason:
            raise ValidationError(
                {"code": "REASON_REQUIRED", "message": "Reason is required for this action."}
            )

        submission = transition_submission(
            submission=submission,
            target_state=target_state,
            actor=request.user,
            reason=reason,
        )
        return Response(KYCSubmissionSerializer(submission).data, status=status.HTTP_200_OK)


class ReviewerMetricsView(APIView):
    permission_classes = [IsReviewer]

    def get(self, request):
        payload = build_reviewer_metrics()
        return Response(ReviewerMetricsSerializer(payload).data)
