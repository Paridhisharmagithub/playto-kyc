from django.urls import path

from kyc.views import (
    MerchantSubmissionView,
    MerchantSubmitView,
    ReviewerActionView,
    ReviewerMetricsView,
    ReviewerQueueView,
    ReviewerSubmissionDetailView,
)

urlpatterns = [
    path("merchant/submission/", MerchantSubmissionView.as_view(), name="merchant-submission"),
    path("merchant/submission/submit/", MerchantSubmitView.as_view(), name="merchant-submit"),
    path("reviewer/queue/", ReviewerQueueView.as_view(), name="reviewer-queue"),
    path("reviewer/metrics/", ReviewerMetricsView.as_view(), name="reviewer-metrics"),
    path(
        "reviewer/submissions/<int:submission_id>/",
        ReviewerSubmissionDetailView.as_view(),
        name="reviewer-submission-detail",
    ),
    path(
        "reviewer/submissions/<int:submission_id>/action/",
        ReviewerActionView.as_view(),
        name="reviewer-action",
    ),
]
